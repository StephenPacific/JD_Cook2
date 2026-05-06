"""Adzuna AU adapter.

Adzuna aggregates jobs from many Australian boards (including SEEK postings
re-listed via partners), filling the gap left by JobSpy's missing SEEK
scraper. This module fetches results via Adzuna's public Search API and
shapes them into the same record schema JobSpy returns, so downstream
dedup / hard-filter / scoring code in `search_jobs.py` doesn't need to
care which source a record came from.

Auth: requires ADZUNA_APP_ID and ADZUNA_APP_KEY environment variables
(register a free account at https://developer.adzuna.com/ to get them).
If either is unset, fetch_adzuna_jobs() returns [] without raising — the
search pipeline degrades to JobSpy-only.

Docs: https://developer.adzuna.com/docs/search
"""
from __future__ import annotations

import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

ADZUNA_API_BASE = "https://api.adzuna.com/v1/api/jobs"
DEFAULT_TIMEOUT = 20
MAX_PAGES = 5


def env_credentials() -> tuple[str | None, str | None]:
    return os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")


def has_credentials() -> bool:
    app_id, app_key = env_credentials()
    return bool(app_id and app_key)


def hours_to_days(hours_old: int | None) -> int | None:
    if not hours_old or hours_old <= 0:
        return None
    return max(1, (hours_old + 23) // 24)


def fetch_page(
    country: str,
    page: int,
    params: dict[str, Any],
    timeout: int,
    verbose: int,
) -> dict[str, Any] | None:
    url = f"{ADZUNA_API_BASE}/{country}/search/{page}?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "JDcook/1.0 (+adzuna adapter)"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        print(f"Adzuna HTTP {exc.code} on page {page}: {exc.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as exc:
        print(f"Adzuna network error on page {page}: {exc.reason}", file=sys.stderr)
        return None
    except TimeoutError:
        print(f"Adzuna timeout on page {page}", file=sys.stderr)
        return None
    import json
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        print(f"Adzuna JSON decode error on page {page}: {exc}", file=sys.stderr)
        return None
    if verbose >= 1:
        count = len(payload.get("results", []) or [])
        print(f"Adzuna page {page}: {count} results")
    return payload


def normalize(result: dict[str, Any], search_term: str, search_location: str) -> dict[str, Any]:
    company = ""
    if isinstance(result.get("company"), dict):
        company = str(result["company"].get("display_name") or "").strip()
    location = ""
    if isinstance(result.get("location"), dict):
        location = str(result["location"].get("display_name") or "").strip()
    redirect_url = str(result.get("redirect_url") or "").strip()
    direct_url = redirect_url
    record: dict[str, Any] = {
        "site": "adzuna",
        "id": str(result.get("id") or "").strip(),
        "title": str(result.get("title") or "").strip(),
        "company": company,
        "location": location,
        "description": str(result.get("description") or "").strip(),
        "job_url": redirect_url,
        "job_url_direct": direct_url,
        "date_posted": str(result.get("created") or "").strip(),
        "salary_min": result.get("salary_min") or "",
        "salary_max": result.get("salary_max") or "",
        "category": (result.get("category") or {}).get("label", "") if isinstance(result.get("category"), dict) else "",
        "contract_type": str(result.get("contract_type") or "").strip(),
        "contract_time": str(result.get("contract_time") or "").strip(),
        "_search_term": search_term,
        "_search_location": search_location,
        "_google_search_term": "",
    }
    return record


def fetch_adzuna_jobs(
    plan: list[dict[str, str]],
    results_wanted: int,
    hours_old: int | None,
    country: str = "au",
    timeout: int = DEFAULT_TIMEOUT,
    verbose: int = 0,
) -> list[dict[str, Any]]:
    """Fetch Adzuna search results for each (search_term, location) in `plan`.

    Returns a list of records shaped like JobSpy's flattened output. If no
    credentials are set, returns [] silently — let the caller decide how to
    surface that to the user (the runner already prints which sites it tried).
    """
    app_id, app_key = env_credentials()
    if not app_id or not app_key:
        print(
            "Adzuna skipped: ADZUNA_APP_ID and/or ADZUNA_APP_KEY not set. "
            "Register at https://developer.adzuna.com/ and export both env vars.",
            file=sys.stderr,
        )
        return []

    max_days_old = hours_to_days(hours_old)
    per_page = max(1, min(50, results_wanted))
    pages_needed = max(1, min(MAX_PAGES, (results_wanted + per_page - 1) // per_page))

    records: list[dict[str, Any]] = []
    for item in plan:
        params_base: dict[str, Any] = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": per_page,
            "what": item["search_term"],
            "content-type": "application/json",
        }
        if item.get("location"):
            params_base["where"] = item["location"]
        if max_days_old:
            params_base["max_days_old"] = max_days_old

        gathered = 0
        for page in range(1, pages_needed + 1):
            payload = fetch_page(country, page, params_base, timeout, verbose)
            if not payload:
                break
            results = payload.get("results") or []
            if not results:
                break
            for result in results:
                if gathered >= results_wanted:
                    break
                records.append(normalize(result, item["search_term"], item.get("location", "")))
                gathered += 1
            if gathered >= results_wanted or len(results) < per_page:
                break
            time.sleep(0.25)
    return records
