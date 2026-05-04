#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

from raw_cache import ensure_raw_cache

# Import the triage judge so `make draft` can refuse JDs that triage flags as
# SKIP or VISA-BLOCKED. Path manipulation keeps this script runnable from
# anywhere without packaging.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "jd_search"))
from triage import (  # noqa: E402
    BLOCKING_VERDICTS,
    judge_imported_job,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTEXT_LIMIT = 2
DEFAULT_CONTEXT_THRESHOLD = 25.0
ALLOWED_SAMPLE_STATUSES = {"official", "legacy", "validation-sample", "archive"}
STOPWORDS = {
    "about",
    "across",
    "after",
    "also",
    "and",
    "application",
    "apply",
    "any",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "candidate",
    "candidates",
    "adjustments",
    "background",
    "backgrounds",
    "collaboration",
    "collaborative",
    "company",
    "communication",
    "degree",
    "description",
    "development",
    "during",
    "excellent",
    "experience",
    "engineer",
    "engineering",
    "for",
    "from",
    "global",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "job",
    "knowledge",
    "imported",
    "interpersonal",
    "looking",
    "mode",
    "of",
    "on",
    "or",
    "our",
    "professionals",
    "requirements",
    "role",
    "skills",
    "solid",
    "source",
    "strong",
    "support",
    "supporting",
    "team",
    "technologies",
    "technology",
    "that",
    "the",
    "their",
    "this",
    "to",
    "type",
    "understanding",
    "using",
    "various",
    "we",
    "will",
    "work",
    "working",
    "with",
    "you",
    "your",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def draft_path(job: str) -> Path:
    return ROOT / "drafts" / f"{job}.tex"


def ai_snapshot_path(job: str) -> Path:
    return ROOT / "edits" / job / "ai-draft.tex"


def context_path(job: str) -> Path:
    return ROOT / "edits" / job / "context.md"


def metadata_path(job_dir: Path) -> Path:
    return job_dir / "metadata.md"


def metadata_fields(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- \*\*(.+?):\*\*\s*(.*)$", line)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def sample_status(job_dir: Path) -> str | None:
    value = metadata_fields(metadata_path(job_dir)).get("Status")
    if value is None:
        return None
    if value not in ALLOWED_SAMPLE_STATUSES:
        return "invalid"
    return value


def is_official_sample(job_dir: Path) -> bool:
    approved_root = ROOT / "approved"
    try:
        relative_parts = job_dir.relative_to(approved_root).parts
    except ValueError:
        return False
    if len(relative_parts) != 1:
        return False
    if relative_parts[0].startswith("_"):
        return False
    status = sample_status(job_dir)
    return status is None or status == "official"


def raw_has_evidence() -> bool:
    raw_dir = ROOT / "raw"
    if not raw_dir.exists():
        return False
    return any(
        path.is_file()
        for path in raw_dir.rglob("*")
        if not path.name.startswith(".") and path.name != "_TEMPLATE.md"
    )


def tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z][a-z0-9+#.-]{1,}", text.lower())
    return {
        token.strip(".-")
        for token in tokens
        if len(token.strip(".-")) >= 2 and token.strip(".-") not in STOPWORDS
    }


def role_family_terms(tokens: set[str]) -> set[str]:
    families = {
        "frontend": {"frontend", "front-end", "react", "ui", "javascript", "typescript"},
        "backend": {"backend", "back-end", "api", "server", "node", "flask", "django"},
        "data": {"data", "analytics", "analyst", "sql", "database", "python", "reporting", "pipeline"},
        "finance": {"finance", "financial", "trading", "investment", "portfolio", "quant", "market"},
        "testing": {"test", "testing", "sdet", "qa", "automation", "cypress", "jest", "pytest"},
        "ml": {"ml", "ai", "machine", "learning", "rag", "llm", "model", "pytorch"},
        "network": {"network", "routing", "tcp", "udp", "linux", "unix", "protocol"},
    }
    matched: set[str] = set()
    for family, terms in families.items():
        if tokens & terms:
            matched.add(family)
    return matched


def official_approved_candidates(current_job: str) -> list[Path]:
    approved_root = ROOT / "approved"
    if not approved_root.exists():
        return []
    return sorted(
        path
        for path in approved_root.iterdir()
        if path.is_dir()
        and path.name != current_job
        and is_official_sample(path)
        and (path / f"{path.name}.tex").exists()
    )


def score_candidate(current_tokens: set[str], current_families: set[str], candidate_dir: Path) -> dict[str, object]:
    slug = candidate_dir.name
    jd_path = ROOT / "jobs" / f"{slug}.md"
    tex_path = candidate_dir / f"{slug}.tex"
    if jd_path.exists():
        source_text = jd_path.read_text(encoding="utf-8", errors="ignore")
    else:
        source_text = tex_path.read_text(encoding="utf-8", errors="ignore")

    candidate_tokens = tokenize(source_text + "\n" + slug.replace("-", " "))
    overlap = current_tokens & candidate_tokens
    candidate_families = role_family_terms(candidate_tokens)
    family_overlap = current_families & candidate_families
    denominator = math.sqrt(max(len(current_tokens), 1) * max(len(candidate_tokens), 1))
    normalized_overlap = (len(overlap) / denominator) * 100
    high_signal_overlap = {
        token
        for token in overlap
        if token
        in {
            "ai",
            "analytics",
            "api",
            "automation",
            "backend",
            "c++",
            "cloud",
            "data",
            "database",
            "finance",
            "financial",
            "flask",
            "frontend",
            "investment",
            "javascript",
            "linux",
            "ml",
            "mongodb",
            "network",
            "node",
            "portfolio",
            "python",
            "quant",
            "react",
            "rest",
            "sql",
            "testing",
            "trading",
            "typescript",
            "unix",
        }
    }
    score = normalized_overlap + 8.0 * len(family_overlap) + 3.0 * len(high_signal_overlap)
    if jd_path.exists():
        score += 0.5
    if tex_path.exists():
        score += 0.5

    matched_terms = sorted(overlap, key=lambda token: (-len(token), token))[:12]
    return {
        "slug": slug,
        "tex_path": tex_path,
        "jd_path": jd_path,
        "score": score,
        "matched_terms": matched_terms,
        "family_overlap": sorted(family_overlap),
        "mtime": tex_path.stat().st_mtime if tex_path.exists() else candidate_dir.stat().st_mtime,
    }


def select_context_examples(
    job: str,
    job_text: str,
    limit: int = DEFAULT_CONTEXT_LIMIT,
    threshold: float = DEFAULT_CONTEXT_THRESHOLD,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    current_tokens = tokenize(job_text)
    current_families = role_family_terms(current_tokens)
    scored = [
        score_candidate(current_tokens, current_families, candidate)
        for candidate in official_approved_candidates(job)
    ]
    scored.sort(key=lambda item: (-float(item["score"]), -float(item["mtime"]), str(item["slug"])))
    selected = [item for item in scored if float(item["score"]) >= threshold][:limit]
    skipped = [item for item in scored if item not in selected]
    return selected, skipped


def write_context_file(
    job: str,
    job_text: str,
    force: bool,
    limit: int,
    threshold: float,
) -> tuple[Path, list[dict[str, object]]]:
    selected, skipped = select_context_examples(job, job_text, limit=limit, threshold=threshold)
    path = context_path(job)
    if path.exists() and not force:
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Draft Context: {job}",
        "",
        f"- Generated at: {dt.datetime.now(dt.UTC).isoformat()}",
        "- Generated by: `make draft` context selector",
        f"- Selection limit: {limit}",
        f"- Minimum score: {threshold:.1f}",
        "",
        "## Draft-Time Context Contract",
        "",
        "- Read this file before using approved examples.",
        "- Read only the selected approved examples listed below.",
        "- Do not scan `approved/` recursively during drafting.",
        "- Do not read `edits/*/note.md` during drafting; notes are audit records, not generation context.",
        "- Approved examples are structural examples only; never treat them as fact sources.",
        "- If no examples are selected, use the template and rule files only.",
        "",
        "## Selected Approved Examples",
        "",
    ]
    if selected:
        for idx, item in enumerate(selected, 1):
            matched = ", ".join(item["matched_terms"]) or "none"
            families = ", ".join(item["family_overlap"]) or "none"
            lines.extend(
                [
                    f"{idx}. `{rel(item['tex_path'])}`",
                    f"   - Score: {float(item['score']):.1f}",
                    f"   - Role-family overlap: {families}",
                    f"   - Matched terms: {matched}",
                    "",
                ]
            )
    else:
        lines.append("- None selected; no official sample crossed the similarity threshold.")
        lines.append("")

    lines.extend(["## Skipped Official Samples", ""])
    if skipped:
        for item in skipped[:12]:
            matched = ", ".join(item["matched_terms"][:6]) or "none"
            reason = "below threshold" if float(item["score"]) < threshold else "lower ranked than selected examples"
            lines.append(f"- `{item['slug']}` — score {float(item['score']):.1f}; {reason}; matched: {matched}")
    else:
        lines.append("- None.")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path, selected


def build_prompt(job: str, force: bool, draft_context: Path) -> str:
    overwrite = (
        "Overwrite `drafts/{job}.tex` if it already exists."
        if force
        else "Do not overwrite `drafts/{job}.tex` if it already exists."
    ).format(job=job)
    return f"""Use the `drafting-resume-from-confirmed-assets` skill.

Draft a targeted resume for this imported job:

- JD: `jobs/{job}.md`
- Evidence base: all confirmed source material under `raw/`
- Draft context: `{rel(draft_context)}`
- Output file: `drafts/{job}.tex`

Requirements:

- Read `{rel(draft_context)}` before using approved examples.
- Read approved examples only if they are explicitly listed in `{rel(draft_context)}`.
- Do not scan `approved/` recursively and do not read `edits/*/note.md` during drafting.
- Follow the skill's full workflow, schema, bullet rules, canonical rules, and local preferences.
- Use `references/latex-template.local.tex` if available; otherwise use `references/latex-template.tex`.
- Write exactly one LaTeX file at `drafts/{job}.tex`.
- {overwrite}
- Keep every resume bullet in the required `\\resumeItem{{\\normalsize{{...}}}}` shape.
- Put a `% src:` line immediately after every bullet.
- Add `% TODO:` gap comments for JD requirements not supported by raw evidence.
- Do not compile the PDF; the user will run `make preview` or `make check` after reviewing the draft.
- After writing the file, print a concise summary with bullet count, TODO count, and the main uncovered JD gaps.
"""


def choose_agent(requested: str) -> str:
    if requested != "auto":
        return requested
    if shutil.which("codex"):
        return "codex"
    if shutil.which("claude"):
        return "claude"
    fail("No local draft agent found. Install/login to Codex or Claude, or run `AGENT=print make draft JOB=<slug>` only to inspect the prompt.")


def run_agent(agent: str, prompt: str) -> None:
    if agent == "print":
        print(prompt)
        return

    if agent == "codex":
        # `--full-auto` is deprecated in current Codex CLI; rely on
        # `--sandbox workspace-write` for edit scope and `--ephemeral` to avoid
        # nested Codex session writes under ~/.codex/sessions.
        command = [
            "codex",
            "exec",
            "--cd",
            str(ROOT),
            "--sandbox",
            "workspace-write",
            "--ephemeral",
            "-",
        ]
        result = subprocess.run(command, cwd=ROOT, input=prompt, text=True)
    elif agent == "claude":
        # Claude CLI rejects a positional prompt when other flags follow `-p`;
        # it requires the prompt via stdin or --prompt. Pipe via stdin so the
        # full prompt (including newlines) survives without shell quoting.
        command = [
            "claude",
            "-p",
            "--permission-mode",
            "acceptEdits",
            "--allowedTools",
            "Read,Write,Edit,Glob,Grep",
        ]
        result = subprocess.run(command, cwd=ROOT, input=prompt, text=True)
    else:
        fail(f"Unknown draft agent: {agent}. Use AGENT=auto, codex, claude, or print.")

    if result.returncode != 0:
        fail(f"Draft agent failed with exit code {result.returncode}.")


def snapshot_ai_draft(job: str, force: bool) -> None:
    src = draft_path(job)
    dst = ai_snapshot_path(job)
    if not src.exists():
        fail(f"Missing generated draft: {rel(src)}")
    if dst.exists() and not force:
        fail(f"AI draft snapshot already exists: {rel(dst)}. Use FORCE=1 only for an intentional replacement.")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def import_from_inbox(job: str, force: bool) -> None:
    """Special-case auto-import: pull the staged JD body from
    jd_search/inbox/<slug>.md (produced by `make scan-jobs`) into
    jobs/<slug>.md. This skips import_job.py because we already have a
    normalized JD body on disk.
    """
    staged = ROOT / "jd_search" / "inbox" / f"{job}.md"
    if not staged.exists():
        fail(
            f"Slug `{job}` not found in jd_search/inbox/. "
            "Run `make inbox` to list available candidates, "
            "or `make scan-jobs SEARCH=<slug>` to populate the inbox."
        )
    target = ROOT / "jobs" / f"{job}.md"
    if target.exists() and not force:
        fail(
            f"`{rel(target)}` already exists; refusing to re-import. "
            "Pass FORCE=1 to overwrite."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(staged.read_text(encoding="utf-8"), encoding="utf-8")
    # Mirror import_job.py's source-snapshot convention so downstream tools
    # (status, abort, learn) see a consistent shape.
    snapshot_dir = ROOT / "jobs" / "_sources" / job
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "text.txt").write_text(staged.read_text(encoding="utf-8"), encoding="utf-8")
    (snapshot_dir / "metadata.json").write_text(
        '{"source_type": "jd_search-inbox", "staged_from": "'
        + str(staged.relative_to(ROOT))
        + '"}\n',
        encoding="utf-8",
    )
    print(f"Auto-imported from inbox: {rel(target)} ← {rel(staged)}")


def maybe_auto_import(job: str, args: argparse.Namespace) -> None:
    """If --from / --url is given and the JD has not been imported yet, run
    scripts/import_job.py inline (or, for FROM=inbox, pull from the inbox
    staging dir) so the user can do the whole flow in one command:

        make draft JOB=<slug> FROM=clipboard
        make draft JOB=<slug> FROM=inbox       (after `make scan-jobs`)
        make draft JOB=<slug> URL=...

    `import_job.py --from` only accepts the literal value `clipboard` — file
    paths and "inbox" are handled here, not via import_job.py.

    If the JD already exists, refuse to silently overwrite unless --force.
    """
    has_source = bool(args.from_ or args.url)
    if not has_source:
        return

    if args.from_ and args.from_.lower() == "inbox":
        import_from_inbox(job, args.force)
        return

    if args.from_ and args.from_.lower() != "clipboard":
        fail(
            f"`make draft FROM={args.from_}` is not supported: "
            "valid values are 'clipboard' or 'inbox', or pass URL=... instead. "
            "For a file, run `make import-job JOB={} FROM=clipboard` after "
            "copying the file content.".format(job)
        )

    job_path = ROOT / "jobs" / f"{job}.md"
    if job_path.exists() and not args.force:
        fail(
            f"`{rel(job_path)}` already exists; refusing to re-import. "
            "Pass FORCE=1 to overwrite, or drop FROM=/URL= to use the existing import."
        )

    print(f"Auto-importing JD before drafting: JOB={job}")
    import_cmd = [sys.executable, str(ROOT / "scripts" / "import_job.py"), "--job", job]
    if args.from_:
        import_cmd.extend(["--from", args.from_])
    if args.url:
        import_cmd.extend(["--url", args.url])
    if args.mode:
        import_cmd.extend(["--mode", args.mode])
    if args.force:
        import_cmd.append("--force")
    result = subprocess.run(import_cmd, cwd=ROOT)
    if result.returncode != 0:
        fail(f"Auto-import failed with exit code {result.returncode}.")


def draft(args: argparse.Namespace) -> None:
    job = args.job
    if not job:
        fail("`draft` requires --job.")

    maybe_auto_import(job, args)

    job_path = ROOT / "jobs" / f"{job}.md"
    if not job_path.exists():
        fail(
            f"Missing imported JD: {rel(job_path)}. "
            "Either pass FROM=clipboard / FROM=<file> / URL=... to auto-import, "
            f"or run `make import-job JOB={job} ...` first."
        )
    if not raw_has_evidence():
        fail("No raw evidence found under `raw/`. Add confirmed source material before drafting.")
    if draft_path(job).exists() and not args.force:
        fail(f"Draft already exists: {rel(draft_path(job))}. Use FORCE=1 only for an intentional replacement.")
    if ai_snapshot_path(job).exists() and not args.force:
        fail(f"AI draft snapshot already exists: {rel(ai_snapshot_path(job))}. Use FORCE=1 only for an intentional replacement.")
    if args.context_limit < 0:
        fail("--context-limit must be 0 or greater.")
    if args.context_threshold < 0:
        fail("--context-threshold must be 0 or greater.")

    agent = choose_agent(args.agent)
    ensure_raw_cache(quiet=False)

    # Pre-draft triage gate: refuse to draft for JDs the judge marks SKIP or
    # VISA-BLOCKED. Cached after the first run, so the second `make draft` of
    # the same JD does not re-judge. Bypass with FORCE=1.
    if agent != "print":
        triage_agent = "codex" if agent == "codex" else "claude"
        try:
            decision, cached, triage_title, _ = judge_imported_job(
                job, triage_agent
            )
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: triage check failed ({exc}); proceeding without gate.", file=sys.stderr)
            decision = None
        if decision is not None:
            verdict = decision.get("verdict", "")
            confidence = decision.get("confidence", "")
            visa = decision.get("visa_status", "")
            cache_tag = " [cached]" if cached else ""
            print(f"Triage{cache_tag}: {verdict} ({confidence}) — visa: {visa}")
            if verdict in BLOCKING_VERDICTS and not args.force:
                concerns = decision.get("concerns") or []
                print("Refusing to draft because triage blocked this JD:", file=sys.stderr)
                for item in concerns[:3]:
                    print(f"  - {item}", file=sys.stderr)
                reasoning = decision.get("reasoning", "").strip()
                if reasoning:
                    print(f"  Reasoning: {reasoning}", file=sys.stderr)
                print("Override with FORCE=1 if you have new context.", file=sys.stderr)
                raise SystemExit(2)
            if verdict in BLOCKING_VERDICTS and args.force:
                print("Triage block overridden by FORCE=1.")

    job_text = job_path.read_text(encoding="utf-8")
    draft_context, selected_examples = write_context_file(
        job,
        job_text,
        args.force,
        limit=args.context_limit,
        threshold=args.context_threshold,
    )
    prompt = build_prompt(job, args.force, draft_context)
    print(f"Draft request ready: {job}")
    print(f"- agent: {agent}")
    print(f"- JD: {rel(job_path)}")
    print(f"- context: {rel(draft_context)}")
    if selected_examples:
        selected = ", ".join(rel(item["tex_path"]) for item in selected_examples)
    else:
        selected = "none"
    print(f"- approved examples: {selected}")
    print(f"- output: {rel(draft_path(job))}")

    run_agent(agent, prompt)

    if agent == "print":
        print("Prompt printed only. This does not create a valid cycle snapshot. Use a supported agent through `make draft` to generate the draft.")
        return

    if not draft_path(job).exists():
        fail(f"Draft agent finished but did not create {rel(draft_path(job))}.")

    snapshot_ai_draft(job, args.force)
    print(f"Draft ready: {rel(draft_path(job))}")
    print(f"AI draft snapshot ready: {rel(ai_snapshot_path(job))}")
    print("Next: review/edit the draft, then run `make check JOB={}`.".format(job))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a resume draft via a local AI agent.")
    parser.add_argument("--job", required=True)
    parser.add_argument("--agent", default="auto", choices=("auto", "codex", "claude", "print"))
    parser.add_argument("--context-limit", type=int, default=DEFAULT_CONTEXT_LIMIT)
    parser.add_argument("--context-threshold", type=float, default=DEFAULT_CONTEXT_THRESHOLD)
    parser.add_argument("--force", action="store_true")
    # Optional auto-import: passing --from / --url runs import_job.py first
    # so the user can do  `make draft JOB=<slug> FROM=clipboard`  in one shot.
    parser.add_argument(
        "--from",
        dest="from_",
        help="Auto-import shorthand: 'clipboard' or a file path. Mirrors `make import-job FROM=...`.",
    )
    parser.add_argument("--url", help="Auto-import from a public URL before drafting.")
    parser.add_argument("--mode", choices=("auto", "http", "js"), help="URL fetch mode passed through to import_job.")
    return parser


def main() -> None:
    draft(build_parser().parse_args())


if __name__ == "__main__":
    main()
