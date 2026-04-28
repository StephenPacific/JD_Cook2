# JDcook

## Import a JD

The resume workflow reads `jobs/<job>.md`. You can still create that file by
hand, but the preferred path is to import the JD first.

If the JD is open in your browser, select the JD text, copy it, then run:

```sh
make import-job JOB=agentic-ai-engineer FROM=clipboard
```

For public pages, URL imports are available:

```sh
make import-job JOB=agentic-ai-engineer URL="https://..." MODE=http
make import-job JOB=agentic-ai-engineer URL="https://..." MODE=js
```

If `MODE` is omitted, the importer uses `auto`: try HTTP first, then JS if the
page looks too sparse. `MODE=js` is for JS-heavy pages and requires Playwright.
It does not log in, solve CAPTCHA, click Apply, or bypass access controls.
Imports write `jobs/<job>.md` and a private snapshot under
`jobs/_sources/<job>/`.

## Local PDF Preview

Use the local LaTeX toolchain for preview instead of copying `.tex` into Overleaf.

Compile a draft:

```sh
make draft JOB=ml-genai-engineer
```

Compile an approved resume:

```sh
make approved JOB=ml-genai-engineer
```

PDFs are written under `build/pdf/<scope>/<job>.pdf`.

This only compiles existing LaTeX files. It does not change the drafting workflow,
raw evidence, approved artifacts, or memory loop.

## Standard Cycle

After a skill-generated draft exists, start a cycle snapshot before manual edits:

```sh
make begin JOB=agentic-ai-engineer
```

Edit `drafts/<job>.tex` with local PDF preview, then run the approval checks:

```sh
make check JOB=agentic-ai-engineer
```

When the resume is ready to approve:

```sh
make approve JOB=agentic-ai-engineer
```

Approval stores two LaTeX versions:

- `approved/<job>/<job>.tex` — internal audit copy, keeps `% src:` / `% TODO:`
- `approved/<job>/<job>.public.tex` — share-safe source, strips `% src:` / `% TODO:`

Then generate learning materials for the memory loop:

```sh
make learn JOB=agentic-ai-engineer
```

`make approve` refuses to overwrite an existing `approved/<job>/` directory.
Use `FORCE=1` only for an intentional replacement.
If you later edit the internal approved `.tex`, regenerate the public source with
`FORCE=1 make export JOB=<job>`.

`make learn` does not update rule files automatically. It creates a diff and
three-tier `note.md` template under `edits/<job>/` so you can manually decide
whether an edit belongs in canonical rules, personal preferences, or should stay
JD-specific. It is meant for current `official` samples and refuses legacy,
validation, or archive samples unless you deliberately override with `FORCE=1`.

## Status and Corpus Checks

Check one job's lifecycle and approved-sample class:

```sh
make status JOB=agentic-ai-engineer
```

`status` reports whether the slug is imported, drafted, begun, approved, and
learned. `checked` is intentionally not stored; run `make check JOB=<job>` when
you want to validate the current draft.

Approved samples are classified as:

- `official` — current examples the skill may use for structure
- `legacy` — retained history, not a current example
- `validation-sample` — flow/regression test material
- `archive` — retired or parked material under `approved/_*/`

Validate every current official approved artifact:

```sh
make check-all
```

`check-all` compiles and checks approved resumes, not drafts. It skips `legacy`,
`validation-sample`, and `archive` samples.
