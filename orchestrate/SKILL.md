---
name: orchestrate
description: Run this session in "brains of the operation" mode — the main agent analyzes each task, architects a dispatch strategy (linear, fan-out, delegated campaign, team, workflow, or hybrid — never a fixed reflex), then routes and verifies while model-routed subagents do all implementation lifting. Invoke with a task (/orchestrate fix issues 22 and 24) or bare to arm the mode for the whole session.
---

# Orchestrate — the main agent steers, subagents build

When this skill is invoked, apply it to the given task (if arguments were
passed) and to ALL subsequent substantive work in this session. Armed bare:
acknowledge the mode in one line and proceed. Trivial Q&A stays direct —
never add dispatch ceremony to a question.

This skill is model-agnostic: "the main agent" is whatever model is running
this session (Fable, Opus, anything else). Tiers below are ROLES relative to
the session, not fixed names.

## The economy

Two scarce resources, guarded separately:

1. **The main agent's context** — drains from BOTH sides: output tokens
   (writing code) and input tokens (reading files, raw diffs, verbose
   reports). The main agent spends tokens on exactly one thing — judgment:
   decomposition, decisions, briefs, arbitration. Everything mechanical
   (searching, reading at length, writing code, running batteries) happens in
   disposable subagent contexts.
2. **A budget hierarchy, not one pool.** (a) The Fable weekly allowance is
   the premium resource — conserved for the lead/judgment seat, never spent
   on execution. (b) The pennies pool — `ds-flash` and `ds-flash-lite`
   (DeepSeek V4 Flash 0731, Sonnet-class on benchmarks at 1/35th the
   price) — is the volume default: it absorbs ALL checkable work,
   specified execution and judgment-adjacent duty alike, so the
   subscription survives the week. (c) Anthropic subscription capacity
   (Opus, Sonnet, Haiku) is finite weekly headroom, the conserved
   resource: reserved for taste, creativity, vision, safety-adjacent
   correctness, and arbitration — what the pennies pool structurally
   cannot hold. (d) GLM, Kimi K3, `ds-pro`, and `ds-pro-max` bill real
   money at real rates: deliberate occasional spends, never defaults.
   **If its output is checkable, send it to flash; if it needs taste,
   vision, or safety judgment, spend headroom on Anthropic; pay the others
   only when they are genuinely the point.** See the spend doctrine in
   `references/routing.md`.

The product of the main agent's spending is **leverage**: a brief good enough
that a cheaper model executes at near-top-tier quality. Routing is not fixed
by the task — it is fixed by the brief. A better brief moves the same task
DOWN a tier. Quality is held by the discipline — decisions pre-made,
acceptance criteria runnable, done-claims refuted by independent verifiers —
not by paying for an expensive first pass. Cheap-and-verified beats
expensive-and-trusted.

## Division of labor

**The main agent does directly (the exceptions):**
- Classification, planning, and writing the briefs subagents execute —
  including the "hard 10%" (see Distillation).
- Reading verdicts and evidence; arbitrating disagreements; cross-PR conflict
  checks; merge/cleanup mechanics.
- Team-lead duty when a team is up: task creation, assignment, plan
  approvals, steering — never claiming implementation tasks itself.
- Trivial one-liners where dispatch overhead exceeds the work (a brittle test
  string, a stale comment) — fix, note it, move on.
- Knowledge-distillation writing (CLAUDE.md, design rulings, memory) where the
  main context IS the source material a subagent doesn't have.

**Everything else is dispatched.** The main agent is never
implementer-of-record for feature work.

## Routing

Governing principle: route by how expensive a mistake is to **detect**, not
just to make. If tests and linters catch errors mechanically, a fully
specified brief on `ds-flash` costs pennies, and its retries cost pennies
again. If errors only surface under judgment (subtle UI fidelity,
concurrency, security, API design taste), keep the work on Anthropic
subscription capacity, or split it so the judgment stays in the brief and
only the mechanical remainder goes to flash.

Read `references/routing.md` at the first dispatch of the session — it holds
the full model dossiers, the spend doctrine, and the mechanics (gateway
agent types, thinking control via `effort`). Quick table:

| Route | Use for |
|---|---|
| session model (Fable) | judgment only: plans, briefs, arbitration — the premium seat, never bulk work |
| `ds-flash` — DeepSeek V4 Flash 0731, max thinking | DEFAULT for checkable work of BOTH kinds: fully-specified execution (mechanical edits, file surgery from a fix-point map, glue code, scaffolding, churn) AND judgment-adjacent duty whose output the lead or a battery can check (recon, distillation shield, refute-verification, first drafts, campaign mid-orchestration). Sonnet-class benchmarks at pennies; text-only, verbose — cap its reports. Taste, creativity, and safety judgment stay off it |
| `ds-flash-lite` — same model, thinking off | grunt tier: template edits with a worked example, format conversions, fixtures, report collection, high-volume sweeps — no deliberation latency |
| `sonnet` | taste-bearing judgment: ambiguity resolution, UX/API-surface taste, creative and user-facing writing, vision-in-the-loop checks, arbitration support; first escalation when flash fails. Finite weekly headroom — do not burn it on work flash does identically |
| `opus` | correctness-critical or safety-adjacent implementation; subtle multi-file judgment; arbitration-grade second opinions |
| `haiku` | speed-critical mechanical sweeps (fast where flash is slow); grunt duty that conserves cash instead of headroom |
| `glm` — GLM 5.2 | DELIBERATE SPEND: frontend/UI ceiling, repo-scale refactors, long agentic runs |
| `kimi` — Kimi K3 | DELIBERATE SPEND: reads exceeding the session's own context; vision + synthesis verdicts; cross-family panel seats |
| `ds-pro-max` — DeepSeek V4 Pro, max thinking | DELIBERATE SPEND: knowledge-heavy technical work where parameter depth beats Flash's benchmarks; intra-family second opinions |
| `ds-pro` — DeepSeek V4 Pro, thinking off | DELIBERATE SPEND: legacy instruct fallback when `ds-flash-lite` disappoints on a task class |

Claude tiers dispatch as `model:` on a generic agent type (e.g.
`general-purpose`); gateway models dispatch as `subagent_type:` directly.

Effort routing too, where supported: low effort for mechanical stages, high
tiers only for the hardest verify/judge work.

**Escalation ladder (on subagent failure):**
1. Amend the brief naming exactly what went wrong; retry the SAME tier —
   prefer continuing the same agent where the harness supports it (warm
   context, no re-brief cost). A `ds-flash` failure almost always means the
   brief left something unspecified: fix the brief, not the routing. One
   in-pool exception: a `ds-flash-lite` failure that looks like missing
   reasoning (not missing specification) goes straight up to `ds-flash` —
   same pennies, thinking on.
2. Second failure: move UP a tier, or into a different model family —
   Sonnet, then Opus, or a cash-billed gateway model. A different-family
   move on repeat failure is legitimate, not a face-saving spend.
3. Top tier fails too: the brief is wrong, not the model. Re-recon,
   rediagnose. The main agent implementing directly is the LAST rung, never a
   shortcut, and gets flagged in the report when it happens.

## The strategy gate — analyze first, then architect

Every substantive task — the `/orchestrate <task>` arguments, and each new
task while the mode is armed — passes through an explicit strategy step
BEFORE any dispatch. No vehicle is a reflex: not teams, not fan-out, not
solo handling. The gate has two moves:

1. **Analyze the prompt.** What is the deliverable? How decomposable is
   the work, and are the parts independent or coupled? Are errors
   mechanically checkable or judgment-surfaced? Does any part need taste,
   vision, or safety judgment? What volume of reading/writing is involved,
   and how much of it must never touch the main context? Would workers
   gain from talking to each other, or only report results?
2. **Write the dispatch strategy** — a short block, posted before acting,
   naming: the chosen architecture (from the menu below, or a hybrid),
   the route per seat, the verification plan, and what stays with the
   lead. One paragraph or a small table; ceremony is a failure mode, so a
   trivial task gets one line ("direct — dispatch overhead exceeds the
   work").

Architecture menu — pick by the analysis, combine freely:

| Architecture | Choose when |
|---|---|
| Direct handling | trivial Q&A or a fix smaller than the brief it would need |
| Single routed subagent | one self-contained deliverable, one seat |
| Linear pipeline | stages feed each other (recon → implement → verify); parallelism would be theater |
| Parallel fan-out | independent result-only units — disjoint files, separate concerns |
| Delegated campaign | high-volume boundable program: a `ds-flash` mid-orchestrator drives grunt agents, returns one distilled deliverable (see Delegated campaigns) |
| Workflow script | the loop/fan-out structure is fully known upfront — deterministic orchestration beats a model doing it |
| Agent team | interaction IS the value: competing hypotheses, debating review panels, peer-negotiated interfaces (see Agent teams) |
| Hybrid | most real campaigns: e.g. fan-out recon → team for the contested design → campaign for the sweep → flash refuters |

The strategy is revisable — a surprise mid-execution (scope growth, failed
route, contradicted premise) reopens the gate, and the revision is stated,
not silent.

## The standard flow

1. **Recon** (parallel, routed): map the relevant code, return a distilled
   brief — findings, exact file:line evidence, open questions. Recon routes
   to `ds-flash` by default since 0731 — mechanical recon (file maps,
   symbol traces, log digests) and checkable judgment recon alike; Sonnet
   when the recon question is itself a taste call ("is this design sound"),
   `kimi` (deliberate spend) when the read exceeds flash-practical bulk.
   Use Explore agents for broad searches. Never let an implementer explore
   from scratch what a recon pass can map first.
2. **Plan** (main agent): turn briefs into a plan — every decision made
   ("implement exactly this, don't relitigate"), verified fix-point tables,
   acceptance criteria as runnable commands, scope fences. Read
   `references/dispatch.md` at first dispatch for the brief skeleton and the
   standing-orders block to paste.
3. **Dispatch** — pick the vehicle, then the models:
   - **Subagents** (Agent tool; `isolation: worktree` for anything that
     commits): the default — result-only work where agents don't need to
     talk. One branch/PR per concern. Parallel agents get **disjoint file
     ownership** spelled out both ways; dry-run `git merge-tree` between
     sibling branches before reporting them compatible.
   - **Delegated campaign**: high-volume boundable programs — a `ds-flash`
     mid-orchestrator drives grunts and returns one distilled deliverable.
     See Delegated campaigns below.
   - **Agent team**: when the value comes from interaction between workers —
     see Agent teams below. Read `references/teams.md` before first spawn.
   - **Workflow tool** where available, for N-item sweeps or verify panels
     (pipeline + schema outputs) — invoking this skill is the standing
     opt-in, within session size guidance. Prefer it over a campaign when
     the loop structure needs no adaptation between rounds.
4. **Verify** (routed, then arbitrated — see Verification).

## Agent teams — route the collaboration pattern too

Subagents report back and never talk to each other; teammates share a task
list, message each other directly, and challenge each other's findings. Both
are dispatch vehicles — choose by whether interaction adds value:

- **Fan-out subagents (default):** result-only work — recon, implementation
  against a fixed brief, verification. Cheaper, simpler, no coordination tax.
- **Agent team:** competing-hypothesis debugging (teammates actively refute
  each other's theories), multi-lens review panels that debate findings,
  cross-layer features where interface owners negotiate directly instead of
  routing every question through the lead, research that benefits from live
  challenge.

Non-negotiables when a team is up (full doctrine in `references/teams.md`):
the lead is this session and NEVER claims implementation tasks; spawn
prompts are full briefs — teammates inherit no conversation history;
teammate models are pinned via the routing agent types (a definition's
`model` is honored; its `effort` is not — teammates follow the lead's
effort); disjoint file ownership per teammate; plan approval required for
implementation teammates.

## Delegated campaigns — a mid-orchestrator on the pennies pool

Confirmed harness fact (probed 2026-08-01): gateway subagents hold the
Agent tool — a dispatched `ds-flash` agent can itself dispatch grunt
subagents and relay their results. That enables a third dispatch shape
between fan-out and teams:

- **When:** high-volume, boundable work-programs whose per-item work is
  grunt-shaped and whose loop needs SOME adaptation between rounds —
  research sweeps over many sources, N-file audits, corpus collection,
  iterate-until-battery-green churn. Two disqualifiers: a loop whose
  structure is fully known upfront belongs to a Workflow script
  (deterministic beats model-managed), and items needing taste belong on
  Anthropic tiers, not in a campaign at all.
- **Shape:** the lead writes ONE campaign brief; a `ds-flash`
  mid-orchestrator runs the dispatch loop — grunts on `ds-flash-lite`
  (conserves headroom) or `haiku` (conserves cash, faster wall-clock) —
  iterates against the acceptance criteria, and returns ONE distilled
  deliverable. The main context receives a single report instead of N;
  the subscription receives almost nothing; flash's near-free cache reads
  make the manager's long loop cost cents.
- **The campaign brief** carries everything a normal brief does PLUS the
  delegation protocol from `references/dispatch.md` (campaign appendix):
  the grunt-brief template with the standing-orders and comms blocks to
  paste into every grunt, grunt routing per item class, per-grunt report
  shape with a hard cap, batch size, an iteration ceiling, and the
  escalation rule (stop-and-report, never re-scope).
- **Limits:** the mid-orchestrator makes no taste decisions — an
  unresolved Decision Request stops the campaign and is forwarded
  unchanged; delegation depth is ONE (grunts do
  not spawn agents); and the campaign's deliverable is a judgment claim —
  verify it like one (Tier 1: independent refuter on the result, spot-check
  one grunt's raw output against what the manager reported about it).

## Distillation — what makes a brief carry top-tier quality

Subagents start cold; the brief is the transfer medium. The levers, in order
of power:

1. **Decisions, not questions.** Resolve every fork before dispatch. The
   standing order for forks discovered mid-work is a Decision Request —
   never choosing.
2. **Write the hard 10% yourself.** Signatures, invariants, the edge-case
   table, pseudocode for the one tricky algorithm — inline in the brief.
   Main-agent output spent here is the cheapest quality lever there is; it is
   what converts an Opus task into a `ds-flash` task.
3. **One worked example beats ten rules** for repetitive work — the highest
   return sentence in any brief, because it is what makes `ds-flash` safe on
   work that would otherwise need Sonnet.
4. **Pre-mortem the brief:** name the 2–3 most likely wrong turns for THIS
   task ("you will be tempted to X — don't, because Y").
5. **Pointers, not content.** The subagent reads files itself for cheap —
   give paths and fix-points, not pasted file bodies. Inline ONLY what the
   agent cannot derive: decisions, invariants, the hard 10%.
6. **Acceptance criteria as commands** the agent runs and pastes verbatim,
   with baseline numbers to compare against (test counts, lint state).
7. **Write to the comms standard.** A brief that names every referent exactly
   and marks its own confidence is the difference between a cheap model
   executing correctly and executing something adjacent.

The levers compound toward one target: **the more completely a brief
specifies the work, the further down the cost ladder it lands, and the bottom
rung is `ds-flash` at pennies.** Main-agent effort spent making a brief exact
is the highest-return spend in the session, because it converts expensive
execution into cheap execution without touching quality. The limit is fixed:
flash supplies no creativity and no taste. Where the work genuinely needs
either, specifying harder is the wrong move — route it to an Anthropic tier
and keep the output.

Every brief also restates the repo's workflow rules (branch naming, commit/PR
conventions, TDD, verification battery) and ends with the standing-orders +
report-shape block from `references/dispatch.md` — pasted, not paraphrased.

## Comms — how agents talk to each other

Every agent-to-agent message obeys the comms standard. The standard adapts
ASD-STE100 Simplified Technical English for machine readers and adds what STE
lacks: evidence attribution, confidence marking, and referent precision. It
binds briefs, reports, spawn prompts, teammate messages, workflow prompts,
and task-list entries. The comms block is baked into the gateway agent
definitions so routed agents comply by default, and pasted into briefs as
reinforcement — a deliberate two-layer design. Read
`references/comms.md` for the standard and its pasteable block;
`tools/comms-lint.py` scores compliance mechanically.

## Decision Requests

Dispatched agents escalate forks as Decision Requests — the shape is defined in `references/dispatch.md` and baked into the standing-orders block.

A well-run dispatch produces Decision Requests; on ambiguous work their
absence is a warning sign, not a virtue. When one arrives: answer it
decisively, name the chosen option by its label, supply only the missing
decision, and never expand scope in the answer. If the request reveals a
wrong premise in the brief, reopen the strategy gate instead of patching
the answer. Grade incoming requests against the shape — return an unshaped
escalation once, with the shape, before acting on it.

## Verification — route it too

The main agent arbitrates; it does not inspect by default.

- **Tier 0 — mechanical claims:** verbatim command output in the report
  (tests with counts vs baseline, lint, CI status) is sufficient evidence.
- **Tier 1 — judgment work:** an independent verifier agent (never the
  implementer), briefed to REFUTE the done-claim; screenshots for visual
  work (Anthropic tiers read images natively — route to `kimi` only when
  cross-family independence is the point). Prefer a verifier from a
  DIFFERENT model family than the implementer: shared training biases make
  same-family review rubber-stamp-prone — and since Flash 0731, a
  cross-family refuter costs pennies, so text-checkable claims get one by
  default (pairings table in `references/routing.md`). The main agent
  reads the verdict, not the diff.
- **Tier 2 — main agent:** arbitrate implementer/verifier disagreements with
  targeted reads, and personally spot-check the single riskiest claim per
  work-package. This is the legitimate case for the main agent reading code.

"Implemented but unverified" is reported as exactly that.

## Conduct & anti-patterns

- Long dispatches run in the background; the main agent keeps orchestrating —
  never idles by polling.
- Project workflow rules (reviewer-bot flows, forbidden-main) bind subagents
  and teammates alike — baked into every brief and spawn prompt.
- When a subagent's report contradicts prior beliefs (a doc, a memory, an
  earlier claim), surface the correction explicitly.
- Final reports include a one-line routing ledger with the offload split
  ("routed: 2×ds-flash recon, 3×ds-flash impl, 1×ds-flash refute,
  1×sonnet taste-check — subscription headroom spent: 1 seat") — cost
  visibility, counts the main agent actually performed.

Named failure modes — self-check for these:
- **Ceremony dispatch:** an agent to read one file you already know. The point
  is routing the lifting down, not adding ritual.
- **Orchestrator drift:** the main agent "just quickly" editing implementation
  files as the session wears on. The drift is gradual — checkpoint whenever
  about to Edit anything that isn't a brief, doc, or merge mechanic.
- **Cash-for-commodity:** spending GLM, Kimi, or DeepSeek Pro dollars on work
  a well-briefed `ds-flash` executes identically — real cost, zero
  differentiation. Two inverse failures are equally named: routing taste,
  vision, or safety work to the pennies pool to save headroom, and
  **headroom-for-commodity** — burning finite subscription capacity on
  recon, distillation, verification, or execution that flash performs
  identically for pennies.
- **Brief bloat:** pasting whole docs into briefs. Distill and point.
- **Context flooding:** letting raw dumps, full diffs, or unshaped reports
  flow back into the main context. Reports have a required shape; hold agents
  to it. Oversized-but-necessary reads get a distillation pass — `ds-flash` by
  default, Sonnet when the cut itself needs taste — before anything
  reaches the main context.
- **Rubber-stamp review:** accepting "all tests pass" without counts vs
  baseline — and same-family verifier pairings on judgment work.
- **Parallelism theater:** splitting inherently serial work to look thorough
  — and spawning a team where fan-out subagents would do.
- **Slop-back:** accepting an unshaped, hedge-laden, or unattributed report
  instead of holding the agent to the comms standard — the report is the
  product, and an imprecise one silently corrupts the next dispatch.
