# Aegis Evidence System

A local, provenance-preserving ingestion and question-answering system for the fictional Aegis Series-7 Hydraulic Control System assessment. It indexes the supplied 20-file evidence package, answers supported questions with source locations, preserves firmware-specific facts, and abstains when the package cannot establish an answer.

## Run it on Windows

Use Python 3.10 or newer.

```powershell
cd C:\Users\rjaya\OneDrive\Desktop\Projects\Ageis\Aegis
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m aegis validate
python -m aegis evaluate
python -m aegis serve
```

Open <http://127.0.0.1:8765> in a browser. Stop the server with Ctrl+C. The server listens on loopback by default and refuses public bind addresses. No API key, model endpoint, or network call is required. The assessment source package remains in the sibling `../aegis-dataset/aegis-dataset/` folder.

To use the command line instead of the browser:

```powershell
python -m aegis ask "What changed at software revision 3.2?"
python -m aegis ask "What is the maximum continuous operating temperature of PS-04A?" --json
python -m aegis ingest --force
```

`ingest` fingerprints and extracts the corpus into `.aegis/index.sqlite3`. The index rebuilds automatically when an input file changes. `validate` checks that claims have evidence, entity links resolve, aliases do not collide across entities, and every source is indexed. `evaluate` runs the supplied 23-question set and refreshes the reports in `reports/`.

## What is included

- `aegis/`: file extractors, index management, entity resolution, deterministic query service, evaluation harness, CLI, and loopback web app.
- `aegis/knowledge/entities.json`: canonical identities, declared aliases, and entity relationships.
- `aegis/knowledge/facts.json`: typed, version-scoped facts with provenance, confidence class, and evidence quotes.
- `aegis/knowledge/answer_rules.json`: explicit answer and abstention rules used by both the CLI and web API.
- `aegis/knowledge/visual_evidence.json`: reviewed image, diagram, and scanned-page transcriptions with page or normalized image region locations.
- `aegis/benchmarks/questions.json`: transcribed assessment questions and a locally curated expected-route/fact key.
- `ARCHITECTURE.md`: design report, pipeline, confidence and loss analysis, and known limits.
- `reports/EVALUATION.md`, `reports/evaluation_results.csv`, and `reports/evaluation_results.json`: results for all 23 prompts.

## Extraction and source reliability

Digital PDFs use `pypdf` page extraction. HTML, spreadsheets, Word documents, and presentations use structured, local parsers. JSON values retain their key paths. Spreadsheet rows retain sheet and cell locators. Slides retain slide and shape numbers. Image-derived content is an explicitly labelled, visually reviewed transcription with bounding-box metadata. The skewed calibration scan has no text layer, so its table was transcribed from the rendered page and checked against the image; it is not presented as automatic OCR. No model generates source facts.

Each indexed source segment records its relative path, locator, format, extraction method, and SHA-256 source hash. Curated facts independently cite one or more exact source excerpts. Source tiers and limits appear as evidence, not as a single global trust score: controlled revision-specific manuals and ECNs support direct operating claims, while the undated site-survey observations remain low-confidence field claims. A screenshot shows stored image content, never live machine state.

## Evaluation

Run `python -m aegis evaluate` to reproduce the metrics and individual question results. The evaluator scores answerable questions and designed abstentions separately, verifies expected claim identifiers and source references, and reports claim recall and citation completeness. See [reports/EVALUATION.md](reports/EVALUATION.md).

The assessment supplies no official gold answers or scoring rubric. The answer key and expected claims were curated from the supplied evidence package; therefore the scores describe this known 23-question benchmark rather than general language performance on new documentation.

## Scope and limitations

This is a self-contained, reviewable system for the supplied fictional dataset. Intent routing is deterministic and based on the documented rule file. If no rule matches, the system returns indexed text excerpts and explicitly abstains from synthesizing a new answer. A local administrator can add a reviewed fact, rule, or transcription while preserving the source path and location. It does not generate recommendations from raw evidence or state that it covers an external Aegis product.

The brief describes 12-page and 18-page manuals, but the actual supplied operator and maintenance PDFs contain two and one pages, respectively. The system indexes the files that exist and does not invent missing sections. The calibration appendix itself says that the applicable maintenance calibration schedule is not included. The planned revision 3.3 row in the supplied revision history is retained as source text; a planned date in a file does not prove that the release happened or that later changes were unchanged.

The search fallback uses SQLite FTS5 when available, with a SQLite `LIKE` fallback. The HTTP interface has no external authentication and is restricted to loopback for local use. Put it behind an authenticated gateway before any shared-network deployment. Visual transcriptions are reviewed for this dataset; new scans or image-only inputs require their own reviewed transcription before their text can support a claim.
