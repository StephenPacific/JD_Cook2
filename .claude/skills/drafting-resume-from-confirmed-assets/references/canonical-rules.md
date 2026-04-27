# Canonical Rules

Universal resume-engineering principles that apply to **any user, any stack, any JD**.

These rules were extracted from real cycles but abstracted to remove user-specific stacks, projects, or career-stage assumptions. They are safe to ship in any open-source distribution of this skill.

**Each rule has:**
- **ID** — `C###` for canonical (universal). Personal carve-outs live in `preferences.md` with the original `P###` / `L###` IDs and reference back to the relevant canonical rule.
- **Why** — the principle behind the rule.
- **How to apply** — operational instruction.
- **Anti-example** — what to avoid (when illustrative).

Rules in this file are promoted from `preferences.md` only after passing the 4-criterion test:
1. Stack-agnostic (works regardless of tech stack)
2. Domain-agnostic (works regardless of industry)
3. Seniority-agnostic (works for grad / mid / senior)
4. Example-defrostable (rule survives without specific examples)

---

## Content rules

### C001 — Precise ownership verbs

**Why:** Precise verbs convey ownership scope unambiguously. Generic verbs invite follow-up questions about what the candidate actually did.

**How to apply:** Prefer ownership-precise verbs over generic ones.
- ✅ **Prefer:** built / shipped / refactored / architected / wrapped / migrated / reviewed / contributed
- ❌ **Avoid (alone):** integrated / designed / worked on / helped with / was responsible for
- Use generic verbs only when the underlying evidence does not support a more precise one.

### C002 — Layer decomposition for full-stack and multi-tier work

**Why:** Naming architectural layers explicitly signals system-level thinking and makes scope obvious at a glance. A flat tech tuple hides where the responsibility boundaries are.

**How to apply:** When describing multi-tier work, name the architectural layers (UI / API / business logic / data / infra / orchestration) instead of listing technologies as a flat list.
- ✅ **Prefer:** "Built features across a [front end], [REST API back end], and [persistence layer]…"
- ❌ **Avoid:** "Built a full-stack platform using [tech], [tech], and [tech]."

### C003 — User-facing outcome verbs

**Why:** User-facing verbs show product sense and make impact legible to non-technical readers. Abstract descriptions like "reliable processing" hide what the system actually does for the people using it.

**How to apply:** In architecture / platform bullets, include what users (or stakeholders) can *do* with the system, not only what was built. Read "user" broadly: end-users, internal teams, downstream services, researchers, operators — whoever the system serves.
- ✅ **Prefer:** "enabling [stakeholder] to [verb] [scope]"
- ❌ **Avoid:** "enabling reliable processing of [scope]"

### C004 — Separate internal audit LaTeX from public LaTeX

**Why:** TODOs, evidence-source notes, risk comments, and drafting metadata are useful for internal review but should never be shared as public LaTeX source. They expose gaps, uncertainty, or tailoring logic to anyone parsing the `.tex`.

**How to apply:** Keep `% TODO:`, `% src: …`, JD-gap notes, and any other audit comments in `drafts/<job>.tex` and the internal `approved/<job>/<job>.tex`. For shareable source, use a generated `<job>.public.tex` (auto-stripped of internal comments). PDF rendering hides comments; `.tex` parsing does not.

### C005 — Replace student-flavor language with engineering validation language

**Why:** Terms like *"full marks"*, *"auto-grader"*, *"course assignment"*, *"homework"* can make strong technical work read like a classroom exercise. Engineering language presents the same evidence as validation, robustness, and quality assurance.

**How to apply:** Prefer *"validated against tests covering…"*, *"tested under…"*, *"verified behavior under…"*, *"evaluated on…"* instead of grading-oriented language. Keep academic context (e.g., school name, industry-partner course code, named lab) only when it adds external credibility, not when it reads as a grade-driven claim.

### C006 — Exclude incomplete projects when interview risk exceeds resume signal

**Why:** A partially implemented project can invite probing questions about missing core logic. If the missing component is central to the domain, the project may hurt more than it helps.

**How to apply:** Before including a project, identify the core domain expectation. If that core feature is missing, choose one of:
1. **Omit** the project entirely.
2. **Describe only the completed subsystem** honestly.
3. **Prepare a strong interview explanation** before including.

Avoid phrases like *"in progress"*, *"next milestone"*, *"currently building"* unless the project is already valuable without the unfinished parts.

### C007 — Use metrics only when they strengthen the claim

**Why:** Metrics are valuable when they show scale, impact, quality, latency, reliability, accuracy, cost, or adoption. Weak or contextless metrics can make an achievement look smaller than it is.

**How to apply:** Keep strong metrics (clear baseline + meaningful magnitude). For weak, narrow, or hard-to-explain metrics, reframe the bullet around the engineering problem solved — reliability, robustness, scale, validation, maintainability. Avoid standalone small metrics unless the baseline and context make them meaningful in the target domain.

**Anti-example:** "Improved F1 by ~2 percentage points" in front of a non-ML reader without baseline context. Reframe as the engineering practice that achieved it (preprocessing, label remapping, class-weighted training).

### C008 — Prefer transferable system framing over narrow tool framing

**Why:** A project built from a personal or niche use case can still demonstrate general engineering value. Naming it too narrowly may make it look less relevant to the target role.

**How to apply:** When a project's original domain is not central to the JD, frame it by the transferable system problem — document processing, evidence extraction, data validation, workflow orchestration, reliability, traceability, large-data handling. Avoid overly narrow product labels (e.g., a personal automation tool framed as the tool's user-facing purpose) unless the JD's domain matches that purpose.

### C009 — Select evidence by JD signal, not by personal attachment

**Why:** Different roles reward different evidence. A strong full-stack project may be weaker than a systems / data project for a quant role, and vice versa. Forcing a favorite project into every resume dilutes JD fit.

**How to apply:** For each JD, rank evidence by:
1. Direct keyword match
2. Domain relevance
3. Technical depth
4. Interview defensibility

Re-rank for every cycle. Do not include a project just because it is recent, well-documented, or personally meaningful if a different project gives stronger JD signal.

### C010 — One bullet, one workstream/source

**Why:** Mixing two unrelated workstreams in one bullet (joined by "; also" or "; and") hides the engineering thesis. Each bullet should make one coherent claim a reviewer can probe and the candidate can defend.

**How to apply:** Default to one raw project source per bullet. Multiple `% src:` lines are allowed only when they support the same coherent workstream (e.g., a project note plus a master CV that both describe the same role). Never use multiple sources to stitch separate projects into one bullet.

**Enforced in code:** `cycle.py check` parses `% src:` blocks per bullet and fails if more than one distinct `raw/code/<file>.md` source is cited per bullet.

---

## Layout / structure rules

### C011 — Bold high-signal items, not just tool names

**Why:** Recruiters scan resumes in under 10 seconds. Bold should mark the highest-signal items the reader needs to notice — not every tool or library.

**How to apply:** Extend `\textbf{}` beyond tech names to cover the highest-signal token(s) in each bullet. Eligible categories include:
- Primary language or core algorithm
- Major system concept
- Measurable outcome
- Domain phrase the JD recruiter recognizes
- Named pipeline / system the candidate built

Avoid bolding entire sentences, generic English words, or every tool in a stack chain.

(Specific bold-density preferences — e.g., 1 vs 2 bolds per bullet — belong in `preferences.md` as personal carve-outs.)

### C012 — No keyword stuffing

**Why:** Long bolded tool chains create visual noise and weaken the main achievement. The reader should notice the engineering claim, not pattern-match every tech mention.

**How to apply:** Bold only the most JD-critical technologies in a bullet. Do not bold every tech mention. Avoid long chains like `\textbf{X}, \textbf{Y}, \textbf{Z}, \textbf{W}, \textbf{V}` (any chain longer than 3 bolded items in one bullet) unless each item is essential to the engineering claim and the bullet still explains a problem and result.

(Specific bold-budget thresholds belong in `preferences.md`.)

### C013 — Skills section is JD-filtered, not full inventory

**Why:** Long category labels and oversized skill inventories reduce scanability. Surplus items add noise without signal. Recruiters usually skim the first few items in each row.

**How to apply:** Order items in each skills row by JD relevance, not by personal familiarity or total inventory. Remove low-signal skills for the target role (e.g., front-end skills for a backend role; ML libraries for a non-ML role).

(Specific row-count limits and label-length preferences belong in `preferences.md`.)

---

## Notes for promotion

To promote a rule from `preferences.md` to this file:
1. Run the 4-criterion test (stack / domain / seniority / example-defrostable).
2. Verify the rule has been observed in ≥2 cycles or has a clear theoretical basis.
3. Abstract examples to remove user-specific names.
4. Move the abstracted version here with a `C###` ID.
5. In `preferences.md`, retain only the personal carve-out (if any) referencing back to `C###`.

To demote a rule from canonical:
1. Document the cycle/JD where it failed to apply.
2. Add a carve-out before considering removal.
3. If the carve-out is too broad, demote back to `preferences.md` (personal-only).
