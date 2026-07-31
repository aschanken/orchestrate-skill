# Teams reference — running an agent team under orchestrate

Read once, before the first teammate spawn of the session. Requires
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; if teams aren't available, fall
back to fan-out subagents and say so — never silently degrade the plan.

## When a team, when subagents

Teammates cost like full sessions (each has its own context window; token
spend scales linearly with headcount) and add coordination tax. A team must
be justified by INTERACTION value — teammates messaging, challenging, and
negotiating with each other. Otherwise fan-out subagents win.

Team-shaped work:
- **Competing-hypothesis debugging:** one teammate per theory, standing
  orders to actively refute the others' theories via direct messages, a
  shared findings doc as the convergence artifact. Kills anchoring —
  the surviving theory earned it.
- **Adversarial review panels:** distinct lenses (security / perf / tests /
  API surface) that debate overlapping findings instead of filing four
  disjoint reports the lead must reconcile.
- **Cross-layer features:** frontend, backend, and test owners who negotiate
  interface questions peer-to-peer instead of routing every mismatch through
  the lead. The lead pre-decides the contract; teammates negotiate within it.
- **Research with live challenge:** parallel investigators instructed to
  attack each other's conclusions before reporting.

Sequential work, same-file work, and result-only work are NOT team-shaped.

## Lead discipline

The lead is this session — the orchestrator. Non-negotiables:
- The lead NEVER claims implementation tasks. Its work while a team runs:
  task creation and sequencing, assignment, plan approvals, arbitration,
  steering messages, synthesis. If tempted to "just do" a task, that's
  orchestrator drift — dispatch or assign it.
- The lead stays responsive, not idle: teammate messages and idle
  notifications arrive automatically — no polling loops.
- Teammates cannot spawn teammates and in-process teammates cannot run
  background subagents — all fan-out is the lead's job. A teammate that
  needs a sweep reports back; the lead dispatches it.

## Spawning — the spawn prompt IS a brief

Teammates inherit no conversation history; they load project context
(CLAUDE.md, skills, MCP) plus exactly what the spawn prompt carries. So the
spawn prompt uses the full skeleton from `dispatch.md` — decisions, fix
points, scope fences, workflow rules, acceptance criteria, standing-orders
block — plus a team appendix:

```
## Team context
- Your name: <name>. Teammates: <name — role, name — role, ...>.
- Task list: claim only tasks assigned to you or unassigned tasks you're
  named eligible for; mark tasks completed ONLY with verification evidence
  in hand; if blocked, message the lead — never silently stall.
- Messaging: coordinate directly with <names> on <specific interfaces or
  disputes>; keep messages distilled (conclusions + file:line evidence,
  never raw dumps). Route decision forks to the lead.
- Comms: every message you send obeys the comms block in this prompt. Peer messages carry the same evidence and confidence marking as reports to the lead.
- File ownership: you own <paths>; <teammate> owns <paths>; do not cross.
```

Spawn mechanics:
- Name every teammate at spawn (stable names → addressable later).
- Pin each teammate's model by referencing a routing agent type from
  `routing.md` ("spawn a teammate using the `glm` agent type"). The
  definition's `model` is honored. Its `effort` is NOT — teammates follow
  the lead's effort — so `ds-pro` vs `ds-pro-max` thinking distinctions
  blur in teams; compensate in the spawn prompt or keep those routes for
  subagents.
- 3–5 teammates; 5–6 tasks per teammate. Three focused beat five scattered.
- Disjoint file ownership spelled out in EVERY spawn prompt, both ways.

Routing inside a team follows `routing.md` unchanged: `glm` implementers,
`kimi` for the vision/large-context seat, `ds-pro-max` backend engineers,
Anthropic tiers where judgment demands. A mixed-family panel is a feature
for review teams — uncorrelated blind spots argue better.

## Task list discipline

- Decompose to self-contained deliverables (a function, a test file, a
  review) with dependency edges — a task with unresolved dependencies can't
  be claimed, which is the team's execution-order guarantee. Wire the DAG
  deliberately.
- Completion bar: a task is marked completed only with its acceptance
  evidence; the lead spot-audits claims like any other done-claim
  (verification tiers from SKILL.md apply unchanged — teams don't lower
  the bar).
- Task status can lag (known limitation): a "stuck" task means check whether
  the work actually finished, then update status or nudge the teammate by
  name.

## Message discipline

Peer-to-peer messages obey the comms standard exactly as reports do. A
teammate's message to another teammate carries file:line evidence and a
CONFIRMED/UNCERTAIN/REFUTED marker, never a bare assertion. Task-list
`subject` fields are imperative and name their target (`Fix retry backoff in
src/net/client.py`, not `Fix the client bug`); task `description` fields state
acceptance criteria. Unmarked-confidence claims propagating between teammates
is the specific failure this prevents — a bare "this works" forwarded through
two hops becomes an uncheckable assertion by the third.

## Plan approval

Require plan approval for every implementation teammate ("require plan
approval before changes"); research/review teammates skip it. The lead
approves autonomously against pre-set criteria — put them in the spawn
prompt era decision, e.g.: plan must name files touched (inside ownership),
tests to be added, and the verification battery; reject plans that expand
scope or touch another teammate's files, with one-line feedback.

## Failure handling

- The subagent escalation ladder applies per-teammate: amend by direct
  message and let the same teammate retry (warm context is the point of
  teams); on repeat failure spawn a replacement on a higher tier or
  different family, reassign the task, shut the failed teammate down.
- A teammate that errors out notifies the lead; a teammate that goes quiet
  gets a direct status ping before any replacement decision.
- Shut down teammates by name once their task queue drains — idle teammates
  hold context you're not using. Cleanup is automatic at session end, but a
  drained teammate mid-session is a deliberate shutdown, not a leak.
- Teams don't survive `/resume`; after a resume, re-spawn from the task
  list rather than messaging ghosts.

## Team anti-patterns

- **Team-for-the-sake-of-it:** a team where fan-out subagents would do —
  paying interaction tax for work with no interaction value.
- **Shared-file roulette:** two teammates owning one file. Ownership is
  disjoint or the split is wrong.
- **Lead-as-implementer:** the drift is gradual; the checkpoint is claiming
  any task.
- **Unattended sprawl:** teams drift without steering — synthesize as
  findings land, redirect early, keep headcount at the minimum that argues.
- **Ghost messaging:** after resume or shutdown, messaging teammates that no
  longer exist instead of re-spawning.
