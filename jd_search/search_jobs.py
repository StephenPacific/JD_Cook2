#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

from raw_profile import build_profile_from_raw


ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOT = ROOT / "jd_search" / "searches"
DEFAULT_GENERATED_PROFILE = ROOT / "jd_search" / "profiles" / "generated-from-raw.json"
DEFAULT_SITES = ["indeed", "linkedin", "glassdoor", "google"]
STOPWORDS = {
    "and",
    "are",
    "for",
    "from",
    "job",
    "jobs",
    "near",
    "of",
    "or",
    "role",
    "the",
    "to",
    "with",
}
TITLE_ONLY_AVOID_KEYWORDS = {
    "manager",
    "principal",
    "staff",
    "staff engineer",
    "lead engineer",
    "director",
    "head of",
}


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


def load_profile(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"Missing profile: {rel(path) if path.is_relative_to(ROOT) else path}")
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Profile is not valid JSON: {exc}")
    if not isinstance(profile, dict):
        fail("Profile must be a JSON object.")
    return profile


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def parse_csv_list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def time_phrase(hours_old: int | None) -> str:
    if not hours_old:
        return ""
    if hours_old <= 24:
        return "since yesterday"
    if hours_old <= 72:
        return "in the last 3 days"
    if hours_old <= 168:
        return "in the last week"
    return "in the last month"


def build_query_plan(
    profile: dict[str, Any],
    explicit_queries: list[str],
    explicit_locations: list[str],
    max_queries: int,
    hours_old: int | None,
) -> list[dict[str, str]]:
    roles = unique(explicit_queries or as_list(profile.get("target_roles")))
    locations = unique(explicit_locations or as_list(profile.get("locations")) or [""])
    if not roles:
        fail("Profile needs target_roles, or pass --query.")

    plan: list[dict[str, str]] = []
    phrase = time_phrase(hours_old)
    for role in roles:
        for location in locations:
            google_parts = [role, "jobs"]
            if location:
                google_parts.extend(["near", location])
            if phrase:
                google_parts.append(phrase)
            plan.append(
                {
                    "search_term": role,
                    "location": location,
                    "google_search_term": " ".join(google_parts),
                }
            )
            if len(plan) >= max_queries:
                return plan
    return plan


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z][a-z0-9+#.-]{1,}", text.lower())
        if token not in STOPWORDS
    }


def phrase_in_text(phrase: str, text: str) -> bool:
    phrase = phrase.strip().lower()
    if not phrase:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    flat = dict(record)
    location = flat.get("location")
    if isinstance(location, dict):
        flat["location"] = ", ".join(
            str(location.get(key))
            for key in ("city", "state", "country")
            if location.get(key)
        )
    for key, value in list(flat.items()):
        if value is None:
            flat[key] = ""
        elif isinstance(value, (list, dict)):
            flat[key] = json.dumps(value, ensure_ascii=False, default=str)
        else:
            flat[key] = str(value)
    return flat


def hard_filter_reason(record: dict[str, Any], profile: dict[str, Any]) -> str | None:
    constraints = profile.get("constraints") or {}
    title = str(record.get("title", "")).lower()
    text = f"{record.get('title', '')}\n{record.get('description', '')}".lower()
    for keyword in as_list(constraints.get("avoid_keywords")):
        haystack = title if keyword.lower() in TITLE_ONLY_AVOID_KEYWORDS else text
        if phrase_in_text(keyword, haystack):
            return f"avoid keyword: {keyword}"

    required = as_list(constraints.get("required_keywords"))
    missing = [keyword for keyword in required if not phrase_in_text(keyword, text)]
    if missing:
        return "missing required keyword: " + ", ".join(missing)
    return None


def score_record(record: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    title = str(record.get("title", ""))
    description = str(record.get("description", ""))
    location = str(record.get("location", ""))
    haystack = f"{title}\n{description}".lower()
    title_tokens = tokenize(title)
    role_tokens = tokenize(" ".join(as_list(profile.get("target_roles"))))

    skills = profile.get("skills") or {}
    strong = as_list(skills.get("strong"))
    usable = as_list(skills.get("usable"))
    gaps = as_list(skills.get("gap"))
    evidence = as_list(profile.get("evidence_keywords"))
    profile_locations = [item.lower() for item in as_list(profile.get("locations"))]

    role_hits = sorted(title_tokens & role_tokens)
    strong_hits = [skill for skill in strong if phrase_in_text(skill, haystack)]
    usable_hits = [skill for skill in usable if phrase_in_text(skill, haystack)]
    evidence_hits = [term for term in evidence if phrase_in_text(term, haystack)]
    gap_hits = [skill for skill in gaps if phrase_in_text(skill, haystack)]
    location_hit = any(item and phrase_in_text(item, location) for item in profile_locations)

    score = 0
    score += min(30, len(role_hits) * 10)
    score += min(35, len(strong_hits) * 9)
    score += min(18, len(usable_hits) * 5)
    score += min(12, len(evidence_hits) * 4)
    score += 5 if location_hit else 0
    score -= min(20, len(gap_hits) * 7)
    score = max(0, min(100, score))

    return {
        "match_score": score,
        "role_hits": role_hits,
        "strong_skill_hits": strong_hits,
        "usable_skill_hits": usable_hits,
        "evidence_hits": evidence_hits,
        "gap_risks": gap_hits,
        "location_hit": location_hit,
    }


def dedupe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for record in records:
        key = (
            str(record.get("job_url") or record.get("job_url_direct") or "").lower()
            or "|".join(
                str(record.get(field, "")).lower().strip()
                for field in ("site", "title", "company", "location")
            )
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(record)
    return out


def dataframe_to_records(df: Any) -> list[dict[str, Any]]:
    if hasattr(df, "to_dict"):
        return [dict(item) for item in df.to_dict("records")]
    fail("JobSpy returned an unsupported result type.")


def run_jobspy(plan: list[dict[str, str]], args: argparse.Namespace, profile: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        from jobspy import scrape_jobs
    except ImportError:
        fail(
            "python-jobspy is not installed. Install it yourself with "
            "`python3 -m pip install -U python-jobspy`, or run with --dry-run."
        )

    records: list[dict[str, Any]] = []
    for item in plan:
        df = scrape_jobs(
            site_name=args.sites,
            search_term=item["search_term"],
            google_search_term=item["google_search_term"],
            location=item["location"] or None,
            results_wanted=args.results_wanted,
            hours_old=args.hours_old,
            country_indeed=args.country_indeed or profile.get("country_indeed", "Australia"),
            description_format="markdown",
            linkedin_fetch_description=args.linkedin_fetch_description,
            verbose=args.verbose,
        )
        for record in dataframe_to_records(df):
            record["_search_term"] = item["search_term"]
            record["_search_location"] = item["location"]
            record["_google_search_term"] = item["google_search_term"]
            records.append(flatten_record(record))
    return records


def write_csv(path: Path, records: list[dict[str, Any]], force: bool) -> None:
    if path.exists() and not force:
        fail(f"Refusing to overwrite existing file: {rel(path)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for record in records for key in record.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def shortlist_markdown(search: str, records: list[dict[str, Any]]) -> str:
    lines = [
        f"# JD Search Shortlist: {search}",
        "",
        f"- Generated at: {dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"- Results: {len(records)}",
        "",
    ]
    for rank, record in enumerate(records[:25], start=1):
        title = record.get("title") or "Untitled"
        company = record.get("company") or record.get("company_name") or "Unknown company"
        score = record.get("match_score", 0)
        url = record.get("job_url") or record.get("job_url_direct") or ""
        gaps = ", ".join(record.get("gap_risks", [])) if isinstance(record.get("gap_risks"), list) else ""
        lines.extend(
            [
                f"## {rank}. {title} — {company}",
                "",
                f"- Match score: {score}",
                f"- Site: {record.get('site', '')}",
                f"- Location: {record.get('location', '')}",
                f"- URL: {url}",
                f"- Strong hits: {', '.join(record.get('strong_skill_hits', [])) if isinstance(record.get('strong_skill_hits'), list) else ''}",
                f"- Gap risks: {gaps}",
                "",
            ]
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search and rank jobs for a JDcook profile.")
    parser.add_argument("--profile")
    parser.add_argument("--profile-from-raw", action="store_true")
    parser.add_argument("--raw-root", default="raw")
    parser.add_argument("--profile-out", default=str(DEFAULT_GENERATED_PROFILE.relative_to(ROOT)))
    parser.add_argument("--search", required=True, help="Search output slug.")
    parser.add_argument("--query", action="append", default=[])
    parser.add_argument("--location", action="append", default=[])
    parser.add_argument("--sites", default=",".join(DEFAULT_SITES))
    parser.add_argument("--results-wanted", type=int, default=10)
    parser.add_argument("--hours-old", type=int, default=168)
    parser.add_argument("--country-indeed")
    parser.add_argument("--max-queries", type=int, default=8)
    parser.add_argument("--linkedin-fetch-description", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--verbose", type=int, default=0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    validate_slug(args.search, "SEARCH")
    args.sites = parse_csv_list(args.sites, DEFAULT_SITES)
    if args.results_wanted < 1:
        fail("--results-wanted must be at least 1.")

    explicit_locations = args.location
    if args.profile_from_raw or not args.profile:
        profile_path = resolve_path(args.profile_out)
        raw_root = resolve_path(args.raw_root)
        profile = build_profile_from_raw(
            raw_root,
            locations=explicit_locations or None,
            country_indeed=args.country_indeed,
        )
        write_new(
            profile_path,
            json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
            force=True,
        )
    else:
        profile_path = resolve_path(args.profile)
        profile = load_profile(profile_path)
    plan = build_query_plan(profile, args.query, args.location, args.max_queries, args.hours_old)
    search_dir = SEARCH_ROOT / args.search

    plan_doc = {
        "search": args.search,
        "profile": rel(profile_path) if profile_path.is_relative_to(ROOT) else str(profile_path),
        "sites": args.sites,
        "results_wanted_per_site_per_query": args.results_wanted,
        "hours_old": args.hours_old,
        "country_indeed": args.country_indeed or profile.get("country_indeed", "Australia"),
        "linkedin_fetch_description": args.linkedin_fetch_description,
        "queries": plan,
    }
    write_new(search_dir / "query_plan.json", json.dumps(plan_doc, indent=2, ensure_ascii=False) + "\n", force=args.force)

    if args.dry_run:
        print(f"Query plan ready: {rel(search_dir / 'query_plan.json')}")
        return

    raw_records = run_jobspy(plan, args, profile)
    raw_records = dedupe(raw_records)
    write_csv(search_dir / "raw_results.csv", raw_records, args.force)

    ranked: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for record in raw_records:
        reason = hard_filter_reason(record, profile)
        if reason:
            skipped.append({**record, "skip_reason": reason})
            continue
        ranked.append({**record, **score_record(record, profile)})

    ranked.sort(key=lambda item: int(item.get("match_score", 0)), reverse=True)
    write_new(search_dir / "ranked_jobs.json", json.dumps(ranked, indent=2, ensure_ascii=False, default=str) + "\n", force=args.force)
    write_new(search_dir / "skipped_jobs.json", json.dumps(skipped, indent=2, ensure_ascii=False, default=str) + "\n", force=args.force)
    write_new(search_dir / "shortlist.md", shortlist_markdown(args.search, ranked), force=args.force)
    print(f"Search complete: {rel(search_dir)}")
    print(f"- raw results: {len(raw_records)}")
    print(f"- ranked: {len(ranked)}")
    print(f"- skipped: {len(skipped)}")


if __name__ == "__main__":
    main()
