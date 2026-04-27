# Bullet Rules

## Shape
`<Action verb> <system/component> <engineering problem/constraint> <supported result/scope>, <how/tech>.`

Tools are supporting evidence, not the point of the bullet. Prefer bullets that explain why the technical work mattered. Use at most 1–3 core technologies when they clarify the claim.

## Length
- Target 10–18 words, hard cap 22
- One line per bullet

## Verbs
- Past tense except current role
- Forbidden: worked on, helped with, was responsible for, participated in
- Prefer: designed, shipped, reduced, migrated, built, owned

## Evidence-to-verb mapping (critical)

| Raw source says     | Bullet may say             | Bullet may NOT say        |
|---------------------|----------------------------|---------------------------|
| contributed to X    | contributed, helped ship   | built, owned, led         |
| built X             | built, shipped, implemented| designed, architected*    |
| used tech Y         | used, worked with          | expert in, specialized in |
| familiar with Z     | (omit from bullet)         | any active verb           |

*unless the raw source explicitly says "designed" or "architected"

## Numbers
- Only use metrics present in at least one raw file
- Keep original precision; do not round up
- Raw "~20%" → bullet "~20%", never "25%"

## Impact hierarchy
- Best: measured outcomes from raw evidence (latency, failure rate, users, datasets, recovery time, coverage, cost)
- Good: concrete supported scope (production-used, internal tool, research workflow, 100GB-scale data, long-running jobs)
- Acceptable: technical capability only, when no outcome evidence exists
- Avoid: unsupported impact words such as "improved", "scaled", "production", or "reliable" without raw support

## Engineering depth
When raw evidence supports it, prefer depth signals over tool inventory:
- reliability, health checks, logging, failure recovery
- API boundaries, data model, state management, integration points
- testing strategy, CI, validation, debugging path
- performance, deployment constraints, security/authentication, operational support

## Style guardrails
- **No student flavor:** avoid "full marks", grades, assignment/course framing, or "student project" as the selling point. If coursework is used, frame the technical system and validation.
- **No tool flavor:** avoid leading with a niche internal product category (e.g., a personal automation framed as the tool's user-facing purpose) unless the JD's domain matches. Use engineering framing instead: document pipeline, evidence validation, traceability, reproducibility, large-data handling.
- **No keyword stuffing:** avoid bullets whose main content is a list of bolded tools. Bold only the few technologies central to the problem/action/result.
- **No workstream/source stitching:** avoid semicolon bullets that combine unrelated projects (e.g. "built RAG pipeline; also fixed TLS bugs"). Default to one raw project source per bullet; use multiple `% src:` lines only when they support the same workstream.

## Mandatory source comment
Every resume bullet is followed by a LaTeX source comment on the next line:
`% src: <raw/path/to/file>[:<page|section>]`.
No exceptions. Unsourced bullets must be deleted. Prefer exactly one project source per bullet; do not use multiple source comments to glue unrelated projects into one bullet.
