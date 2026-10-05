from __future__ import annotations

import json
import os
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from io import BytesIO
from PIL import Image

from aegis.evaluate import run_benchmark
from aegis.system import PROJECT_DIR, _grounded_fallback_answer, _search, answer_question, choose_rule, ensure_index, load_catalog, resolve_entities, validate_knowledge
from aegis.web import Handler


class AegisSystemTests(unittest.TestCase):
    def test_knowledge_and_corpus_validate(self):
        self.assertEqual(validate_knowledge(), [])
        report = ensure_index()
        self.assertEqual(report["dataset_file_count"], 20)
        self.assertEqual(report["segment_count"], 121)
        self.assertEqual(report["warnings"], [])

    def test_full_curated_benchmark(self):
        metrics = run_benchmark(write_reports=False)["metrics"]
        self.assertEqual(metrics["questions_total"], 23)
        self.assertEqual(metrics["questions_correct"], 23)
        self.assertEqual(metrics["answerable_questions_correct"], 18)
        self.assertEqual(metrics["unanswerable_abstentions_correct"], 5)
        self.assertEqual(metrics["citation_completeness"], 1.0)

    def test_revision_scoped_pressure(self):
        response = answer_question("What is the normal HPU pressure now and before revision 3.2?")
        self.assertEqual(response["status"], "answered")
        self.assertEqual(response["route_id"], "normal_pressure")
        self.assertEqual({claim["id"] for claim in response["claims"]}, {"f.pressure.current", "f.pressure.legacy"})
        self.assertIn("200 bar", response["answer"])
        self.assertIn("180 bar", response["answer"])

    def test_entity_aliases_do_not_merge_distinct_sensors(self):
        resolved = resolve_entities("Is PS-04 the same as PS-04A?")
        self.assertEqual({item["canonical_id"] for item in resolved}, {"PS-04", "PS-04A"})
        response = answer_question("What tag appears on the diagnostics screen and which component does it match?")
        self.assertEqual(response["route_id"], "diagnostics_tag")
        self.assertEqual(response["claims"][0]["value"], "P.S.04-A")
        self.assertTrue(any(item["canonical_id"] == "PS-04A" for item in response["resolved_entities"]))
        self.assertTrue(any(item["extraction_method"] == "human_transcription" for item in response["evidence"]))

    def test_unknown_temperature_is_explicitly_abstained(self):
        response = answer_question("What is the maximum operating temperature for PS-04A?")
        self.assertEqual(response["status"], "abstained")
        self.assertEqual(response["route_id"], "sensor_temperature")
        self.assertIsNone(response["claims"][0]["value"])
        self.assertTrue(response["evidence"])

    def test_citations_refer_to_existing_sources_and_locators(self):
        response = answer_question("What does alarm A17 indicate, and what are its possible causes?")
        self.assertEqual(response["status"], "answered")
        self.assertTrue(response["evidence"])
        for citation in response["evidence"]:
            self.assertTrue((PROJECT_DIR.parent / citation["source"]).is_file())
            self.assertTrue(citation["locator"])
            self.assertTrue(citation["quote"])
            self.assertTrue(citation["extraction_method"])

    def test_unmatched_question_returns_retrieval_without_claims(self):
        response = answer_question("What is the documented bearing material for pump Z-999?")
        self.assertEqual(response["status"], "insufficient_evidence")
        self.assertEqual(response["route_id"], "fallback_search")
        self.assertEqual(response["claims"], [])

    def test_field_observation_does_not_match_normal_pressure_rule(self):
        _facts, rules = load_catalog()
        self.assertIsNone(choose_rule("Can the field note's roughly 175 bar reading be treated as the controlled normal setpoint?", rules))

    def test_retrieval_prioritizes_exact_firmware_revision_and_wiring_diagram(self):
        revision = _search("What does the supplied revision history say about software 3.3, and does the package show a released change?")
        self.assertEqual(revision[0]["locator"], "Sheet Revision History, row 6, cells A6:D6")
        wiring = _search("In the wiring diagram, what devices are associated with TB-7's J-14 and J-15 branches?")
        self.assertEqual(Path(wiring[0]["source_path"]).name, "wiring_diagram.pdf")

    def test_grounded_fallback_accepts_answer_only_with_valid_citation(self):
        completion_result = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
            "status": "answered", "answer": "J-14 is the pressure transducer and J-15 is the IV-21 solenoid.", "citation_ids": [1]
        })))])
        passages = [{"source_path": "dataset/wiring_diagram.pdf", "locator": "p. 1", "text": "J-14 PRESSURE XDCR; J-15 IV-21 SOLENOID"}]
        fake_litellm = SimpleNamespace(completion=lambda **_kwargs: completion_result)
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}), patch.dict(sys.modules, {"litellm": fake_litellm}):
            generated = _grounded_fallback_answer("What is wired at J-14 and J-15?", {}, passages)
        self.assertEqual(generated["status"], "answered")
        self.assertEqual(len(generated["evidence"]), 1)
        self.assertEqual(generated["evidence"][0]["source"], "dataset/wiring_diagram.pdf")

    def test_fallback_citation_shape_is_ready_for_web_client_without_ai(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
            response = answer_question("How is the HPU referred to in the terminology glossary?")
        self.assertEqual(response["route_id"], "fallback_search")
        self.assertTrue(response["evidence"])
        self.assertTrue(all(item.get("source") and item.get("quote") for item in response["evidence"]))

    def test_local_http_health_and_answer_endpoints(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(base + "/", timeout=10) as result:
                self.assertIn("img-src 'self'", result.headers["Content-Security-Policy"])
            with urlopen(base + "/health", timeout=10) as result:
                health = json.loads(result.read())
                self.assertEqual(result.status, 200)
                self.assertEqual(result.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual((health["indexed_files"], health["segments"]), (20, 121))
            with urlopen(base + "/source/aegis-dataset/aegis-dataset/manuals/operator_manual.pdf", timeout=10) as result:
                self.assertEqual(result.status, 200)
                self.assertEqual(result.headers["Content-Type"], "application/pdf")
                self.assertTrue(result.headers["Content-Disposition"].startswith("inline"))
                self.assertTrue(result.read(5).startswith(b"%PDF"))
            with urlopen(base + "/source/aegis-dataset/aegis-dataset/screenshots/screen_03_diagnostics.png", timeout=10) as result:
                self.assertEqual(result.status, 200)
                self.assertEqual(result.headers["Content-Type"], "image/png")
                self.assertTrue(result.headers["Content-Disposition"].startswith("inline"))
                self.assertEqual(result.read(8), b"\x89PNG\r\n\x1a\n")
            with urlopen(base + "/source-view/aegis-dataset/aegis-dataset/manuals/legacy_manual_v1.html", timeout=10) as result:
                self.assertEqual(result.status, 200)
                self.assertIn("text/html", result.headers["Content-Type"])
                self.assertIn("Content-Security-Policy", result.headers)
            with urlopen(base + "/source-view/aegis-dataset/aegis-dataset/reference/component_register.xlsx?" + urlencode({"quote": "PS-04A | Pressure Sensor 04A | P04A; PS04A", "locator": "Components!A5:F5"}), timeout=10) as result:
                self.assertEqual(result.status, 200)
                self.assertIn("text/html", result.headers["Content-Type"])
                self.assertIn(b"<mark>PS-04A</mark>", result.read())
            preview_query = urlencode({"page": 1, "quote": "This is the normal operating pressure for software revision 3.2 and later."})
            with urlopen(base + "/source-preview/aegis-dataset/aegis-dataset/manuals/operator_manual.pdf?" + preview_query, timeout=20) as result:
                self.assertEqual(result.status, 200)
                self.assertEqual(result.headers["Content-Type"], "image/png")
                preview = result.read()
                self.assertEqual(preview[:8], b"\x89PNG\r\n\x1a\n")
            pixels = Image.open(BytesIO(preview)).convert("RGB").tobytes()
            # The citation overlay should be present but translucent enough to
            # keep the document text readable beneath it.
            self.assertTrue(any(pixels[i] > pixels[i + 1] + 3 and pixels[i + 1] > 200 and 160 < pixels[i + 2] < 240 for i in range(0, len(pixels), 3)))
            with self.assertRaises(Exception):
                urlopen(base + "/source/aegis-dataset/aegis-dataset/%2e%2e/%2e%2e/README.md", timeout=10)
            request = Request(base + "/api/ask", data=json.dumps({"question": "Where is IV-21 located?"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=10) as result:
                answer = json.loads(result.read())
                self.assertEqual(result.status, 200)
            self.assertEqual(answer["status"], "answered")
            self.assertTrue(answer["evidence"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
