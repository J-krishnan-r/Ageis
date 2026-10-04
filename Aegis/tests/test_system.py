from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import unittest
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from io import BytesIO
from PIL import Image

from aegis.evaluate import run_benchmark
from aegis.system import PROJECT_DIR, answer_question, ensure_index, resolve_entities, validate_knowledge
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
