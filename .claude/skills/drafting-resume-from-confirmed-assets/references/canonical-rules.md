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

### C001 — Strongest interview-defensible engineering verbs

**Why:** Recruiters scan for ownership scope in seconds. Weak verbs ("worked on") leak junior signal even when the underlying work is strong; over-aggressive verbs ("Built X" for review-only contributions) collapse under interview probing. The right verb is the strongest one the candidate can defend with concrete details.

**How to apply:** Three tiers, picked by the strongest defensible action — tier is decided by **scope**, not the verb itself, so some verbs appear in more than one tier:

- **Tier 1 — concrete delivery (use when the candidate materially built, shipped, or drove the work):**
  led / owned / built / shipped / delivered / designed / implemented / refactored / migrated / validated

- **Tier 2 — bounded participation in a larger team effort (upgrade weak raw phrasing to the most specific concrete action):**
  implemented / integrated / reviewed / debugged / tested / validated / contributed to

  Some verbs (`implemented`, `validated`) appear in both tiers — pick by scope:
  - **Tier 1 use:** the candidate drove the core component end-to-end (e.g., *"implemented the core training service"*, *"validated the migration end-to-end"*).
  - **Tier 2 use:** the candidate built a bounded sub-component within someone else's flow (e.g., *"implemented a parser"*, *"validated specific resource flows"*).

  When using `integrated`, name what was integrated and what changed because of it (e.g., *"integrated mTLS into the Rust client so local authenticated tests exercise the real handshake path"*). Otherwise `integrated X` reads as tier-3 disguised.

  `Contributed to` is a fallback, not a default — prefer the actual engineering action whenever possible.

- **Tier 3 — avoid (vague or junior-coded openers):**
  worked on / helped with / participated in / was responsible for / involved in / supported

**Aggressive framing rule:** A team project may say `Built X` if the candidate materially built X **and** can defend the relevant component, design tradeoffs, bugs, and implementation details in interview. Do not invent users, production status, ownership level, metrics, or outcomes. Use derived or approximate scope only when it can be traced to raw evidence, code structure, or repository history; when uncertain, prefer the conservative number and document the source on the `% src:` line.

**Anti-example:**
- ❌ "Worked on a Python RAG system" — tier 3, dilutes any actual contribution.
- ❌ "Built the entire LLaMA fine-tuning pipeline" when raw shows teammate ownership — invented scope.
- ✅ "Designed the RAG retrieval preprocessing layer for a fine-tuned BERT pipeline (UNSW × SEEK), addressing BERT's 512-token limit through cosine-similarity feature selection." — tier 1 verb tied to a defensible component.

### C002 — Layer decomposition for full-stack and multi-tier work

**Why:** Naming architectural layers explicitly signals system-level thinking and makes scope obvious at a glance. A flat tech tuple hides where the responsibility boundaries are.

**How to apply:** When describing multi-tier work, name the architectural layers (UI / API / business logic / data / infra / orchestration) instead of listing technologies as a flat list.
- ✅ **Prefer:** "Built features across a [front end], [REST API back end], and [persistence layer]…"
- ❌ **Avoid:** "Built a full-stack platform using [tech], [tech], and [tech]."

### C003 — Direct outcome / cause-effect wording

**Why:** Bullets should make the user-facing or system-level outcome legible without leaning on career-coach templates. Phrasings like *"enabling [stakeholder] to [verb]"* are widely flagged as resume-template clichés that read as generic and recruiter-coached. A direct cause-effect construction conveys the same content with stronger engineering voice.

**How to apply:** When describing outcomes, use direct cause-effect or *"so [stakeholder] [verb]"* wording, or restructure as a result clause attached to the action. Read "user" broadly: end-users, internal teams, downstream services, researchers, operators — whoever the system serves.

- ✅ **Prefer:** *"so researchers iterate against one reproducible Linux/Docker environment"*
- ✅ **Prefer:** *"cutting deploy time from N to M minutes"* / *"surfacing inference logs and loss curves for runtime monitoring"*
- ✅ **Prefer:** *"…built [thing], reducing [pain] for [user]"* — outcome attached as result clause.
- ❌ **Avoid:** *"enabling [stakeholder] to [verb]"* — career-coach template phrasing.
- ❌ **Avoid:** *"enabling reliable processing of [scope]"* — abstract, no user-visible effect.

**Anti-example:**
- ❌ *"Built a Flask backend, enabling researchers to access data."* — template phrasing, vague outcome.
- ✅ *"Built a Flask backend with MongoDB-tracked job state, so researchers can resume long-running pipelines after crashes."* — direct cause-effect, concrete user-visible benefit.

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

## Voice / tone / professionalism rules

### C014 — Default bullet shape: Action → Outcome → Mechanism

**Why:** The most widely cited resume-craft pattern (Google's XYZ formula — *"Accomplished X, as measured by Y, by doing Z"* — and the Pragmatic Engineer template) puts the **action and the outcome before the mechanism**. F-pattern eye-tracking studies show recruiters spend the most attention on the first words of each bullet, so leading with the verb and the change-it-caused captures more signal than tech-stack chains. This is a **default shape**, not a mandatory formula — strong bullets may compress one segment when an evidence axis is genuinely missing.

**How to apply:** Default shape per bullet:
1. **Action** — Tier-1 / Tier-2 verb (per C001) + the system or scope acted on.
2. **Outcome** — measurable change, business/system effect, or user-visible benefit (per C003).
3. **Mechanism** — the technique, technology, or design choice that produced the action/outcome.

When all three axes have evidence, prefer this order. When one axis is missing or weak, drop it rather than padding. Mechanism is the most droppable axis — surfacing the same tech in Skills or in another bullet often suffices.

- ✅ **Prefer:** *"Built a Flask + MongoDB backend (Action) cutting researcher onboarding from days to hours (Outcome) by exposing reproducible job/result tracking via REST (Mechanism)."*
- ✅ **Acceptable when no clear outcome metric exists:** *"Designed RAG retrieval preprocessing for a fine-tuned BERT pipeline, addressing BERT's 512-token limit through cosine-similarity feature selection."* (Action + Mechanism; outcome is implicit in the named constraint solved.)
- ❌ **Avoid:** *"Used Python, Flask, MongoDB, Docker, and Linux to build a backend system."* — flat tech tuple, no outcome, mechanism dominates.

### C015 — Tense conventions

**Why:** Industry convention is past tense for completed work and present tense for ongoing duties at the current role. Mixing tenses within a single bullet leaks amateur signal. Hiring-manager and resume-craft references (Resume Worded, Pragmatic Engineer) are consistent on this convention. **However, tense grouping is subordinate to JD-signal-first ordering** (per C009 / project-ordering rules) — the strongest, most JD-relevant bullet must lead each entry, even if that means a past-tense bullet appears before a present-tense one in the current role.

**How to apply:**
- Past tense for completed work, even at the current employer.
- Present tense only for genuinely ongoing duties at the current role (not "completed work I happen to still touch sometimes").
- Never mix tenses within a single bullet (no *"Built X and maintains Y"*).
- **Within a role, order bullets by JD signal and strength first.** Group same-tense bullets together only when doing so does not weaken the strongest-first ordering. If the strongest current-role bullet is completed work, lead with it.

**Anti-example:**
- ❌ *"Build and maintain Python/Flask APIs..."* mixed with *"Designed subprocess isolation..."* in the same bullet — tense mixing within a single bullet.
- ❌ Pushing the strongest *"Built X..."* bullet down to position 3 just to put a weaker *"Maintain Y..."* present-tense bullet at the top — tense ordering wrongly overriding JD-signal-first.
- ✅ *"Built subprocess isolation for long-running PyTorch jobs..."* (past, strongest, leads) followed by *"Maintain Python/Flask APIs serving researcher data workflows."* (present, ongoing, supporting).

### C016 — Implied first person, active voice only

**Why:** Resume default voice is **implied first person** — bullets start with a verb, never with "I". Passive constructions (*"was responsible for"*, *"tasked with"*, *"in charge of"*) read as junior or HR-coded regardless of underlying scope. Multiple hiring-manager sources (Stack Overflow blog by Gergely Orosz, Pragmatic Engineer, HN hiring-manager threads) flag these constructions as instant junior signal.

**How to apply:**
- Every bullet starts with a verb (Tier-1 or Tier-2 from C001).
- Never use first-person pronouns (*"I"*, *"my"*).
- Never use *"was responsible for"*, *"tasked with"*, *"in charge of"*, *"duties included"*.
- Active voice always; if a passive construction appears, restructure around the verb.

**Anti-example:**
- ❌ *"I built a Python pipeline that..."* — first person.
- ❌ *"Was responsible for designing the inference layer..."* — passive + tier-3 framing.
- ✅ *"Built a Python pipeline that..."* / *"Designed the inference layer that..."*

### C017 — Bullet length guidance

**Why:** Industry consensus across hiring-manager guides (Pragmatic Engineer, Stack Overflow blog, careerscribe's "12-word rule") is that resume bullets should be readable in a single eye-pass: long bullets push the result/outcome past the F-pattern scan and waste the highest-attention real estate. Excessively long bullets are also a tell that the candidate is trying to compress two workstreams into one (see C010).

**How to apply:**
- **Target 12–18 words** per bullet.
- **Above 25 words: rewrite or split.** If a bullet cannot be compressed below 25 without losing essential signal, split it into two coherent bullets (subject to the 1-page page-budget proxy).
- This rule is **drafting / self-check guidance**, not a `cycle.py check` hard validator. The single hard layout gate remains one-page PDF fit.

**Anti-example:**
- ❌ A 33-word bullet stitching action + 5 mechanism details + outcome + extra qualifier — reader misses the result; rewrite by dropping mechanism details to Skills or splitting into two bullets.
- ✅ A 14-word Action → Outcome → Mechanism bullet (per C014) that fits one rendered line.

### C018 — Specificity OR metric, never neither

**Why:** Hiring-manager guidance is consistent: **a fabricated metric is more damaging than no metric**, and concrete technical specificity (named subsystem, mechanism, constraint, scope) carries credibility on its own. The failure mode this rule prevents is a bullet that is **simultaneously vague and unquantified** — generic narrative that names neither a number nor a specific technical artifact. Such bullets read as filler and consume scarce bullet-budget without conveying engineering content.

**How to apply:** Every bullet must satisfy at least one of:
- **(a) Concrete number** — scale, latency, dataset size, team size, endpoints, throughput, error-rate delta, version, page count, coverage %, etc. The number must be defensible from raw evidence (`% src:`); approximate-but-defensible counts are allowed when their derivation can be explained (per C001 aggressive-framing rule).
- **(b) Concrete technical specificity** — named subsystem / module / mechanism / constraint that a reviewer can probe in an interview (e.g., *"p99 inference latency on FastAPI service behind nginx"*, *"BERT 512-token limit via cosine-similarity retrieval"*, *"subprocess isolation with CUDA-safe spawn"*, *"mTLS handshake with CA-pinned client certs"*).

Bullets satisfying neither (a) nor (b) — pure narrative such as *"Built backend services to support data workflows"* — must be reframed or dropped. Numbers and specificity together are strongest, but **specificity alone is acceptable** when the underlying evidence does not support a credible metric. **Do not invent metrics to satisfy this rule.**

**Anti-example:**
- ❌ *"Improved system reliability and supported the team's research goals."* — neither a number nor a named subsystem.
- ✅ *"Hardened reliability of the Stage1/Stage2 training service through subprocess isolation, streamed stdout/stderr, and stop/cleanup fallback."* — specificity present (named services, named mechanisms).
- ✅ *"Maintained Python/Flask APIs for a 6-person team across ~100 GB micro-CT datasets."* — number present (team size, dataset scale).

### C019 — Self-adjective ban

**Why:** Self-descriptive adjectives (*"passionate"*, *"self-motivated"*, *"results-driven"*, *"thrive in"*, *"hard-working"*, *"dedicated"*, *"detail-oriented"*, *"strong communication skills"*) are explicit hiring-manager red flags. They consume scarce bullet/summary budget without conveying engineering content; recruiters consistently dismiss any bullet containing them as marketing fluff. Resume voice is what the candidate **did**, not what they **are**.

**How to apply:**
- Never include self-descriptive adjectives in bullets, summary lines, or skills section.
- If raw evidence describes a personality trait, drop it during drafting.
- This rule applies binarily: any presence of these terms is a fail.

**Banned terms (non-exhaustive):** passionate / self-motivated / motivated / results-driven / thrive / hard-working / dedicated / detail-oriented / strong (skills / communicator / work ethic) / proactive / dynamic / innovative (when self-attributed) / team player / go-getter.

**Anti-example:**
- ❌ *"Passionate self-motivated developer with strong communication skills."*
- ✅ Drop entirely; replace with a concrete problem-and-action bullet.

### C020 — Domain-vocabulary credibility test

**Why:** Domain or platform vocabulary carries credibility only when grounded in a concrete subsystem, mechanism, and constraint. High-level architecture phrases used in the abstract — *"scalable distributed microservices"*, *"cloud-native architecture"*, *"production-grade ML platform"* — read as senior cosplay (LARPing) when no specific component or measurement backs them. Hiring-manager threads on HN and Pragmatic Engineer commentary call this out repeatedly: the difference between credible and LARP signal is **specificity**, not vocabulary level.

**How to apply:** When using domain or platform vocabulary (SRE, ML platform, distributed systems, security, networking), the bullet must name at least two of:
- **(a) System or subsystem** — *FastAPI service*, *Stage2 training pipeline*, *mTLS handshake layer*, *RAG retrieval preprocessing*.
- **(b) Mechanism** — *subprocess isolation with CUDA-safe spawn*, *cosine-similarity top-k retrieval*, *CA-pinned client cert validation*, *p99 tail-latency tracking*.
- **(c) Constraint or measurement** — *BERT's 512-token limit*, *~100 GB micro-CT dataset*, *3-second crash-recovery SLA*, *concurrent-write contention on MongoDB job table*.

If a sentence uses senior-level vocabulary but names none of (a)/(b)/(c), demote the vocabulary to plain language or drop the bullet.

**Anti-example:**
- ❌ *"Designed scalable distributed microservices with cloud-native architecture."* — zero specificity.
- ✅ *"Designed a Flask inference service running long-running PyTorch jobs under subprocess isolation, with checkpoint resume after stop/cleanup."* — names subsystem, mechanism, and the failure-mode constraint it addresses.

### C021 — Self-check: "What got better because the candidate did this?"

**Why:** Stack Overflow blog (Gergely Orosz) and Pragmatic Engineer both treat this as the single highest-leverage bullet test. A bullet that only describes activity (*"Built X"*, *"Worked on Y"*) without surfacing what changed reads as a task list rather than an engineering contribution. The test forces every bullet to declare a delta.

**How to apply:** For every bullet, run the silent test: *"What got better because the candidate did this?"* Acceptable answers include:
- A user / stakeholder gained a capability they previously lacked.
- A system became faster, more reliable, more reproducible, or cheaper.
- A team unblocked a workflow or reduced manual steps.
- A previously-broken or risky behavior was made safer or testable.
- A piece of work shipped, was deployed, or was adopted by real users.

If no answer fits, the bullet describes activity rather than change — reframe to surface the delta, attach a result clause (per C003 / C014), or drop the bullet.

**Anti-example:**
- ❌ *"Worked on the inference pipeline using Python and PyTorch."* — describes activity, not change.
- ✅ *"Hardened the inference pipeline with subprocess isolation and stop/cleanup fallback, so a stuck training job no longer freezes the desktop app."* — change is explicit.

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
