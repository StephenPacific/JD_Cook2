#!/usr/bin/env python3
"""Lv2 web-search adapter: spawn Claude Code with WebSearch + WebFetch tools
to discover JD URLs that JobSpy/Adzuna miss (Lever, Greenhouse, Ashby boards,
Built In Sydney/Melbourne, Wellfound AU, employer career pages).

Output: jd_search/web-searches/<slug>/results.md — a reviewable URL list.
The user picks which URLs to import via `make import-job URL=...`.

This step deliberately does NOT auto-stage to inbox/ or auto-triage. It is
a pure discovery aid that complements the JobSpy + Adzuna scrape; the user
decides which URLs are worth pursuing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSONA_PATH = ROOT / "jd_search" / "persona.md"
SEEN_TSV = ROOT / "jd_search" / "seen.tsv"
OUT_ROOT = ROOT / "jd_search" / "web-searches"
DEFAULT_TIMEOUT_SECS = 600


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s[:60] or "untitled"


def load_seen_urls() -> set[str]:
    if not SEEN_TSV.exists():
        return set()
    urls: set[str] = set()
    for line in SEEN_TSV.read_text(encoding="utf-8").splitlines()[1:]:
        if "\t" in line:
            urls.add(line.split("\t", 1)[0].lower())
    return urls


def build_prompt(query: str, persona: str) -> str:
    return f"""You are helping Stephen find Australian job postings on sources that
JobSpy and Adzuna do NOT cover. Your goal is breadth + accuracy beyond the
existing scrape.

# Stephen's persona

{persona}

# Search task

Find {query}.

Use the WebSearch tool. Prioritise these source types:
- Lever ATS (jobs.lever.co/<company>/...)
- Greenhouse ATS (job-boards.greenhouse.io/<company>/jobs/...)
- Ashby ATS (jobs.ashbyhq.com/<company>/...)
- Workable, Recruitee, SmartRecruiters
- Built In Sydney (builtinsydney.au)
- Built In Melbourne (builtinmelbourne.com)
- Wellfound (wellfound.com Australia listings)
- Direct employer careers pages (e.g. canva.com/careers, atlassian.com/careers)
- Curated lists (GitHub job-list repos)

Avoid (already covered by JobSpy/Adzuna):
- linkedin.com, indeed.com, au.indeed.com, glassdoor.com

Only return URLs to specific job postings (NOT category/listing pages).
Each URL must point to one concrete role. Aim for 8–15 strong matches.
Verify the role is junior / 1–4 yr level and based in Australia (or remote-AU)
before including it.

# Output format

Return ONLY a JSON array, no prose, no markdown fence. Schema:

[
  {{
    "title": "<role title>",
    "company": "<company name>",
    "location": "<city, state, country>",
    "url": "<direct URL to the JD>",
    "why_relevant": "<one sentence on why this matches Stephen's persona>"
  }}
]

If you cannot find any qualifying postings, return [].
"""


def run_claude(prompt: str) -> str:
    """Pipe the prompt over stdin to avoid CLI arg-length and shell-escaping
    pitfalls (mirrors triage.py's invocation pattern)."""
    result = subprocess.run(
        [
            "claude",
            "-p",
            "--allowedTools",
            "WebSearch,WebFetch",
            "--output-format",
            "json",
            "--no-session-persistence",
        ],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=DEFAULT_TIMEOUT_SECS,
    )
    if result.returncode != 0:
        fail(f"claude -p exited {result.returncode}: {result.stderr.strip()[:500]}")
    return result.stdout


def extract_json_array(text: str) -> list[dict]:
    """Pull the first JSON array out of mixed text (claude --output-format json
    wraps the result in its own envelope; the agent's actual output is in
    payload['result'] as a string and may include explanatory prose around
    the JSON). Use raw_decode so trailing prose after the array is ignored."""
    try:
        envelope = json.loads(text)
    except json.JSONDecodeError:
        fail("claude returned non-JSON envelope; check stderr above for parse errors.")
    payload = envelope.get("result", "") if isinstance(envelope, dict) else ""
    if not isinstance(payload, str):
        fail("claude envelope missing string 'result' field.")
    start = payload.find("[")
    if start < 0:
        return []
    decoder = json.JSONDecoder()
    try:
        obj, _end = decoder.raw_decode(payload[start:])
    except json.JSONDecodeError as exc:
        fail(f"agent JSON array parse error: {exc}; first 400 chars: {payload[start:start+400]!r}")
    if not isinstance(obj, list):
        return []
    return obj


def render_results_md(query: str, candidates: list[dict], filtered: int) -> str:
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [
        "# Web Search Results",
        "",
        f"- Query: {query}",
        f"- Generated at: {generated_at}",
        f"- Candidates: {len(candidates)}",
        f"- Filtered (already in seen.tsv): {filtered}",
        "",
        "Pick interesting URLs and import them with:",
        "",
        "```sh",
        "make import-job URL=\"<url>\" JOB=<slug>",
        "make triage JOB=<slug>",
        "```",
        "",
        "---",
        "",
    ]
    if not candidates:
        lines.append("_No qualifying postings found beyond what JobSpy/Adzuna already cover._")
        return "\n".join(lines) + "\n"
    for i, rec in enumerate(candidates, start=1):
        lines.extend(
            [
                f"## {i}. {rec.get('title', '?')} — {rec.get('company', '?')}",
                "",
                f"- Location: {rec.get('location', '?')}",
                f"- URL: {rec.get('url', '')}",
                f"- Why: {rec.get('why_relevant', '')}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Lv2 web-search via Claude WebSearch.")
    parser.add_argument("--query", required=True, help="Free-form search intent.")
    args = parser.parse_args()

    if not PERSONA_PATH.exists():
        fail(f"Missing persona: {PERSONA_PATH}")
    persona = PERSONA_PATH.read_text(encoding="utf-8")
    seen_urls = load_seen_urls()

    print(f"Searching: {args.query}", flush=True)
    raw = run_claude(build_prompt(args.query, persona))
    candidates = extract_json_array(raw)

    fresh: list[dict] = []
    filtered_count = 0
    for rec in candidates:
        url = str(rec.get("url", "")).strip().lower()
        if url and url in seen_urls:
            filtered_count += 1
            continue
        fresh.append(rec)

    slug = slugify(args.query)
    out_dir = OUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "results.md"
    out_file.write_text(render_results_md(args.query, fresh, filtered_count), encoding="utf-8")

    print(f"Found {len(candidates)} candidates ({filtered_count} already seen).", flush=True)
    print(f"Results: {out_file.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
