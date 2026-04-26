#!/usr/bin/env python3
"""Import job descriptions into stable local markdown inputs.

Scope: this helper snapshots user-provided clipboard text or public job pages.
It does not log in, solve CAPTCHA, click apply buttons, or bypass access
controls. If a URL import is incomplete, use the clipboard path.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
MIN_CLIPBOARD_CHARS = 80
MIN_URL_CHARS = 300
JS_TEXT_SELECTORS = [
    "main",
    "article",
    "[role='main']",
    "[class*='job-description']",
    "[class*='jobDescription']",
    "[class*='job_description']",
    "[class*='job-details']",
    "[class*='jobDetails']",
    "[id*='job-description']",
    "[id*='jobDescription']",
    "#job-details",
    "#jobDetails",
    "body",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"WARN: {message}", file=sys.stderr)


def force_enabled(args: argparse.Namespace) -> bool:
    return bool(args.force or os.environ.get("FORCE") == "1")


def write_text_new(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        fail(f"Refusing to overwrite existing file: {rel(path)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_bytes_new(path: Path, content: bytes, force: bool = False) -> None:
    if path.exists() and not force:
        fail(f"Refusing to overwrite existing file: {rel(path)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def validate_job_slug(job: str) -> None:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", job):
        fail("JOB must be a lowercase slug using letters, numbers, and hyphens.")


def source_dir(job: str) -> Path:
    return ROOT / "jobs" / "_sources" / job


def job_path(job: str) -> Path:
    return ROOT / "jobs" / f"{job}.md"


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def require_useful_text(
    text: str,
    minimum: int,
    source_label: str,
    short_text_hint: str,
) -> None:
    if not text.strip():
        fail(f"{source_label} produced no text.")
    if len(text.strip()) < minimum:
        fail(
            f"{source_label} produced only {len(text.strip())} characters. "
            f"{short_text_hint}"
        )


def run_clipboard_command(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or "clipboard command failed"
        fail(detail)
    return completed.stdout


def read_clipboard() -> str:
    if sys.platform == "darwin" and shutil.which("pbpaste"):
        return run_clipboard_command(["pbpaste"])

    if os.name == "nt" and shutil.which("powershell"):
        return run_clipboard_command(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"]
        )

    linux_commands = [
        ("wl-paste", ["wl-paste", "--no-newline"]),
        ("xclip", ["xclip", "-selection", "clipboard", "-o"]),
        ("xsel", ["xsel", "--clipboard", "--output"]),
    ]
    for binary, command in linux_commands:
        if shutil.which(binary):
            return run_clipboard_command(command)

    fail("No supported clipboard reader found. On macOS this expects pbpaste.")


BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
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
    "nav",
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


class VisibleTextExtractor(HTMLParser):
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
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "li":
            self.append_break()
            self.parts.append("- ")
        elif tag in BLOCK_TAGS:
            self.append_break()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in BLOCK_TAGS:
            self.append_break()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if data.strip():
            self.parts.append(data)


def html_to_text(html_text: str) -> str:
    extractor = VisibleTextExtractor()
    extractor.feed(html_text)
    return normalize_text("".join(extractor.parts))


def html_title(html_text: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.I | re.S)
    if not match:
        return None
    title = re.sub(r"<[^>]+>", "", match.group(1))
    title = normalize_text(html.unescape(title))
    return title or None


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        fail("URL must be an http(s) URL.")


def fetch_http(url: str) -> dict[str, object]:
    validate_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "JDcook/0.1 personal job-description import",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            final_url = response.geturl()
    except urllib.error.URLError as exc:
        fail(f"HTTP import failed: {exc}")

    html_text = raw.decode(encoding, errors="replace")
    return {
        "mode": "http",
        "url": url,
        "final_url": final_url,
        "raw_name": "source.html",
        "raw_bytes": raw,
        "text": html_to_text(html_text),
        "title": html_title(html_text),
    }


async def fetch_js_async(url: str) -> dict[str, object]:
    validate_url(url)
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        fail(
            "MODE=js requires Playwright. Install it with "
            "`python3 -m pip install playwright` and `python3 -m playwright install chromium`, "
            "or use FROM=clipboard."
        )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                await page.wait_for_selector(
                    "main, article, [role='main'], h1, body",
                    timeout=10000,
                )
            except Exception:
                warn("JS import did not see a content selector within 10s; extracting current page text.")
            await page.wait_for_timeout(1000)
            title = await page.title()
            text, text_selector = await extract_js_text(page)
            html_text = await page.content()
            screenshot = await page.screenshot(full_page=True)
            final_url = page.url
        finally:
            await browser.close()

    return {
        "mode": "js",
        "url": url,
        "final_url": final_url,
        "raw_name": "rendered.html",
        "raw_bytes": html_text.encode("utf-8"),
        "text": normalize_text(text),
        "text_selector": text_selector,
        "title": normalize_text(title) if title else None,
        "screenshot": screenshot,
    }


async def extract_js_text(page: object) -> tuple[str, str]:
    best_text = ""
    best_selector = "body"
    for selector in JS_TEXT_SELECTORS:
        try:
            candidate = await page.locator(selector).first.inner_text(timeout=2000)
        except Exception:
            continue

        candidate = normalize_text(candidate)
        if len(candidate) >= MIN_URL_CHARS:
            return candidate, selector
        if len(candidate) > len(best_text):
            best_text = candidate
            best_selector = selector

    return best_text, best_selector


def fetch_js(url: str) -> dict[str, object]:
    return asyncio.run(fetch_js_async(url))


def build_job_markdown(job: str, text: str, metadata: dict[str, object]) -> str:
    lines = [
        f"# Job Description: {job}",
        "",
        f"- Imported at: {metadata['imported_at']}",
        f"- Source type: {metadata['source_type']}",
    ]

    if metadata.get("source_url"):
        lines.append(f"- Source URL: {metadata['source_url']}")
    if metadata.get("final_url") and metadata.get("final_url") != metadata.get("source_url"):
        lines.append(f"- Final URL: {metadata['final_url']}")
    if metadata.get("page_title"):
        lines.append(f"- Page title: {metadata['page_title']}")
    if metadata.get("mode"):
        lines.append(f"- Import mode: {metadata['mode']}")

    lines.extend(["", "---", "", text.strip(), ""])
    return "\n".join(lines)


def import_from_clipboard(args: argparse.Namespace) -> dict[str, object]:
    if args.url:
        validate_url(args.url)
    text = normalize_text(read_clipboard())
    require_useful_text(
        text,
        MIN_CLIPBOARD_CHARS,
        "Clipboard import",
        "Copy the full JD text and retry.",
    )
    return {
        "mode": "clipboard",
        "url": args.url,
        "raw_name": "clipboard.txt",
        "raw_bytes": text.encode("utf-8"),
        "text": text,
        "title": None,
    }


def import_from_url(args: argparse.Namespace) -> dict[str, object]:
    mode = args.mode or "auto"
    if mode not in {"auto", "http", "js"}:
        fail("MODE must be one of: auto, http, js.")

    if mode == "js":
        result = fetch_js(args.url)
        require_useful_text(
            str(result["text"]),
            MIN_URL_CHARS,
            "JS import",
            "Use FROM=clipboard or paste a more complete JD.",
        )
        return result

    http_result = fetch_http(args.url)
    http_text = str(http_result["text"])
    if len(http_text.strip()) >= MIN_URL_CHARS or mode == "http":
        require_useful_text(
            http_text,
            MIN_URL_CHARS,
            "HTTP import",
            "Try MODE=js or use FROM=clipboard.",
        )
        return http_result

    warn(
        f"HTTP import produced only {len(http_text.strip())} characters; "
        "trying MODE=js fallback."
    )
    result = fetch_js(args.url)
    require_useful_text(
        str(result["text"]),
        MIN_URL_CHARS,
        "JS import",
        "Use FROM=clipboard or paste a more complete JD.",
    )
    return result


def import_job(args: argparse.Namespace) -> None:
    validate_job_slug(args.job)
    force = force_enabled(args)
    dst = job_path(args.job)
    src_dir = source_dir(args.job)

    if dst.exists() and not force:
        fail(f"Refusing to overwrite existing job file: {rel(dst)}")
    if src_dir.exists() and any(src_dir.iterdir()) and not force:
        fail(f"Refusing to overwrite existing source snapshot: {rel(src_dir)}")

    if args.source == "clipboard":
        result = import_from_clipboard(args)
        source_type = "clipboard"
    elif args.url:
        result = import_from_url(args)
        source_type = "url"
    else:
        fail("Provide either FROM=clipboard or URL=...")

    text = str(result["text"])
    imported_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    metadata: dict[str, object] = {
        "job": args.job,
        "imported_at": imported_at,
        "source_type": source_type,
        "source_url": result.get("url"),
        "final_url": result.get("final_url"),
        "mode": result.get("mode"),
        "page_title": result.get("title"),
        "text_selector": result.get("text_selector"),
        "raw_path": rel(src_dir / str(result["raw_name"])),
        "text_path": rel(src_dir / "text.txt"),
        "job_path": rel(dst),
        "char_count": len(text),
    }

    write_bytes_new(src_dir / str(result["raw_name"]), result["raw_bytes"], force=force)
    if result.get("screenshot"):
        write_bytes_new(src_dir / "screenshot.png", result["screenshot"], force=force)
        metadata["screenshot_path"] = rel(src_dir / "screenshot.png")
    write_text_new(src_dir / "text.txt", text + "\n", force=force)
    write_text_new(
        src_dir / "metadata.json",
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        force=force,
    )
    write_text_new(dst, build_job_markdown(args.job, text, metadata), force=force)

    print(f"Imported job: {rel(dst)}")
    print(f"- source: {source_type}")
    print(f"- mode: {metadata['mode']}")
    print(f"- chars: {len(text)}")
    print(f"- snapshot: {rel(src_dir)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a JD into jobs/<JOB>.md")
    parser.add_argument("--job", required=True)
    parser.add_argument("--from", dest="source", choices=("clipboard",))
    parser.add_argument("--url")
    parser.add_argument("--mode", choices=("auto", "http", "js"))
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.source and args.mode:
        fail("MODE only applies to URL imports.")
    import_job(args)


if __name__ == "__main__":
    main()
