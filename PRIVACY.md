# Privacy & Sharing Guide

JDcook is designed to run locally with your own resume, your own project notes, and your own JD history. Most content here is personal and should NOT be pushed to a public repo.

This file maps every directory to a **share status** and gives two publishing paths.

---

## File-by-file audit

| Path | Contains | Push to public repo? |
|---|---|---|
| `.claude/skills/...` (SKILL.md, schema, bullet-rules, content-strategy, anti-patterns, **canonical-rules**) | Rules / methodology — universal layer | ✅ Yes |
| `.claude/skills/.../references/latex-template.tex` | Header placeholders + body placeholder bullets (sanitized) | ✅ Yes (after Sprint 1.1 sanitization) |
| `.claude/skills/.../references/latex-template.local.tex` | Your name / phone / email + your real body content | ❌ Never (gitignored) |
| `.agents/skills/...` | Mirror of above | Same rules |
| `Makefile` | Build orchestration | ✅ Yes |
| `scripts/import_job.py` | JD import helper; no personal data baked into source | ✅ Yes |
| `scripts/cycle.py` | Cycle helper | ✅ Yes |
| `scripts/__pycache__/` | Python bytecode | ❌ Never (gitignore) |
| `README.md`, `GUIDE.md`, `PRIVACY.md`, `ROADMAP.md` | Generic documentation and product planning | ✅ Yes |
| `raw/code/_TEMPLATE.md` | Blank repo-note template | ✅ Yes |
| `raw/resumes/*.pdf` | Your personal resume, PII throughout | ❌ Never |
| `raw/code/*.md` (filled) | Real project descriptions, supervisor names, mentor identity, grades | ❌ Never |
| `raw/.cache/` | Derived text extracted from private PDF evidence + raw manifest | ❌ Never (gitignored) |
| `jobs/*.md` | JD text (may be company IP) + links to real companies | ❌ Never |
| `jobs/_sources/<slug>/*` | Clipboard/web snapshots, rendered text, screenshots, URL metadata | ❌ Never |
| `jd_search/README.md`, `jd_search/search_jobs.py`, `jd_search/import_result.py`, `jd_search/profiles/example.json` | Search framework + sanitized profile template | ✅ Yes |
| `jd_search/profiles/*.json` except `example.json` | Personal target roles, constraints, and fit preferences | ❌ Never |
| `jd_search/searches/<slug>/*` | Real search results, shortlists, ranking notes, application targets | ❌ Never |
| `drafts/*.tex` | Personal resume body + PII header | ❌ Never |
| `approved/<slug>/*` | Final submitted resumes, internal audit `.tex`, share-safe `.public.tex` | ❌ Never |
| `edits/<slug>/*` | AI draft + final + diff + note (full PII) | ❌ Never |
| `preferences.md` | **Personal** style preferences + carve-outs over canonical rules. Examples reference your real cycles. | ❌ Never (Path A) — gitignored. Universal rules already live in `canonical-rules.md`. |
| `build/` | Compiled PDFs and intermediate files | ❌ Never (gitignored) |

---

## Two publishing paths

### Path A — Open-source the framework only (recommended for a public repo)

Share the reusable tooling; keep all personal data private.

**What gets pushed:**
```
.claude/skills/drafting-resume-from-confirmed-assets/
    SKILL.md
    references/
        resume-schema.md
        bullet-rules.md
        content-strategy.md
        canonical-rules.md        ← universal C### rules (Sprint 1 added)
        anti-patterns.md
        latex-template.tex        ← header + body now all placeholders (Sprint 1.1)
.agents/skills/...                (same content, mirror)
Makefile
scripts/import_job.py
scripts/cycle.py
README.md
GUIDE.md
ROADMAP.md
PRIVACY.md
raw/code/_TEMPLATE.md
.gitignore
```

**What gets gitignored:**
```
# Personal data
raw/resumes/
raw/code/*.md
!raw/code/_TEMPLATE.md
raw/.cache/
jobs/
# includes jobs/_sources/<slug>/ import snapshots
drafts/
approved/
edits/
preferences.md                    ← optional; see "On preferences.md" below

# Build
build/
.DS_Store
*.aux
*.fdb_latexmk
*.fls
*.log
*.out
*.synctex.gz
scripts/__pycache__/
*.pyc
```

**Before pushing, sanitize the LaTeX template header.** Find the `\begin{center} ... \end{center}` block in both `.claude/skills/.../references/latex-template.tex` and `.agents/skills/.../references/latex-template.tex`, and replace your real name/phone/email/LinkedIn with placeholders:

```latex
\begin{center}
    {\color{nameblue}\huge Your Name} \\ \vspace{8pt}
    \href{}{\color{black}{City, State  \textbar{}}}
    \href{}{\color{black}{+1 (000) 000 0000 \textbar{}}}
    \href{}{ \color{black}{your.email@example.com }}
    \vspace{-1pt}
\end{center}
```

Also replace the `\newcommand{\JobURL}{...}` / `\newcommand{\Cloud}{...}` URLs pointing to your GitHub with generic `https://github.com/username/...` placeholders.

---

### Path B — Personal private repo (backup + history)

Push everything to a **private** GitHub repo. You get full version history of your applications, approved resumes, and cycle notes without exposing anything publicly. Personal data stays behind GitHub auth.

**What gets pushed:** everything except `build/` and LaTeX intermediates.

**Use this when:** you want off-machine backup or multi-device sync and you trust GitHub's private-repo privacy model.

---

## On `preferences.md`

After Sprint 1, all universal rules were promoted to `references/canonical-rules.md` (the open-source layer). Only personal preferences and carve-outs remain in `preferences.md` — they intentionally include cycle-specific examples that reference real projects, datasets, percentages, or university-partner names.

`preferences.md` is **gitignored under Path A**. New users who fork JDcook get the universal `canonical-rules.md` and an empty `preferences.md` to grow their own personal layer.

If you ever want to share your `preferences.md` (e.g., as a teaching example), either:

- Sanitize example phrases to generic placeholders (`"large dataset"`, `"partner organisation"`, `"measurable reduction"`), or
- Ship a minimal `preferences.example.md` with 1–2 neutral sample rules and keep your real `preferences.md` gitignored.

---

## Quick safety check before `git push`

```bash
# Verify nothing personal is staged
git status --porcelain | grep -E '(raw/resumes|raw/code|jobs|drafts|approved|edits)' \
  && echo "❌ Personal data staged! Stop." \
  || echo "✅ Clean — nothing personal queued"

# Verify latex-template.tex has been sanitized.
# Replace the placeholders below with YOUR real PII before running this check,
# and keep the modified version out of git (e.g. in a local scripts/privacy-check.sh).
grep -E "<YOUR_FIRST_NAME>|<YOUR_LAST_NAME>|<YOUR_PHONE_DIGITS>|<YOUR_EMAIL_LOCALPART>" \
  .claude/skills/*/references/latex-template.tex \
  .agents/skills/*/references/latex-template.tex \
  && echo "❌ Real PII still in template!" \
  || echo "✅ Template sanitized"
```

If both checks come back ✅, push is safe.
