#!/usr/bin/env python3
"""
PDF text cache for raw/ evidence.

Why: PDFs are slow + expensive for AI agents to read directly. This script
extracts text once per PDF and stores it as Markdown under raw/.cache/.
The cache is gitignored, regenerated on PDF change (sha256), and serves as
a reading aid only — citations in resume drafts must always point to the
original PDF, never to the cache.

Outputs:
  raw/.cache/<mirror-of-raw-path>.md   for each PDF
  raw/.cache/MANIFEST.md                listing all raw files

Usage:
  python3 scripts/raw_cache.py        # idempotent; skips unchanged PDFs
  python3 scripts/raw_cache.py --force  # rebuild all caches
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
CACHE_DIR = RAW_DIR / ".cache"
PREFERRED_EXTRACTOR = "pdftotext-layout"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def stored_hash(cache_path: Path) -> str | None:
    if not cache_path.exists():
        return None
    text = cache_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^- Source sha256: `([0-9a-f]{64})`", text, flags=re.M)
    return match.group(1) if match else None


def stored_extractor(cache_path: Path) -> str | None:
    if not cache_path.exists():
        return None
    text = cache_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^- Extractor: `([^`]+)`", text, flags=re.M)
    return match.group(1) if match else None


def available_extractor() -> str:
    if shutil.which("pdftotext"):
        return PREFERRED_EXTRACTOR
    return "pypdf"


def extract_with_pdftotext(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pdftotext failed")
    return result.stdout.strip()


def extract_with_pypdf(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        print(
            "ERROR: pypdf is not installed. Run: pip install pypdf",
            file=sys.stderr,
        )
        raise SystemExit(1)

    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for i, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
        except Exception as e:  # extraction failures should not crash the build
            text = f"[extraction error on page {i}: {e}]"
        pages.append(f"### Page {i}\n\n{text.strip()}")
    return "\n\n".join(pages)


def extract_pdf_text(pdf_path: Path) -> tuple[str, str]:
    if available_extractor() == PREFERRED_EXTRACTOR:
        try:
            text = extract_with_pdftotext(pdf_path)
            if text:
                return text, PREFERRED_EXTRACTOR
        except Exception as e:
            print(
                f"WARNING: pdftotext failed for {rel(pdf_path)} ({e}); falling back to pypdf.",
                file=sys.stderr,
            )
    return extract_with_pypdf(pdf_path), "pypdf"


def cache_path_for(pdf_path: Path) -> Path:
    return CACHE_DIR / pdf_path.relative_to(RAW_DIR).with_suffix(".md")


def write_cache(pdf_path: Path, text: str, sha: str, extractor: str) -> None:
    cache_path = cache_path_for(pdf_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    body = f"""# Cached PDF Text: {pdf_path.name}

- Source PDF: `{rel(pdf_path)}`
- Source sha256: `{sha}`
- Extractor: `{extractor}`
- Generated at: {dt.datetime.now(dt.UTC).isoformat()}
- Citation rule: cite the source PDF, never this cache file. Use this only as a reading aid.

---

## Extracted Text

{text}
"""
    cache_path.write_text(body, encoding="utf-8")


def ensure_pdf_cache(pdf_path: Path, force: bool = False) -> str:
    """Return one of: 'regenerated', 'created', 'skipped'."""
    sha = sha256_of_file(pdf_path)
    cache_path = cache_path_for(pdf_path)
    existing = stored_hash(cache_path)
    existing_extractor = stored_extractor(cache_path)
    preferred = available_extractor()

    if not force and existing == sha and existing_extractor == preferred:
        return "skipped"

    text, extractor = extract_pdf_text(pdf_path)
    write_cache(pdf_path, text, sha, extractor)
    return "created" if existing is None else "regenerated"


def find_pdfs() -> list[Path]:
    if not RAW_DIR.exists():
        return []
    return sorted(p for p in RAW_DIR.rglob("*.pdf") if CACHE_DIR not in p.parents)


def find_all_raw_files() -> list[Path]:
    if not RAW_DIR.exists():
        return []
    out: list[Path] = []
    for path in RAW_DIR.rglob("*"):
        if not path.is_file():
            continue
        if CACHE_DIR in path.parents or path == CACHE_DIR:
            continue
        if path.name.startswith(".DS_Store"):
            continue
        out.append(path)
    return sorted(out)


def write_manifest(raw_files: list[Path]) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = CACHE_DIR / "MANIFEST.md"

    pdf_paths = [p for p in raw_files if p.suffix.lower() == ".pdf"]
    md_paths = [p for p in raw_files if p.suffix.lower() == ".md"]
    other_paths = [p for p in raw_files if p.suffix.lower() not in (".pdf", ".md")]

    def line_for(p: Path) -> str:
        size = p.stat().st_size
        return f"- `{rel(p)}` ({size:,} bytes)"

    sections: list[str] = [
        "# Raw Evidence Manifest",
        "",
        f"- Generated at: {dt.datetime.now(dt.UTC).isoformat()}",
        f"- Total files: {len(raw_files)}",
        "",
        "**Why this file exists:** `raw/` is mostly gitignored, which makes ",
        "`rg --files raw` blind to your evidence. Read this manifest first ",
        "before exploring `raw/` so you see every file.",
        "",
        "**For PDFs**, prefer reading the cached `.md` under `raw/.cache/` ",
        "(faster + cheaper). Always cite the source PDF in `% src:` markers, ",
        "never the cache file.",
        "",
        "## PDFs (with text cache)",
        "",
    ]
    if pdf_paths:
        for p in pdf_paths:
            cache_p = cache_path_for(p)
            cache_marker = f" → cache: `{rel(cache_p)}`" if cache_p.exists() else " (no cache yet)"
            sections.append(f"{line_for(p)}{cache_marker}")
    else:
        sections.append("- (none)")

    sections.extend(["", "## Markdown notes", ""])
    if md_paths:
        sections.extend(line_for(p) for p in md_paths)
    else:
        sections.append("- (none)")

    sections.extend(["", "## Other files", ""])
    if other_paths:
        sections.extend(line_for(p) for p in other_paths)
    else:
        sections.append("- (none)")
    sections.append("")

    manifest.write_text("\n".join(sections), encoding="utf-8")
    return manifest


def ensure_raw_cache(force: bool = False, quiet: bool = False) -> dict[str, int]:
    """
    Public entry point used by draft_resume.py.
    Returns counts: {created, regenerated, skipped}.
    """
    counts = {"created": 0, "regenerated": 0, "skipped": 0}
    pdfs = find_pdfs()
    for pdf in pdfs:
        status = ensure_pdf_cache(pdf, force=force)
        counts[status] += 1
        if status == "created" and not quiet:
            cache = cache_path_for(pdf)
            print(
                f"Cache created: {rel(cache)} — please verify once before relying on it."
            )
        elif status == "regenerated" and not quiet:
            print(f"Cache regenerated: {rel(cache_path_for(pdf))}")

    raw_files = find_all_raw_files()
    manifest = write_manifest(raw_files)
    if not quiet and (counts["created"] or counts["regenerated"]):
        print(f"Manifest updated: {rel(manifest)}")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PDF text cache for raw/ evidence.")
    parser.add_argument("--force", action="store_true", help="Rebuild all caches even if hash unchanged.")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-file output.")
    args = parser.parse_args()

    counts = ensure_raw_cache(force=args.force, quiet=args.quiet)
    pdfs = find_pdfs()
    raw_files = find_all_raw_files()
    print(
        f"raw_cache: {len(pdfs)} PDF(s) — "
        f"{counts['created']} created, "
        f"{counts['regenerated']} regenerated, "
        f"{counts['skipped']} unchanged. "
        f"Manifest covers {len(raw_files)} raw file(s)."
    )


if __name__ == "__main__":
    main()
