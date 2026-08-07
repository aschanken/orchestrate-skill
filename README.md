# orchestrate — a Claude Code skill

Turn your top-tier Claude model into the **brains of the operation**: it plans,
routes, and verifies, while cheaper model-routed subagents do all the
implementation lifting — checkable work on a pennies-priced gateway default,
taste-bearing work on Anthropic tiers — each in an isolated git worktree, each
delivering a branch/PR with evidence.

One command replaces the paragraph of instructions you'd otherwise repeat every
session:

```
/orchestrate fix issues 22 and 24
```

or arm it for the whole session:

```
/orchestrate
```

## Why

If you run Claude Code on a premium model tier, spending those tokens on bulk
edits and file wiring is waste — but downgrading the whole session loses the
planning quality. This skill encodes the split: the expensive model thinks,
plans, and checks; disposable subagents on cheaper models execute
carefully-written briefs.

The core claim the skill is built around: **routing is fixed by the brief, not
the task**. A brief that pre-makes every decision and pre-solves the hard 10%
(signatures, invariants, edge cases, the one tricky algorithm) moves the same
task down a model tier. The main agent's token spend concentrates in exactly
that — recon synthesis, plan authorship, brief writing, evidence arbitration —
while multi-hundred-tool-call implementation runs happen on routed subagent
seats, at pennies when the brief is complete.

The skill guards the main context from **both** directions: no writing code
(output tokens), and no reading at length either (input tokens) — recon comes
back as distilled file:line briefs, verification comes back as verdicts, and
subagent reports are held to a required shape with no raw diffs or file dumps.

## What the mode enforces

- **Division of labor** — the main agent never implements features directly.
  Its hands-on exceptions: brief writing (including the hard 10%), evidence
  arbitration, trivial one-liners where dispatching costs more than the fix,
  and knowledge-distillation writing where the main conversation context is
  the source material.
- **Routing by error-detection cost** — if tests catch mistakes mechanically,
  route down; if mistakes only surface under judgment, route up or keep the
  judgment in the brief. A pennies-priced gateway model (`ds-flash` in the
  reference setup) is the default for checkable work — recon, context
  packets, fully-specified implementation, refute-verification; Anthropic
  tiers hold taste, vision, and safety-adjacent correctness; cash-billed
  specialists (GLM, Kimi, DeepSeek Pro) are deliberate spends, never
  defaults. Dossiers and the spend doctrine live in
  `orchestrate/references/routing.md`.
- **A strategy gate before any dispatch** — every substantive task gets an
  explicit architecture choice (direct, single seat, pipeline, fan-out,
  delegated campaign, workflow script, agent team, or hybrid), posted before
  acting; no vehicle is a reflex.
- **An escalation ladder for failures** — amend the brief and retry the same
  tier (warm context) → up-tier the model → rediagnose the brief itself.
  Double failures usually mean the brief was wrong, not the model. The main
  agent implementing directly is the last rung, flagged when used.
- **A four-step flow** — cheap parallel recon (a decision brief for the lead
  plus a token-priced **context packet** handed to implementers by path,
  scaffolded by a deterministic code-map tool) → a plan with decisions
  already made → worktree-isolated dispatch with disjoint file ownership and
  `git merge-tree` dry-runs between sibling branches → routed verification.
- **Distillation levers for briefs** — decisions not questions; the hard 10%
  written by the main agent; one worked example over ten rules; a per-task
  pre-mortem ("you will be tempted to X — don't"); pointers not pasted
  content; acceptance criteria as runnable commands with baselines.
- **Routed verification** — mechanical claims verified by verbatim command
  output; judgment work verified by an independent agent briefed to *refute*
  the done-claim; the main agent only arbitrates disagreements and
  spot-checks the single riskiest claim per work-package.
- **Named anti-patterns** — ceremony dispatch, orchestrator drift (the main
  agent "just quickly" editing files as the session wears on), brief bloat,
  context flooding, rubber-stamp review, parallelism theater.

## Layout

- `orchestrate/SKILL.md` — the kernel, loaded on every invocation. Kept lean
  on purpose: a skill about token conservation shouldn't be fat.
- `orchestrate/references/dispatch.md` — read once per session at first
  dispatch: the brief skeleton, a verbatim standing-orders + report-shape
  block to paste into every dispatch prompt, the context-packet shape recon
  delivers to implementers, and the refute-oriented verifier brief.
- `orchestrate/references/routing.md` — model dossiers, the spend doctrine,
  and dispatch mechanics for model-routed seats.
- `orchestrate/references/comms.md` — the agent-to-agent comms standard and
  its pasteable block.
- `orchestrate/references/teams.md` — agent-team doctrine for when
  interaction between workers is the point.
- `orchestrate/tools/codemap.py` — deterministic signature maps and
  token-priced file trees (stdlib Python, no dependencies); the model-free
  scaffold recon starts from. Ported from RepoPrompt's CodeMaps idea.

## Install

Personal (all your projects):

```bash
git clone https://github.com/aschanken/orchestrate-skill
mkdir -p ~/.claude/skills
cp -r orchestrate-skill/orchestrate ~/.claude/skills/
```

Per-project (checked into a repo, applies to anyone using Claude Code there):

```bash
cp -r orchestrate-skill/orchestrate <your-repo>/.claude/skills/
```

Claude Code picks it up automatically; type `/orchestrate` to invoke.

## Requirements

- Claude Code with the Agent tool available (subagent dispatch).
- Python 3 on PATH for `tools/codemap.py` (stdlib only; the skill degrades
  gracefully without it — recon just loses the free deterministic scaffold).
- A git repo if you want worktree-isolated implementers (recommended).
- Works best when the session model is a higher tier than the subagent models —
  that asymmetry is the entire point.
- Optional: gateway-routed agent types for third-party models (the reference
  setup defines `ds-flash`, `ds-flash-lite`, `glm`, `kimi`, `ds-pro`,
  `ds-pro-max`); without them the routing table degrades gracefully to
  Anthropic-only tiers.
- Optional: the Workflow tool for N-item sweeps and adversarial verify panels
  (the skill treats its own invocation as the opt-in), and a large-context
  delegate agent for oversized reads.

## Customizing

`orchestrate/SKILL.md` and the `orchestrate/references/` docs are plain
markdown — edit the routing table, the flow, the brief skeleton, or the
standing-orders block to match your team's conventions (e.g. squash vs merge
commits, your CI battery, a reviewer bot workflow). The skill deliberately
tells the main agent to restate project workflow rules inside every subagent
brief rather than assume them.

## License

MIT — see [LICENSE](LICENSE).
