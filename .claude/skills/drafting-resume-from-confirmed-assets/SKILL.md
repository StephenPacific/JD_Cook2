---
name: drafting-resume-from-confirmed-assets
description: Use when drafting or revising a resume targeted at a specific
  job description, using raw source materials under raw/ as the evidence
  base. Outputs LaTeX matching the user's resume template
  (references/latex-template.tex). Do NOT use for initial raw-material
  collection, or for open-ended brainstorming about career direction.
---

# Drafting Resume (MVP 0 — reads raw/, outputs LaTeX)

## When to invoke
- User provides a JD (path under `jobs/` or pasted text)
- `raw/` contains at least one source (resume PDF, project note, etc.)
- User explicitly asks for a draft, first pass, or revision

## Required reading before drafting
1. **Always:** the LaTeX template — prefer `references/latex-template.local.tex` if it exists (has real name/phone/email/LinkedIn/GitHub URLs); otherwise fall back to `references/latex-template.tex` (placeholder version, safe for public repo). Copy preamble verbatim; use its custom commands and section order.
2. **Always:** `references/resume-schema.md` — section order, entry formats, LaTeX conventions (escaping, bold tech, src, TODO).
3. **Always:** `references/bullet-rules.md` — bullet shape, verbs, evidence-to-verb mapping.
4. **Always:** `preferences.md` at project root — accumulated user style rules.
5. **Always:** all files under `raw/` — evidence base. PDFs read via Read tool.
6. If any exist: up to 3 most recent files in `approved/` — structural examples only, NEVER fact sources.
7. If unsure: `references/anti-patterns.md`.

## Inputs
- JD: `jobs/<slug>.md` or inline text
- Evidence: all files under `raw/`
- Approved examples: up to 3 most recent under `approved/`
- Preferences: `preferences.md`
- Template: `references/latex-template.local.tex` if present, else `references/latex-template.tex`

## Rules (strict)
1. Every factual claim (metric, ownership, duration, tech, title, company) must be traceable to a specific location in `raw/`. Not in raw → not in draft.
2. Every bullet followed by `% src: <raw/path>[:section]` on the very next line. Unsourced bullets must be deleted.
3. JD requirement with no supporting evidence in `raw/` → `% TODO: no raw evidence supports <requirement>` at the top (after preamble, before `\begin{document}` body). Do NOT invent.
4. `approved/` examples inform tone/structure only. Never copy numbers, company names, or specifics from them.
5. Do not upgrade evidence: raw "contributed to X" → bullet cannot say "built X" or "owned X". See `bullet-rules.md` evidence-to-verb mapping.
6. Output exactly one file: `drafts/<job-slug>.tex`. Overwrite if exists.
7. Preamble and custom commands from `latex-template.tex` copied verbatim. Only the body (Header + 4 sections) is composed by you.
8. **About template body:** the body inside `references/latex-template.tex` is a structural example (equivalent to `approved/` entries). Use it for ordering, tone, phrasing. **Never source facts to it.** If a bullet appears in both template body and `raw/`, source to `raw/`. Dates, numbers, and scope claims in the template body may be stale — always defer to `raw/`.
9. **Page budget (hard):** Output MUST fit on **1 compiled page**. To preserve this, total `\resumeItem` count across all sections ≤ **10**. If projected to overflow: (a) drop the least-JD-relevant PROJECTS entry first, (b) if still overflowing, shorten older Experience roles to 1–2 bullets, (c) if still overflowing, drop PROJECTS entirely. **Never** shrink font, margins, or spacing to "cheat" the page — template sizing is calibrated.
10. **Projects ordering by JD relevance:** The section order (Header → EDUCATION → EXPERIENCE → PROJECTS → TECHNICAL SKILLS) is fixed. But **within PROJECTS**, order entries by **JD relevance** (most relevant first), not by chronology or alphabet. Include as many PROJECTS entries as fit the bullet budget — 0 is fine if Experience already covers the JD; 2–3 is fine when each adds distinct JD-relevant signal. Each project entry: ≤ 3 bullets.

## Self-check before returning
- [ ] Every `\resumeItem{...}` has a `% src: ...` on the immediately following line
- [ ] No `% src:` points to `latex-template.tex`. All facts sourced to `raw/`.
- [ ] Total `\resumeItem` count ≤ 10 (page-budget proxy)
- [ ] PROJECTS entries ordered by JD relevance (most relevant first), not chronology
- [ ] Section order: Header → EDUCATION → EXPERIENCE → PROJECTS → TECHNICAL SKILLS
- [ ] Every tech mention inside bullets wrapped in `\textbf{...}`
- [ ] `%`, `_`, `&`, `#` properly escaped in body text
- [ ] Date ranges use `--`; ongoing uses `Present`
- [ ] Every `\newcommand{\XxxURL}` referenced in body is defined in preamble
- [ ] No metric appears that is not in `raw/`
- [ ] No tech claimed as proficiency that `raw/` only shows as "used"
- [ ] TODO block at top for any uncovered JD requirement
- [ ] File ends with `\end{document}`

## Anti-patterns
See `references/anti-patterns.md`. LaTeX-specific additions:
- Never leave `\textbf{...}` or `\resumeItem{...}` with unclosed braces.
- Do not duplicate the preamble or `\begin{document}`.
- Do not wrap tech names in `\textbf{}` outside bullets (Skills section uses plain lists).

## Output
- File: `drafts/<job-slug>.tex`
- Print one-line summary: (a) bullet count, (b) TODO count, (c) uncovered JD requirements, (d) reminder to compile in VSCode with LaTeX Workshop to preview PDF.
