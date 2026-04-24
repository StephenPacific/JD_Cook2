# Privacy & Sharing Guide

JDcook is designed to run locally with your own resume, your own project notes, and your own JD history. Most content here is personal and should NOT be pushed to a public repo.

This file maps every directory to a **share status** and gives two publishing paths.

---

## File-by-file audit

| Path | Contains | Push to public repo? |
|---|---|---|
| `.claude/skills/...` (SKILL.md, schema, bullet-rules, anti-patterns) | Rules / methodology | ✅ Yes |
| `.claude/skills/.../references/latex-template.tex` | Your name / phone / email baked in the header | ⚠️ Sanitize OR gitignore |
| `.agents/skills/...` | Mirror of above | Same rules |
| `Makefile` | Build orchestration | ✅ Yes |
| `scripts/cycle.py` | Cycle helper | ✅ Yes |
| `scripts/__pycache__/` | Python bytecode | ❌ Never (gitignore) |
| `README.md`, `USAGE.md`, `PRIVACY.md` | Generic documentation | ✅ Yes |
| `raw/code/_TEMPLATE.md` | Blank repo-note template | ✅ Yes |
| `raw/resumes/*.pdf` | Your personal resume, PII throughout | ❌ Never |
| `raw/code/*.md` (filled) | Real project descriptions, supervisor names, mentor identity, grades | ❌ Never |
| `jobs/*.md` | JD text (may be company IP) + links to real companies | ❌ Never |
| `drafts/*.tex` | Personal resume body + PII header | ❌ Never |
| `approved/<slug>/*` | Final submitted resumes | ❌ Never |
| `edits/<slug>/*` | AI draft + final + diff + note (full PII) | ❌ Never |
| `preferences.md` | Style rules; examples may reference specific projects | ⚠️ Depends — see below |
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
        anti-patterns.md
        latex-template.tex        ← sanitize header to placeholders first (see below)
.agents/skills/...                (same content, mirror)
Makefile
scripts/cycle.py
README.md
USAGE.md
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
jobs/
drafts/
approved/
edits/
preferences.md                    ← optional; see "On preferences.md" below

# Build
build/
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

The rules themselves (P001–P007, L001) are generic and safe to share. But the **example phrases** embedded in them may leak project details:

- Specific dataset descriptions — may tie to a real lab / facility
- University-partner phrases like `"<school>--<company>"` — reveal a specific industry partnership
- Concrete percentage metrics — identify a particular project outcome

If you're going Path A (public), either:

- Sanitize example phrases in `preferences.md` to generic placeholders (`"large dataset"`, `"partner organisation"`, `"measurable reduction"`), or
- Keep `preferences.md` gitignored and ship a minimal `preferences.example.md` with 1–2 neutral sample rules

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
