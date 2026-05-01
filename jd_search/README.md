# JD Search

`jd_search` is the job-discovery layer for JDcook. It keeps search, ranking, and
candidate selection separate from the resume drafting cycle.

The intended flow is:

```text
raw/
  -> generated local profile
  -> query plan
  -> JobSpy search
  -> normalized job records
  -> profile-aware ranking
  -> shortlist
  -> selected result imported to jobs/<slug>.md
  -> existing JDcook draft/check/approve/learn cycle
```

## Files

- `profiles/example.json` — safe template for a user profile.
- `profiles/generated-from-raw.json` — local cache produced by `match-jobs`,
  gitignored.
- `raw_profile.py` — local, heuristic profile builder from `raw/`.
- `search_jobs.py` — builds a query plan and, when `python-jobspy` is installed,
  searches job boards and writes ranked results.
- `import_result.py` — imports one ranked result into `jobs/<slug>.md`.
- `searches/<search>/` — local output directory, gitignored.

## Profile Contract

Profiles are JSON so the first version does not require a YAML dependency.

Important fields:

- `target_roles` — roles the search planner expands into queries.
- `locations` — preferred locations or remote markets.
- `country_indeed` — JobSpy country value for Indeed and Glassdoor.
- `skills.strong` — evidence-backed strengths to reward heavily.
- `skills.usable` — useful but less central skills.
- `skills.gap` — known weak areas; matching jobs are not discarded, but risks are
  surfaced.
- `constraints.avoid_keywords` — hard exclusions such as manager, sales, unpaid.
- `constraints.required_keywords` — optional hard requirements.

Keep real profiles local. `.gitignore` allows only `profiles/example.json`.

## Commands

One-command raw-driven flow:

```sh
make match-jobs SEARCH=raw-fit
```

This reads `raw/` locally, writes `profiles/generated-from-raw.json`, sends only
broad role/location queries to JobSpy, and ranks results locally against the
generated profile.

Preview the raw-driven query plan without installing or running JobSpy:

```sh
make match-jobs SEARCH=raw-fit DRY_RUN=1 FORCE=1
```

Preview a hand-authored profile's query plan:

```sh
make plan-jobs SEARCH=ai-engineer-sydney PROFILE=jd_search/profiles/example.json
```

Run a search after installing JobSpy yourself:

```sh
python3 -m pip install -U python-jobspy
make search-jobs SEARCH=ai-engineer-sydney PROFILE=jd_search/profiles/my-profile.json
```

Use explicit search terms when you want tighter control:

```sh
make search-jobs SEARCH=llm-eval-sydney \
  PROFILE=jd_search/profiles/my-profile.json \
  QUERY="LLM evaluation engineer" \
  LOCATION="Sydney NSW"
```

Import a selected result into the normal JDcook workflow:

```sh
make import-search-result SEARCH=ai-engineer-sydney RANK=1 JOB=my-target-role
make draft JOB=my-target-role
```

## Safety Notes

This layer does not log in, click Apply, solve CAPTCHA, or bypass access
controls. JobSpy issues HTTP requests to public job-board endpoints and can be
rate limited. The raw-driven command does not send raw resume/project text to
JobSpy; raw content is used locally to infer broad target roles and score results.
Start with small `RESULTS_WANTED` values and use `DRY_RUN=1` before running a
real scrape.
