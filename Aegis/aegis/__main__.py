"""Command-line entry point for the Aegis evidence system."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from . import __version__
from .evaluate import run_benchmark
from .system import answer_question, ensure_index, validate_knowledge
from .web import serve


def main() -> int:
    parser = argparse.ArgumentParser(prog="aegis", description="Index and query the fictional Aegis Series-7 HCS evidence package.")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    ingest_parser = subparsers.add_parser("ingest", help="(Re)build the local source index")
    ingest_parser.add_argument("--force", action="store_true", help="Re-extract all supplied sources")
    ask_parser = subparsers.add_parser("ask", help="Ask a question and print the answer and evidence")
    ask_parser.add_argument("question", nargs="+", help="Natural-language question")
    ask_parser.add_argument("--json", action="store_true", help="Print the complete JSON response")
    subparsers.add_parser("evaluate", help="Run and save the 23-question benchmark")
    subparsers.add_parser("validate", help="Validate fact provenance, relationships, and corpus index")
    serve_parser = subparsers.add_parser("serve", help="Start the local evidence web application")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Loopback address (default 127.0.0.1)")
    serve_parser.add_argument("--port", default=8765, type=int, help="Local port (default 8765)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        if args.command == "ingest":
            report = ensure_index(force=args.force)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        if args.command == "ask":
            response = answer_question(" ".join(args.question))
            if args.json:
                print(json.dumps(response, ensure_ascii=False, indent=2))
            else:
                print(f"[{response['status']}] {response['answer']}\n")
                for source in response["evidence"]:
                    print(f"  {source['source']} — {source['locator']} ({source['extraction_method']})")
                    print(f"  “{source['quote']}”\n")
                for note in response["unresolved"]:
                    print(f"  Unresolved: {note}")
            return 0
        if args.command == "evaluate":
            report = run_benchmark()
            print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))
            print("Saved reports/evaluation_results.json, evaluation_results.csv, and EVALUATION.md")
            return 0 if report["metrics"]["questions_correct"] == report["metrics"]["questions_total"] else 1
        if args.command == "validate":
            errors = validate_knowledge()
            index = ensure_index()
            if errors or index["warnings"]:
                print(json.dumps({"errors": errors, "warnings": index["warnings"]}, ensure_ascii=False, indent=2))
                return 1
            print(json.dumps({"valid": True, "facts": len(__import__("aegis.system", fromlist=["load_catalog"]).load_catalog()[0]), "indexed_files": index["dataset_file_count"], "segments": index["segment_count"], "warnings": index["warnings"]}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "serve":
            serve(args.host, args.port)
            return 0
    except (ValueError, FileNotFoundError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
