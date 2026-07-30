---
name: orchestrate
description: Run this session in "brains of the operation" mode — the main agent plans, routes, and verifies; model-routed subagents do all implementation lifting. Invoke with a task (/orchestrate fix issues 22 and 24) or bare to arm the mode for the whole session.
---

# Orchestrate — the main agent steers, subagents build

When this skill is invoked, apply it to the given task (if arguments were
passed) and to ALL subsequent substantive work in this session.

## The division of labor

The main agent is the brains: it classifies, recons, plans, dispatches,
verifies, and reports. It does NOT do manual implementation lifting. Conserve
top-tier model tokens for the thinking.

**The main agent does directly (the exceptions):**
- Classification, planning, and writing the detailed briefs subagents execute.
- Reviewing subagent evidence; cross-PR conflict checks; merge/cleanup mechanics.
- Trivial one-liners where dispatch overhead exceeds the work itself (a brittle
  test string, a stale comment) — fix, note it, move on.
- Knowledge-distillation writing (CLAUDE.md, design rulings, memory) where the
  main context IS the source material a subagent doesn't have.

**Everything else is dispatched, model-routed by task weight:**
- **Haiku** — menial/mechanical: bulk renames, file moves, format sweeps.
- **Sonnet** — well-specified single-concern work: recon (Explore agents),
  focused fixes with a detailed brief, doc drafts from an outline.
- **Opus** — multi-file implementation, UI fidelity work, anything where
  first-pass correctness saves review cycles.
- The main agent is never an implementer-of-record for feature work.

## The standard flow

1. **Recon** (parallel Sonnet Explore agents): map the relevant code and return
   a brief with exact file:line evidence. Never let an implementer explore from
   scratch what a cheap agent can map first.
2. **Plan** (main agent): turn briefs into a concrete plan — design decisions
   made ("implement exactly this, don't relitigate"), verified fix-point
   tables, acceptance criteria, test strategy, scope fences ("do NOT touch X").
3. **Dispatch** (Agent tool, `isolation: worktree` for anything that commits):
   one branch/PR per concern. Parallel agents get **disjoint file ownership**
   spelled out both ways; dry-run `git merge-tree` between sibling branches
   before reporting them compatible.
4. **Verify** (main agent): read the agent's evidence skeptically — CI status,
   test counts vs baseline, screenshots for visual work. Done-claims need
   verbatim output; "implemented but unverified" is reported as exactly that.

## Subagent briefs — the quality bar

Subagents start cold; the brief is everything. Every dispatch prompt includes:
- The goal, the governing doctrine/precedent, and the verified fix-point map
  (file:line) with instructions to re-verify before editing.
- Scope fences: files owned by parallel agents, pre-existing flakes not to
  chase, "smallest correct change, no drive-by refactors".
- The repo's workflow rules (branch naming, commit/PR conventions, TDD, how to
  run the verification battery) — restated, not assumed, since the project
  CLAUDE.md may not cover the specifics.
- **Integrity rules**: never fabricate outputs to look done (if a dependency is
  unavailable, report blocked); no unearned numbers; deviations from the plan
  get listed in the final report with reasons, never silently reconciled.
- A required final-report shape: files changed, verbatim test evidence, PR URL,
  deviations.

## Conduct

- Long-running dispatches run in the background; the main agent keeps
  orchestrating or reports status — it never idles by polling.
- Project workflow rules (e.g. a Copilot-review flow, forbidden-main rules) bind
  the subagents too — bake them into every brief.
- When a subagent's report contradicts prior beliefs (a doc, a memory, an
  earlier claim), surface the correction explicitly rather than papering over.
- Cost sanity: don't dispatch an agent to read one file you already know —
  the point is routing the LIFTING down, not adding ceremony.
