# JDcook

JDcook is a local-first, evidence-grounded workflow for drafting resumes against
specific job descriptions. It uses your own source material, keeps resume claims
traceable, and turns your edits into personal rules for future drafts.

It is not an auto-apply bot. It does not log in to job boards, click Apply,
solve CAPTCHA, or bypass access controls.

## What It Does

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

The core idea is simple: AI can write the first draft, but every resume claim
should be grounded in real evidence and every useful human edit should make the
next draft better.

## Quick Start

Clone and create local-only working directories:

```bash
git clone https://github.com/StephenPacific/JD_Cook2.git
cd JD_Cook2
mkdir -p raw/resumes raw/code jobs drafts approved edits
cp preferences.example.md preferences.md
```

Install the basics:

```bash
brew install --cask basictex
eval "$(/usr/libexec/path_helper)"
sudo tlmgr update --self
sudo tlmgr install latexmk collection-latexrecommended collection-fontsrecommended
```

Then:

1. Put your resume in `raw/resumes/`.
2. Write project notes under `raw/code/` using `raw/code/_TEMPLATE.md`.
3. Copy the LaTeX template to `.local.tex` and add your real contact details.
4. Import a JD.
5. Draft, check, approve, and learn.

```bash
make import-job JOB=my-first-jd FROM=clipboard
make draft JOB=my-first-jd
make check JOB=my-first-jd
make approve JOB=my-first-jd
make learn JOB=my-first-jd
```

Read [GUIDE.md](GUIDE.md) for the full first-cycle tutorial and reference.

## Directory Map

```text
raw/             user evidence: resumes and project notes
jobs/            imported job descriptions
drafts/          active editable resume drafts
approved/        final approved resume records
edits/           AI snapshots, diffs, and learning notes
preferences.md   personal style and layout rules
build/           derived LaTeX/PDF output, safe to regenerate
jd_search/       optional job discovery layer
```

Most of those directories contain personal data and are gitignored. See
[PRIVACY.md](PRIVACY.md) before pushing or sharing a repo.

## Job Search

JDcook includes an optional discovery layer that scans job boards, runs every
candidate through an LLM-as-judge triage, and writes a curated inbox:

```bash
python3 -m pip install -U python-jobspy
make scan-jobs SEARCH=daily             # 1. JobSpy + hard filter + auto-triage
make inbox                              # 2. read jd_search/inbox.md
make draft JOB=<slug> FROM=inbox        # 3. import + gate + draft
```

The pipeline reads `raw/` for the profile, applies a deterministic
visa/seniority hard filter, asks Codex/Claude to judge the rest semantically,
and lists only `APPLY` / `BORDERLINE` candidates in the inbox. Drafting is
never automatic — you pick from the inbox and trigger `make draft` yourself.

Details and the legacy `import-search-result` flow live in
[jd_search/README.md](jd_search/README.md).

## Documentation

- [GUIDE.md](GUIDE.md) - first-cycle tutorial plus command/reference manual.
- [PRIVACY.md](PRIVACY.md) - what is safe to publish and what must stay local.
- [ROADMAP.md](ROADMAP.md) - product direction: MVP, search, and companion learning.
- [jd_search/README.md](jd_search/README.md) - job discovery module details.

## Status

JDcook's current focus is the `1.0` evidence-grounded resume MVP. The next
planned layer is a stronger `2.1` search module, followed later by `3.0`
companion learning for interview practice and skill-gap work.
