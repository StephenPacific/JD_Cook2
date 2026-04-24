# Bullet Rules

## Shape
`<Action verb> <what> <scope/quantity> <outcome>, <how/tech>.`

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

## Mandatory source comment
Every resume bullet is followed by a LaTeX source comment on the next line:
`% src: <raw/path/to/file>[:<page|section>]`.
No exceptions. Unsourced bullets must be deleted.
