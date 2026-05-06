# JD Search

`jd_search` is the job-discovery layer for JDcook. It keeps search, ranking, and
candidate selection separate from the resume drafting cycle.

## Recommended flow (Phase 2 — scan → triage → inbox)

```text
make scan-jobs SEARCH=daily            # 1. JobSpy + hard filter + auto-triage
make inbox                              # 2. read jd_search/inbox.md
make draft JOB=<slug> FROM=inbox        # 3. import + gate (cache hit) + draft
make check / approve / learn            # 4. standard cycle
```

`make scan-jobs` chains `match-jobs` (JobSpy) with `scripts/scan_to_inbox.py`,
which:

1. reads the ranked results,
2. skips URLs already triaged (cross-run dedup via `seen.tsv`),
3. runs the LLM triage judge (`triage.py`) on the top-N candidates,
4. writes the JD body to `jd_search/inbox/<slug>.md` for `FROM=inbox` import,
5. regenerates `jd_search/inbox.md` showing only `APPLY` / `BORDERLINE` (SKIP /
   VISA-BLOCKED entries are kept in `jd_search/decisions.tsv` for audit).

The pipeline deliberately stops at `inbox.md`. Drafting is never automatic;
the user reviews the inbox and triggers `make draft JOB=<slug> FROM=inbox`
themselves. The drafting gate hits the cached triage verdict instantly.

## Legacy flow (single ranked-result import)

`make import-search-result SEARCH=<search> RANK=N JOB=<slug>` still imports
one ranked entry into `jobs/<slug>.md`. Useful when you want to bypass the
inbox layer and pick by raw match-score rank.

## Files

- `profiles/example.json` — safe template for a user profile.
- `profiles/generated-from-raw.json` — local cache produced by `match-jobs`,
  gitignored.
- `raw_profile.py` — local, heuristic profile builder from `raw/`. Reads
  `raw/code/`, `raw/resumes/`, etc., but skips `raw/.cache/` (derived).
- `search_jobs.py` — builds a query plan and, when `python-jobspy` is
  installed, searches job boards and writes ranked results.
- `import_result.py` — legacy: imports one ranked result into `jobs/<slug>.md`.
- `triage.py` — LLM-as-judge for single JDs (Phase 1).
- `persona.md` — natural-language persona for the LLM judge (gitignored;
  must live outside `raw/` so the drafting skill cannot cite it as evidence).
- `searches/<search>/` — local raw + ranked output, gitignored.
- `inbox.md` — auto-generated candidate list (gitignored).
- `inbox/<slug>.md` — staged JD bodies for `FROM=inbox` import (gitignored).
- `seen.tsv` — cross-run URL dedup; tracks last-seen verdict (gitignored).
- `decisions.tsv` / `decisions.md` — full triage decision audit (gitignored).

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

Triage one imported or pasted JD with an LLM judge:

```sh
# From the macOS clipboard (mirrors `make import-job FROM=clipboard`):
make triage FROM=clipboard

# From an already-imported JD:
make triage JOB=fintech-services-australia-junior-developer

# From a public URL (works on plain career pages, not LinkedIn — see below):
make triage URL="https://bilue.com.au/careers/some-role"

# From a saved JD file:
make triage FROM=/tmp/some-jd.txt        # preferred, parallels import-job
make triage FILE=/tmp/some-jd.txt        # legacy alias, still works

# From a Unix pipe (still works for scripting):
pbpaste | make triage
```

Triage uses `jd_search/persona.md` plus the JD text and returns a structured
verdict:

```text
APPLY / BORDERLINE / SKIP / VISA-BLOCKED
HIGH / MEDIUM / LOW confidence
PASS / VERIFY / DEAD visa status
```

The persona deliberately lives **outside** `raw/` so the resume drafting skill
(which reads everything under `raw/` as evidence) never accidentally cites
personal search preferences as resume facts. `cycle.py check` rejects any
`% src:` line that touches `jd_search/` as a defence-in-depth.

It deliberately does **not** produce a numeric fit score. Decisions are cached
locally in `jd_search/decisions.tsv` and logged for reading in
`jd_search/decisions.md`; persona and decisions files are all gitignored.

### Choosing the LLM judge

Triage works with either Codex CLI or Claude Code. The default is Codex; switch
with `TRIAGE_AGENT=claude`. Either is sufficient — install whichever you prefer.

```sh
make triage FROM=clipboard                          # uses Codex (default)
make triage FROM=clipboard TRIAGE_AGENT=claude      # uses Claude Code
make triage FROM=clipboard SECOND_TRIAGE_AGENT=claude
                            # default agent first; Claude as second-opinion
                            # only on BORDERLINE / LOW / VERIFY cases
```

The Codex invocation runs with `--sandbox read-only --ephemeral` because
triage is a one-shot read-only judge: it has no need for either workspace
writes or `~/.codex/sessions` persistence. `--ephemeral` is required —
without it, `--sandbox` denies Codex's own session-file writes outside the
workspace and the call fails with a permission error. If your Codex build
does not support `--ephemeral`, edit `jd_search/triage.py` to drop it and
restore `--sandbox workspace-write`.

### URL fetching limitations

`make triage URL=...` uses plain HTTP to fetch the page, with **no JavaScript
rendering and no login flow**. This means:

- ✅ Works on public career pages (e.g. company careers sites, Greenhouse,
  Lever, Ashby boards) — the JD text is in the HTML directly.
- ❌ **Does not work on LinkedIn job pages** — they return a "Sign in to view"
  placeholder, not the actual JD.
- ❌ **Does not work on SEEK** — login wall.
- ❌ Does not work on any JD behind authentication.

For LinkedIn / SEEK / authenticated JDs, **copy the JD body and paste via stdin**
instead:

```sh
pbpaste | make triage     # macOS clipboard
xclip -o   | make triage   # Linux clipboard
```

Or save it to a file and pass `FILE=`:

```sh
make triage FILE=/tmp/some-jd.txt
```

By default triage uses one judge. To enable a second judge only for uncertain
cases (`BORDERLINE`, `LOW` confidence, or `VERIFY` visa), pass:

```sh
make triage JOB=my-role SECOND_TRIAGE_AGENT=claude
```

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

## Adzuna AU adapter

JobSpy has no SEEK or Adzuna scraper. To cover Australian listings beyond
LinkedIn / Indeed (Adzuna aggregates many AU boards including content
re-listed from SEEK partners), this repo ships a local adapter at
`jd_search/adzuna.py`.

Setup:

```sh
# Register a free account at https://developer.adzuna.com/ to get keys.
export ADZUNA_APP_ID=...
export ADZUNA_APP_KEY=...
```

Adzuna is on the default `SITES` list (`indeed,linkedin,google,adzuna`).
If the env vars are unset the adapter logs a warning to stderr and skips
itself — the rest of the search still runs on JobSpy.

Caveats:

- The Adzuna search API returns truncated descriptions (~500 chars). They
  are usually long enough to clear the `scan_to_inbox.py` 80-char floor and
  to feed the LLM judge, but full JD bodies still live on the original
  posting site.
- `job_url` is Adzuna's redirect link; clicking through lands on the
  original employer / SEEK / LinkedIn page.

## Safety Notes

This layer does not log in, click Apply, solve CAPTCHA, or bypass access
controls. JobSpy issues HTTP requests to public job-board endpoints and can be
rate limited. The Adzuna adapter calls the official Adzuna Search API with the
user's own API key. `make triage URL=...` fetches public job pages only.

The raw-driven search command does not send raw resume/project text to JobSpy;
raw content is used locally to infer broad target roles and score results. LLM
triage does send `jd_search/persona.md` and the JD text to the selected local agent
backend (Codex by default), so keep the persona concise and treat decision logs
as private. Start with small `RESULTS_WANTED` values and use `DRY_RUN=1` before
running a real scrape.
