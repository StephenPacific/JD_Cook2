#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERNAL_COMMENT_PREFIXES = ("% src:", "% TODO:")
ALLOWED_SAMPLE_STATUSES = {"official", "legacy", "validation-sample", "archive"}
PRESERVED_METADATA_FIELDS = (
    "Status",
    "Status notes",
    "Company",
    "Result",
    "Posting URL",
    "Job ID",
    "Applications close",
    "Cycle notes",
    "Legacy note",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def ensure_exists(path: Path, label: str) -> None:
    if not path.exists():
        fail(f"Missing {label}: {rel(path)}")


def write_new(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        fail(f"Refusing to overwrite existing file: {rel(path)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_new(src: Path, dst: Path, force: bool = False) -> None:
    ensure_exists(src, "source")
    if dst.exists() and not force:
        fail(f"Refusing to overwrite existing file: {rel(dst)}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def force_enabled(args: argparse.Namespace) -> bool:
    return bool(args.force or os.environ.get("FORCE") == "1")


def draft_tex(job: str) -> Path:
    return ROOT / "drafts" / f"{job}.tex"


def draft_pdf(job: str) -> Path:
    return ROOT / "build" / "pdf" / "drafts" / f"{job}.pdf"


def draft_log(job: str) -> Path:
    return ROOT / "build" / "latex" / "drafts" / job / f"{job}.log"


def approved_pdf(job: str) -> Path:
    return ROOT / "build" / "pdf" / "approved" / f"{job}.pdf"


def approved_log(job: str) -> Path:
    return ROOT / "build" / "latex" / "approved" / job / f"{job}.log"


def approved_dir(job: str) -> Path:
    return ROOT / "approved" / job


def approved_tex(job: str) -> Path:
    return approved_dir(job) / f"{job}.tex"


def public_tex(job: str) -> Path:
    return approved_dir(job) / f"{job}.public.tex"


def edits_dir(job: str) -> Path:
    return ROOT / "edits" / job


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


def classify_sample(job_dir: Path) -> str:
    approved_root = ROOT / "approved"
    try:
        relative_parts = job_dir.relative_to(approved_root).parts
    except ValueError:
        return "archive"

    if len(relative_parts) >= 2 and relative_parts[0] == "_validation":
        return "validation-sample"
    if relative_parts and relative_parts[0].startswith("_"):
        return "archive"

    status = sample_status(job_dir)
    if status is None:
        return "official"
    return status


def is_official_sample(job_dir: Path) -> bool:
    return classify_sample(job_dir) == "official"


def require_job(args: argparse.Namespace) -> str:
    if not args.job:
        fail(f"`{args.command}` requires --job.")
    return args.job


def official_sample_dirs() -> list[Path]:
    approved_root = ROOT / "approved"
    if not approved_root.exists():
        return []
    return sorted(
        path
        for path in approved_root.iterdir()
        if path.is_dir() and is_official_sample(path)
    )


def sample_dirs_for_job(job: str) -> list[Path]:
    approved_root = ROOT / "approved"
    candidates = [approved_dir(job)]
    if approved_root.exists():
        candidates.extend(
            path / job
            for path in sorted(approved_root.iterdir())
            if path.is_dir() and path.name.startswith("_")
        )
    return [path for path in candidates if path.exists()]


def begin(args: argparse.Namespace) -> None:
    job = require_job(args)
    src = draft_tex(job)
    dst = edits_dir(job) / "ai-draft.tex"
    copy_new(src, dst, force=force_enabled(args))
    print(f"Cycle snapshot ready: {rel(dst)}")


def page_count_from_log(log_text: str) -> int | None:
    matches = re.findall(r"Output written on .*?\((\d+)\s+p\s*a\s*g\s*es?", log_text, flags=re.S)
    return int(matches[-1]) if matches else None


def validate_resume_artifact(
    job: str,
    tex_path: Path,
    pdf_path: Path,
    log_path: Path,
    artifact_label: str,
) -> None:
    ensure_exists(tex_path, f"{artifact_label} tex")
    ensure_exists(pdf_path, f"compiled {artifact_label} PDF")
    ensure_exists(log_path, f"{artifact_label} LaTeX log")
    text = tex_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    bullet_lines = [
        (idx + 1, line)
        for idx, line in enumerate(lines)
        if r"\resumeItem{\normalsize" in line
    ]
    if len(bullet_lines) == 0:
        errors.append(
            r"No detectable resume bullets found. "
            r"Use the required shape \resumeItem{\normalsize{...}} followed by % src:."
        )
    if len(bullet_lines) > 10:
        errors.append(f"Bullet budget exceeded: {len(bullet_lines)} resume bullets found, max is 10.")

    for line_no, _line in bullet_lines:
        next_line = lines[line_no].strip() if line_no < len(lines) else ""
        if not next_line.startswith("% src:"):
            errors.append(f"Line {line_no}: resume bullet is not followed immediately by a % src: comment.")
            continue

        src_block: list[tuple[int, str]] = []
        cursor = line_no
        while cursor < len(lines) and lines[cursor].strip().startswith("% src:"):
            src_block.append((cursor + 1, lines[cursor].strip()))
            cursor += 1

        project_sources = {
            match.group(1)
            for _src_line_no, src_line in src_block
            if (match := re.search(r"% src:\s+(raw/code/[^:\s]+\.md)", src_line))
        }
        if len(project_sources) > 1:
            joined = ", ".join(sorted(project_sources))
            errors.append(
                f"Line {line_no}: resume bullet cites multiple raw/code project sources ({joined}). "
                "Use one project source per bullet or split the workstreams."
            )

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("% src:"):
            continue
        if "approved/" in stripped:
            errors.append(f"Line {idx}: % src must not point to approved/: {stripped}")
        if "latex-template.tex" in stripped:
            errors.append(f"Line {idx}: % src must not point to latex-template.tex.")

    if r"\mid" in text:
        errors.append(r"Found \mid in LaTeX body/template; use text-safe \textbar{} separators.")

    if r"\end{document}" not in text:
        errors.append(r"Missing \end{document}.")

    todo_count = len(re.findall(r"^% TODO:", text, flags=re.M))
    if todo_count == 0:
        errors.append("No % TODO: gap comments found. Keep the JD gap block visible before approval.")

    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    pages = page_count_from_log(log_text)
    if pages is None:
        errors.append(f"Could not determine PDF page count from {rel(log_path)}.")
    elif pages != 1:
        errors.append(f"PDF page count is {pages}; expected exactly 1 page.")

    public_errors = public_internal_comment_errors(job)
    errors.extend(public_errors)

    if errors:
        for item in errors:
            print(f"FAIL: {item}", file=sys.stderr)
        for item in warnings:
            print(f"WARN: {item}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Check passed: {job} ({artifact_label})")
    print(f"- bullets: {len(bullet_lines)}/10")
    print(f"- TODO gaps: {todo_count}")
    print(f"- PDF pages: {pages}")
    for item in warnings:
        print(f"WARN: {item}")


def check(args: argparse.Namespace) -> None:
    job = require_job(args)
    validate_resume_artifact(job, draft_tex(job), draft_pdf(job), draft_log(job), "draft")


def check_approved_job(job: str) -> None:
    sample_dir = approved_dir(job)
    ensure_exists(sample_dir, "approved sample directory")
    sample_class = classify_sample(sample_dir)
    if sample_class != "official":
        fail(f"Approved sample is {sample_class}; check-all only validates official samples.")
    validate_resume_artifact(job, approved_tex(job), approved_pdf(job), approved_log(job), "approved")


def approve(args: argparse.Namespace) -> None:
    job = require_job(args)
    force = force_enabled(args)
    dst_dir = approved_dir(job)
    if dst_dir.exists() and not force:
        fail(f"Approved artifact already exists: {rel(dst_dir)}. Use FORCE=1 only for an intentional replacement.")

    copy_new(draft_tex(job), approved_tex(job), force=force)
    copy_new(draft_pdf(job), dst_dir / f"{job}.pdf", force=force)
    export_public(args)

    jd_source = f"../../jobs/{job}.md" if (ROOT / "jobs" / f"{job}.md").exists() else "TODO"
    today = dt.date.today().isoformat()
    generated_fields = {
        "Internal audit LaTeX": f"`{job}.tex` (copied from `drafts/` on approve; keeps `% src:` / `% TODO:` comments)",
        "Public LaTeX": f"`{job}.public.tex` (auto-exported on approve; strips `% src:` / `% TODO:` comments)",
        "JD source": f"`{jd_source}`",
        "Submission date": today,
        "Company": "TODO",
        "Result": "TODO (update post-interview / rejection / offer for future reference)",
        "Compiled PDF": f"`{job}.pdf` (generated via `make approve JOB={job}`)",
        "Cycle notes": f"pending — run `make learn JOB={job}` after approval notes are ready.",
    }
    if force:
        existing_fields = metadata_fields(dst_dir / "metadata.md")
        for field in PRESERVED_METADATA_FIELDS:
            if field in existing_fields:
                generated_fields[field] = existing_fields[field]

    metadata_order = (
        "Status",
        "Status notes",
        "Internal audit LaTeX",
        "Public LaTeX",
        "JD source",
        "Submission date",
        "Company",
        "Job ID",
        "Posting URL",
        "Applications close",
        "Result",
        "Compiled PDF",
        "Cycle notes",
        "Legacy note",
    )
    metadata_lines = [
        f"- **{field}:** {generated_fields[field]}"
        for field in metadata_order
        if field in generated_fields
    ]
    metadata = f"""# Approved: {job}

{chr(10).join(metadata_lines)}
"""
    write_new(dst_dir / "metadata.md", metadata, force=force)
    print(f"Approved artifact ready: {rel(dst_dir)}")


def is_internal_comment(line: str) -> bool:
    return line.lstrip().startswith(INTERNAL_COMMENT_PREFIXES)


def strip_internal_comments(text: str) -> tuple[str, int]:
    kept: list[str] = []
    removed = 0
    for line in text.splitlines(keepends=True):
        if is_internal_comment(line):
            removed += 1
            continue
        kept.append(line)
    return "".join(kept), removed


def public_internal_comment_errors(job: str) -> list[str]:
    path = public_tex(job)
    if not path.exists():
        return []

    errors: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if is_internal_comment(line):
            errors.append(
                f"{rel(path)} line {line_no}: public LaTeX contains internal audit comment."
            )
    return errors


def export_public(args: argparse.Namespace) -> None:
    job = require_job(args)
    src = approved_tex(job)
    dst = public_tex(job)
    ensure_exists(src, "approved internal tex")

    public_text, removed = strip_internal_comments(src.read_text(encoding="utf-8"))
    write_new(dst, public_text, force=force_enabled(args))
    public_errors = public_internal_comment_errors(job)
    if public_errors:
        for item in public_errors:
            print(f"FAIL: {item}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Public LaTeX ready: {rel(dst)}")
    print(f"- stripped internal comments: {removed}")


def update_metadata_cycle_notes(job: str) -> None:
    path = approved_dir(job) / "metadata.md"
    if not path.exists():
        return

    cycle_notes = f"- **Cycle notes:** `../../edits/{job}/note.md`"
    text = path.read_text(encoding="utf-8")
    if re.search(r"^- \*\*Cycle notes:\*\*.*$", text, flags=re.M):
        text = re.sub(r"^- \*\*Cycle notes:\*\*.*$", cycle_notes, text, flags=re.M)
    else:
        text = text.rstrip() + f"\n{cycle_notes}\n"
    path.write_text(text, encoding="utf-8")


def learn(args: argparse.Namespace) -> None:
    job = require_job(args)
    force = force_enabled(args)
    sample_dirs = sample_dirs_for_job(job)
    approved_sample = sample_dirs[0] if sample_dirs else None
    sample_class = classify_sample(approved_sample) if approved_sample else "none"
    if approved_sample and sample_class != "official" and not force:
        fail(
            f"Sample is {sample_class}; learn refuses to run for non-official samples. "
            "Use FORCE=1 only for an intentional override."
        )

    ai_path = edits_dir(job) / "ai-draft.tex"
    final_path = approved_tex(job)
    final_copy = edits_dir(job) / "final-approved.tex"
    diff_path = edits_dir(job) / "diff.patch"
    note_path = edits_dir(job) / "note.md"

    ensure_exists(ai_path, "cycle snapshot")
    ensure_exists(final_path, "approved tex")

    copy_new(final_path, final_copy, force=force)

    ai_lines = ai_path.read_text(encoding="utf-8").splitlines(keepends=True)
    final_lines = final_path.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = "".join(
        difflib.unified_diff(
            ai_lines,
            final_lines,
            fromfile=rel(ai_path),
            tofile=rel(final_path),
        )
    )
    write_new(diff_path, diff or "# No text diff detected.\n", force=force)

    note_template = f"""# Edits Note — {job}

## Context

- Cycle status: approved artifact in `approved/{job}/` (`.tex` internal audit + `.public.tex` share-safe).
- Diff source: `edits/{job}/diff.patch`
- AI snapshot: `edits/{job}/ai-draft.tex`
- Final user-edited: `edits/{job}/final-approved.tex`
- Purpose: triage edits into 3 tiers (canonical rule / personal preference / JD-specific) so the rule system grows without overfitting.

**Promotion is manual.** This file extracts candidates; **you** decide what to promote and where. AI does NOT modify `references/canonical-rules.md`, `preferences.md`, or `SKILL.md` from a single cycle.

---

## 1. What changed

Summarize substantive edits from AI draft → final approved. Reference `diff.patch` for line-level detail.

- TODO: bullet-by-bullet or pattern-by-pattern summary

---

## 2. Canonical rule candidates → `references/canonical-rules.md`

Promote to canonical (`Cxxx` ID) ONLY if all 4 criteria pass:

- **T1 STACK-AGNOSTIC** — rule works regardless of tech stack (React / Spring / Go / etc.)
- **T2 DOMAIN-AGNOSTIC** — rule works regardless of industry (finance / health / SaaS / etc.)
- **T3 SENIORITY-AGNOSTIC** — rule applies to grad / mid / senior (or explicitly scoped)
- **T4 EXAMPLE-DEFROSTABLE** — rule survives once user-specific examples are removed

Also recommended: rule has been observed in ≥2 cycles (not just this one) before canonical promotion.

- TODO: list candidates with explicit T1/T2/T3/T4 verdict for each.

---

## 3. Personal preference candidates → `preferences.md`

For user-specific aesthetic/voice or carve-outs over canonical rules.

- Pure personal: assign new `Pxxx` (content) or `Lxxx` (layout) ID.
- Carve-out over canonical: reference the parent `Cxxx` and document the tighter constraint (e.g., "P008 carve-out over C012: this user prefers ≤1 bold per bullet, tighter than C012's ≤3").

- TODO: list candidates with proposed ID and (if carve-out) parent `Cxxx`.

---

## 4. JD-specific choices (do NOT promote)

Edits driven by THIS JD only. Documenting them prevents future cycles from accidentally generalizing the same edit.

- TODO: list edits with the JD-specific reason (e.g., "removed LOB project — quant firm probes matching engine; for non-trading JDs, LOB stays").

---

## 5. Do Not Promote (tempting but unsafe)

Generalizations that look attractive but have known failure modes. Recording them here prevents re-discovery in future cycles.

- TODO: list "almost-rules" with the failure mode that disqualifies them.

---

## 6. Manual promotion checklist

When you've decided what to promote, run through this checklist:

- [ ] Append canonical candidates to `references/canonical-rules.md` with `Cxxx` IDs
- [ ] Append personal candidates to `preferences.md` with `Pxxx` / `Lxxx` IDs (or carve-out references)
- [ ] Mirror any `references/canonical-rules.md` change to `.agents/skills/.../references/canonical-rules.md`
- [ ] Run `make check JOB=<recent-slug>` on a recent draft to verify no regression
- [ ] **Do NOT** modify `SKILL.md` strict rules from a single cycle. Only promote to strict rules after ≥3 cycles confirm the same pattern AND the rule is mechanically enforceable in `cycle.py check`.
- [ ] Update `SKILL.md` preflight checklist if a new `Cxxx` / `Pxxx` was added

---

## 7. Open questions

To revisit after interview / rejection / offer outcome.

- TODO: list anything contingent on outcome.
"""
    write_new(note_path, note_template, force=force)
    update_metadata_cycle_notes(job)
    print(f"Learning materials ready: {rel(edits_dir(job))}")


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def status(args: argparse.Namespace) -> None:
    job = require_job(args)
    job_edits_dir = edits_dir(job)
    sample_dirs = sample_dirs_for_job(job)
    approved_sample = sample_dirs[0] if sample_dirs else None
    sample_class = classify_sample(approved_sample) if approved_sample else "none"
    fields = metadata_fields(metadata_path(approved_sample)) if approved_sample else {}

    lifecycle = {
        "imported": (ROOT / "jobs" / f"{job}.md").exists(),
        "drafted": draft_tex(job).exists(),
        "begun": (job_edits_dir / "ai-draft.tex").exists(),
        "approved": approved_sample is not None,
        "learned": (job_edits_dir / "note.md").exists(),
    }

    issues: list[str] = []
    warnings: list[str] = []

    status_value = fields.get("Status")
    if status_value and status_value not in ALLOWED_SAMPLE_STATUSES:
        issues.append(f"metadata Status is not an exact enum value: {status_value}")

    if lifecycle["approved"]:
        if len(sample_dirs) > 1:
            joined = ", ".join(rel(path) for path in sample_dirs)
            warnings.append(f"multiple approved sample directories found; using first match: {joined}")
        if "JD source" not in fields or fields["JD source"] == "`TODO`":
            issues.append("approved metadata is missing a concrete JD source")
        if sample_class == "official":
            if "Internal audit LaTeX" not in fields or "Public LaTeX" not in fields:
                issues.append("official sample lacks current internal/public metadata fields")
            if not approved_tex(job).exists():
                issues.append(f"missing internal approved LaTeX: {rel(approved_tex(job))}")
            if not public_tex(job).exists():
                issues.append(f"missing public approved LaTeX: {rel(public_tex(job))}")
    if lifecycle["learned"] and not lifecycle["begun"]:
        warnings.append("learned note exists but begin snapshot is missing; learning may be manual/reconstructed")
    if lifecycle["approved"] and not lifecycle["learned"] and sample_class == "official":
        warnings.append("official sample is approved but not learned")

    print(f"Status: {job}")
    print("- lifecycle:")
    for name in ("imported", "drafted", "begun", "approved", "learned"):
        print(f"  - {name}: {yes_no(lifecycle[name])}")
    print("  - checked: not persisted; run `make check JOB={}` to evaluate now".format(job))
    print("- sample:")
    print(f"  - class: {sample_class}")
    if approved_sample:
        print(f"  - approved dir: {rel(approved_sample)}")
        print(f"  - metadata Status: {status_value or '<missing; defaults to official>'}")
    else:
        print("  - approved dir: none")
    if issues:
        print("- issues:")
        for item in issues:
            print(f"  - {item}")
    if warnings:
        print("- warnings:")
        for item in warnings:
            print(f"  - {item}")
    if not issues and not warnings:
        print("- issues: none")


def check_all(args: argparse.Namespace) -> None:
    samples = official_sample_dirs()
    if not samples:
        print("No official approved samples found.")
        return

    failures: list[str] = []
    print("Official samples:", flush=True)
    for sample in samples:
        print(f"- {sample.name}", flush=True)

    for sample in samples:
        job = sample.name
        print(f"\n== check approved {job} ==", flush=True)
        result = subprocess.run(
            ["make", "approved-pdf", f"JOB={job}"],
            cwd=ROOT,
            text=True,
        )
        if result.returncode != 0:
            failures.append(job)
            continue
        try:
            check_approved_job(job)
        except SystemExit:
            failures.append(job)

    if failures:
        fail("check-all failed for: " + ", ".join(failures))
    print("\ncheck-all passed.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JDcook cycle helper")
    parser.add_argument("command", choices=("begin", "check", "approve", "export", "learn", "status", "check-all"))
    parser.add_argument("--job")
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "begin":
        begin(args)
    elif args.command == "check":
        check(args)
    elif args.command == "approve":
        approve(args)
    elif args.command == "export":
        export_public(args)
    elif args.command == "learn":
        learn(args)
    elif args.command == "status":
        status(args)
    elif args.command == "check-all":
        check_all(args)


if __name__ == "__main__":
    main()
