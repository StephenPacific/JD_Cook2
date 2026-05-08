# Resume Schema (LaTeX — user's template)

**Ground truth template:** `references/latex-template.tex`. Preamble MUST be copied verbatim (document class, packages, custom commands, color definitions). You only compose the body.

## Output
- File: `drafts/<job-slug>.tex`
- Format: LaTeX matching the template above
- Compiled by user in VSCode with LaTeX Workshop extension

## Section order (strict)
1. Header: name in `\color{nameblue}\huge`, one contact line using `\textbar{}` separators
2. **EDUCATION** — most recent first
3. **EXPERIENCE** — reverse chronological, 3–5 entries
4. **PROJECTS** — 0–3 entries; drop if none strengthen fit beyond Experience
5. **TECHNICAL SKILLS** — last

## Forbidden sections
- Summary / Objective (user preference)
- References
- Hobbies
- Publications (unless JD is research-oriented)

## Section heading format
All sections: `\section{\color{nameblue}\Large SECTIONNAME}` (all caps)

## Entry — EDUCATION

```latex
\resumeSubheading
  {Institution}{Start -- End}
  {Degree and field}{City, Country}
% src: raw/path
```

## Entry — EXPERIENCE

```latex
\resumeSubheading
  {\large Role}{Start -- End (or Present)}
  {Company}{City, Country}
  \resumeItemListStart
    \resumeItem{\normalsize{bullet with restrained \textbf{tech} emphasis only when central.}}
    % src: raw/path
  \resumeItemListEnd
```

- Most recent role: up to 5 bullets
- Older roles: 2–3 bullets
- Each bullet: target 12–18 words (see `bullet-rules.md`); rewrite or split above 25. **Length is drafting guidance, not a hard validator gate** — the only hard validator gate is one-page PDF fit.

## Entry — PROJECTS

```latex
\resumeSingleSubheading
  {Project Name \href{\XxxURL}{\small [GitHub]}}{Start -- End}
  \resumeItemListStart
    \resumeItem{\normalsize{bullet with one or two central \textbf{tech} names if useful.}}
    % src: raw/path
  \resumeItemListEnd
```

Define `\newcommand{\XxxURL}{https://...}` at top of preamble.

## Entry — TECHNICAL SKILLS

```latex
\section{\color{nameblue} \Large TECHNICAL SKILLS}
 \begin{itemize}[leftmargin=0in, label={}]
    \small{\item{
     \textbf{\normalsize{Programming Languages: }}{\normalsize{list}} \\
      \vspace{4pt}
     \textbf{\normalsize{Technologies \& Tools: }}{\normalsize{list}} \\
    \vspace{4pt}
     }}
 \end{itemize}
% src: raw/path
```

Template default is 2 categories (Languages, Technologies & Tools). A 3rd category (e.g. `AI/ML`) is acceptable when the JD heavily weights that domain.

## LaTeX conventions (required)

**Restrained bold tech inline:** bold only 1–3 JD-critical technologies that are central to the bullet's claim. Do not bold every tool mention, and do not create long bolded tool chains.
- ✅ `orchestrated long-running jobs with \textbf{Python} subprocesses`
- ✅ `built a \textbf{PySide6} desktop workflow for large image datasets`
- ❌ `using \textbf{React}, \textbf{Flask}, \textbf{MongoDB}, \textbf{Docker}, \textbf{Linux}, and \textbf{Git}`

**Escaping in body text:**
| Char | Escaped |
|---|---|
| `%` | `\%` |
| `_` | `\_` |
| `&` | `\&` |
| `#` | `\#` |

**Date ranges:** `--` between start and end. Ongoing: `Present`.

**Src tracking:** `% src: raw/path[:section]` on the line immediately after each `\resumeItem{...}`. LaTeX comments (`%`), not HTML comments.

**TODO comments:** block of `% TODO: <requirement>` right after the custom-commands section of the preamble (before `\begin{document}`), to flag JD asks with no raw evidence.

**URLs:** define at top as `\newcommand{\XxxURL}{https://...}`, reference inside project titles via `\href{\XxxURL}{\small [GitHub]}`. Keep preamble's existing `\newcommand`s even if unused (harmless).

## Length / layout priority
- **Hard validator gate:** 1-page PDF fit (enforced by `make check`).
- **Per-bullet length:** target 12–18 words, rewrite/split above 25 — **drafting guidance only, not a `make check` failure.**
- If overflow, drop the least JD-relevant Projects first, then shorten older Experience entries to 1–2 bullets.
- `preferences.md` may override.
