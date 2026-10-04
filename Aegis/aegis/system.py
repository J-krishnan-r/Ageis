"""Index management, deterministic question routing, and evidence packaging."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
from typing import Any
import hashlib
import json
import re
import sqlite3
import unicodedata

from .extract import extract_corpus

PROJECT_DIR = Path(__file__).resolve().parent.parent
PACKAGE_DIR = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_DIR.parent / "aegis-dataset" / "aegis-dataset"
KNOWLEDGE_DIR = PACKAGE_DIR / "knowledge"
BENCHMARK_DIR = PACKAGE_DIR / "benchmarks"
RUNTIME_DIR = PROJECT_DIR / ".aegis"
DB_PATH = RUNTIME_DIR / "index.sqlite3"
REPORT_PATH = RUNTIME_DIR / "extraction_report.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    facts_file = _read_json(KNOWLEDGE_DIR / "facts.json")
    rule_file = _read_json(KNOWLEDGE_DIR / "answer_rules.json")
    return {fact["id"]: fact for fact in facts_file["facts"]}, rule_file["rules"]


def _source_manifest() -> list[dict[str, str]]:
    if not DATASET_DIR.is_dir():
        raise FileNotFoundError(f"Dataset folder was not found: {DATASET_DIR}")
    supported = {".pdf", ".html", ".htm", ".json", ".xlsx", ".xlsm", ".docx", ".pptx", ".png"}
    manifest = []
    for path in sorted(p for p in DATASET_DIR.rglob("*") if p.is_file() and p.suffix.lower() in supported):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append({"path": path.resolve().relative_to(PROJECT_DIR.parent.resolve()).as_posix(), "sha256": digest})
    return manifest


def _build_database(segments: list[Any], manifest: list[dict[str, str]]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    temporary = DB_PATH.with_suffix(".sqlite3.tmp")
    temporary.unlink(missing_ok=True)
    use_fts = True
    with closing(sqlite3.connect(temporary)) as conn:
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("CREATE TABLE segments (segment_id TEXT PRIMARY KEY, source_path TEXT NOT NULL, media_type TEXT NOT NULL, locator TEXT NOT NULL, text TEXT NOT NULL, extraction_method TEXT NOT NULL, source_sha256 TEXT NOT NULL, metadata_json TEXT NOT NULL)")
        conn.execute("CREATE INDEX segments_source ON segments(source_path)")
        conn.execute("CREATE TABLE manifest (source_path TEXT PRIMARY KEY, sha256 TEXT NOT NULL)")
        try:
            conn.execute("CREATE VIRTUAL TABLE segment_fts USING fts5(segment_id UNINDEXED, source_path UNINDEXED, locator UNINDEXED, text, tokenize='unicode61 remove_diacritics 2')")
        except sqlite3.OperationalError:
            use_fts = False
        conn.executemany("INSERT INTO manifest(source_path, sha256) VALUES (?, ?)", [(entry["path"], entry["sha256"]) for entry in manifest])
        row_values = [
            (s.segment_id, s.source_path, s.media_type, s.locator, s.text, s.extraction_method, s.source_sha256, json.dumps(s.metadata, ensure_ascii=False))
            for s in segments
        ]
        conn.executemany("INSERT INTO segments VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row_values)
        if use_fts:
            conn.executemany("INSERT INTO segment_fts(segment_id,source_path,locator,text) VALUES (?,?,?,?)", [(s.segment_id, s.source_path, s.locator, s.text) for s in segments])
        conn.commit()
    temporary.replace(DB_PATH)
    report = {
        "schema_version": "1.0",
        "dataset_root": "../aegis-dataset/aegis-dataset",
        "dataset_file_count": len(manifest),
        "segment_count": len(segments),
        "search_backend": "sqlite_fts5" if use_fts else "sqlite_like_fallback",
        "documents": [
            {
                **entry,
                "segment_count": sum(s.source_path == entry["path"] for s in segments),
                "extraction_methods": sorted({s.extraction_method for s in segments if s.source_path == entry["path"]}),
                "status": "indexed" if any(s.source_path == entry["path"] for s in segments) else "metadata_only",
            }
            for entry in manifest
        ],
        "warnings": [],
        "notes": [
            "Screenshot text, schematic topology, and the rasterized calibration page were transcribed and visually reviewed; each segment retains its transcription method and location.",
            "Dataset question prompts were not ingested as factual source material.",
        ],
    }
    report_tmp = REPORT_PATH.with_suffix(".json.tmp")
    report_tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_tmp.replace(REPORT_PATH)


def ensure_index(force: bool = False) -> dict[str, Any]:
    manifest = _source_manifest()
    current = {entry["path"]: entry["sha256"] for entry in manifest}
    stale = force or not DB_PATH.exists() or not REPORT_PATH.exists()
    if not stale:
        try:
            with closing(sqlite3.connect(DB_PATH)) as conn:
                indexed = dict(conn.execute("SELECT source_path, sha256 FROM manifest"))
            stale = indexed != current
        except sqlite3.Error:
            stale = True
    if stale:
        sidecars = {"visual_evidence": _read_json(KNOWLEDGE_DIR / "visual_evidence.json")}
        segments, extraction_summary = extract_corpus(PROJECT_DIR, DATASET_DIR, sidecars)
        _build_database(segments, manifest)
        result = {**extraction_summary, "rebuilt": True}
    else:
        result = _read_json(REPORT_PATH)
        result["rebuilt"] = False
    return result


def _normalize(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_text.lower())


def resolve_entities(text: str) -> list[dict[str, str]]:
    """Resolve explicit name/code aliases without merging distinct assets."""
    entities = _read_json(KNOWLEDGE_DIR / "entities.json")["entities"]
    candidates: list[tuple[int, int, int, str, str, str]] = []
    for entity in entities:
        for alias in {entity["id"], entity["preferred_name"], *entity.get("aliases", [])}:
            pieces = re.findall(r"[A-Za-z]+|\d+", alias)
            code_alias = len(pieces) > 1 and any(piece.isdigit() for piece in pieces)
            if code_alias:
                pattern = r"(?<![A-Za-z0-9])" + r"[\s.\-/]*".join(re.escape(piece) for piece in pieces) + r"(?![A-Za-z0-9])"
            else:
                pattern = r"(?<![A-Za-z0-9])" + re.escape(alias).replace(r"\ ", r"\s+") + r"(?![A-Za-z0-9])"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                candidates.append((match.start(), -len(match.group()), match.end(), entity["id"], entity["type"], alias))
    candidates.sort()
    occupied: list[tuple[int, int]] = []
    found: dict[str, dict[str, str]] = {}
    for start, _neg_length, end, canonical_id, kind, alias in candidates:
        same_span_ids = {item[3] for item in candidates if item[0] == start and item[2] == end}
        if len(same_span_ids) != 1 or any(start < right and end > left for left, right in occupied):
            continue
        found.setdefault(canonical_id, {"canonical_id": canonical_id, "type": kind, "matched_alias": alias, "matched_text": text[start:end]})
        occupied.append((start, end))
    return list(found.values())


def choose_rule(question: str, rules: list[dict[str, Any]]) -> tuple[dict[str, Any], int] | None:
    normalized = _normalize(question)
    matches: list[tuple[int, int, dict[str, Any]]] = []
    for rule in rules:
        if rule["id"] == "fallback_search":
            continue
        groups = rule.get("all", [])
        if not groups:
            continue
        hits = sum(any(_normalize(option) in normalized for option in group) for group in groups)
        if hits == len(groups):
            literal_weight = sum(max(len(_normalize(option)) for option in group) for group in groups)
            matches.append((literal_weight, len(groups), rule))
    if not matches:
        return None
    matches.sort(key=lambda result: (result[0], result[1]), reverse=True)
    if len(matches) > 1 and matches[0][:2] == matches[1][:2] and matches[0][2]["id"] != matches[1][2]["id"]:
        return None
    selected = matches[0]
    return selected[2], selected[0]


def _search(question: str, limit: int = 5) -> list[dict[str, Any]]:
    terms = list(dict.fromkeys(re.findall(r"[A-Za-z0-9]+", question.lower())))
    if not terms:
        return []
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        try:
            match = " OR ".join('"' + term.replace('"', '""') + '"' for term in terms[:16])
            rows = conn.execute(
                "SELECT source_path, locator, snippet(segment_fts,3,'[',']',' … ',12) AS text, segment_id "
                "FROM segment_fts WHERE segment_fts MATCH ? ORDER BY bm25(segment_fts) LIMIT ?",
                (match, limit),
            ).fetchall()
        except sqlite3.Error:
            pattern = "%" + "%".join(terms[:8]) + "%"
            rows = conn.execute("SELECT source_path,locator,substr(text,1,500) AS text,segment_id FROM segments WHERE lower(text) LIKE ? LIMIT ?", (pattern, limit)).fetchall()
        return [dict(row) for row in rows]


def answer_question(question: str) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise ValueError("Enter a question before submitting it.")
    if len(question) > 1200:
        raise ValueError("Questions must contain no more than 1,200 characters.")
    ensure_index()
    facts, rules = load_catalog()
    match = choose_rule(question, rules)
    if not match:
        return {
            "status": "insufficient_evidence",
            "route_id": "fallback_search",
            "answer": "I could not find a matching supported claim for this question. Here are the closest indexed passages. Their presence does not by itself establish an answer.",
            "claims": [],
            "evidence": _search(question),
            "resolved_entities": resolve_entities(question),
            "unresolved": ["No answer rule matched with enough specificity. The system abstained rather than generate an unsupported conclusion."],
            "limitations": ["Question routing is deterministic and may require different wording or a documented rule."],
        }
    rule, _score = match
    claims = []
    evidence: list[dict[str, Any]] = []
    for fact_id in rule["facts"]:
        fact = facts[fact_id]
        claims.append({k: fact[k] for k in ("id", "subject", "predicate", "value", "unit", "scope", "confidence", "assertion") if k in fact})
        for source in fact["evidence"]:
            evidence.append({
                "source": source["source"],
                "locator": source["locator"],
                "quote": source["quote"],
                "extraction_method": _extraction_method(source["source"], source["locator"]),
                "claim_id": fact_id,
                "confidence": fact["confidence"],
            })
    # Include the canonical identifiers carried by the matched facts. Some
    # questions deliberately refer to a screenshot, row, or concept without
    # repeating the displayed tag itself.
    entity_context = question + " " + " ".join(claim["subject"] for claim in claims)
    # Keep references unique without discarding separate claims supported by the
    # same line; claim_id remains part of the uniqueness key.
    unique: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in evidence:
        unique[(item["source"], item["locator"], item["claim_id"])] = item
    answered = all(facts[fact_id].get("value") is not None for fact_id in rule["facts"])
    unresolved = []
    if not answered:
        unresolved.append("The supplied evidence does not state the requested value. See the cited scope and missing-information explanation.")
    if rule["id"] == "diagram_controller_connections":
        unresolved.append("The grey PLC-03-to-HPU line conflicts with the drawing's line-type legend.")
    if rule["id"] == "setpoint_applies_scope":
        unresolved.append("Applicability depends on installed firmware and unit configuration; the package also discusses post-2024 manufacture in ECN-1042.")
    return {
        "status": "answered" if answered else "abstained",
        "route_id": rule["id"],
        "answer": rule["answer"],
        "claims": claims,
        "evidence": list(unique.values()),
        "resolved_entities": resolve_entities(entity_context),
        "unresolved": unresolved,
        "limitations": ["The system describes only the supplied, fictional documentation package and makes no claim about a real Aegis product or any live machine."],
    }


def _extraction_method(source_path: str, locator: str) -> str:
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            row = conn.execute("SELECT extraction_method FROM segments WHERE source_path=? AND locator=? LIMIT 1", (source_path, locator)).fetchone()
            if not row:
                pdf_page = re.match(r"p\.?\s*(\d+)\b", locator, re.IGNORECASE)
                sheet_cell = re.search(r"!([A-Z]+\d+)", locator)
                paragraph = re.search(r"paragraph\s+(\d+)", locator, re.IGNORECASE)
                slide = re.search(r"slide\s+(\d+)", locator, re.IGNORECASE)
                region = locator.split(",")[0].strip()
                if pdf_page:
                    query = f"Page {pdf_page.group(1)}"
                    row = conn.execute("SELECT extraction_method FROM segments WHERE source_path=? AND locator=? LIMIT 1", (source_path, query)).fetchone()
                elif sheet_cell:
                    cell = sheet_cell.group(1)
                    sheet_row = int(re.search(r"\d+", cell).group())
                    row = conn.execute("SELECT extraction_method FROM segments WHERE source_path=? AND locator LIKE ? AND locator LIKE ? LIMIT 1", (source_path, f"%row {sheet_row}%", f"%{cell}%")).fetchone()
                elif paragraph:
                    row = conn.execute("SELECT extraction_method FROM segments WHERE source_path=? AND locator LIKE ? LIMIT 1", (source_path, f"Paragraph {paragraph.group(1)} %")).fetchone()
                elif slide:
                    row = conn.execute("SELECT extraction_method FROM segments WHERE source_path=? AND locator LIKE ? LIMIT 1", (source_path, f"Slide {slide.group(1)},%")).fetchone()
                elif locator.startswith("$"):
                    row = conn.execute("SELECT extraction_method FROM segments WHERE source_path=? AND locator=? LIMIT 1", (source_path, locator)).fetchone()
                else:
                    row = conn.execute("SELECT extraction_method FROM segments WHERE source_path=? AND locator=? LIMIT 1", (source_path, region)).fetchone()
            if not row:
                row = conn.execute("SELECT extraction_method FROM segments WHERE source_path=? LIMIT 1", (source_path,)).fetchone()
        if row:
            return row[0]
    except sqlite3.Error:
        pass
    return "curated_source_excerpt"


def validate_knowledge() -> list[str]:
    """Validate the internal fact/schema/rule graph before serving queries."""
    errors: list[str] = []
    facts, rules = load_catalog()
    for fact_id, fact in facts.items():
        if not fact.get("evidence"):
            errors.append(f"{fact_id}: has no provenance")
        for source in fact.get("evidence", []):
            if not source.get("source") or not source.get("locator") or not source.get("quote"):
                errors.append(f"{fact_id}: incomplete provenance")
    seen = set()
    for rule in rules:
        if rule["id"] in seen:
            errors.append(f"duplicate rule id: {rule['id']}")
        seen.add(rule["id"])
        for fact_id in rule.get("facts", []):
            if fact_id not in facts:
                errors.append(f"{rule['id']}: references missing fact {fact_id}")
    entities = _read_json(KNOWLEDGE_DIR / "entities.json")["entities"]
    entity_ids = {entity["id"] for entity in entities}
    for entity in entities:
        if entity["id"] in seen and entity["id"] not in {"A17", "A18", "A19"}:
            errors.append(f"entity id conflicts with rule id: {entity['id']}")
        for relation in entity.get("relations", []):
            if relation.get("target") not in entity_ids:
                errors.append(f"{entity['id']}: unresolved relation target {relation.get('target')}")
    alias_owners: dict[str, str] = {}
    for entity in entities:
        for alias in {entity["id"], entity["preferred_name"], *entity.get("aliases", [])}:
            normalized = _normalize(alias)
            if normalized in alias_owners and alias_owners[normalized] != entity["id"]:
                errors.append(f"ambiguous alias {alias!r}: {alias_owners[normalized]} and {entity['id']}")
            else:
                alias_owners[normalized] = entity["id"]
    return errors
