#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
# Persona deliberately lives outside raw/ so it cannot pollute resume drafting:
# the drafting skill reads everything under raw/ as evidence, and
# `% src: raw/persona.md` would be a wrong citation. cycle.py rejects any
# `% src` line that touches jd_search/ to enforce this at check time too.
DEFAULT_PERSONA = ROOT / "jd_search" / "persona.md"
DECISIONS_TSV = ROOT / "jd_search" / "decisions.tsv"
DECISIONS_MD = ROOT / "jd_search" / "decisions.md"

VERDICTS = {"APPLY", "BORDERLINE", "SKIP", "VISA-BLOCKED"}
CONFIDENCES = {"HIGH", "MEDIUM", "LOW"}
VISA_STATUSES = {"PASS", "VERIFY", "DEAD"}
DECISION_FIELDS = [
    "cache_key",
    "decided_at",
    "source_type",
    "source",
    "title",
    "company",
    "verdict",
    "confidence",
    "visa_status",
    "agent",
    "decision_json",
]

DEAD_VISA_PATTERNS: list[tuple[str, str]] = [
    ("Australian citizenship", r"\baustralian citizen(s|ship)?\b|\bcitizenship required\b"),
    ("Permanent residency", r"\bpermanent resident(s)?\b|\bpermanent residency\b|\bpr required\b"),
    ("Security clearance", r"\bsecurity clearance\b|\bagsva\b|\bnv1\b|\bnv2\b|\bbaseline clearance\b"),
    (
        "Continuous Australian residency",
        r"\bcontinuous australian residency\b|(?:3|three|5|five)\+?\s+years?.{0,40}\bresiden(?:t|cy)\b",
    ),
]
VERIFY_VISA_PATTERNS: list[tuple[str, str]] = [
    ("Unrestricted work rights", r"\bunrestricted (work|working) rights\b"),
    ("Full working rights", r"\bfull (work|working) rights\b"),
    ("Valid Australian work rights", r"\bvalid australian (work|working) rights\b"),
    ("No sponsorship", r"\b(no|not)\s+(visa\s+)?sponsor(ship)?\b|\bmust not require sponsorship\b"),
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


class VisibleTextExtractor(HTMLParser):
    BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "figure",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
    SKIP_TAGS = {"script", "style", "svg", "canvas", "noscript", "head"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def append_break(self) -> None:
        if not self.parts or self.parts[-1].endswith("\n"):
            return
        self.parts.append("\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "li":
            self.append_break()
            self.parts.append("- ")
        elif tag in self.BLOCK_TAGS:
            self.append_break()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.append_break()

    def handle_data(self, data: str) -> None:
        if not self.skip_depth and data.strip():
            self.parts.append(data)


def html_to_text(html_text: str) -> str:
    extractor = VisibleTextExtractor()
    extractor.feed(html_text)
    return normalize_text("".join(extractor.parts))


def run_clipboard_command(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0 and completed.stderr.strip():
        fail(completed.stderr.strip())
    return completed.stdout


def read_clipboard() -> str:
    """Mirror of scripts/import_job.py::read_clipboard so triage can accept
    the same `FROM=clipboard` UX as `make import-job`. Cross-platform fallback
    chain: pbpaste (macOS) → powershell Get-Clipboard (Windows) →
    wl-paste / xclip / xsel (Linux)."""
    if sys.platform == "darwin" and shutil.which("pbpaste"):
        return run_clipboard_command(["pbpaste"])
    if os.name == "nt" and shutil.which("powershell"):
        return run_clipboard_command(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"]
        )
    for binary, command in (
        ("wl-paste", ["wl-paste", "--no-newline"]),
        ("xclip", ["xclip", "-selection", "clipboard", "-o"]),
        ("xsel", ["xsel", "--clipboard", "--output"]),
    ):
        if shutil.which(binary):
            return run_clipboard_command(command)
    fail("No supported clipboard reader found. On macOS this expects pbpaste.")


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 JDcook triage/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read()
    except urllib.error.URLError as exc:
        fail(f"URL fetch failed: {exc}")
    return html_to_text(raw.decode(charset, errors="replace"))


def read_job(job: str) -> tuple[str, str, str]:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", job):
        fail("JOB must be a lowercase slug using letters, numbers, and hyphens.")
    path = ROOT / "jobs" / f"{job}.md"
    if not path.exists():
        fail(f"Missing imported job: {rel(path)}")
    return path.read_text(encoding="utf-8"), "job", rel(path)


def read_input(args: argparse.Namespace) -> tuple[str, str, str]:
    sources = [bool(args.url), bool(args.file), bool(args.job), bool(args.from_)]
    if sum(sources) > 1:
        fail("Use only one of --url, --file, --job, or --from.")
    if args.url:
        return fetch_url(args.url), "url", args.url
    if args.from_:
        # FROM=clipboard mirrors `make import-job FROM=clipboard`. Anything
        # else is treated as a file path so users can write either
        # `FROM=/tmp/jd.txt` or the older `FILE=/tmp/jd.txt`.
        if args.from_.lower() == "clipboard":
            text = read_clipboard()
            if not text.strip():
                fail(
                    "Clipboard is empty or unavailable to this runtime. Copy the JD body, "
                    "then run `make triage FROM=clipboard`; if `pbpaste` works in your "
                    "own terminal but fails inside Codex, save the JD to a file and use "
                    "`make triage FROM=/path/to/jd.txt`."
                )
            return text, "clipboard", "clipboard"
        path = resolve_path(args.from_)
        if not path.exists():
            fail(f"Missing JD file: {path}")
        return path.read_text(encoding="utf-8"), "file", str(path)
    if args.file:
        path = resolve_path(args.file)
        if not path.exists():
            fail(f"Missing JD file: {path}")
        return path.read_text(encoding="utf-8"), "file", str(path)
    if args.job:
        return read_job(args.job)
    if sys.stdin.isatty():
        fail("Pass --url, --file, --job, --from, or pipe JD text on stdin.")
    return sys.stdin.read(), "stdin", "stdin"


def cache_key(source_type: str, source: str, jd_text: str) -> str:
    if source_type == "url":
        material = f"url:{source.strip().lower()}"
    elif source_type in {"file", "job"}:
        material = f"{source_type}:{source}:{hashlib.sha256(jd_text.encode()).hexdigest()}"
    else:
        # stdin / clipboard / inline / anything else: dedup by content alone so
        # the same pasted JD reuses an earlier verdict regardless of how it
        # arrived (pbpaste pipe vs `FROM=clipboard` vs paste-into-file).
        material = f"paste:{hashlib.sha256(jd_text.encode()).hexdigest()}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def visa_precheck(jd_text: str) -> dict[str, Any]:
    text = jd_text.lower()
    dead = [label for label, pattern in DEAD_VISA_PATTERNS if re.search(pattern, text, flags=re.I)]
    if dead:
        return {"visa_status": "DEAD", "matches": dead}
    verify = [label for label, pattern in VERIFY_VISA_PATTERNS if re.search(pattern, text, flags=re.I)]
    if verify:
        return {"visa_status": "VERIFY", "matches": verify}
    return {"visa_status": "PASS", "matches": []}


def extract_metadata(jd_text: str, source: str) -> tuple[str, str]:
    title = ""
    company = ""
    title_match = re.search(r"^- Page title:\s*(.+)$", jd_text, flags=re.M)
    if title_match:
        title = title_match.group(1).strip()
    heading_match = re.search(r"^# Job Description:\s*(.+)$", jd_text, flags=re.M)
    if not title and heading_match:
        title = heading_match.group(1).strip()
    for label in ("Company", "Company name"):
        match = re.search(rf"^- {label}:\s*(.+)$", jd_text, flags=re.M)
        if match:
            company = match.group(1).strip()
            break
    return title or source, company


def load_cached_decision(key: str) -> dict[str, Any] | None:
    """Return the LATEST decision matching this cache key.

    Iterates the entire file (not break-on-first) so that if a duplicate
    or a re-judgement was appended later, we surface the freshest verdict.
    Skips spurious duplicate-header rows where cache_key == "cache_key".
    """
    if not DECISIONS_TSV.exists():
        return None
    latest: dict[str, Any] | None = None
    with DECISIONS_TSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row.get("cache_key") != key:
                continue
            try:
                latest = json.loads(row.get("decision_json", "{}"))
            except json.JSONDecodeError:
                continue
    return latest


def needs_header(path: Path) -> bool:
    """Return True only when the file is missing or its first line is not the header.

    Robust against accidental file deletion + concurrent appends:
    checks actual content, not just file existence.
    """
    if not path.exists():
        return True
    try:
        with path.open("r", encoding="utf-8") as handle:
            first_line = handle.readline().strip()
    except OSError:
        return True
    return not first_line.startswith(DECISION_FIELDS[0])


def append_decision(
    key: str,
    source_type: str,
    source: str,
    title: str,
    company: str,
    agent: str,
    decision: dict[str, Any],
) -> None:
    DECISIONS_TSV.parent.mkdir(parents=True, exist_ok=True)
    decided_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    row = {
        "cache_key": key,
        "decided_at": decided_at,
        "source_type": source_type,
        "source": source,
        "title": title,
        "company": company,
        "verdict": decision.get("verdict", ""),
        "confidence": decision.get("confidence", ""),
        "visa_status": decision.get("visa_status", ""),
        "agent": agent,
        "decision_json": json.dumps(decision, ensure_ascii=False, separators=(",", ":")),
    }
    write_header = needs_header(DECISIONS_TSV)
    with DECISIONS_TSV.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_FIELDS, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    with DECISIONS_MD.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {decided_at} - {decision.get('verdict', '')} - {title}\n\n")
        handle.write(f"- Cache key: `{key}`\n")
        handle.write(f"- Source: {source}\n")
        if company:
            handle.write(f"- Company: {company}\n")
        handle.write(f"- Visa: {decision.get('visa_status', '')}\n")
        handle.write(f"- Confidence: {decision.get('confidence', '')}\n")
        handle.write("\n### Evidence Matches\n\n")
        for item in decision.get("evidence_matches", []):
            handle.write(f"- {item}\n")
        handle.write("\n### Concerns\n\n")
        for item in decision.get("concerns", []):
            handle.write(f"- {item}\n")
        handle.write("\n### Next Action\n\n")
        handle.write(f"{decision.get('next_action', '')}\n\n")
        handle.write("### Reasoning\n\n")
        handle.write(f"{decision.get('reasoning', '')}\n")


def blocked_decision(matches: list[str]) -> dict[str, Any]:
    matched = ", ".join(matches)
    return {
        "verdict": "VISA-BLOCKED",
        "confidence": "HIGH",
        "visa_status": "DEAD",
        "evidence_matches": [],
        "concerns": [f"Visa hard dealbreaker matched: {matched}."],
        "next_action": "Skip this JD unless the visa/citizenship requirement is confirmed to be incorrect.",
        "reasoning": "The JD appears to require a visa status or clearance that is incompatible with the current persona. Technical fit is not judged because the deterministic visa layer blocked the role.",
    }


def build_prompt(persona: str, jd_text: str, precheck: dict[str, Any]) -> str:
    return f"""You are a job-fit judge for JDcook.

Read the user persona and the job description. Decide whether this JD is worth applying to.

Return ONLY a valid JSON object with exactly these keys:

{{
  "verdict": "APPLY" | "BORDERLINE" | "SKIP" | "VISA-BLOCKED",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "visa_status": "PASS" | "VERIFY" | "DEAD",
  "evidence_matches": ["short evidence-grounded reason", "..."],
  "concerns": ["short missing evidence or risk", "..."],
  "next_action": "one sentence recommendation",
  "reasoning": "2-3 sentences explaining the verdict"
}}

Rules:
- Do not include a numeric score.
- Use the persona's hard dealbreakers strictly.
- If visa is ambiguous, use "VERIFY" and explain the HR check needed.
- Judge semantic fit against the evidence base, not only exact keywords.
- Do not invent evidence. If support is weak, put it in concerns.
- Keep evidence_matches and concerns concise.

Deterministic visa precheck from the script:
{json.dumps(precheck, ensure_ascii=False, indent=2)}

PERSONA:
{persona}

JOB DESCRIPTION:
{jd_text[:20000]}
"""


AGENT_TIMEOUT_SECS = 120  # generous for a 5-30s LLM judgment; aborts if stuck


def run_agent(agent: str, prompt: str) -> str:
    if agent == "print":
        print(prompt)
        return ""
    if agent == "codex":
        # read-only sandbox: triage never writes files via the agent — it only
        # asks for JSON output, which we parse and persist ourselves in Python.
        # --ephemeral: triage is a one-shot judge with no persistent state, so
        # we tell Codex not to write anything to ~/.codex/sessions. Without
        # this, the sandbox blocks Codex's own session-file writes (which live
        # outside the workspace) and the call dies with a permission error
        # — even though our prompt is purely read-only.
        # `--full-auto` is intentionally omitted: deprecated in current Codex
        # CLI and its semantics conflict with read-only.
        # If your Codex build does not support `read-only` or `--ephemeral`,
        # remove the flag(s) and switch sandbox back to `workspace-write`.
        command = [
            "codex",
            "exec",
            "--cd",
            str(ROOT),
            "--sandbox",
            "read-only",
            "--ephemeral",
            "-",
        ]
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=AGENT_TIMEOUT_SECS,
            )
        except subprocess.TimeoutExpired:
            fail(f"codex judge timed out after {AGENT_TIMEOUT_SECS}s.")
    elif agent == "claude":
        command = ["claude", "-p", prompt]
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=AGENT_TIMEOUT_SECS,
            )
        except subprocess.TimeoutExpired:
            fail(f"claude judge timed out after {AGENT_TIMEOUT_SECS}s.")
    else:
        fail(f"Unknown agent: {agent}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        fail(f"{agent} judge failed with exit code {result.returncode}: {detail}")
    return f"{result.stdout}\n{result.stderr}".strip()


def extract_json_object(text: str) -> dict[str, Any]:
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    candidates = fenced or [text[i:] for i, ch in enumerate(text) if ch == "{"]
    decoder = json.JSONDecoder()
    parsed: list[dict[str, Any]] = []
    for candidate in candidates:
        try:
            obj, _end = decoder.raw_decode(candidate.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "verdict" in obj:
            parsed.append(obj)
    if not parsed:
        fail("Could not parse a JSON verdict from agent output.")
    return parsed[-1]


def validate_decision(decision: dict[str, Any]) -> dict[str, Any]:
    verdict = str(decision.get("verdict", "")).upper()
    confidence = str(decision.get("confidence", "")).upper()
    visa_status = str(decision.get("visa_status", "")).upper()
    if verdict not in VERDICTS:
        fail(f"Invalid verdict from judge: {verdict}")
    if confidence not in CONFIDENCES:
        fail(f"Invalid confidence from judge: {confidence}")
    if visa_status not in VISA_STATUSES:
        fail(f"Invalid visa_status from judge: {visa_status}")
    decision["verdict"] = verdict
    decision["confidence"] = confidence
    decision["visa_status"] = visa_status
    for key in ("evidence_matches", "concerns"):
        value = decision.get(key, [])
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            value = []
        decision[key] = [str(item).strip() for item in value if str(item).strip()]
    decision["next_action"] = str(decision.get("next_action", "")).strip()
    decision["reasoning"] = str(decision.get("reasoning", "")).strip()
    return decision


RECOMMENDATION_HEADLINE = {
    "APPLY": "RECOMMENDATION: APPLY — worth tailoring a resume for this role.",
    "BORDERLINE": "RECOMMENDATION: BORDERLINE — review concerns before deciding.",
    "SKIP": "RECOMMENDATION: SKIP — does not fit your profile well.",
    "VISA-BLOCKED": "RECOMMENDATION: SKIP — visa hard dealbreaker matched.",
}


def print_decision(decision: dict[str, Any], title: str, company: str, cached: bool) -> None:
    verdict = decision["verdict"]
    confidence = decision["confidence"]
    visa_status = decision["visa_status"]
    headline = RECOMMENDATION_HEADLINE.get(verdict, f"RECOMMENDATION: {verdict}")
    # First line: a one-glance recommendation so the user does not have to
    # read three blocks of evidence to find the verb.
    print(f"{headline} (confidence {confidence}, visa {visa_status})")
    print("")
    prefix = "Cached " if cached else ""
    print(f"=== {prefix}JD Triage Verdict ===")
    print(f"Title: {title}")
    if company:
        print(f"Company: {company}")
    print(f"Verdict: {verdict}")
    print(f"Confidence: {confidence}")
    print(f"Visa: {visa_status}")
    print("")
    print("Evidence matches:")
    for item in decision.get("evidence_matches", []) or ["(none)"]:
        print(f"- {item}")
    print("")
    print("Concerns:")
    for item in decision.get("concerns", []) or ["(none)"]:
        print(f"- {item}")
    print("")
    print(f"Next action: {decision.get('next_action', '')}")
    second = decision.get("_second_judge")
    if isinstance(second, dict):
        print("")
        print("Second judge:")
        print(
            f"- Verdict: {second.get('verdict', '')}; "
            f"Confidence: {second.get('confidence', '')}; "
            f"Visa: {second.get('visa_status', '')}"
        )
        if (
            second.get("verdict") != decision.get("verdict")
            or second.get("visa_status") != decision.get("visa_status")
        ):
            print("- Disagreement: review both judgments manually before acting.")
    print("")
    print(decision.get("reasoning", ""))


def should_run_second_judge(decision: dict[str, Any]) -> bool:
    return (
        decision.get("verdict") == "BORDERLINE"
        or decision.get("confidence") == "LOW"
        or decision.get("visa_status") == "VERIFY"
    )


# Verdicts that should block downstream actions (e.g. make draft refusing
# to draft for a citizen-only role). APPLY and BORDERLINE are allowed through.
BLOCKING_VERDICTS = {"SKIP", "VISA-BLOCKED"}


def judge_jd(
    jd_text: str,
    persona: str,
    agent: str,
    *,
    source_type: str = "inline",
    source: str = "inline",
    use_cache: bool = True,
    refresh: bool = False,
    second_agent: str | None = None,
) -> tuple[dict[str, Any], bool]:
    """Run the full triage pipeline on raw JD text and return (decision, was_cached).

    This is the importable entry point used by `scripts/draft_resume.py`. The
    `main()` CLI in this module also calls it under the hood, so the CLI and
    the in-process callers share the same logic, caching, and visa precheck.
    """
    jd_text = normalize_text(jd_text)
    if len(jd_text) < 80:
        fail("JD text is too short to triage.")

    key = cache_key(source_type, source, jd_text)
    title, company = extract_metadata(jd_text, source)

    if use_cache and not refresh:
        cached = load_cached_decision(key)
        if cached:
            return validate_decision(cached), True

    precheck = visa_precheck(jd_text)
    if precheck["visa_status"] == "DEAD":
        decision = blocked_decision(precheck["matches"])
    else:
        prompt = build_prompt(persona, jd_text, precheck)
        output = run_agent(agent, prompt)
        decision = validate_decision(extract_json_object(output))
        if precheck["visa_status"] == "VERIFY" and decision["visa_status"] == "PASS":
            decision["visa_status"] = "VERIFY"
            decision.setdefault("concerns", []).append(
                "Deterministic visa precheck found wording that should be verified with HR."
            )
        if second_agent and second_agent != agent and should_run_second_judge(decision):
            second_output = run_agent(second_agent, prompt)
            second = validate_decision(extract_json_object(second_output))
            if precheck["visa_status"] == "VERIFY" and second["visa_status"] == "PASS":
                second["visa_status"] = "VERIFY"
            decision["_second_judge"] = second

    if use_cache:
        append_decision(key, source_type, source, title, company, agent, decision)
    return decision, False


def judge_imported_job(
    job_slug: str,
    agent: str,
    *,
    persona_path: Path | None = None,
    use_cache: bool = True,
    refresh: bool = False,
    second_agent: str | None = None,
) -> tuple[dict[str, Any], bool, str, str]:
    """Convenience wrapper used by `scripts/draft_resume.py`.

    Reads `jobs/<slug>.md` and `jd_search/persona.md`, then delegates to
    `judge_jd`. Returns (decision, was_cached, title, company) so the caller
    can print a short summary.
    """
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", job_slug):
        fail("JOB must be a lowercase slug using letters, numbers, and hyphens.")
    job_path = ROOT / "jobs" / f"{job_slug}.md"
    if not job_path.exists():
        fail(f"Missing imported job: {rel(job_path)}")

    persona_file = persona_path or DEFAULT_PERSONA
    if not persona_file.exists():
        fail(
            f"Missing persona file: {rel(persona_file) if persona_file.is_relative_to(ROOT) else persona_file}"
        )

    jd_text = job_path.read_text(encoding="utf-8")
    persona = persona_file.read_text(encoding="utf-8")
    decision, cached = judge_jd(
        jd_text,
        persona,
        agent,
        source_type="job",
        source=rel(job_path),
        use_cache=use_cache,
        refresh=refresh,
        second_agent=second_agent,
    )
    title, company = extract_metadata(normalize_text(jd_text), rel(job_path))
    return decision, cached, title, company


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Triage one JD against jd_search/persona.md using LLM-as-judge.")
    parser.add_argument("--url")
    parser.add_argument("--file")
    parser.add_argument("--job")
    parser.add_argument(
        "--from",
        dest="from_",
        help="Shorthand for --file or 'clipboard'. Mirrors `make import-job FROM=...`.",
    )
    parser.add_argument("--persona", default=str(DEFAULT_PERSONA.relative_to(ROOT)))
    parser.add_argument("--agent", default="codex", choices=("codex", "claude", "print"))
    parser.add_argument("--second-agent", choices=("codex", "claude"))
    parser.add_argument("--refresh", action="store_true", help="Ignore an existing cached decision and re-judge.")
    parser.add_argument("--no-cache", action="store_true", help="Do not read or write decisions.tsv/decisions.md.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    persona_path = resolve_path(args.persona)
    if not persona_path.exists():
        fail(f"Missing persona file: {rel(persona_path) if persona_path.is_relative_to(ROOT) else persona_path}")
    persona = persona_path.read_text(encoding="utf-8")
    jd_text, source_type, source = read_input(args)

    # `--agent print` is a CLI-only debugging helper that dumps the prompt and
    # exits before any LLM call. Keep it out of the importable judge_jd path.
    if args.agent == "print":
        normalized = normalize_text(jd_text)
        if len(normalized) < 80:
            fail("JD text is too short to triage.")
        precheck = visa_precheck(normalized)
        if precheck["visa_status"] == "DEAD":
            print(f"[print mode] visa precheck: DEAD ({', '.join(precheck['matches'])})")
            print("[print mode] no prompt would be sent to an agent for a DEAD visa.")
            return
        print(build_prompt(persona, normalized, precheck))
        return

    decision, cached = judge_jd(
        jd_text,
        persona,
        args.agent,
        source_type=source_type,
        source=source,
        use_cache=not args.no_cache,
        refresh=args.refresh,
        second_agent=args.second_agent,
    )
    title, company = extract_metadata(normalize_text(jd_text), source)
    print_decision(decision, title, company, cached=cached)


if __name__ == "__main__":
    main()
