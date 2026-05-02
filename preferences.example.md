# User Preferences (Personal) - Example

This file is the structural spec for `preferences.md`. To start your own
preferences file:

```bash
cp preferences.example.md preferences.md
```

The real `preferences.md` is gitignored. Sections under "Personal-only
preferences" and "Personal carve-outs over canonical rules" are read by the
drafting skill as active rules. The "Structural Examples" section at the bottom
is inert and exists only to show the markdown shape that `make learn` reads and
writes.

Rule layers:

- `C###` canonical rules live in `references/canonical-rules.md` and should be
  universal across users.
- `P###` and `L###` personal rules live in `preferences.md` and describe this
  user's content and layout preferences.
- JD-specific choices stay in `edits/<slug>/note.md`; do not promote them into
  reusable rules.

---

## Personal-only preferences

_No personal preferences yet. `make learn` appends new `P###` / `L###` entries
here, just above the carve-outs marker._

---

## Personal carve-outs over canonical rules

_No personal carve-outs yet. Use this section for rules that override or
specialise an entry in `references/canonical-rules.md` (`C###`)._

---

## Structural Examples (not active rules)

> The examples below are illustrative only. Do not treat them as active
> preferences. The drafting skill should skip this section.

### P001 — Spell out abbreviations on first use

**Rule:** When an industry-specific abbreviation appears in a bullet, write the
full name on first use, then use the short form afterward.
- Prefer: "built a Continuous Integration (CI) pipeline that...", later
  "extended the CI workflow..."
- Avoid: "built a CI pipeline" with no expansion when the JD audience may not be
  technical.

**Why:** Recruiters from non-engineering backgrounds may screen the resume
before a technical reviewer sees it. Spelling out abbreviations on first use is
a small, low-cost readability gain.

**Source:** illustrative example only; not derived from a real cycle.

### L001 — Match dash style across date ranges

**Rule:** Use the LaTeX en-dash `--` consistently for all date ranges across
Education, Experience, and Projects sections.
- Prefer: `Sep 2023 -- Sep 2025`
- Avoid: mixing `Sep 2023 - Sep 2025` and `Sep 2023 -- Sep 2025` across entries.

**Why:** Mixed dash styles look like a copy-paste artifact and undermine the
otherwise polished typography of the LaTeX template.

**Source:** illustrative example only; not derived from a real cycle.

---

## Notes on this file

- Examples are illustrative. Keep, replace, or delete them as your real cycles
  produce real preferences.
- The structure (`### ID — Title`, `**Rule:**` / `**Why:**` / `**Source:**`) is
  what `make learn` reads and writes. Keep that shape so future edits remain
  machine-friendly.
- The example IDs `P001` / `L001` are placeholders. Real IDs are issued by
  `make learn` sequentially or chosen by you when hand-writing rules.
- Universal resume-engineering rules belong in `references/canonical-rules.md`
  (`C###`), not here.

