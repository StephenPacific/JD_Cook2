# JDcook Guide

JDcook is a local-first, evidence-grounded workflow for drafting resumes against
specific job descriptions. It is designed to keep the user's facts local,
preserve an audit trail for every claim, and learn from the user's edits over
time.

This guide has two parts:

- **Part A - First Cycle Tutorial**: follow this linearly the first time.
- **Part B - Reference**: come back here when you need commands, file meanings,
  validators, or lifecycle details.

## Part A - First Cycle Tutorial

### 1. What You Are Building

At the end of the first cycle you should have:

- a one-page PDF resume tailored to one real JD
- an approved submission record under `approved/<slug>/`
- learning materials under `edits/<slug>/`
- a starting `preferences.md` file for your own style rules

The standard loop is:

```text
raw evidence
  + job description
  + rules/preferences
  -> AI draft
  -> human edit
  -> check
  -> approve
  -> learn from the diff
```

### 2. Prerequisites

You need:

- **Claude Code** or **Codex** to run the drafting agent.
- **Python 3.10+** for the scripts.
- **BasicTeX / TeX Live** plus `latexmk` for PDF compilation.
- **Playwright** only if you want JS-rendered URL imports.
- **VS Code + LaTeX Workshop** if you want a comfortable local preview loop.

On macOS:

```bash
brew install --cask basictex
eval "$(/usr/libexec/path_helper)"
sudo tlmgr update --self
sudo tlmgr install latexmk collection-latexrecommended collection-fontsrecommended
```

Verify:

```bash
which pdflatex
which latexmk
```

For JS-heavy job pages:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

On Linux, use your distro's TeX Live packages. On Windows, WSL2 is the most
predictable path.

### 3. First-Time Setup

Clone the repo:

```bash
git clone https://github.com/StephenPacific/JD_Cook2.git
cd JD_Cook2
```

Create the local-only working directories:

```bash
mkdir -p raw/resumes raw/code jobs drafts approved edits
cp preferences.example.md preferences.md
```

These paths are gitignored because they contain personal resumes, project
evidence, job history, drafts, approved artifacts, and style preferences.

Create local LaTeX template overrides:

```bash
cp .claude/skills/drafting-resume-from-confirmed-assets/references/latex-template.tex \
   .claude/skills/drafting-resume-from-confirmed-assets/references/latex-template.local.tex

cp .agents/skills/drafting-resume-from-confirmed-assets/references/latex-template.tex \
   .agents/skills/drafting-resume-from-confirmed-assets/references/latex-template.local.tex
```

Edit the `.local.tex` files with your real name, city, phone, email, and project
URLs. Keep the tracked `latex-template.tex` sanitized.

### 4. Add Your Evidence

JDcook is only as good as `raw/`. Every generated resume bullet must trace back
to confirmed source material.

Add your current resume:

```bash
cp ~/Downloads/my-resume.pdf raw/resumes/
```

Write one note per project or experience you want the system to use:

```bash
cp raw/code/_TEMPLATE.md raw/code/my-project-slug.md
```

Fill the template honestly:

- what the project does
- what you personally built
- what you did not do
- tech stack with depth, such as `daily`, `used`, `learned-here`, or
  `referenced-only`
- real outcomes and metrics, only if they are true
- caveats and inflation risks

Sanity-check:

```bash
ls raw/resumes/
ls raw/code/
```

No raw evidence means no trustworthy draft. Thin raw evidence usually produces
generic bullets and more `% TODO:` gaps.

### 5. Import Your First JD

Choose a lowercase slug:

```text
stripe-backend
atlassian-fullstack
my-first-jd
```

If the JD is open in your browser, copy the JD text and run:

```bash
make import-job JOB=my-first-jd FROM=clipboard
```

For public pages:

```bash
make import-job JOB=my-first-jd URL="https://..." MODE=http
make import-job JOB=my-first-jd URL="https://..." MODE=js
```

If `MODE` is omitted, import uses `auto`: HTTP first, then JS rendering if the
page looks too sparse. URL import does not log in, solve CAPTCHA, click Apply,
or bypass access controls.

The import writes:

```text
jobs/my-first-jd.md
jobs/_sources/my-first-jd/
```

Manual creation is also fine: create `jobs/my-first-jd.md` and paste the JD
verbatim.

### 6. Draft, Check, Approve, Learn

Generate the AI draft:

```bash
make draft JOB=my-first-jd
```

This does four things:

- writes `edits/my-first-jd/context.md`
- invokes the local agent with the `drafting-resume-from-confirmed-assets` skill
- writes `drafts/my-first-jd.tex`
- snapshots the untouched AI version to `edits/my-first-jd/ai-draft.tex`

Do not edit before the snapshot exists. The learn step depends on comparing the
AI snapshot with your final approved version.

Edit `drafts/my-first-jd.tex` in your editor, then validate:

```bash
make check JOB=my-first-jd
```

> **⚠️ Editing rule — preserve `% src:` and `% TODO:` lines.**
> Each `\resumeItem{...}` is followed by a `% src: raw/...` audit line, and
> the file head holds 1–4 `% TODO:` evidence-gap comments. `make check`
> will fail (zero `% src:` after a bullet, missing TODO block) if these
> are deleted. They are stripped automatically from the public `.public.tex`
> at approve time, so reviewers never see them — they only exist for
> internal audit and the learn step.

Fix failures and rerun `make check` until it passes. When ready:

```bash
make approve JOB=my-first-jd
```

Approval writes:

```text
approved/my-first-jd/my-first-jd.tex
approved/my-first-jd/my-first-jd.public.tex
approved/my-first-jd/my-first-jd.pdf
approved/my-first-jd/metadata.md
```

`make approve` also automatically runs the **applied** step at the end:
it deletes `jd_search/inbox/<slug>.md`, marks the `seen.tsv` row as
`APPLIED` (so the inbox regenerator hides it next scan), stamps an
`Applied at:` timestamp into `metadata.md`, and appends a row to
`approved/_applied.tsv` (a cross-slug submission log).

The semantic of approve is therefore: **"this version is final and is
the one I am submitting"**. If you only want to freeze a version without
counting it as submitted, use `make export` instead. To re-approve after
a polish pass, use `FORCE=1` — but note this also bumps the applied
timestamp and adds a duplicate row to `_applied.tsv`.

Run learning when you made meaningful edits, or when you want to record that the
AI draft was accepted as-is:

```bash
make learn JOB=my-first-jd
```

For a non-empty diff, learning writes:

```text
edits/my-first-jd/final-approved.tex
edits/my-first-jd/diff.patch
edits/my-first-jd/note.md
```

For an AI-only cycle, it writes only a stub `note.md`; there is no useful diff
to learn from.

If the terminal is interactive, `make learn` asks whether to promote a personal
content rule (`P###`), a personal layout rule (`L###`), or leave canonical
candidates for manual review. Promotion into `preferences.md` is always a human
choice.

After approval, inspect the cycle:

```bash
make status JOB=my-first-jd
make check-all
```

`make check-all` validates current official approved samples, not active drafts.

## Part B - Reference

### 7. Directory Structure

```text
.claude/skills/drafting-resume-from-confirmed-assets/    Claude skill + references
.agents/skills/drafting-resume-from-confirmed-assets/    Codex mirror
raw/                                                      user evidence
  resumes/                                               past resumes
  code/                                                  project notes
  .cache/                                                derived PDF text cache (gitignored)
jobs/                                                     one JD per slug
  _sources/<slug>/                                       import snapshots
drafts/                                                   active editable drafts
approved/<slug>/                                          final submission record
edits/<slug>/                                             context, snapshots, diffs, notes
preferences.md                                            personal style rules
build/                                                    compiled PDFs and LaTeX cache
jd_search/                                                job discovery layer
scripts/                                                  workflow helpers
```

Source of truth:

```text
inputs:        raw/ + jobs/ + preferences.md + skill rules
active work:   drafts/
final record:  approved/
learning:      edits/ + preferences.md
cache:         raw/.cache/ + build/ + jd_search/searches/
```

### 8. Make Commands

| Target | What it does |
|---|---|
| `make import-job JOB=<slug> FROM=clipboard` | Reads clipboard text and writes `jobs/<slug>.md` plus `jobs/_sources/<slug>/`. |
| `make import-job JOB=<slug> URL="..." MODE=http/js` | Imports a public JD URL. Omitting `MODE` uses `auto`. `MODE=js` requires Playwright. |
| `make draft JOB=<slug>` | Refreshes `raw/.cache/`, writes `edits/<slug>/context.md`, invokes the local agent, writes `drafts/<slug>.tex`, then snapshots it to `edits/<slug>/ai-draft.tex`. |
| `make raw-cache` | Refreshes derived PDF text caches and `raw/.cache/MANIFEST.md` without drafting. Mostly useful for debugging. |
| `make preview JOB=<slug>` / `make draft-pdf JOB=<slug>` | Compiles active draft to `build/pdf/drafts/<slug>.pdf`. |
| `make approved JOB=<slug>` | Compiles `approved/<slug>/<slug>.tex` to `build/pdf/approved/<slug>.pdf`. |
| `make check JOB=<slug>` | Compiles and validates the active draft. |
| `make approve JOB=<slug>` | Runs `check`, copies the internal `.tex` and PDF to `approved/<slug>/`, exports `.public.tex`, writes metadata, removes the active draft, **and auto-runs `applied` (deletes inbox staging, marks `seen.tsv` APPLIED, stamps `Applied at:` in metadata, appends to `approved/_applied.tsv`)**. Pass `FORCE=1` to re-approve. |
| `make applied JOB=<slug>` | Standalone "mark as submitted" step. Normally not needed — `make approve` already chains it. Use only as an escape hatch (back-fill old approved slugs, or stamp a delayed-submission timestamp). |
| `make export JOB=<slug>` | Regenerates the share-safe `.public.tex` from the internal approved `.tex`. |
| `make learn JOB=<slug>` | Compares `ai-draft.tex` with approved `.tex`, writes learning materials, and optionally promotes personal rules. |
| `make clean-draft JOB=<slug>` | Safely removes `drafts/<slug>.tex` after an approved artifact exists. |
| `make abort JOB=<slug>` | Removes an unapproved imported cycle. Refuses when approved artifacts exist. |
| `make status JOB=<slug>` | Reports lifecycle state, sample class, metadata issues, and check guidance. |
| `make check-all` | Compiles and validates every current official approved artifact. |
| `make triage FROM=clipboard` | Triage one JD via the LLM judge. Accepts `URL=`, `FILE=`, `JOB=`, or pipe via stdin. |
| `make match-jobs SEARCH=<slug>` | Builds a raw-driven profile, runs JobSpy, ranks results, writes a shortlist. |
| `make scan-jobs SEARCH=<slug>` | `match-jobs` + auto-triage top-N + writes `jd_search/inbox.md`. |
| `make triage-inbox SEARCH=<slug>` | Resume the triage half only — re-runs the LLM judge over an existing `searches/<slug>/ranked_jobs.json` and regenerates `inbox.md`. Use after a `scan-jobs` run where the JobSpy/Adzuna scrape succeeded but the triage stage failed (e.g. wrong `TRIAGE_AGENT`, transient LLM hang). Saves you from re-scraping. |
| `make inbox` | Cat `jd_search/inbox.md` (only `APPLY` / `BORDERLINE` candidates). |
| `make draft JOB=<slug> FROM=inbox` | Import a candidate from `inbox.md` and draft (gate hits cache). |
| `make import-search-result SEARCH=<slug> RANK=1 JOB=<job>` | Legacy: import one ranked search result by score rank. |

Use `FORCE=1` only for intentional replacement. `LINKEDIN_FETCH=0` disables
LinkedIn description fetching (default on; required for non-empty `description`
to flow into triage).

### 9. Job Lifecycle

Lifecycle states are derived from files:

| State | Meaning |
|---|---|
| `imported` | `jobs/<slug>.md` exists. |
| `drafted` | `drafts/<slug>.tex` exists as active work. |
| `snapshotted` | `edits/<slug>/ai-draft.tex` exists. |
| `checked` | Not persisted; run `make check JOB=<slug>` now. |
| `approved` | `approved/<slug>/` exists. |
| `learned` | `edits/<slug>/note.md` exists. |

Approved sample classes:

- `official` - current examples the skill may use for structure
- `legacy` - retained history, not a current example
- `validation-sample` - flow/regression material
- `archive` - retired material under `approved/_*/`

Allowed `Status` values in metadata are exact:

```text
official | legacy | validation-sample | archive
```

### 10. Approved, Draft, Public, and Build

`drafts/<slug>.tex` is active editable work. It is not the archive.

`approved/<slug>/<slug>.tex` is the internal audit copy. It keeps `% src:` and
`% TODO:` comments so every claim can be inspected.

`approved/<slug>/<slug>.public.tex` is the share-safe source copy. It strips
internal comments. If someone asks for LaTeX source, share this file, not the
internal audit file.

`approved/<slug>/<slug>.pdf` is the submitted PDF record.

`build/` contains derived compilation output:

```text
build/latex/drafts/<slug>/
build/latex/approved/<slug>/
build/pdf/drafts/<slug>.pdf
build/pdf/approved/<slug>.pdf
```

`build/` is useful for preview and validation, but it is not a source of truth.
It can be regenerated.

### 11. Check Validators

Every resume bullet must use this machine-readable shape:

```latex
\resumeItem{\normalsize{...content...}}
% src: <path-in-raw>
```

`make check` validates the active draft. `make check-all` applies the same rules
to official approved artifacts. The current validators enforce:

1. 1-10 detectable resume bullets.
2. Every bullet is followed immediately by `% src:`.
3. No `% src:` points to `approved/`.
4. No `% src:` points to `latex-template.tex`.
5. No `\mid`; use `\textbar{}` for text-mode vertical bars.
6. `\end{document}` exists.
7. PDF page count is exactly 1.
8. At least one `% TODO:` gap comment is present.
9. Public approved `.tex`, when present, contains no `% src:` or `% TODO:`.

### 12. Learning Notes and Preferences

`make learn` compares:

```text
edits/<slug>/ai-draft.tex
approved/<slug>/<slug>.tex
```

It creates a deterministic diff report, not an LLM memory. The generated
`note.md` separates:

- what changed
- canonical rule candidates
- personal preference candidates
- JD-specific choices
- do-not-promote warnings
- open questions

Use `preferences.md` only for stable user preferences:

- repeated wording choices
- layout or visual preferences
- user-specific carve-outs over canonical rules
- preferences supported by real edits

Do not use `preferences.md` for one-off JD positioning, temporary keyword
targeting, bug fixes, or universal rules that belong in the skill's
`references/canonical-rules.md`.

The skill reads both layers:

| File | IDs | Scope |
|---|---|---|
| `references/canonical-rules.md` | `C###` | Universal resume-engineering rules. |
| `preferences.md` | `P###` / `L###` | Personal content and layout preferences. |

### 13. Search Module

The `jd_search/` layer can:

- read `raw/`
- generate a local profile
- build a query plan
- run JobSpy
- rank jobs locally
- import selected results into `jobs/<slug>.md`

Install JobSpy only if you want real board searches:

```bash
python3 -m pip install -U python-jobspy
make match-jobs SEARCH=raw-fit
```

Preview without searching:

```bash
make match-jobs SEARCH=raw-fit DRY_RUN=1 FORCE=1
```

Import a ranked result:

```bash
make import-search-result SEARCH=raw-fit RANK=1 JOB=my-target-job
```

See `jd_search/README.md` for module details. This layer does not log in, click
Apply, solve CAPTCHA, or bypass access controls.

### 14. Runtime Notes

`AGENT=auto` chooses a local drafting agent:

```text
codex if the `codex` command exists
otherwise claude if the `claude` command exists
otherwise fail
```

It runs only one agent. If Codex exists but fails, the script fails rather than
falling through to Claude.

Codex uses the `.agents/skills/` mirror. Claude Code uses `.claude/skills/`.
If your runtime does not auto-discover the skill, invoke it explicitly:

```text
Read `.agents/skills/drafting-resume-from-confirmed-assets/SKILL.md` and follow
its rules to draft a resume for `jobs/my-first-jd.md`.
```

### 15. Troubleshooting

- **`make check` cannot determine PDF page count**: inspect
  `build/latex/drafts/<slug>/<slug>.log` for LaTeX errors.
- **Missing `.sty` file**: install the package with `sudo tlmgr install <name>`.
- **Draft is empty or generic**: `raw/` is underseeded or the resume PDF is not
  readable enough. Add project notes.
- **Draft is over one page**: shorten bullets and reduce bullet count.
- **A JD is a poor fit before approval**: use `make abort JOB=<slug>`.
- **`make approve` refuses to overwrite**: use `FORCE=1` only if replacement is
  intentional.
- **`make learn` refuses on legacy/validation/archive**: learning is for current
  official samples; inspect with `make status JOB=<slug>`.
- **`make check-all` fails but `make check` passes**: one validates approved
  artifacts, the other validates the active draft.
- **VS Code preview does not update**: ensure `latexmk` is installed and restart
  VS Code after installing LaTeX tools.

### 16. Privacy

Most useful files in a real cycle are private: `raw/`, `jobs/`, `drafts/`,
`approved/`, `edits/`, `.local.tex`, and `preferences.md`. Read `PRIVACY.md`
before pushing or sharing a repo.
