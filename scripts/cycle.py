#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import os
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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


def approved_dir(job: str) -> Path:
    return ROOT / "approved" / job


def approved_tex(job: str) -> Path:
    return approved_dir(job) / f"{job}.tex"


def edits_dir(job: str) -> Path:
    return ROOT / "edits" / job


def begin(args: argparse.Namespace) -> None:
    job = args.job
    src = draft_tex(job)
    dst = edits_dir(job) / "ai-draft.tex"
    copy_new(src, dst, force=force_enabled(args))
    print(f"Cycle snapshot ready: {rel(dst)}")


def page_count_from_log(log_text: str) -> int | None:
    matches = re.findall(r"Output written on .*?\((\d+)\s+pages?", log_text, flags=re.S)
    if not matches:
        matches = re.findall(r"Output written on .*?\((\d+)\s+page", log_text, flags=re.S)
    return int(matches[-1]) if matches else None


def check(args: argparse.Namespace) -> None:
    job = args.job
    tex_path = draft_tex(job)
    pdf_path = draft_pdf(job)
    log_path = draft_log(job)

    ensure_exists(tex_path, "draft tex")
    ensure_exists(pdf_path, "compiled draft PDF")
    ensure_exists(log_path, "LaTeX log")

    text = tex_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    bullet_lines = [
        (idx + 1, line)
        for idx, line in enumerate(lines)
        if r"\resumeItem{\normalsize" in line
    ]
    if len(bullet_lines) > 10:
        errors.append(f"Bullet budget exceeded: {len(bullet_lines)} resume bullets found, max is 10.")

    for line_no, _line in bullet_lines:
        next_line = lines[line_no].strip() if line_no < len(lines) else ""
        if not next_line.startswith("% src:"):
            errors.append(f"Line {line_no}: resume bullet is not followed immediately by a % src: comment.")

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

    if errors:
        for item in errors:
            print(f"FAIL: {item}", file=sys.stderr)
        for item in warnings:
            print(f"WARN: {item}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Check passed: {job}")
    print(f"- bullets: {len(bullet_lines)}/10")
    print(f"- TODO gaps: {todo_count}")
    print(f"- PDF pages: {pages}")
    for item in warnings:
        print(f"WARN: {item}")


def approve(args: argparse.Namespace) -> None:
    job = args.job
    force = force_enabled(args)
    dst_dir = approved_dir(job)
    if dst_dir.exists() and not force:
        fail(f"Approved artifact already exists: {rel(dst_dir)}. Use FORCE=1 only for an intentional replacement.")

    copy_new(draft_tex(job), approved_tex(job), force=force)
    copy_new(draft_pdf(job), dst_dir / f"{job}.pdf", force=force)

    jd_source = f"../../jobs/{job}.md" if (ROOT / "jobs" / f"{job}.md").exists() else "TODO"
    today = dt.date.today().isoformat()
    metadata = f"""# Approved: {job}

- **Final artifact:** `{job}.tex` (copied from `drafts/` on approve)
- **JD source:** `{jd_source}`
- **Submission date:** {today}
- **Company:** TODO
- **Result:** TODO (update post-interview / rejection / offer for future reference)
- **Compiled PDF:** `{job}.pdf` (generated via `make approve JOB={job}`)
- **Cycle notes:** pending — run `make learn JOB={job}` after approval notes are ready.
"""
    write_new(dst_dir / "metadata.md", metadata, force=force)
    print(f"Approved artifact ready: {rel(dst_dir)}")


def learn(args: argparse.Namespace) -> None:
    job = args.job
    force = force_enabled(args)
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

- Cycle status: approved artifact exists in `approved/{job}/`.
- Diff source: `edits/{job}/diff.patch`.
- Purpose: capture user edits and decide what, if anything, should be promoted to `preferences.md`.

---

## What Changed

- TODO: summarize the substantive edits from AI draft to final approved version.

## Preference Candidates

- TODO: list repeated style/layout preferences that may generalize beyond this JD.

## JD-Specific Choices

- TODO: list choices that were only made because of this JD and should not become global rules.

## Do Not Promote

- TODO: list tempting but unsafe generalizations.

## Promote To `preferences.md`

- TODO: promote only stable preferences confirmed by this cycle and prior cycles.

## Open Questions

- TODO: note anything to revisit after interview / rejection / offer outcome.
"""
    write_new(note_path, note_template, force=force)
    print(f"Learning materials ready: {rel(edits_dir(job))}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JDcook cycle helper")
    parser.add_argument("command", choices=("begin", "check", "approve", "learn"))
    parser.add_argument("--job", required=True)
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
    elif args.command == "learn":
        learn(args)


if __name__ == "__main__":
    main()
