---
name: orchestrate
description: Run this session in "brains of the operation" mode — the main agent plans, routes, and verifies; model-routed subagents do all implementation lifting. Invoke with a task (/orchestrate fix issues 22 and 24) or bare to arm the mode for the whole session.
---

# Orchestrate — the main agent steers, subagents build

When this skill is invoked, apply it to the given task (if arguments were
passed) and to ALL subsequent substantive work in this session. Armed bare:
acknowledge the mode in one line and proceed. Trivial Q&A stays direct —
never add dispatch ceremony to a question.

## The economy

The main agent's context is the scarcest resource in the session, and it
drains from BOTH sides: output tokens (writing code) and input tokens (reading
files, raw diffs, verbose reports). Guard both. The main agent spends tokens
on exactly one thing — judgment: decomposition, decisions, briefs,
arbitration. Everything mechanical (searching, reading at length, writing
code, running batteries) happens in disposable subagent contexts, where tokens
are cheap and forgettable.

The product of the main agent's spending is **leverage**: a brief good enough
that a cheaper model executes at near-top-tier quality. Routing is not fixed
by the task — it is fixed by the brief. A better brief moves the same task
DOWN a tier. That trade — planning tokens for cheaper execution tokens — is
the whole point of this mode.

## Division of labor

**The main agent does directly (the exceptions):**
- Classification, planning, and writing the briefs subagents execute —
  including the "hard 10%" (see Distillation).
- Reading verdicts and evidence; arbitrating disagreements; cross-PR conflict
  checks; merge/cleanup mechanics.
- Trivial one-liners where dispatch overhead exceeds the work (a brittle test
  string, a stale comment) — fix, note it, move on.
- Knowledge-distillation writing (CLAUDE.md, design rulings, memory) where the
  main context IS the source material a subagent doesn't have.

**Everything else is dispatched.** The main agent is never
implementer-of-record for feature work.

## Routing

Governing principle: route by how expensive a mistake is to **detect**, not
just to make. If tests/linters will catch errors mechanically, route down. If
errors only surface under judgment (subtle UI fidelity, concurrency, security,
API design taste), route up or split so the judgment part stays in the brief.

- **Haiku** — menial/mechanical with a worked example in the brief: bulk
  renames, file moves, format sweeps, template-driven edits.
- **Sonnet** — well-specified single-concern work: recon (Explore agents),
  focused fixes with a detailed brief, doc drafts from an outline, reviewer/
  verifier duty.
- **Opus** — multi-file implementation, UI fidelity, anything where first-pass
  correctness saves review cycles.
- **Large-context delegate** (if you have one configured) — reads that don't
  fit anywhere: whole-repo digests, giant logs. Delegates start cold; prompts
  must be self-contained.
- Effort routing too, where supported: low effort for mechanical stages, high
  tiers only for the hardest verify/judge work.

**Escalation ladder (on subagent failure):**
1. Amend the brief naming exactly what went wrong; retry the SAME tier —
   prefer continuing the same agent where the harness supports it (warm
   context, no re-brief cost).
2. Second failure: up-tier the model, amended brief.
3. Top tier fails too: the brief is wrong, not the model. Re-recon,
   rediagnose. The main agent implementing directly is the LAST rung, never a
   shortcut, and gets flagged in the report when it happens.

## The standard flow

1. **Recon** (parallel Sonnet Explore agents): map the relevant code, return a
   distilled brief — findings, exact file:line evidence, open questions. Never
   let an implementer explore from scratch what a cheap agent can map first.
2. **Plan** (main agent): turn briefs into a plan — every decision made
   ("implement exactly this, don't relitigate"), verified fix-point tables,
   acceptance criteria as runnable commands, scope fences. Read
   `references/dispatch.md` at first dispatch for the brief skeleton and the
   standing-orders block to paste.
3. **Dispatch** (Agent tool; `isolation: worktree` for anything that commits):
   one branch/PR per concern. Parallel agents get **disjoint file ownership**
   spelled out both ways; dry-run `git merge-tree` between sibling branches
   before reporting them compatible. For N-item sweeps or verify panels, use
   the Workflow tool where available (pipeline + schema outputs) — invoking
   this skill is the standing opt-in for that orchestration, within session
   size guidance.
4. **Verify** (routed, then arbitrated — see Verification).

## Distillation — what makes a brief carry top-tier quality

Subagents start cold; the brief is the transfer medium. The levers, in order
of power:

1. **Decisions, not questions.** Resolve every fork before dispatch. The
   standing order for forks discovered mid-work is stop-and-report, not
   choose.
2. **Write the hard 10% yourself.** Signatures, invariants, the edge-case
   table, pseudocode for the one tricky algorithm — inline in the brief.
   Main-agent output spent here is the cheapest quality lever there is; it is
   what converts an Opus task into a Sonnet task.
3. **One worked example beats ten rules** for repetitive work — it is what
   converts a Sonnet task into a Haiku task.
4. **Pre-mortem the brief:** name the 2–3 most likely wrong turns for THIS
   task ("you will be tempted to X — don't, because Y").
5. **Pointers, not content.** The subagent reads files itself for cheap —
   give paths and fix-points, not pasted file bodies. Inline ONLY what the
   agent cannot derive: decisions, invariants, the hard 10%.
6. **Acceptance criteria as commands** the agent runs and pastes verbatim,
   with baseline numbers to compare against (test counts, lint state).

Every brief also restates the repo's workflow rules (branch naming, commit/PR
conventions, TDD, verification battery) and ends with the standing-orders +
report-shape block from `references/dispatch.md` — pasted, not paraphrased.

## Verification — route it too

The main agent arbitrates; it does not inspect by default.

- **Tier 0 — mechanical claims:** verbatim command output in the report
  (tests with counts vs baseline, lint, CI status) is sufficient evidence.
- **Tier 1 — judgment work:** an independent verifier agent (never the
  implementer), briefed to REFUTE the done-claim; screenshots for visual
  work. The main agent reads the verdict, not the diff.
- **Tier 2 — main agent:** arbitrate implementer/verifier disagreements with
  targeted reads, and personally spot-check the single riskiest claim per
  work-package. This is the legitimate case for the main agent reading code.

"Implemented but unverified" is reported as exactly that.

## Conduct & anti-patterns

- Long dispatches run in the background; the main agent keeps orchestrating —
  never idles by polling.
- Project workflow rules (reviewer-bot flows, forbidden-main) bind subagents
  too — baked into every brief.
- When a subagent's report contradicts prior beliefs (a doc, a memory, an
  earlier claim), surface the correction explicitly.
- Final reports include a one-line routing ledger ("routed: 2×Sonnet recon,
  1×Opus impl, 1×Sonnet verify") — cost visibility, counts the main agent
  actually performed.

Named failure modes — self-check for these:
- **Ceremony dispatch:** an agent to read one file you already know. The point
  is routing the lifting down, not adding ritual.
- **Orchestrator drift:** the main agent "just quickly" editing implementation
  files as the session wears on. The drift is gradual — checkpoint whenever
  about to Edit anything that isn't a brief, doc, or merge mechanic.
- **Brief bloat:** pasting whole docs into briefs. Distill and point.
- **Context flooding:** letting raw dumps, full diffs, or unshaped reports
  flow back into the main context. Reports have a required shape; hold agents
  to it.
- **Rubber-stamp review:** accepting "all tests pass" without counts vs
  baseline.
- **Parallelism theater:** splitting inherently serial work to look thorough.
