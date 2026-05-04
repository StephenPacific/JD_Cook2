#!/usr/bin/env python3
"""Phase 2 — Scan JobSpy results, auto-triage them, write inbox.md.

Pipeline:
  1. Read jd_search/searches/<search>/ranked_jobs.json (from `make match-jobs`).
  2. For each top-N candidate:
       - Skip if its URL is already in jd_search/seen.tsv (cross-run dedup).
       - Otherwise call triage.judge_jd() to get a verdict.
       - Stage the JD body under jd_search/inbox/<slug>.md so
         `make draft JOB=<slug> FROM=inbox` can import it later.
  3. Update jd_search/seen.tsv with every new judgement.
  4. Regenerate jd_search/inbox.md, sorted by verdict + recency. SKIP and
     VISA-BLOCKED entries are deliberately not shown — they live in
     jd_search/decisions.tsv for audit only.

The pipeline deliberately STOPS at inbox.md. Drafting is never automatic;
the user reviews inbox.md and triggers `make draft JOB=<slug> FROM=inbox`
themselves.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOT = ROOT / "jd_search" / "searches"
INBOX_DIR = ROOT / "jd_search" / "inbox"
INBOX_MD = ROOT / "jd_search" / "inbox.md"
SEEN_TSV = ROOT / "jd_search" / "seen.tsv"
DEFAULT_PERSONA = ROOT / "jd_search" / "persona.md"

SEEN_FIELDS = [
    "url",
    "first_seen_at",
    "last_seen_at",
    "last_verdict",
    "last_confidence",
    "last_visa",
    "last_search",
    "slug",
    "title",
    "company",
    "location",
]

# Verdicts surfaced in inbox.md (other verdicts kept in decisions.tsv only).
VISIBLE_VERDICTS = {"APPLY", "BORDERLINE"}

# Make the triage logic importable.
sys.path.insert(0, str(ROOT / "jd_search"))
from triage import judge_jd  # noqa: E402


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def slug_from_record(jd: dict[str, Any]) -> str:
    """Stable, unique slug from company + title, salted by 6 hex chars of the
    URL hash so two postings with identical titles don't collide."""
    title = (jd.get("title") or "untitled").strip()
    company = (jd.get("company") or jd.get("company_name") or "").strip()
    raw = f"{company} {title}".strip() or "untitled"
    base = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    if not base:
        base = "untitled"
    base = base[:60].rstrip("-")
    url = (jd.get("job_url") or jd.get("job_url_direct") or "").strip()
    suffix = hashlib.sha256((url or raw).encode()).hexdigest()[:6]
    return f"{base}-{suffix}"


def load_seen() -> dict[str, dict[str, str]]:
    """Return URL → row mapping. Spurious duplicate-header rows are skipped."""
    if not SEEN_TSV.exists():
        return {}
    seen: dict[str, dict[str, str]] = {}
    with SEEN_TSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            url = (row.get("url") or "").strip()
            if not url or url == "url":
                continue
            seen[url] = {field: (row.get(field) or "") for field in SEEN_FIELDS}
    return seen


def save_seen(seen: dict[str, dict[str, str]]) -> None:
    SEEN_TSV.parent.mkdir(parents=True, exist_ok=True)
    with SEEN_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SEEN_FIELDS, delimiter="\t")
        writer.writeheader()
        for row in seen.values():
            writer.writerow({field: row.get(field, "") for field in SEEN_FIELDS})


def stage_jd_body(slug: str, jd_body: str) -> Path:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    path = INBOX_DIR / f"{slug}.md"
    path.write_text(jd_body, encoding="utf-8")
    return path


def build_jd_body(jd: dict[str, Any]) -> str:
    """Render the JD into the same lightweight format `make import-job` produces,
    so downstream draft tooling reads it the same way as a clipboard import."""
    title = (jd.get("title") or "Untitled").strip()
    company = (jd.get("company") or jd.get("company_name") or "Unknown company").strip()
    location = (jd.get("location") or "").strip()
    site = (jd.get("site") or "").strip()
    url = (jd.get("job_url") or jd.get("job_url_direct") or "").strip()
    description = (jd.get("description") or "").strip() or "_No description captured._"
    imported_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return "\n".join(
        [
            "# Job Description (auto-staged from jd_search inbox)",
            "",
            f"- Imported at: {imported_at}",
            "- Source type: jd_search-inbox",
            f"- Search site: {site}",
            f"- Source URL: {url}",
            f"- Title: {title}",
            f"- Company: {company}",
            f"- Location: {location}",
            "",
            "---",
            "",
            f"## {title}",
            "",
            f"Company: {company}",
            "",
            description,
            "",
        ]
    )


def section_lines(heading: str, entries: list[dict[str, str]]) -> list[str]:
    if not entries:
        return []
    out = [f"## {heading}", ""]
    for entry in entries:
        slug = entry.get("slug", "")
        out.extend(
            [
                f"### {slug}",
                f"- Title: {entry.get('title', '')}",
                f"- Company: {entry.get('company', '')}",
                f"- Location: {entry.get('location', '')}",
                f"- Visa: {entry.get('last_visa', '')}",
                f"- Source: {entry.get('last_search', '')}",
                f"- URL: {entry.get('url', '')}",
                f"- Last seen: {entry.get('last_seen_at', '')}",
                f"- **Action:** `make draft JOB={slug} FROM=inbox`",
                "",
            ]
        )
    return out


def build_inbox_markdown(seen: dict[str, dict[str, str]]) -> str:
    buckets: dict[tuple[str, str], list[dict[str, str]]] = {}
    for entry in seen.values():
        verdict = entry.get("last_verdict", "")
        if verdict not in VISIBLE_VERDICTS:
            continue
        confidence = entry.get("last_confidence", "")
        buckets.setdefault((verdict, confidence), []).append(entry)

    for entries in buckets.values():
        entries.sort(key=lambda e: e.get("last_seen_at", ""), reverse=True)

    visible_count = sum(len(v) for v in buckets.values())
    skipped_count = sum(
        1 for e in seen.values() if e.get("last_verdict", "") not in VISIBLE_VERDICTS
    )
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

    lines: list[str] = [
        "# JD Inbox",
        "",
        f"- Generated at: {generated_at}",
        f"- Visible candidates: {visible_count}",
        f"- Hidden (SKIP / VISA-BLOCKED): {skipped_count} — see `jd_search/decisions.tsv`",
        "",
        "Run `make draft JOB=<slug> FROM=inbox` to import any candidate below into",
        "the standard JDcook cycle. The triage gate inside `make draft` will hit",
        "this file's cached verdict instantly — no re-judgement cost.",
        "",
        "---",
        "",
    ]

    section_order = [
        ("APPLY", "HIGH", "APPLY (HIGH confidence)"),
        ("APPLY", "MEDIUM", "APPLY (MEDIUM confidence)"),
        ("APPLY", "LOW", "APPLY (LOW confidence)"),
        ("BORDERLINE", "HIGH", "BORDERLINE (HIGH confidence)"),
        ("BORDERLINE", "MEDIUM", "BORDERLINE (MEDIUM confidence)"),
        ("BORDERLINE", "LOW", "BORDERLINE (LOW confidence)"),
    ]
    for verdict, confidence, heading in section_order:
        lines.extend(section_lines(heading, buckets.get((verdict, confidence), [])))

    if visible_count == 0:
        lines.extend(
            [
                "_No APPLY or BORDERLINE candidates yet. Run_",
                "_`make scan-jobs SEARCH=<slug>` to discover and triage some._",
                "",
            ]
        )

    return "\n".join(lines)


def truncate(text: str, n: int = 80) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Auto-triage JobSpy results into jd_search/inbox.md.")
    parser.add_argument("--search", required=True, help="Search slug under jd_search/searches/.")
    parser.add_argument("--top-n", type=int, default=25, help="How many top-ranked JDs to triage (default 25).")
    parser.add_argument("--agent", default="codex", choices=("codex", "claude"), help="Triage judge agent.")
    parser.add_argument("--persona", default=str(DEFAULT_PERSONA.relative_to(ROOT)))
    parser.add_argument("--rejudge", action="store_true", help="Re-triage URLs already in seen.tsv.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    persona_path = resolve_path(args.persona)
    if not persona_path.exists():
        fail(f"Missing persona: {rel(persona_path) if persona_path.is_relative_to(ROOT) else persona_path}")
    persona = persona_path.read_text(encoding="utf-8")

    ranked_path = SEARCH_ROOT / args.search / "ranked_jobs.json"
    if not ranked_path.exists():
        fail(
            f"Missing ranked results: {rel(ranked_path)}. "
            f"Run `make match-jobs SEARCH={args.search}` first."
        )

    ranked = json.loads(ranked_path.read_text(encoding="utf-8"))
    if not isinstance(ranked, list):
        fail("ranked_jobs.json must contain a list.")

    ranked.sort(key=lambda j: int(j.get("match_score", 0) or 0), reverse=True)
    candidates = ranked[: args.top_n]

    seen = load_seen()
    print(f"Scanning {len(candidates)} top-{args.top_n} candidates (out of {len(ranked)} ranked) from search '{args.search}'.")

    new_count = cached_count = empty_count = 0
    for jd in candidates:
        url = (jd.get("job_url") or jd.get("job_url_direct") or "").strip()
        description = (jd.get("description") or "").strip()
        title = jd.get("title", "?")

        if not description or len(description) < 80:
            empty_count += 1
            print(f"  · skip (empty desc): {truncate(title, 60)}")
            continue

        if url and url in seen and not args.rejudge:
            cached_count += 1
            seen[url]["last_seen_at"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
            seen[url]["last_search"] = args.search
            continue

        slug = slug_from_record(jd)
        jd_body = build_jd_body(jd)

        try:
            decision, _was_cached = judge_jd(
                jd_body,
                persona,
                args.agent,
                source_type="url",
                source=url or slug,
                use_cache=True,
                refresh=False,
            )
        except SystemExit:
            print(f"  ✗ triage failed: {truncate(title, 60)}")
            continue

        stage_jd_body(slug, jd_body)

        now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        prev = seen.get(url, {})
        seen[url] = {
            "url": url,
            "first_seen_at": prev.get("first_seen_at") or now,
            "last_seen_at": now,
            "last_verdict": decision.get("verdict", ""),
            "last_confidence": decision.get("confidence", ""),
            "last_visa": decision.get("visa_status", ""),
            "last_search": args.search,
            "slug": slug,
            "title": title,
            "company": jd.get("company") or jd.get("company_name") or "",
            "location": jd.get("location") or "",
        }

        new_count += 1
        verdict = decision.get("verdict", "?")
        confidence = decision.get("confidence", "?")
        print(f"  • {verdict:<13} {confidence:<6} {slug}")

    save_seen(seen)
    inbox_md = build_inbox_markdown(seen)
    INBOX_MD.write_text(inbox_md, encoding="utf-8")

    visible = sum(
        1
        for e in seen.values()
        if e.get("last_verdict", "") in VISIBLE_VERDICTS
    )
    print()
    print(f"Scan complete:")
    print(f"  - new judgements:    {new_count}")
    print(f"  - cached (skipped):  {cached_count}")
    print(f"  - empty descriptions:{empty_count}")
    print(f"  - inbox visible now: {visible}")
    print(f"  - inbox.md:          {rel(INBOX_MD)}")
    print(f"  - seen.tsv:          {rel(SEEN_TSV)}")
    print()
    print("Review with `make inbox`, then `make draft JOB=<slug> FROM=inbox`.")


if __name__ == "__main__":
    main()
