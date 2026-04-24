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
    \resumeItem{\normalsize{bullet with \textbf{tech} names bolded.}}
    % src: raw/path
  \resumeItemListEnd
```

- Most recent role: up to 5 bullets
- Older roles: 2–3 bullets
- Each bullet: 10–22 words (see `bullet-rules.md`)

## Entry — PROJECTS

```latex
\resumeSingleSubheading
  {Project Name \href{\XxxURL}{\small [GitHub]}}{Start -- End}
  \resumeItemListStart
    \resumeItem{\normalsize{bullet with \textbf{tech}.}}
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

**Bold tech names inline:** every tech mention in a bullet wrapped in `\textbf{...}`.
- ✅ `using \textbf{Python}, \textbf{Flask}`
- ❌ `using Python, Flask`

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

## Length
- Default: 1 page
- If overflow, drop the least JD-relevant Projects first, then shorten older Experience entries to 1–2 bullets
- `preferences.md` may override
