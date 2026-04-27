# JDcook — Onboarding (first-time setup)

If you're new to this repo, this is the file to read first. It takes you from `git clone` to your first approved, PDF-compiled, JD-tailored resume with a working memory loop.

Expected time: **30–45 minutes** the first time (most of it is writing your own raw data honestly in Step 5). After that, each new JD takes **10–20 minutes** of real work.

---

## What you'll have at the end

- A compiled 1-page PDF resume tailored to one real JD
- An immutable record of that submission in `approved/<slug>/`
- Cycle materials in `edits/<slug>/` showing exactly what you changed from the AI draft
- The first few rules in your personal `preferences.md` that will make future drafts closer to your voice

---

## Runtime compatibility

- **Claude Code** — primary runtime. Skills in `.claude/skills/` are discovered automatically via the `description` field in each SKILL.md frontmatter. This is the path tested end-to-end.
- **Codex** (or any skill-aware runtime that reads `.agents/skills/`) — supported structurally (the skill files are mirrored), but skill auto-discovery behaviour varies by runtime. You may need to explicitly point Codex at the SKILL.md instead of relying on frontmatter discovery. See [Codex-specific notes](#codex-specific-notes) below.
- **Vanilla ChatGPT / Claude.ai web UIs** — not designed for this workflow. They can't read your local files, run `make`, or invoke skills. Stick to a local agent runtime.

---

## Prerequisites

| Tool | Why | Install |
|---|---|---|
| **Claude Code** (or Codex) | Runs the drafting skill | https://www.anthropic.com/claude-code |
| **Homebrew** (macOS) | Installs BasicTeX | https://brew.sh |
| **BasicTeX** | LaTeX compiler (`pdflatex`, `latexmk`) | `brew install --cask basictex` |
| **LaTeX packages** | Template dependencies | `sudo tlmgr install latexmk collection-latexrecommended collection-fontsrecommended` |
| **Python 3** (3.10+) | Runs `scripts/import_job.py` and `scripts/cycle.py`; clipboard/http imports use the standard library only | Usually preinstalled on macOS |
| **Playwright** | Optional; only needed for `make import-job ... MODE=js` | `python3 -m pip install playwright && python3 -m playwright install chromium` |
| **VS Code** + **LaTeX Workshop** extension | Live PDF preview while editing | Recommended, not strictly required |

### If you're on Linux

Replace `brew install --cask basictex` with your distro's TeX Live (`sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended latexmk` on Debian/Ubuntu). The rest of the workflow is identical.

### If you're on Windows

WSL2 + the Linux path above works. Native Windows LaTeX (MiKTeX) should also work but hasn't been tested end-to-end.

---

## Step 1 — Clone

```bash
git clone https://github.com/StephenPacific/JD_Cook2.git
cd JD_Cook2
```

Everything in this guide assumes your working directory is the repo root.

Create the local-only working directories that are intentionally absent from the public repo:

```bash
mkdir -p raw/resumes raw/code jobs drafts approved edits
touch preferences.md
```

These paths are gitignored because they will contain your resume, JD history, generated drafts, and personal style rules.

---

## Step 2 — Install the LaTeX toolchain

One-time, ~5 minutes, ~400 MB download:

```bash
brew install --cask basictex

# Refresh PATH (or restart your terminal)
eval "$(/usr/libexec/path_helper)"

# Install the packages this repo's template depends on
sudo tlmgr update --self
sudo tlmgr install latexmk collection-latexrecommended collection-fontsrecommended
```

Verify:

```bash
which pdflatex && which latexmk
# Both commands should print paths; if either says "not found", something didn't install.
```

If a future compile fails with `File 'foo.sty' not found`, just run:

```bash
sudo tlmgr install <the-package-that-provides-foo.sty>
```

Usually the package name matches or closely matches the missing `.sty`.

---

## Step 3 — Install Claude Code

Follow the official install link. Log in with your own Anthropic API key — the LLM calls are billed to your account, nothing goes through this repo.

If you're using Codex instead, see [Codex-specific notes](#codex-specific-notes).

---

## Step 4 — Personalise the local LaTeX template

This repo ships `latex-template.tex` with placeholder header info so the public repo stays safe to share. Keep that tracked file sanitized, and create local overrides for your real details:

```bash
cp .claude/skills/drafting-resume-from-confirmed-assets/references/latex-template.tex \
   .claude/skills/drafting-resume-from-confirmed-assets/references/latex-template.local.tex

cp .agents/skills/drafting-resume-from-confirmed-assets/references/latex-template.tex \
   .agents/skills/drafting-resume-from-confirmed-assets/references/latex-template.local.tex
```

Find the `\begin{center} ... \end{center}` block (near line ~193) and replace:

```latex
\begin{center}
    {\color{nameblue}\huge Your Name} \\ \vspace{8pt}
    \href{}{\color{black}{City, State  \textbar{}}}
    \href{}{\color{black}{+1 (000) 000 0000 \textbar{}}}
    \href{}{ \color{black}{your.email@example.com }}
    \vspace{-1pt}
\end{center}
```

With your real name, city, phone, email in the `.local.tex` files. Also update the `\newcommand{\XxxURL}{...}` lines near line ~30 to point to your real project repos, and add/remove entries as needed.

**Tip:** edit one file, then copy it over to the mirror to stay consistent:

```bash
cp .claude/skills/drafting-resume-from-confirmed-assets/references/latex-template.local.tex \
   .agents/skills/drafting-resume-from-confirmed-assets/references/latex-template.local.tex
```

The skill prefers `latex-template.local.tex` when it exists, then falls back to the placeholder `latex-template.tex`. Both `.local.tex` files are ignored by git.

---

## Step 5 — Seed your raw data (this is the real work)

The skill produces evidence-grounded resumes, which means **every bullet it generates must trace back to a file in `raw/`**. No raw files = empty draft. Garbage in `raw/` = inflated bullets and missed TODOs.

### 5a. Drop your current resume

```bash
mkdir -p raw/resumes
cp ~/Downloads/my-resume.pdf raw/resumes/
```

Any PDF works. The skill uses it as the primary fact source for roles, dates, achievements, and tech stack.

### 5b. Write one note per project you want on any resume

For every GitHub repo / work project / academic project you'd mention:

```bash
cp raw/code/_TEMPLATE.md raw/code/my-project-slug.md
```

Then open `raw/code/my-project-slug.md` and fill every section. The sections (copied from the template) include:

- **What it actually does** — user-perspective description of the system
- **What YOU personally built** — 3–8 specific things you owned (use the weakest honest verb)
- **What YOU did NOT do** (guardrail) — bound your contribution; this prevents the skill from inflating
- **Tech stack with depth** — annotate each tool as `daily` / `used` / `learned-here` / `referenced-only`
- **Outcomes / metrics** — only if real; leave blank otherwise
- **Notes for future self** — inflation risks, caveats, framing tips

Plan for **15–30 minutes per project** the first time. This is the highest-leverage step: a good raw note produces great drafts; a lazy raw note produces generic ones.

### 5c. Sanity-check

```bash
ls raw/resumes/  # should have at least 1 PDF
ls raw/code/     # should have multiple project .md files (plus _TEMPLATE.md)
```

---

## Step 6 — Your first cycle

### 6a. Import a JD

The workflow reads one stable file: `jobs/<slug>.md`. The easiest path is clipboard import:

```bash
# Open the JD in your browser, select the JD text, copy it, then:
make import-job JOB=my-first-jd FROM=clipboard
```

This writes `jobs/my-first-jd.md` and keeps a private source snapshot in `jobs/_sources/my-first-jd/`.

For public pages, URL import is also available:

```bash
make import-job JOB=my-first-jd URL="https://..." MODE=http
make import-job JOB=my-first-jd URL="https://..." MODE=js
```

If `MODE` is omitted, the importer uses `auto`: try HTTP first, then JS if the page looks too sparse. Use `MODE=http` for normal static pages. Use `MODE=js` for JS-heavy pages; it requires Playwright and only renders public pages. It does not log in, solve CAPTCHA, click Apply, or bypass access controls.

Manual creation is still fine: create `jobs/my-first-jd.md` in your editor and paste the JD text verbatim. The skill reads that file to do gap analysis.

### 6b. Start Claude Code and invoke the skill

```bash
claude  # or however your runtime starts
```

Then, in the Claude Code chat:

> Use the `drafting-resume-from-confirmed-assets` skill to draft a resume for `jobs/my-first-jd.md`.

The skill reads `preferences.md` (empty or near-empty on first cycle), scans `raw/`, analyses the JD, and writes `drafts/my-first-jd.tex`.

### 6c. Snapshot the AI draft **before** editing

```bash
make begin JOB=my-first-jd
```

This copies the AI version to `edits/my-first-jd/ai-draft.tex`. **Do this before you open the editor.** If you edit first, the snapshot captures your edits and the learn-step diff loses its meaning.

### 6d. Edit + validate loop

Open `drafts/my-first-jd.tex` in VS Code. Cmd+Alt+V opens the PDF preview on the right.

Edit until you're happy. When you want to validate:

```bash
make check JOB=my-first-jd
```

This auto-compiles and runs validators (bullet count ≤ 10, every bullet has a `% src:` comment, no `\mid`, PDF is 1 page, TODO block present, public export stripped when present, etc.). Any failure prints a clear `FAIL: ...` message and exits non-zero.

Fix the failures in the editor, re-run `make check`, repeat until it says `Check passed`.

### 6e. Approve and learn

```bash
make approve JOB=my-first-jd
make learn JOB=my-first-jd
```

`approve` re-runs `check` as a dependency (so you can't approve a broken draft), then copies the internal audit `.tex` + `.pdf` into `approved/my-first-jd/`, auto-generates `my-first-jd.public.tex`, and writes `metadata.md`.

Inside `approved/my-first-jd/`:

- `my-first-jd.tex` keeps `% src:` / `% TODO:` comments for your audit trail.
- `my-first-jd.public.tex` strips those comments and is the version to share if anyone asks for LaTeX source.
- `my-first-jd.pdf` is the normal application PDF.

`learn` compares `edits/.../ai-draft.tex` against the approved version, produces a unified `diff.patch`, and drops a `note.md` template with TODO sections for you to fill in.

### 6f. Promote stable patterns to `preferences.md`

Open `edits/my-first-jd/note.md`. Fill the six sections:

- **What Changed** — summarise your substantive edits
- **Preference Candidates** — rules that might generalise beyond this JD
- **JD-Specific Choices** — edits you made only because of this JD (do not promote)
- **Do Not Promote** — tempting-looking patterns that would be unsafe to generalise
- **Promote to `preferences.md`** — final decisions
- **Open Questions** — things to revisit after interview / rejection / offer

For each entry you decide to promote, open `preferences.md` and add a new rule using the existing format:

```markdown
### P### — Short rule name

**Rule:** The operational instruction.
- ✅ **Prefer:** positive example
- ❌ **Avoid:** negative example

**Why:** the observation that led to it.

**Source:** `edits/my-first-jd/note.md` (bullet N — quoted evidence).
```

Use `P###` for content rules, `L###` for layout rules.

---

## Step 7 — Second cycle and onwards

From the second JD onwards, the skill reads your personal `preferences.md` first and applies your rules proactively. You should notice:

- Cycle 2: still 3–5 manual edits per draft; mostly new patterns
- Cycle 3–5: fewer edits, mostly extensions or caveats to existing rules
- Cycle 6+: the skill produces drafts very close to your voice; most edits are JD-specific tailoring

If your manual edit count isn't decreasing, the skill isn't reading `preferences.md` correctly — investigate before adding more rules.

---

## Codex-specific notes

The `.agents/skills/` tree mirrors `.claude/skills/` so that any runtime following the emerging `.agents/skills/<skill>/SKILL.md` convention can see the same skill.

Caveats to be aware of:

- **Auto-discovery may differ.** Claude Code uses the `description` field in SKILL.md frontmatter to decide when to activate a skill. Not every runtime does this yet. If your Codex setup doesn't auto-invoke the skill from a casual prompt, invoke it explicitly:
  > "Read `.agents/skills/drafting-resume-from-confirmed-assets/SKILL.md` and follow its rules to draft a resume for `jobs/my-first-jd.md`."
- **Progressive disclosure may be less strict.** SKILL.md names the reference files it expects the runtime to load lazily. Some runtimes read everything in the skill directory upfront — this still works, just uses more context tokens.
- **The `% src:` discipline is runtime-agnostic.** Whatever runtime you use, the drafts it produces should be validated with `make check`, which enforces the rules at the file level regardless of how the runtime was prompted.

If you find a Codex-specific issue, open an issue on the repo — the structural compatibility is deliberate but the runtime behaviour isn't all tested yet.

---

## Troubleshooting

- **`make check` fails with "Could not determine PDF page count"** — the latexmk log is in `build/latex/drafts/<slug>/<slug>.log`. Open it, scroll to the bottom, and check for compilation errors that prevented a clean PDF.
- **`FAIL: File 'fontaxes.sty' not found` or similar** — run `sudo tlmgr install fontaxes`. Repeat for each missing `.sty` the error names.
- **Skill generates an empty or generic draft** — `raw/` is underseeded. Fill more project notes, or check that the resume PDF is readable (`file raw/resumes/*.pdf` should report PDF).
- **Draft is over 1 page** — bullets are too long. Validator 7 will tell you explicitly. Compress until 10 bullets × ~22 words each fits.
- **`make approve` is refusing to overwrite** — that's the safety default. If you really want to re-approve the same slug: `FORCE=1 make approve JOB=<slug>`.
- **PDF preview not updating in VS Code** — LaTeX Workshop's default builder is `latexmk`. Make sure it's installed (`which latexmk`). Fully quit VS Code (Cmd+Q) and reopen after installing new LaTeX tooling so the extension picks up the updated PATH.

---

## Where to go next

- **`USAGE.md`** — the reference manual for day-to-day use (Makefile targets, cycle semantics, check validators, preference-model notes)
- **`PRIVACY.md`** — what to push to a public repo vs keep local; sanitisation checklist before `git push`
- **`preferences.md`** — your accumulated style rules; read and edit as it grows
- **`.claude/skills/drafting-resume-from-confirmed-assets/SKILL.md`** — the skill itself; worth reading once to understand the contract it follows
