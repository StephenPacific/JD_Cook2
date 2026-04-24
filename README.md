# JDcook

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

Then generate learning materials for the memory loop:

```sh
make learn JOB=agentic-ai-engineer
```

`make approve` refuses to overwrite an existing `approved/<job>/` directory.
Use `FORCE=1` only for an intentional replacement.

`make learn` does not update `preferences.md` automatically. It creates a diff
and note template under `edits/<job>/` so preference promotion stays reviewed.
