# Aegis Evidence System

Aegis is a local, evidence-backed question-answering system for the fictional Series-7 Hydraulic Control System assessment. It indexes the supplied documents, answers supported questions with source citations, and clearly abstains when the evidence does not establish an answer.

## Run locally

Requires Python 3.10 or newer. From the repository root, run:

```powershell
cd Aegis
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m aegis validate
python -m aegis evaluate
python -m aegis serve
```

Open <http://127.0.0.1:8765> in your browser. The web server is loopback-only by default. To ask from the command line, use `python -m aegis ask "What changed at software revision 3.2?"`.

## Repository layout

- `Aegis/` — application code, knowledge records, tests, architecture notes, and evaluation reports.
- `aegis-dataset/aegis-dataset/` — the 20 source files indexed by the application.
- `task-description.pdf` and `evaluation-questions.pdf` — assessment brief and question set.

The benchmark contains 23 assessment questions and a curated expected-answer key because the assessment does not provide an official gold set. See [Aegis/README.md](Aegis/README.md) for implementation details and [Aegis/reports/EVALUATION.md](Aegis/reports/EVALUATION.md) for results and limitations.
