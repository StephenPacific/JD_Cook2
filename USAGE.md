# JDcook — Usage Guide

A skill-based, evidence-grounded workflow for drafting JD-tailored resumes, with a memory loop that learns from your edits over time.

---

## What it is

Three layers:

- **Skill** (`.claude/skills/` and `.agents/skills/`) — the workflow + rules the agent follows when drafting. Rules are split in two:
  - `references/canonical-rules.md` — universal resume-engineering rules (`C###`), safe to ship to any user
  - `preferences.md` (project root) — personal style preferences and carve-outs (`P###` / `L###`), gitignored under Path A
- **Raw** (`raw/`) — your facts (past resumes, project notes); every bullet in a draft must trace back to here
- **Memory** (`approved/`, `edits/`, `preferences.md`) — what got submitted, how it differed from the AI draft, and the accumulated personal style rules that apply next time

One skill is live: `drafting-resume-from-confirmed-assets`. It:
1. Reads `references/canonical-rules.md` (universal) and `preferences.md` (personal); applies both.
2. Reads all files under `raw/`.
3. Reads the JD you specify.
4. Produces `drafts/<slug>.tex` with a `% src:` comment after every bullet, TODO comments for unmet JD requirements, and no hallucinated claims.

---

## Prerequisites

- **Claude Code** (or a Codex-compatible runtime that reads `.agents/skills/`)
- **BasicTeX** (via Homebrew: `brew install --cask basictex`)
- **Extra LaTeX packages**: `sudo tlmgr install collection-latexrecommended collection-fontsrecommended`
- **Python 3** for `scripts/import_job.py` and `scripts/cycle.py` (clipboard/http imports use the standard library only)
- **Playwright** only if you want `MODE=js` URL imports: `python3 -m pip install playwright && python3 -m playwright install chromium`
- **VS Code** with the **LaTeX Workshop** extension (recommended for live preview)

---

## Directory layout

```
.claude/skills/drafting-resume-from-confirmed-assets/    SKILL + references
.agents/skills/drafting-resume-from-confirmed-assets/    Codex mirror
raw/                                                      evidence base
  ├── resumes/                                              past resumes (PDF)
  └── code/                                                 repo/project notes (md)
jobs/                                                     one file per JD you apply to
  └── _sources/<slug>/                                      import snapshots (clipboard/url)
drafts/                                                   AI-generated + your edits
approved/<slug>/                                          immutable submission record
edits/<slug>/context.md                                   selected draft context
edits/<slug>/                                             cycle learning materials
preferences.md                                            accumulated style rules (P### / L###)
Makefile                                                  cycle orchestration
scripts/import_job.py                                     clipboard/url -> jobs/<slug>.md
scripts/cycle.py                                          check / approve / learn / status
build/                                                    compiled PDFs (gitignored)
```

---

## The three-phase workflow for one JD

### Phase 1 — Generate the first draft

1. Pick a **slug** (lowercase, hyphens): `stripe-backend`, `atlassian-fullstack`, etc.
2. Import or save the JD as `jobs/<slug>.md`.

   Recommended, if you already have the JD open in your browser:

   ```bash
   # Select the JD text in the browser, copy it, then:
   make import-job JOB=<slug> FROM=clipboard
   ```

   URL imports are also supported for public pages:

   ```bash
   make import-job JOB=<slug> URL="https://..." MODE=http
   make import-job JOB=<slug> URL="https://..." MODE=js
   ```

   If `MODE` is omitted, the importer uses `auto`: try HTTP first, then JS if the page looks too sparse. `MODE=js` uses Playwright for JS-heavy pages. It does not log in, solve CAPTCHA, click Apply, or bypass access controls. If a site blocks automated rendering, use `FROM=clipboard`.
3. Generate the initial draft:

   ```bash
   make draft JOB=<slug>
   ```

   `make draft` first writes `edits/<slug>/context.md`, selecting only similar official approved examples for structure and forbidding draft-time reads of unselected approved files or `edits/*/note.md`. The default context limit is 2 examples; use `CONTEXT_LIMIT=3` only when a role genuinely benefits from more history. It then invokes a local agent (`codex` first, then `claude`) with the `drafting-resume-from-confirmed-assets` skill. The skill reads canonical rules plus `preferences.md`, applies learned rules, writes `drafts/<slug>.tex`, and snapshots the untouched AI draft to `edits/<slug>/ai-draft.tex`.

### Phase 2 — Cycle (Makefile)

Run these in order from the project root:

```bash
# Edit drafts/<slug>.tex in VS Code, Overleaf, or your LaTeX editor.
# Validate whenever you want (auto-compiles first):
make check JOB=<slug>

# When everything passes, approve:
make approve JOB=<slug>

# Optional: generate diff.patch and a prefilled note.md for learning.
# If the AI draft was approved without any human edit (empty diff), `learn`
# short-circuits to a stub note.md only — final-approved.tex / diff.patch /
# promotion review are all skipped.
make learn JOB=<slug>
```

**Order matters.** `make draft` must run before you edit because it creates both the draft and the AI snapshot used by optional `make learn`. Manual draft insertion is not part of the standard flow. `make approve` completes the application record; `make learn` is a post-approval memory step for cases where you want to capture edit lessons.

### Phase 3 — Triage learning into rules

1. If you ran `make learn`, review the `edits/<slug>/note.md` it printed. For non-empty diff cycles, answer the promotion prompt:
   - **What Changed** — prefilled from the diff; verify the summary
   - **Canonical Rule Candidates** — rules that may generalise across users, stacks, domains, and seniority levels
   - **Personal Preference Candidates** — your own voice, visual style, or carve-outs over canonical rules
   - **JD-Specific Choices** — this JD only, don't promote
   - **Do Not Promote** — tempting but unsafe generalisations
   - **Manual Promotion Checklist** — final human review before changing rule files
2. Press Enter / choose `0` if nothing should be promoted yet.
3. Choose `1` or `2` to append a personal `P###` or `L###` rule to `preferences.md`.
4. Choose `3` for canonical candidates; these stay manual because public `C###` rules must pass the 4-criterion test.
5. For AI-only cycles, the stub `note.md` is the end of the learning step; no promotion prompt appears.
6. Next time the skill runs, it reads both rule layers automatically.

---

## Job lifecycle and sample classes

The workflow has two separate concepts:

- **Job lifecycle** — how far a single slug has moved through the pipeline.
- **Sample class** — whether an approved artifact should be treated as a current official example, a legacy learning source, a validation sample, or archive.

### Job lifecycle states

These states are derived from files on disk, except `checked`, which is an action that must be run now:

| State | Meaning |
|---|---|
| `imported` | `jobs/<slug>.md` exists. |
| `drafted` | `drafts/<slug>.tex` exists as an active working draft. Completed cycles normally show `drafted: no` after `make approve` cleans the workspace copy. |
| `snapshotted` | `edits/<slug>/ai-draft.tex` exists. This is created by `make draft` before user edits. |
| `checked` | `make check JOB=<slug>` can pass now. This is not persisted; do not treat it as historical proof. |
| `approved` | `approved/<slug>/` exists with the approved artifact set. |
| `learned` | `edits/<slug>/note.md` exists. |

### Approved sample classes

Approved samples are classified with deterministic tie-breaks:

1. `approved/_validation/<slug>/` is `validation-sample`, regardless of metadata.
2. Any other `approved/_*/<slug>/` path is `archive`, regardless of metadata.
3. A top-level approved directory with exact metadata `Status: validation-sample` is `validation-sample`.
4. A top-level approved directory with exact metadata `Status: legacy` is `legacy`.
5. A top-level approved directory with exact metadata `Status: archive` is `archive`.
6. A top-level approved directory with exact metadata `Status: official`, or no `Status` field, is `official`.

Allowed `Status` values are exact enum values only:

```text
official | legacy | validation-sample | archive
```

Do not put explanatory text in `Status`. Use `Status notes` for prose such as "pre-current internal/public audit format" or "flow test only".

### Metadata ownership

`make approve` and `make learn` may write metadata. On intentional replacement (`FORCE=1`), generated fields may be refreshed, but user-editable fields should be preserved when possible.

Machine-managed fields:

- `Internal audit LaTeX`
- `Public LaTeX`
- `JD source`
- `Submission date`
- `Compiled PDF`

User-editable / preserve-on-replace fields:

- `Status`
- `Status notes`
- `Company`
- `Result`
- `Posting URL`
- `Job ID`
- `Applications close`
- `Cycle notes`
- `Legacy note`

`Cycle notes` may be initialized by `make approve` as an optional learning reminder and is refreshed by `make learn` when learning materials exist. `make approve FORCE=1` should not erase an existing human-curated note path.

---

## Make targets reference

| Target | What it does |
|---|---|
| `make import-job JOB=<slug> FROM=clipboard` | Reads your clipboard and writes `jobs/<slug>.md` plus `jobs/_sources/<slug>/`. |
| `make import-job JOB=<slug> URL="..." MODE=http/js` | Imports a public JD URL into `jobs/<slug>.md`; omitting `MODE` uses `auto`, and `MODE=js` requires Playwright. |
| `make draft JOB=<slug>` | Writes `edits/<slug>/context.md` with selected similar approved examples (default 2; override with `CONTEXT_LIMIT=3`), invokes a local agent to generate `drafts/<slug>.tex` from `jobs/<slug>.md` + `raw/`, then snapshots it to `edits/<slug>/ai-draft.tex`. This is the only standard way to create an editable draft. |
| `make preview JOB=<slug>` / `make draft-pdf JOB=<slug>` | Compile active `drafts/<slug>.tex` → `build/pdf/drafts/<slug>.pdf`. Used by `check`. |
| `make approved JOB=<slug>` | Compile `approved/<slug>/<slug>.tex` → `build/pdf/approved/<slug>.pdf`. |
| `make check JOB=<slug>` | Compiles + runs validators via `scripts/cycle.py`. Fails on any violation. |
| `make approve JOB=<slug>` | Runs `check` first, then copies the internal audit `.tex` + `.pdf` into `approved/<slug>/`, auto-generates `<slug>.public.tex`, writes `metadata.md`, and removes the active `drafts/<slug>.tex` workspace copy. |
| `make export JOB=<slug>` | Generates `approved/<slug>/<slug>.public.tex` from the internal approved `.tex` by stripping `% src:` / `% TODO:` comments. Use `FORCE=1` to regenerate. |
| `make learn JOB=<slug>` | Optional post-approval memory step. Two paths: (a) **non-empty diff** — generates `edits/<slug>/final-approved.tex` + `diff.patch` + a prefilled `note.md`, prints the note, asks whether to promote a personal `P###` / `L###` rule. (b) **empty diff (AI-only approve)** — short-circuits to a stub `note.md` only; skips `final-approved.tex`, `diff.patch`, and the promotion review since there's nothing to learn. Both paths update metadata and refuse non-official samples unless `FORCE=1`. To downgrade a previously full-format learn into a stub (e.g. you re-ran after manually reverting your edits), use `FORCE=1`. |
| `make clean-draft JOB=<slug>` | Safely removes `drafts/<slug>.tex` after an approved artifact exists. Useful for old cycles created before automatic cleanup. |
| `make abort JOB=<slug>` | Terminates an unsuitable unapproved cycle and removes `jobs/<slug>.md`, `jobs/_sources/<slug>/`, `drafts/<slug>.tex`, `edits/<slug>/`, and draft build artifacts. Refuses if `approved/<slug>/` exists. |
| `make status JOB=<slug>` | Reports lifecycle state, sample class, metadata issues, and non-persisted `checked` guidance for one slug. |
| `make check-all` | Compiles and validates every current `official` approved artifact; skips `legacy`, `validation-sample`, and `archive`. |

**`FORCE=1`** (env or `--force` flag for `cycle.py`) lets any step overwrite an existing artifact. Use deliberately.

### Approved vs public LaTeX

`approved/<slug>/<slug>.tex` is the internal audit copy. It intentionally keeps
`% src:` and `% TODO:` comments so the evidence chain remains inspectable.

`approved/<slug>/<slug>.public.tex` is the share-safe source copy. It is
generated automatically by `make approve` and can be regenerated with
`FORCE=1 make export JOB=<slug>`.

If someone asks for the LaTeX source, share `.public.tex`, not the internal
audit `.tex`.

### Active draft cleanup

`drafts/` is an active workspace, not the long-term archive. After `make approve`
succeeds, the approved resume already exists in `approved/`, so `make approve`
removes `drafts/<slug>.tex` to keep the active draft folder focused on in-progress
work.

For completed cycles, `make status` may therefore show `drafted: no` while
`approved: yes`. `learned: no` is also valid when you chose not to run the
optional learning step.

For older cycles created before this cleanup behavior, run
`make clean-draft JOB=<slug>` after confirming the cycle is approved.

If a JD turns out to be a poor fit before approval, terminate the active cycle:

```sh
make abort JOB=<slug>
```

`abort` is intentionally limited to unapproved cycles. Once `approved/<slug>/`
exists, the job is submission history and must be archived or edited
intentionally rather than deleted by active-workspace cleanup.

---

## Bullet shape contract

Every resume bullet must use this exact shape:

```latex
\resumeItem{\normalsize{...content...}}
% src: <path-in-raw>
```

The `\normalsize{...}` wrapper is part of the machine-readable contract, not just
styling. `scripts/cycle.py check` uses `\resumeItem{\normalsize` as the bullet
recognition anchor; removing the wrapper makes bullets invisible to the
validator and can create false passes with zero detectable resume bullets.

---

## What `check` validators enforce

From `scripts/cycle.py`:

`make check` applies these validators to the current draft. `make check-all`
reuses the same validators against compiled `official` approved artifacts.

1. 1–10 detectable resume bullets (Rule #9 — page-budget proxy; zero bullets fails because it usually means the bullet shape contract was broken)
2. Every `\resumeItem{\normalsize...}` is followed on the next line by `% src:`
3. No `% src:` points to `approved/` (would create circular references)
4. No `% src:` points to `latex-template.tex` (Rule #8 — template body is a format reference, not a fact source)
5. No `\mid` anywhere (use `\textbar{}` for text-mode vertical bars)
6. `\end{document}` exists
7. PDF page count is exactly 1 (parsed from the latexmk log)
8. At least one `% TODO:` gap comment is present (the JD-gap block must be visible before approval)
9. If `approved/<slug>/<slug>.public.tex` exists, it must not contain `% src:` or `% TODO:` internal audit comments

---

## Common pitfalls

- **Editing outside `make draft`** — snapshot may be missing or may not match the AI draft, so the learn-step diff loses meaning. Always start with `make draft`.
- **Mixing `\mid` and `\textbar{}`** — `\mid` is math-mode only; in text it raises *"Missing $ inserted"*. Validator 5 catches this.
- **Adding a bullet without `% src:`** — validator 2 fails. Either add the source comment or delete the bullet.
- **Bullets too long** — each bullet > ~25 words pushes rendering to 2 lines; 10 bullets × 2 lines overflows the 1-page budget. Validator 7 catches the overflow.
- **Promoting a JD-specific choice to rules** — pollutes either the universal layer or your personal style profile. If only one cycle has confirmed a pattern, keep it in the candidate list and reconsider after the next cycle.
- **Skipping Phase 3** — you archived a resume but didn't update canonical or personal rules. Next time the skill still makes the same mistakes you manually corrected. Phase 3 is the learning step; without it the memory loop doesn't close.

---

## Rules model: dual layer (canonical + personal)

The skill applies BOTH its mirrored `references/canonical-rules.md` file and the project-root `preferences.md`. They serve different purposes:

| File | ID prefix | Scope | Distribution |
|---|---|---|---|
| Skill `references/canonical-rules.md` | `C###` | Universal — works for any user, stack, JD | Open-source ship |
| `preferences.md` | `P###` / `L###` | Personal — your style, your carve-outs | Gitignored under Path A |

A rule in `preferences.md` may be **purely personal** (your aesthetic/voice) OR a **carve-out over canonical** (a tighter / narrower variant of a `C###` rule). Carve-outs reference the parent canonical rule explicitly.

Each rule has:

- **ID** — `C###` (canonical), `P###` (content preference), or `L###` (layout preference)
- **Why** — the principle / observation behind the rule
- **How to apply** — operational instruction
- **Example from cycle** (preferences only) — concrete cycle that produced it

Rules are **promoted retrospectively** from `edits/<slug>/note.md`, never added speculatively. To promote into canonical rules, a rule must pass the 4-criterion test (stack-agnostic, domain-agnostic, seniority-agnostic, example-defrostable) — see the skill's `references/canonical-rules.md` for the protocol. If two cycles disagree on a rule, that's a signal — refine the condition, demote, or delete.

---

## Growing the preferences file over time

Expected trajectory:

- **Cycle 1:** 4–6 rules extracted from first approve (large delta: AI default vs your real voice)
- **Cycle 2:** 1–3 new rules + possible extensions of existing ones
- **Cycle 3–5:** 0–2 new rules per cycle; extensions and caveats more common than new rules
- **Cycle 6+:** Mostly stable. New rules signal either a domain switch (e.g. ML → backend) or a genuinely new style insight

**Your manual editing load should trend downward.** If it's not dropping, `preferences.md` isn't being read or applied — investigate the skill's runtime behavior before blaming the rules.

---

## Files that are safe to share; files that are not

See `PRIVACY.md` (or the `.gitignore` rules) for what to push and what to keep private.
