# JDcook

JDcook is a local-first workflow for drafting job-specific resumes from raw
evidence, a job description, and reusable writing rules.

The project is built around a simple belief: AI can speed up the first draft,
but the final resume should still be grounded in facts the candidate can defend
in an interview.

## What It Does

It supports three connected workflows:

- Resume drafting from local evidence under `raw/`
- Human review, validation, approval, and learning from edits
- Optional job discovery through a local search and triage layer

The core loop:

```text
raw evidence
  + job description
  + canonical rules
  + personal preferences
  -> AI draft
  -> human edit
  -> check
  -> approved resume
  -> learning note
```

## What It Does Not Do

JDcook is not an auto-apply bot. It does not log in to job boards, click
Apply, solve CAPTCHA, bypass access controls, or submit applications without
human review.

Drafting is always explicit: you choose the job, inspect the draft, edit it,
and approve it.

## Quick Start

Clone the repo and create local-only working directories:

```bash
git clone https://github.com/StephenPacific/JD_Cook2.git
cd JD_Cook2
mkdir -p raw/resumes raw/code jobs drafts approved edits
cp preferences.example.md preferences.md
```

Install the PDF toolchain on macOS:

```bash
brew install --cask basictex
eval "$(/usr/libexec/path_helper)"
sudo tlmgr update --self
sudo tlmgr install latexmk collection-latexrecommended collection-fontsrecommended
```

Add your evidence locally:

1. Put your resume in `raw/resumes/`.
2. Write project notes under `raw/code/` using `raw/code/_TEMPLATE.md`.
3. Copy the LaTeX template to `.local.tex` and add your real contact details.

Run one resume cycle:

```bash
make import-job JOB=my-first-jd FROM=clipboard
make draft JOB=my-first-jd
make check JOB=my-first-jd
make approve JOB=my-first-jd
make learn JOB=my-first-jd
```

For the full first-cycle walkthrough, read [GUIDE.md](GUIDE.md).

## Optional Job Discovery

JDcook can scan job boards, run a local triage judge, and write a curated inbox:

```bash
python3 -m pip install -U python-jobspy
make scan-jobs SEARCH=daily
make inbox
make draft JOB=<slug> FROM=inbox
```

This layer only discovers and ranks candidates. Details live in
[jd_search/README.md](jd_search/README.md).

## Privacy Model

Most working directories contain personal data and are gitignored:

```text
raw/        private resumes and project evidence
jobs/       imported job descriptions and source snapshots
drafts/     editable resume drafts
approved/   final approved resume records
edits/      AI snapshots, diffs, and learning notes
build/      generated PDFs and LaTeX intermediates
```

The tracked repo is for reusable tooling, sanitized templates, and universal
rules. Read [PRIVACY.md](PRIVACY.md) before pushing or sharing.

## Repository Map

```text
.agents/skills/   Codex skill for resume drafting
.claude/skills/   Claude skill mirror
scripts/          import, draft, check, and learning helpers
jd_search/        optional job discovery module
raw/code/         local project notes; only _TEMPLATE.md is tracked
```

## Documentation

- [GUIDE.md](GUIDE.md) - first-cycle tutorial and command reference
- [PRIVACY.md](PRIVACY.md) - public/private sharing boundaries
- [jd_search/README.md](jd_search/README.md) - search, triage, inbox, and Adzuna details
- [ROADMAP.md](ROADMAP.md) - current status and product direction
