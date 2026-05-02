# JDcook Roadmap

JDcook is currently an evidence-grounded resume workflow. The next product
direction is to grow it into a local-first career companion, but the immediate
priority is still to finish a useful MVP before expanding the surface area.

## Product North Star

JDcook should help a user move from raw career evidence to better job outcomes:

```text
raw evidence
  -> user profile
  -> job discovery
  -> fit evaluation
  -> tailored resume
  -> application support
  -> interview and skill practice
  -> updated profile
```

The core promise is not "generate a resume fast." The promise is:

> Help the user understand where they fit, apply truthfully, improve through
> feedback, and get better at the roles they are targeting.

## Current State

JDcook already has a strong resume core:

- `raw/` stores the user's evidence base.
- `jobs/` stores imported job descriptions.
- `make draft` generates a JD-tailored resume draft.
- `make check` validates formatting and evidence markers.
- `make approve` stores an auditable submitted artifact.
- `make learn` extracts reusable lessons from human edits.
- `preferences.md` stores personal writing and layout preferences.
- `jd_search/` can generate a local profile from `raw/`, search via JobSpy, rank results, and import selected jobs.

This means JDcook already has a user profile, but it is distributed across
several layers:

- Fact profile: `raw/`
- Search profile: `jd_search/profiles/generated-from-raw.json`
- Style profile: `preferences.md`
- Historical acceptance profile: `approved/` and `edits/`

## 1.0 - MVP: Evidence-Grounded Resume Workflow

The MVP is not complete until the core resume loop is reliable enough to use
repeatedly without manual repair.

### MVP Goal

A user can take one real JD from discovery/import through final approved resume,
with evidence tracking and learning notes preserved locally.

### MVP Scope

- Import a JD from clipboard or public URL.
- Draft a tailored LaTeX resume from `raw/`.
- Require evidence markers for resume bullets.
- Compile local PDF previews.
- Check formatting, bullet count, and public/private separation.
- Approve a resume into `approved/`.
- Learn from human edits without overfitting one job.
- Keep private user data local by default.

### MVP Completion Criteria

- Run several real end-to-end cycles without needing ad hoc fixes.
- `make draft`, `make check`, `make approve`, and `make learn` behave predictably.
- The approved/public artifact split is clear and safe.
- The user can inspect why each resume claim is supported.
- Documentation explains the standard path without requiring chat history.

## 2.1 - Search Module

Search is the next practical upgrade after the MVP. The goal is not to copy
career-ops wholesale, but to add a focused discovery layer that fits JDcook.

### Search Goal

JDcook should find relevant jobs, rank them against the user's profile, and put
good candidates into a reviewable inbox before any resume work begins.

### Inspiration From career-ops

career-ops does search through:

- a portal/company config file
- direct ATS API scans for Greenhouse, Ashby, and Lever
- title filters with positive and negative keywords
- scan history and deduplication
- a pending pipeline inbox
- optional liveness checks for stale links

JDcook should borrow the operating pattern, not the whole architecture.

### Proposed JDcook Search Files

```text
jd_search/
  portals.yml
  scan_portals.py
  inbox.md
  scan_history.tsv
  searches/
```

### Proposed Commands

```sh
make scan-jobs
make search-jobs
make inbox
make import-inbox JOB=<slug> RANK=1
```

### 2.1 Scope

- Keep the existing JobSpy search path.
- Add target-company scanning.
- Add direct ATS support where public APIs are available.
- Add `inbox.md` for candidate jobs waiting for review.
- Add `scan_history.tsv` to avoid repeated work.
- Deduplicate against imported jobs and approved applications.
- Allow selected jobs to flow into the existing `jobs/<slug>.md` workflow.

### 2.1 Non-Goals

- Do not auto-submit applications.
- Do not log in to job boards.
- Do not bypass CAPTCHA, access controls, or platform restrictions.
- Do not turn every search result into a resume draft.

## 3.0 - Companion Learning

Companion learning is the larger product idea. It should come after the resume
MVP and search module are stable.

### 3.0 Goal

Use the user's profile, target jobs, gaps, notes, and application history to
help them improve over time.

JDcook should become a career companion that can say:

- "You are strong enough to apply for this role."
- "This role is promising, but React testing is an interview risk."
- "Your profile has evidence for Python and RAG, but not enough for Kubernetes."
- "Here are three questions to practice before applying."
- "This approved resume suggests you prefer dense bullets and restrained bolding."

### 3.0 Profile Expansion

The user profile could grow into:

```text
facts:
  projects, resumes, claims, metrics

preferences:
  writing style, layout choices, resume structure

skills:
  known strengths, weak areas, confidence level

targets:
  roles, companies, locations, compensation, constraints

practice:
  questions answered, mistakes, spaced repetition schedule

interview:
  STAR stories, project explanations, weak answers
```

### 3.0 Features

- Skill map generated from `raw/`, JDs, and approved resumes.
- Gap detection from target roles.
- Random practice drills from weak spots.
- React, Python, system design, SQL, AI, and behavioral interview questions.
- STAR story bank tied to real evidence.
- Interview simulations based on jobs in the inbox.
- Progress tracking across practice sessions.
- Suggested mini-projects only when they address real target-role gaps.

### Example Companion Loop

```text
JDcook sees:
- User has React project evidence.
- Recent target JDs ask for hooks, testing, and state management.
- Approved resumes mention React, but not deep testing ownership.

JDcook asks:
1. Explain when `useEffect` cleanup runs.
2. How would you debounce an API-backed search box?
3. How would you test a React component that calls an async endpoint?

Then JDcook records:
- React hooks confidence: medium
- React testing confidence: weak
- Suggested next drill: async component testing
```

## Product Principles

- Local-first: personal data should stay in the workspace by default.
- Evidence-grounded: do not invent experience or metrics.
- Human-in-the-loop: JDcook can suggest, draft, and check, but the user decides.
- Fit before effort: do not spend resume time on low-quality or poor-fit jobs.
- Learning over automation: the system should help the user become stronger, not only click faster.
- Small loops first: finish the MVP before building the larger companion system.

## Near-Term Order

1. Finish and harden the `1.0` resume MVP.
2. Add `2.1` search as a small inbox-driven module.
3. Use search and approved cycles to collect better gap signals.
4. Design `3.0` companion learning once the profile data is trustworthy.

