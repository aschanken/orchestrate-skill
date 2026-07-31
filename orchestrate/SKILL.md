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
2. **Three separate budgets, not one.** (a) Prepaid Anthropic capacity —
   Sonnet and Opus draw on session/weekly limits already paid for; unspent
   capacity is wasted capacity, and the marginal cost of Sonnet reading
   files or building context is zero. (b) The Fable weekly allowance — the
   genuinely scarce Anthropic resource, conserved for the lead/judgment
   seat. (c) Marginal cash — DeepSeek, GLM, and Kimi bill real dollars per
   token through the gateway. **Commodity work goes to prepaid capacity.
   Cash buys differentiation, never volume.** The test for every gateway
   dispatch: what does this route provide that a prepaid Sonnet does not?
   When Anthropic session/weekly limits ARE under pressure, gateway models
   absorb volume instead — see the spend doctrine in `references/routing.md`.

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
just to make. If tests/linters will catch errors mechanically, route down —
retries at DeepSeek prices cost less than first-passes at Opus prices. If
errors only surface under judgment (subtle UI fidelity, concurrency,
security, API design taste), route up or split so the judgment part stays in
the brief.

Read `references/routing.md` at the first dispatch of the session — it holds
the full model dossiers, the spend doctrine, and the mechanics (gateway
agent types, thinking control via `effort`). Quick table:

| Route | Use for |
|---|---|
| session model | judgment only: plans, briefs, arbitration — never bulk work |
| `opus` | correctness-critical or safety-adjacent implementation; subtle multi-file judgment |
| `sonnet` | DEFAULT for recon, file reading, context building, distillation, single-concern fixes, verifier duty — prepaid, so it is the first choice for commodity work |
| `haiku` | pure-mechanical template edits with a worked example |
| `glm` — GLM 5.2 | frontend/UI implementation, long agentic runs, terminal-heavy work, repo-scale refactors |
| `kimi` — Kimi K3 | large-context delegate (whole-repo digests, giant logs), vision/screenshot verification, research synthesis |
| `ds-pro-max` — DeepSeek V4 Pro, max thinking | technical code authoring, algorithms, engineering critique and second opinions, log-driven debugging — the fresh-perspective seat |
| `ds-pro` — DeepSeek V4 Pro, thinking off | RESERVE: fast bulk instruct work when Anthropic quota is under pressure |
| `ds-flash` — DeepSeek V4 Flash, max thinking | RESERVE: high-volume mechanical work when Anthropic quota is under pressure |

Claude tiers dispatch as `model:` on a generic agent type (e.g.
`general-purpose`); gateway models dispatch as `subagent_type:` directly.

Effort routing too, where supported: low effort for mechanical stages, high
tiers only for the hardest verify/judge work.

**Escalation ladder (on subagent failure):**
1. Amend the brief naming exactly what went wrong; retry the SAME tier —
   prefer continuing the same agent where the harness supports it (warm
   context, no re-brief cost).
2. Second failure: up-tier the model — or switch model family at the same
   tier; families have uncorrelated blind spots, and a family swap is often
   free where an up-tier isn't.
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
   what converts an Opus task into a GLM or DeepSeek task.
3. **One worked example beats ten rules** for repetitive work — it is what
   converts a Sonnet task into a `ds-flash` or Haiku task.
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
  work (route those to `kimi` — it reads images). Prefer a verifier from a
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
  ("routed: 2×ds-pro recon, 1×glm impl, 1×kimi verify, 1×sonnet arbitration
  — Anthropic tokens spent on judgment only") — cost visibility, counts the
  main agent actually performed.

Named failure modes — self-check for these:
- **Ceremony dispatch:** an agent to read one file you already know. The point
  is routing the lifting down, not adding ritual.
- **Orchestrator drift:** the main agent "just quickly" editing implementation
  files as the session wears on. The drift is gradual — checkpoint whenever
  about to Edit anything that isn't a brief, doc, or merge mechanic.
- **Cash-for-commodity:** spending gateway dollars on work a prepaid Sonnet
  executes identically under the same brief — the cost is real and the
  differentiation is zero. The inverse failure — routing judgment work down
  to a cheap model to save tokens — is just as named: quality is never the
  trade.
- **Brief bloat:** pasting whole docs into briefs. Distill and point.
- **Context flooding:** letting raw dumps, full diffs, or unshaped reports
  flow back into the main context. Reports have a required shape; hold agents
  to it. Oversized-but-necessary reads get a `ds-pro` or `kimi` distillation
  pass before anything reaches the main context.
- **Rubber-stamp review:** accepting "all tests pass" without counts vs
  baseline — and same-family verifier pairings on judgment work.
- **Parallelism theater:** splitting inherently serial work to look thorough
  — and spawning a team where fan-out subagents would do.
- **Slop-back:** accepting an unshaped, hedge-laden, or unattributed report
  instead of holding the agent to the comms standard — the report is the
  product, and an imprecise one silently corrupts the next dispatch.
