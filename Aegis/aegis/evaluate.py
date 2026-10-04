"""Reproducible evaluation harness for the 23 supplied challenge questions."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import csv
import json

from .system import BENCHMARK_DIR, PROJECT_DIR, answer_question, ensure_index, load_catalog, validate_knowledge

REPORTS_DIR = PROJECT_DIR / "reports"


def run_benchmark(write_reports: bool = True) -> dict[str, Any]:
    errors = validate_knowledge()
    if errors:
        raise ValueError("Knowledge validation failed: " + "; ".join(errors))
    index_report = ensure_index()
    catalog, _ = load_catalog()
    benchmark = json.loads((BENCHMARK_DIR / "questions.json").read_text(encoding="utf-8"))
    results = []
    correct = 0
    answered_total = answered_correct = 0
    abstained_total = abstained_correct = 0
    expected_fact_total = expected_fact_found = 0
    expected_citation_total = valid_citation_total = 0

    for case in benchmark["cases"]:
        response = answer_question(case["question"])
        expected_facts = set(case["expected_facts"])
        returned_facts = {claim["id"] for claim in response["claims"]}
        facts_found = expected_facts & returned_facts
        expected_fact_total += len(expected_facts)
        expected_fact_found += len(facts_found)

        citations_by_fact = {fact_id: [] for fact_id in expected_facts}
        for item in response["evidence"]:
            if item.get("claim_id") in citations_by_fact:
                citations_by_fact[item["claim_id"]].append(item)
        valid_citations = 0
        for fact_id in expected_facts:
            fact = catalog[fact_id]
            for source in fact["evidence"]:
                expected_citation_total += 1
                exists = (PROJECT_DIR.parent / source["source"]).is_file()
                has_locator = bool(source.get("locator"))
                has_quote = bool(source.get("quote", "").strip())
                emitted = any(
                    item.get("source") == source["source"]
                    and item.get("locator") == source["locator"]
                    and item.get("quote") == source["quote"]
                    for item in citations_by_fact[fact_id]
                )
                if exists and has_locator and has_quote and emitted:
                    valid_citation_total += 1
                    valid_citations += 1

        right_status = response["status"] == case["expected_status"]
        right_route = response["route_id"] == case["expected_route"]
        all_facts_present = expected_facts <= returned_facts
        citations_complete = valid_citations == sum(len(catalog[fid]["evidence"]) for fid in expected_facts)
        case_correct = right_status and right_route and all_facts_present and citations_complete
        correct += int(case_correct)
        if case["expected_status"] == "answered":
            answered_total += 1
            answered_correct += int(response["status"] == "answered" and right_route and all_facts_present and citations_complete)
        else:
            abstained_total += 1
            abstained_correct += int(response["status"] in {"abstained", "insufficient_evidence"} and right_route and all_facts_present and citations_complete)
        results.append({
            "id": case["id"],
            "question": case["question"],
            "expected_route": case["expected_route"],
            "actual_route": response["route_id"],
            "expected_status": case["expected_status"],
            "actual_status": response["status"],
            "expected_fact_ids": sorted(expected_facts),
            "returned_fact_ids": sorted(returned_facts),
            "fact_recall": len(facts_found) / len(expected_facts) if expected_facts else 1.0,
            "expected_citations": sum(len(catalog[fid]["evidence"]) for fid in expected_facts),
            "valid_citations": valid_citations,
            "correct": case_correct,
            "answer": response["answer"],
        })

    metrics = {
        "benchmark": benchmark["benchmark"],
        "system_version": "1.0.0",
        "questions_total": len(results),
        "answerable_questions": answered_total,
        "answerable_questions_correct": answered_correct,
        "answerable_accuracy": answered_correct / answered_total if answered_total else None,
        "unanswerable_questions": abstained_total,
        "unanswerable_abstentions_correct": abstained_correct,
        "unanswerable_abstention_accuracy": abstained_correct / abstained_total if abstained_total else None,
        "overall_exact_evidence_accuracy": correct / len(results) if results else None,
        "questions_correct": correct,
        "claim_fact_recall": expected_fact_found / expected_fact_total if expected_fact_total else None,
        "citation_completeness": valid_citation_total / expected_citation_total if expected_citation_total else None,
        "valid_citations": valid_citation_total,
        "expected_citations": expected_citation_total,
        "extraction_segments": index_report["segment_count"],
        "source_files_indexed": index_report["dataset_file_count"],
        "scoring_note": "An exact case counts as correct only when route, answer/abstention, all expected fact IDs, and every curated source locator/quote match; source files must exist.",
    }
    report = {"metrics": metrics, "results": results}
    if write_reports:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        json_path = REPORTS_DIR / "evaluation_results.json"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        csv_path = REPORTS_DIR / "evaluation_results.csv"
        fieldnames = ["id", "question", "expected_status", "actual_status", "expected_route", "actual_route", "fact_recall", "expected_citations", "valid_citations", "correct", "answer"]
        with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow({key: result[key] for key in fieldnames})
        summary_path = REPORTS_DIR / "EVALUATION.md"
        summary_path.write_text(_markdown_summary(metrics, results), encoding="utf-8")
    return report


def _markdown_summary(metrics: dict[str, Any], results: list[dict[str, Any]]) -> str:
    pct = lambda value: "n/a" if value is None else f"{value:.1%}"
    lines = [
        "# Evaluation results",
        "",
        "The deterministic evidence system was run against all 23 questions in the supplied evaluation PDF.",
        "",
        f"- Questions: {metrics['questions_total']} ({metrics['answerable_questions']} answerable, {metrics['unanswerable_questions']} designed for abstention)",
        f"- Answerable question accuracy: {pct(metrics['answerable_accuracy'])} ({metrics['answerable_questions_correct']}/{metrics['answerable_questions']})",
        f"- Correct abstention on unanswerable questions: {pct(metrics['unanswerable_abstention_accuracy'])} ({metrics['unanswerable_abstentions_correct']}/{metrics['unanswerable_questions']})",
        f"- Overall exact evidence accuracy: {pct(metrics['overall_exact_evidence_accuracy'])} ({metrics['questions_correct']}/{metrics['questions_total']})",
        f"- Expected fact recall: {pct(metrics['claim_fact_recall'])}",
        f"- Citation completeness: {pct(metrics['citation_completeness'])} ({metrics['valid_citations']}/{metrics['expected_citations']} expected source citations)",
        f"- Corpus indexed: {metrics['source_files_indexed']} files, {metrics['extraction_segments']} source segments",
        "",
        "An answer counts as correct only when the route and answerability status match, every expected fact is present, every expected citation is emitted with its source, locator and quote, and all cited source files exist. Expected facts and answers were curated from the supplied corpus because the brief provides no official answer key.",
        "",
        "| ID | Result | Evidence route | Answer / abstention |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        safe_answer = result["answer"].replace("|", "&#124;").replace("\n", " ")
        lines.append(f"| {result['id']} | {'PASS' if result['correct'] else 'FAIL'} | `{result['actual_route']}` | {safe_answer} |")
    lines += ["", "## Evaluation limits", "", "This is a transparent, rule-based evaluation against the supplied question set and a reviewed local answer key. It measures these known questions and their provenance; it does not estimate general language understanding, measure model calibration, or validate the system on unseen equipment documentation.", ""]
    return "\n".join(lines)
