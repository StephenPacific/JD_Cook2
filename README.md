# JDcook

## Import a JD

The resume workflow reads `jobs/<job>.md`. You can still create that file by
hand, but the preferred path is to import the JD first.

If the JD is open in your browser, select the JD text, copy it, then run:

```sh
make import-job JOB=my-first-jd FROM=clipboard
```

For public pages, URL imports are available:

```sh
make import-job JOB=my-first-jd URL="https://..." MODE=http
make import-job JOB=my-first-jd URL="https://..." MODE=js
```

If `MODE` is omitted, the importer uses `auto`: try HTTP first, then JS if the
page looks too sparse. `MODE=js` is for JS-heavy pages and requires Playwright.
It does not log in, solve CAPTCHA, click Apply, or bypass access controls.
Imports write `jobs/<job>.md` and a private snapshot under
`jobs/_sources/<job>/`.

## Local PDF Preview

Use the local LaTeX toolchain for preview instead of copying `.tex` into Overleaf.

Preview a draft PDF:

```sh
make preview JOB=my-first-jd
```

`make draft-pdf JOB=<job>` is the same compile-only operation. `make draft`
is reserved for AI draft generation.

Compile an approved resume:

```sh
make approved JOB=my-first-jd
```

PDFs are written under `build/pdf/<scope>/<job>.pdf`.

Preview commands only compile existing LaTeX files. They do not change raw
evidence, approved artifacts, or the memory loop.

## Standard Cycle

After importing a JD, generate the initial AI draft:

```sh
make draft JOB=my-first-jd
```

`make draft` invokes a local agent (`codex` first, then `claude`) with the
`drafting-resume-from-confirmed-assets` skill. Before the agent runs, the
harness writes `edits/<job>/context.md`, selecting only the most similar
official approved examples for structure. The default limit is 2 selected
examples (`CONTEXT_LIMIT=3` if you intentionally want more). The agent may read
only those selected examples, never all of `approved/`, and never
`edits/*/note.md` during drafting. It then writes `drafts/<job>.tex` and
automatically snapshots the untouched AI version to `edits/<job>/ai-draft.tex`.

Edit `drafts/<job>.tex` in VS Code, Overleaf, or any LaTeX editor, then run the
approval checks:

```sh
make check JOB=my-first-jd
```

When the resume is ready to approve:

```sh
make approve JOB=my-first-jd
```

Approval stores two LaTeX versions:

- `approved/<job>/<job>.tex` — internal audit copy, keeps `% src:` / `% TODO:`
- `approved/<job>/<job>.public.tex` — share-safe source, strips `% src:` / `% TODO:`

Then generate learning materials for the memory loop:

```sh
make learn JOB=my-first-jd
```

`make approve` refuses to overwrite an existing `approved/<job>/` directory.
Use `FORCE=1` only for an intentional replacement.
If you later edit the internal approved `.tex`, regenerate the public source with
`FORCE=1 make export JOB=<job>`.

`make learn` does not promote rules without your approval. It creates a diff and
a prefilled `note.md` under `edits/<job>/`, then prints the note so you can
review the suggested triage immediately. In an interactive terminal, it then
asks whether to pass, append a personal `P###` / `L###` rule to `preferences.md`,
or leave a canonical candidate for manual review. The prefill is deterministic:
it summarizes bullet changes, gap-comment changes, and candidate rule signals.
It is meant for current `official` samples and refuses legacy, validation, or
archive samples unless you deliberately override with `FORCE=1`. After the
learning artifacts are safely written, it removes the active `drafts/<job>.tex`
workspace copy because `approved/` and `edits/` now hold the archive records.

For older completed cycles, you can clean the active draft workspace copy with:

```sh
make clean-draft JOB=my-first-jd
```

If a JD is a poor fit before approval, abort the unsubmitted cycle:

```sh
make abort JOB=my-first-jd
```

`abort` removes imported JD, draft, AI snapshot, and draft build artifacts, but
refuses once an `approved/<job>/` record exists.

## Status and Corpus Checks

Check one job's lifecycle and approved-sample class:

```sh
make status JOB=my-first-jd
```

`status` reports whether the slug is imported, has an active draft, has an AI
draft snapshot, is approved, and is learned. `checked` is intentionally not stored;
run `make check JOB=<job>` when you want to validate an active draft. Completed
cycles may show `drafted: no` after `make learn` cleans the workspace copy.

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
