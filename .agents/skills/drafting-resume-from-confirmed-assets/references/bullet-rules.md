# Bullet Rules

## Shape
**Default order: `<Action verb> <system/component> <outcome/change>, <mechanism/tech>.`** — see canonical rule **C014** (Action → Outcome → Mechanism).

This is a default order, not a mandatory formula. Compress one segment when an evidence axis is genuinely missing rather than padding. The Mechanism segment is the most droppable; the Action axis must always be present, and Outcome is preferred whenever raw evidence supports it.

Tools are supporting evidence, not the point of the bullet. Prefer bullets that explain why the technical work mattered. Use at most 1–3 core technologies when they clarify the claim.

## Length (guidance, not a validator gate)
- **Target 12–18 words per bullet.** Above 25 words: rewrite or split — see canonical rule **C017** (bullet length guidance).
- One line per bullet at the template's rendered font size.
- This length rule is **drafting / self-check guidance**, not a `make check` hard fail. The single hard validator gate remains the one-page PDF fit.

## Verbs and voice
- **See canonical rule C001 v2** (*Strongest interview-defensible engineering verbs*) for the three verb tiers and the aggressive-framing rule. Pick by scope, not by verb identity.
- **Tense:** see **C015** — past tense for completed work; present tense only for genuinely ongoing current-role duties; never mix tenses within a single bullet. **Order bullets by JD signal and strength first**; group same-tense bullets only when it does not weaken strongest-first ordering.
- **Voice:** see **C016** — verb-first, no first-person pronouns (`I`, `my`), no passive constructions (*"was responsible for"*, *"tasked with"*, *"in charge of"*, *"duties included"*).

## Evidence-to-verb mapping
The table below shows the **conservative** raw → bullet mapping. Per C001 v2 aggressive-framing rule, weaker raw phrasing may be upgraded to a stronger tier when the candidate materially built the work **and** can defend the relevant component, design tradeoffs, bugs, and implementation details in interview.

| Raw source says     | Conservative bullet may say   | Upgrade allowed only with C001 v2 defensibility |
|---------------------|--------------------------------|--------------------------------------------------|
| contributed to X    | contributed to / implemented   | built, designed (when materially built)          |
| built X             | built, shipped, implemented    | designed, architected (when the design is theirs)|
| used tech Y         | used, worked with              | (no upgrade — usage is usage)                    |
| familiar with Z     | (omit from bullet)             | (no upgrade)                                     |

## Specificity OR metric (C018)
Every bullet must satisfy at least one of:
- **(a) Concrete number** defensible from raw — team size, scale, dataset size, endpoints, latency, version, throughput, error-rate delta, coverage %, etc.
- **(b) Concrete technical specificity** — named subsystem, module, mechanism, or constraint a reviewer can probe in interview.

Bullets satisfying neither (a) nor (b) are pure narrative and must be reframed or dropped. **Do not invent metrics to satisfy this rule** — fabricated numbers are more damaging than no number, and specificity alone is acceptable when raw evidence does not support a credible metric.

## Numbers
- Only use metrics present in at least one raw file.
- Keep original precision; do not round up.
- Raw `~20%` → bullet `~20%`, never `25%`.
- Do not drop fuzzy `~` to create fake precision (per personal preference **P013**). If a fuzzy absolute metric weakens the bullet, reframe directionally instead — e.g., raw *"~59% to ~61%"* → *"lifted validation F1 by 2 points"* — when the delta is defensible.

## Domain-vocabulary guardrails (C020)
When using SRE / ML-platform / distributed-systems / security / networking vocabulary, the bullet must name at least two of:
- **(a) System or subsystem** — e.g., *FastAPI service*, *Stage2 training pipeline*, *mTLS handshake layer*.
- **(b) Mechanism** — e.g., *subprocess isolation with CUDA-safe spawn*, *cosine-similarity top-k retrieval*, *CA-pinned client cert validation*.
- **(c) Constraint or measurement** — e.g., *BERT's 512-token limit*, *~100 GB micro-CT dataset*, *3-second crash-recovery SLA*.

A sentence using senior-level vocabulary that names none of (a)/(b)/(c) reads as senior cosplay (LARPing); demote to plain language or drop the bullet.

## Impact hierarchy
- **Best:** measured outcomes from raw evidence (latency, failure rate, users, datasets, recovery time, coverage, cost).
- **Good:** concrete supported scope (production-used, internal tool, research workflow, 100 GB-scale data, long-running jobs).
- **Acceptable:** technical capability paired with a named subsystem / mechanism / constraint (still satisfies C018(b)) when no outcome evidence exists.
- **Avoid:** unsupported impact words such as *"improved"*, *"scaled"*, *"production"*, or *"reliable"* without raw support.

## Engineering depth
When raw evidence supports it, prefer depth signals over tool inventory:
- reliability, health checks, logging, failure recovery
- API boundaries, data model, state management, integration points
- testing strategy, CI, validation, debugging path
- performance, deployment constraints, security/authentication, operational support

## "What got better?" check (C021)
For every bullet, run the silent test: *"What got better because the candidate did this?"* If no answer fits — a capability gained, a system made faster / more reliable / more reproducible / cheaper, a workflow unblocked, a risky behavior made safer, a deployment shipped — reframe or drop. Activity-only bullets (*"Worked on X"*, *"Built Y to support the team"*) read as task lists, not engineering contributions.

## Style guardrails
- **No student flavor:** avoid *"full marks"*, grades, assignment/course framing, or *"student project"* as the selling point. If coursework is used, frame the technical system and validation.
- **No tool flavor:** avoid leading with a niche internal product category (e.g., a personal automation framed as the tool's user-facing purpose) unless the JD's domain matches. Use engineering framing instead: document pipeline, evidence validation, traceability, reproducibility, large-data handling.
- **No keyword stuffing:** avoid bullets whose main content is a list of bolded tools. Bold only the few technologies central to the problem/action/result.
- **No workstream/source stitching:** avoid semicolon bullets that combine unrelated projects (e.g., *"built RAG pipeline; also fixed TLS bugs"*). Default to one raw project source per bullet; use multiple `% src:` lines only when they support the same workstream.
- **No self-adjectives (C019):** never include *"passionate"*, *"self-motivated"*, *"results-driven"*, *"thrive"*, *"strong skills"*, *"hard-working"*, *"dedicated"*, *"detail-oriented"*, *"proactive"*, *"team player"*, etc.
- **No career-coach templates (C003 v2):** avoid *"enabling [stakeholder] to [verb]"*. Use direct cause-effect or *"so [stakeholder] [verb]"* wording instead.

## Mandatory source comment
Every resume bullet is followed by a LaTeX source comment on the next line:
`% src: <raw/path/to/file>[:<page|section>]`.
No exceptions. Unsourced bullets must be deleted. Prefer exactly one project source per bullet; do not use multiple source comments to glue unrelated projects into one bullet.
