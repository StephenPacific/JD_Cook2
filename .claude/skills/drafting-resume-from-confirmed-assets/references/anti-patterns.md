# Anti-patterns

## 1. Keyword stuffing
JD says Kubernetes, no raw source supports it, bullet claims "deployed to K8s".
→ Omit. Add `% TODO: JD requires Kubernetes; no raw evidence` at top of draft.

## 2. Verb inflation
Raw says: "contributed to migration". Bullet says: "led migration".
→ Use "contributed to" or "supported migration of…"

## 3. Number borrowing
Previous approved resume had "reduced latency 40%". Current draft copies it
for a different role.
→ Only use numbers from raw evidence for THIS role. If none, omit.

## 4. Silent gap
JD requires "distributed systems". No raw source supports it. Draft just skips it.
→ Add TODO at top listing all uncovered JD requirements.

## 5. Section drift
Adding a Summary because the JD says "seeking leader with vision".
→ Schema forbids Summary. Express leadership in Experience bullets.

## 6. Student flavor
Bullet says "Received full marks for a course project using [framework] and [test tool]."
→ Omit the grade. Write the engineering work: state management, tested flows, CI, or validation covered.

## 7. Tool/product flavor
Bullet leads with a niche internal product category (e.g., "Built [personal-tool], a [narrow-use-case] for [niche-audience]").
→ Unless the JD's domain matches that audience, reframe as the transferable engineering system: evidence-grounded document pipeline, validation rules, structured extraction, traceability.

## 8. Bolded keyword chain
Bullet says "Built with `\textbf{A}, \textbf{B}, \textbf{C}, \textbf{D}, \textbf{E}, \textbf{F}, \textbf{G}`."
→ Pick the few technologies central to the claim and explain the problem/result instead of listing tools.

## 9. Workstream stitching
Bullet says "Contributed to [system A]; also debugged [unrelated bugs] in [system B]."
→ Choose the stronger JD-relevant workstream or split into two bullets. Do not hide two unrelated projects in one bullet.

## 10. Source stitching
Bullet cites both `raw/code/<project-A>.md` and `raw/code/<project-B>.md` to justify one compressed claim about two unrelated projects.
→ Default to one raw project source per bullet. Multiple `% src:` lines are only for the same workstream (e.g., a project note plus master CV for the same role), not for unrelated projects.
