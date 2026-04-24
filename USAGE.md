# JDcook — Usage Guide

A skill-based, evidence-grounded workflow for drafting JD-tailored resumes, with a memory loop that learns from your edits over time.

---

## What it is

Three layers:

- **Skills** (`.claude/skills/` and `.agents/skills/`) — the rules the agent follows when drafting
- **Raw** (`raw/`) — your facts (past resumes, project notes); every bullet in a draft must trace back to here
- **Memory** (`approved/`, `edits/`, `preferences.md`) — what got submitted, how it differed from the AI draft, and the accumulated style rules that apply next time

One skill is live: `drafting-resume-from-confirmed-assets`. It:
1. Reads `preferences.md` and applies learned style rules.
2. Reads all files under `raw/`.
3. Reads the JD you specify.
4. Produces `drafts/<slug>.tex` with a `% src:` comment after every bullet, TODO comments for unmet JD requirements, and no hallucinated claims.

---

## Prerequisites

- **Claude Code** (or a Codex-compatible runtime that reads `.agents/skills/`)
- **BasicTeX** (via Homebrew: `brew install --cask basictex`)
- **Extra LaTeX packages**: `sudo tlmgr install collection-latexrecommended collection-fontsrecommended`
- **Python 3** for `scripts/cycle.py` (standard library only, no pip)
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
drafts/                                                   AI-generated + your edits
approved/<slug>/                                          immutable submission record
edits/<slug>/                                             cycle learning materials
preferences.md                                            accumulated style rules (P### / L###)
Makefile                                                  cycle orchestration
scripts/cycle.py                                          begin / check / approve / learn
build/                                                    compiled PDFs (gitignored)
```

---

## The three-phase workflow for one JD

### Phase 1 — Generate the first draft

1. Pick a **slug** (lowercase, hyphens): `stripe-backend`, `atlassian-fullstack`, etc.
2. Save the JD text as `jobs/<slug>.md`.
3. In Claude Code, ask it to draft the resume:

   > "Use the `drafting-resume-from-confirmed-assets` skill to draft a resume for `jobs/<slug>.md`."

   The skill reads `preferences.md` automatically and applies learned rules. Output lands in `drafts/<slug>.tex`.

### Phase 2 — Cycle (Makefile)

Run these in order from the project root:

```bash
# BEFORE editing anything, snapshot the AI draft:
make begin JOB=<slug>

# Edit drafts/<slug>.tex in VS Code (LaTeX Workshop for live PDF preview).
# Validate whenever you want (auto-compiles first):
make check JOB=<slug>

# When everything passes, archive:
make approve JOB=<slug>

# Generate diff.patch and note.md template for learning:
make learn JOB=<slug>
```

**Order matters.** `make begin` must run **before** you edit — otherwise the snapshot captures your edits, not the AI's original, and the diff becomes meaningless.

### Phase 3 — Promote preferences

1. Open `edits/<slug>/note.md` and fill the sections:
   - **What Changed** — summarise your substantive edits
   - **Preference Candidates** — rules that may generalise
   - **JD-Specific Choices** — this JD only, don't promote
   - **Do Not Promote** — tempting but unsafe generalisations
   - **Promote to `preferences.md`** — final call
2. Manually add accepted rules to `preferences.md` using the `P###` (content) or `L###` (layout) convention.
3. Next time the skill runs, it reads the new rules automatically.

---

## Make targets reference

| Target | What it does |
|---|---|
| `make draft JOB=<slug>` | Compile `drafts/<slug>.tex` → `build/pdf/drafts/<slug>.pdf`. Used by `check`. |
| `make approved JOB=<slug>` | Compile `approved/<slug>/<slug>.tex` → `build/pdf/approved/<slug>.pdf`. |
| `make begin JOB=<slug>` | Snapshot `drafts/<slug>.tex` to `edits/<slug>/ai-draft.tex`. Refuses overwrite; `FORCE=1` to override. |
| `make check JOB=<slug>` | Compiles + runs 8 validators via `scripts/cycle.py`. Fails on any violation. |
| `make approve JOB=<slug>` | Runs `check` first (dependency), then copies `.tex` + `.pdf` into `approved/<slug>/` and generates `metadata.md`. |
| `make learn JOB=<slug>` | Generates `edits/<slug>/final-approved.tex` + `diff.patch` + `note.md` template. |

**`FORCE=1`** (env or `--force` flag for `cycle.py`) lets any step overwrite an existing artifact. Use deliberately.

---

## What the 8 `check` validators enforce

From `scripts/cycle.py`:

1. ≤ 10 resume bullets (Rule #9 — page-budget proxy)
2. Every `\resumeItem{\normalsize...}` is followed on the next line by `% src:`
3. No `% src:` points to `approved/` (would create circular references)
4. No `% src:` points to `latex-template.tex` (Rule #8 — template body is a format reference, not a fact source)
5. No `\mid` anywhere (use `\textbar{}` for text-mode vertical bars)
6. `\end{document}` exists
7. PDF page count is exactly 1 (parsed from the latexmk log)
8. At least one `% TODO:` gap comment is present (the JD-gap block must be visible before approval)

---

## Common pitfalls

- **Editing before `make begin`** — snapshot becomes your edit, diff becomes empty. Always `begin` first.
- **Mixing `\mid` and `\textbar{}`** — `\mid` is math-mode only; in text it raises *"Missing $ inserted"*. Validator 5 catches this.
- **Adding a bullet without `% src:`** — validator 2 fails. Either add the source comment or delete the bullet.
- **Bullets too long** — each bullet > ~25 words pushes rendering to 2 lines; 10 bullets × 2 lines overflows the 1-page budget. Validator 7 catches the overflow.
- **Promoting a JD-specific choice to `preferences.md`** — pollutes the style profile. If only one cycle has confirmed a pattern, keep it in the candidate list and reconsider after the next cycle.
- **Skipping Phase 3** — you archived a resume but didn't update `preferences.md`. Next time the skill still makes the same mistakes you manually corrected. Phase 3 is the learning step; without it the memory loop doesn't close.

---

## Preferences model

Each rule in `preferences.md` has:

- **ID** — `P###` for content, `L###` for layout
- **Rule** — the operational instruction
- **Prefer / Avoid** — concrete positive and negative examples
- **Why** — the observation that produced it
- **Source** — the `edits/<slug>/note.md` it came from

Rules are **promoted retrospectively**, never added speculatively. If two cycles disagree on a rule, that's a signal — refine the condition, demote, or delete.

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
