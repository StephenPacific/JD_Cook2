# Content Strategy

Use this after reading the JD and raw evidence, before drafting bullets. The goal is not to add hype; it is to make engineering credibility visible without inventing facts.

## JD analysis

Extract a small requirement map before drafting:
- **Role family:** backend, full-stack, ML/AI, platform, networking, testing, research tooling, etc.
- **Must-have signals:** repeated or explicitly required technologies, responsibilities, domain constraints.
- **Nice-to-have signals:** preferred tools, domain familiarity, collaboration style.
- **Hidden priorities:** reliability, ownership, delivery speed, user workflows, operational support, testing, maintainability.
- **Seniority signal:** individual contributor execution, ownership, technical leadership, stakeholder communication.

## Evidence selection

Prioritize evidence in this order:
1. Recent work/research experience with real users, deployment, operational constraints, or measurable outcomes.
2. Strong projects that add distinct JD-relevant signal not already covered by Experience.
3. Coursework only when it demonstrates a specific technical capability the JD asks for.
4. Older or weaker evidence only when it fills a must-have gap.

Do not include a project just to name-drop a technology if it displaces stronger evidence. If the strongest JD fit is one work platform, make it the resume's main story.

## Framing guardrails

Avoid three resume flavors that weaken senior engineering credibility:

- **Student flavor:** avoid "full marks", grades, assignment/class framing, or "student project" language unless the JD explicitly values academic results. For coursework evidence, lead with technical complexity, state management, testing, CI, validation, or user flow.
- **Tool flavor:** do not lead with a niche internal product category (e.g., a personal tool framed by its end-user purpose) unless the JD's domain matches that purpose. Reframe as the transferable engineering system: evidence-grounded document processing, validation, traceability, reproducible generation, workflow automation.
- **Keyword flavor:** do not stack technologies as the main message. A bullet may name tools only after it explains the engineering problem, action, and supported result/scope.

## Bullet substance

Each bullet should answer "so what?" for a reviewer:
- What system/component did the candidate work on?
- What engineering problem, constraint, or failure mode did it address?
- What technical action was taken?
- What result, scale, validation, or supported scope followed?

Avoid bullets that are only tool lists:
- Weak: "Built a web app using React, Flask, MongoDB, Docker, and Linux."
- Stronger: "Containerized API, frontend, database, and processing services on a shared Linux workstation to support long-running data workflows."

Keep one bullet focused on one workstream and, by default, one raw project source. Do not merge unrelated projects with semicolons or "also" just to save space. If two workstreams are both relevant, rank them by JD signal and include the stronger one; split only when both are strong enough and the 10-bullet budget allows. Multiple `% src:` lines are acceptable only when they support the same workstream.

## Impact without overclaiming

Use measured impact only when raw evidence supports it. If no metric exists, use concrete supported scope:
- users or stakeholder group
- dataset or traffic scale
- deployment status
- workflow supported
- failure mode handled
- test coverage or validation performed
- operational checks, logs, or recovery path

Do not write "production", "reduced", "improved", "scaled", "reliable", or "owned" unless raw evidence supports the claim.

## Engineering depth signals

For stronger companies, prefer bullets that show judgement rather than tool familiarity:
- why a service was containerized
- how logs/health checks helped diagnose failures
- what API boundary or data model was designed
- what state-management or integration issue was handled
- what tests covered user-critical flows
- what validation proved the system worked

## Project framing

Coursework and early-stage personal tools should not be disguised as mature products. Frame them honestly:
- course project -> emphasize technical complexity, state, testing, CI, user flows
- internal automation/tool -> emphasize validation rules, traceability, failure cases, reproducibility
- deployed or user-facing project -> mention deployment/users only if raw evidence supports it

Never use grades or "full marks" as the reason a project matters. Hiring signal comes from engineering difficulty, validation, users, deployment, ownership, or measurable scope.

If a project has no real users, deployment, or measurable outcome, avoid product language. Make the engineering constraint clear instead.

## Section strategy

Allocate the 10-bullet budget around JD relevance:
- strongest current/recent Experience: usually 3-5 bullets
- supporting Experience: 1-3 bullets
- Projects: 0-3 entries only when each adds distinct signal
- Skills: keep aligned to JD and raw proficiency; avoid an unfocused tool inventory

Prefer one clear main story over many shallow signals.

## Final content review

Before writing the `.tex`, ask:
- Would a reviewer see evidence of impact, depth, and ownership?
- Does each bullet explain a problem or constraint, not just a task?
- Is every impact word supported by raw evidence?
- Are weaker course/personal projects taking space from stronger work evidence?
- Does the resume show a coherent fit for this JD rather than a generic list of tools?
- Did I remove student-flavored, tool-flavored, and keyword-heavy phrasing?
- Does each bullet describe one coherent project/workstream and source story rather than stitching together unrelated evidence?
