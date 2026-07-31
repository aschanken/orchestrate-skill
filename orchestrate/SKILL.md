---
name: orchestrate
description: Run this session in "brains of the operation" mode — the main agent plans, routes, and verifies; model-routed subagents and agent teams do all implementation lifting. Invoke with a task (/orchestrate fix issues 22 and 24) or bare to arm the mode for the whole session.
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
   on execution. (b) Anthropic subscription capacity (Opus, Sonnet, Haiku)
   is expendable: already paid for, wasted if unspent, zero marginal cost.
   It is the default pool for anything needing judgment, taste, or
   creativity. (c) `ds-flash` bills cash, but so little that it buys
   enormous throughput for pennies — worth paying for, and its job is to
   absorb fully-specifiable work so subscription capacity stays free for
   what only Anthropic tiers can do. (d) GLM, Kimi K3, `ds-pro`, and
   `ds-pro-max` bill real money at real rates: deliberate occasional spends,
   never defaults. **Specify it and send it to flash; judge it and keep it
   on Anthropic; pay the others only when they are genuinely the point.**
   See the spend doctrine in `references/routing.md`.

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
| `ds-flash` — DeepSeek V4 Flash, max thinking | DEFAULT for fully-specifiable work: mechanical edits, file surgery from an exact fix-point map, glue code, scripts, test scaffolding, fixtures, data munging, churn sweeps. Pennies per run, so it absorbs volume that would otherwise burn subscription capacity. Supplies no creativity — never send it work needing taste |
| `sonnet` | DEFAULT for judgment-bearing work: recon, file reading, context building, distillation, single-concern fixes, verifier duty. Expendable subscription capacity, zero marginal cost |
| `opus` | correctness-critical or safety-adjacent implementation; subtle multi-file judgment; anything where taste decides the outcome |
| `haiku` | pure-mechanical template edits where writing a flash-grade brief costs more than the work itself |
| `ds-pro-max` — DeepSeek V4 Pro, max thinking | DELIBERATE SPEND: cross-family engineering critique of a design before implementation; algorithms when subscription capacity is exhausted |
| `glm` — GLM 5.2 | DELIBERATE SPEND: frontend/UI implementation and long agentic runs when subscription capacity is exhausted |
| `kimi` — Kimi K3 | DELIBERATE SPEND: reads exceeding the session's own context; cross-family adversarial verification |
| `ds-pro` — DeepSeek V4 Pro, thinking off | DELIBERATE SPEND: fast bulk instruct work when subscription capacity is exhausted |

Claude tiers dispatch as `model:` on a generic agent type (e.g.
`general-purpose`); gateway models dispatch as `subagent_type:` directly.

Effort routing too, where supported: low effort for mechanical stages, high
tiers only for the hardest verify/judge work.

**Escalation ladder (on subagent failure):**
1. Amend the brief naming exactly what went wrong; retry the SAME tier —
   prefer continuing the same agent where the harness supports it (warm
   context, no re-brief cost). A `ds-flash` failure almost always means the
   brief left something unspecified: fix the brief, not the routing.
2. Second failure: move UP into Anthropic subscription capacity — Sonnet,
   then Opus. Do not move sideways into a cash-billed gateway model to save
   face; that spends real money on a problem the brief caused.
3. Top tier fails too: the brief is wrong, not the model. Re-recon,
   rediagnose. The main agent implementing directly is the LAST rung, never a
   shortcut, and gets flagged in the report when it happens.

## The standard flow

1. **Recon** (parallel, routed): map the relevant code, return a distilled
   brief — findings, exact file:line evidence, open questions. Recon routes
   to Sonnet by default (prepaid) — mechanical recon (file maps, symbol
   traces, log digests) and judgment recon (architecture assessment, "why
   is this shaped this way") alike. Use Explore agents for broad searches.
   Never let an implementer explore from scratch what a recon pass can map
   first.
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
   - **Agent team**: when the value comes from interaction between workers —
     see Agent teams below. Read `references/teams.md` before first spawn.
   - **Workflow tool** where available, for N-item sweeps or verify panels
     (pipeline + schema outputs) — invoking this skill is the standing
     opt-in, within session size guidance.
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

## Distillation — what makes a brief carry top-tier quality

Subagents start cold; the brief is the transfer medium. The levers, in order
of power:

1. **Decisions, not questions.** Resolve every fork before dispatch. The
   standing order for forks discovered mid-work is stop-and-report, not
   choose.
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

## Verification — route it too

The main agent arbitrates; it does not inspect by default.

- **Tier 0 — mechanical claims:** verbatim command output in the report
  (tests with counts vs baseline, lint, CI status) is sufficient evidence.
- **Tier 1 — judgment work:** an independent verifier agent (never the
  implementer), briefed to REFUTE the done-claim; screenshots for visual
  work (Anthropic tiers read images natively — route to `kimi` only when
  cross-family independence is the point). Prefer a verifier from a
  DIFFERENT model family than the implementer: shared training biases make
  same-family review rubber-stamp-prone. The main agent reads the verdict,
  not the diff.
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
  ("routed: 2×sonnet recon, 3×ds-flash impl, 1×sonnet verify — no
  cash-billed models needed") — cost visibility, counts the
  main agent actually performed.

Named failure modes — self-check for these:
- **Ceremony dispatch:** an agent to read one file you already know. The point
  is routing the lifting down, not adding ritual.
- **Orchestrator drift:** the main agent "just quickly" editing implementation
  files as the session wears on. The drift is gradual — checkpoint whenever
  about to Edit anything that isn't a brief, doc, or merge mechanic.
- **Cash-for-commodity:** spending GLM, Kimi, or DeepSeek Pro dollars on work
  a Sonnet or a well-briefed `ds-flash` executes identically — real cost,
  zero differentiation. Two inverse failures are equally named: routing
  judgment or taste work to `ds-flash` to save money, and leaving flash idle
  while burning subscription capacity on work an exact fix-point map would
  have made mechanical.
- **Brief bloat:** pasting whole docs into briefs. Distill and point.
- **Context flooding:** letting raw dumps, full diffs, or unshaped reports
  flow back into the main context. Reports have a required shape; hold agents
  to it. Oversized-but-necessary reads get a Sonnet distillation pass before
  anything reaches the main context.
- **Rubber-stamp review:** accepting "all tests pass" without counts vs
  baseline — and same-family verifier pairings on judgment work.
- **Parallelism theater:** splitting inherently serial work to look thorough
  — and spawning a team where fan-out subagents would do.
- **Slop-back:** accepting an unshaped, hedge-laden, or unattributed report
  instead of holding the agent to the comms standard — the report is the
  product, and an imprecise one silently corrupts the next dispatch.
