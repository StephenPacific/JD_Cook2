#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOT = ROOT / "jd_search" / "searches"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_slug(value: str, label: str) -> None:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        fail(f"{label} must be a lowercase slug using letters, numbers, and hyphens.")


def write_new(path: Path, text: str, force: bool = False) -> None:
    if path.exists() and not force:
        fail(f"Refusing to overwrite existing file: {rel(path)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_ranked(search: str) -> list[dict[str, Any]]:
    path = SEARCH_ROOT / search / "ranked_jobs.json"
    if not path.exists():
        fail(f"Missing ranked results: {rel(path)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        fail("ranked_jobs.json must contain a list.")
    return [dict(item) for item in data]


def build_markdown(job: str, record: dict[str, Any], search: str, rank: int) -> str:
    title = record.get("title") or "Untitled"
    company = record.get("company") or record.get("company_name") or "Unknown company"
    description = record.get("description") or ""
    imported_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [
        f"# Job Description: {job}",
        "",
        f"- Imported at: {imported_at}",
        "- Source type: jd_search",
        f"- Search: {search}",
        f"- Search rank: {rank}",
        f"- Match score: {record.get('match_score', '')}",
        f"- Company: {company}",
        f"- Title: {title}",
        f"- Site: {record.get('site', '')}",
        f"- Source URL: {record.get('job_url') or record.get('job_url_direct') or ''}",
        f"- Location: {record.get('location', '')}",
        "",
        "---",
        "",
        f"## {title}",
        "",
        f"Company: {company}",
        "",
        description.strip() or "_No description captured._",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import one jd_search ranked result into jobs/<JOB>.md.")
    parser.add_argument("--search", required=True)
    parser.add_argument("--rank", type=int, default=1, help="1-based shortlist rank.")
    parser.add_argument("--job", required=True)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    validate_slug(args.search, "SEARCH")
    validate_slug(args.job, "JOB")
    if args.rank < 1:
        fail("--rank must be 1 or greater.")

    ranked = load_ranked(args.search)
    if args.rank > len(ranked):
        fail(f"Rank {args.rank} is out of range; only {len(ranked)} ranked jobs available.")
    record = ranked[args.rank - 1]

    job_path = ROOT / "jobs" / f"{args.job}.md"
    source_dir = ROOT / "jobs" / "_sources" / args.job
    metadata = {
        "job": args.job,
        "imported_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_type": "jd_search",
        "search": args.search,
        "rank": args.rank,
        "job_path": rel(job_path),
        "raw_path": rel(source_dir / "jobspy_result.json"),
        "text_path": rel(source_dir / "text.txt"),
        "source_url": record.get("job_url") or record.get("job_url_direct"),
        "title": record.get("title"),
        "company": record.get("company") or record.get("company_name"),
        "match_score": record.get("match_score"),
    }

    markdown = build_markdown(args.job, record, args.search, args.rank)
    write_new(source_dir / "jobspy_result.json", json.dumps(record, indent=2, ensure_ascii=False, default=str) + "\n", args.force)
    write_new(source_dir / "metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", args.force)
    write_new(source_dir / "text.txt", markdown + "\n", args.force)
    write_new(job_path, markdown + "\n", args.force)
    print(f"Imported search result: {rel(job_path)}")
    print(f"- source snapshot: {rel(source_dir)}")


if __name__ == "__main__":
    main()
