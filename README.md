# orchestrate — a Claude Code skill

Turn your session's top model into the **brains of the operation**: it plans,
routes, and verifies, while model-routed subagents and agent teams do all the
implementation lifting — worktree-isolated for anything that commits, each
delivering a branch/PR with evidence. The skill is model-agnostic: the "brains" is
whatever model runs the session (Fable, Opus, …), and the execution pool
spans Claude tiers **and** gateway-routed third-party models (DeepSeek V4
Flash/Pro, GLM 5.2, Kimi K3).

One command replaces the paragraph of instructions you'd otherwise repeat
every session:

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

The core claim the skill is built around: **routing is fixed by the brief,
not the task**. A brief that pre-makes every decision and pre-solves the hard
10% (signatures, invariants, edge cases, the one tricky algorithm) moves the
same task down a model tier — and with near-free gateway models in the pool,
"down" now means DeepSeek prices. Since DeepSeek V4 Flash 0731
(Sonnet-class benchmarks at 1/35th the price), the offload doctrine routes
by checkability: everything whose output the lead or a battery can check —
specified execution AND judgment-adjacent duty (recon, distillation,
refute-verification, campaign mid-orchestration) — executes on the pennies
pool (`ds-flash` / `ds-flash-lite`); finite Anthropic subscription headroom
is conserved for taste, creativity, vision, and safety-adjacent judgment.
Quality is held by verification (runnable acceptance criteria +
cross-family refute-verification, itself near-free now), not by paying for
expensive first passes.

The skill guards the main context from **both** directions: no writing code
(output tokens), and no reading at length either (input tokens) — recon comes
back as distilled file:line briefs, bulky reads pass through a cheap
distillation shield, verification comes back as verdicts, and subagent
reports are held to a required shape with no raw diffs or file dumps.

## What the mode enforces

- **A strategy gate before any dispatch** — every task is analyzed
  (deliverable, decomposability, checkability, interaction value, volume)
  and gets an explicit dispatch strategy choosing among direct handling, a
  single routed subagent, a linear pipeline, parallel fan-out, a delegated
  campaign, a Workflow script, an agent team, or a hybrid. No vehicle is a
  reflex — teams included.
- **Division of labor** — the main agent never implements features directly.
  Its hands-on exceptions: brief writing (including the hard 10%), evidence
  arbitration, team-lead duty, trivial one-liners where dispatching costs
  more than the fix, and knowledge-distillation writing where the main
  conversation context is the source material.
- **A routing table across model families** — `ds-flash` (V4 Flash 0731,
  max thinking) as the default for all checkable work and `ds-flash-lite`
  (thinking off) as the grunt tier, both at pennies; Sonnet/Opus/Haiku as
  conserved weekly headroom for taste, vision, safety judgment, and
  escalation; GLM 5.2 (frontend ceiling), Kimi K3
  (large-context/vision/synthesis), and DeepSeek V4 Pro (parameter-depth
  knowledge) as DELIBERATE SPEND when their specific capability is the
  point. Benchmark anchors, full dossiers, the offload doctrine, and
  cross-family verifier pairings live in
  `orchestrate/references/routing.md`.
- **A delegated-campaign pattern** — for high-volume boundable programs, a
  `ds-flash` mid-orchestrator dispatches grunt subagents (nesting is
  supported three layers deep; campaigns use one by rule), iterates
  against acceptance criteria, and returns one distilled deliverable —
  protecting the main context and the subscription at once. The campaign
  delegation protocol lives in `orchestrate/references/dispatch.md`.
- **Agent-team awareness** — teams are a routed *collaboration pattern*:
  fan-out subagents for result-only work, a team when interaction adds value
  (competing-hypothesis debugging, adversarial review panels, cross-layer
  features with peer-negotiated interfaces). Team doctrine — lead never
  implements, spawn prompts are full briefs, model-pinned teammates,
  disjoint file ownership, plan approval for implementers — lives in
  `orchestrate/references/teams.md`.
- **An escalation ladder for failures** — amend the brief and retry the same
  tier (warm context) → up-tier *or switch model family* (uncorrelated blind
  spots) → rediagnose the brief itself. The main agent implementing directly
  is the last rung, flagged when used.
- **A four-step flow** — cheap parallel recon (a decision brief for the lead
  plus a token-priced **context packet** handed to implementers by path,
  scaffolded by a deterministic code-map tool) → a plan with decisions
  already made → worktree-isolated dispatch with disjoint file ownership and
  `git merge-tree` dry-runs between sibling branches → routed verification.
- **Distillation levers for briefs** — decisions not questions; the hard 10%
  written by the main agent; one worked example over ten rules; a per-task
  pre-mortem; pointers not pasted content; acceptance criteria as runnable
  commands with baselines.
- **Routed verification** — mechanical claims verified by verbatim command
  output alone, sufficient on its own; judgment work verified by an
  independent agent from a *different model family* briefed to refute the
  done-claim — Anthropic tiers read screenshots natively, route to Kimi only
  when cross-family independence is the point; the main agent only
  arbitrates disagreements and spot-checks the single riskiest claim per
  work-package.
- **Named anti-patterns** — ceremony dispatch, orchestrator drift,
  cash-for-commodity routing (and its inverse: routing judgment work down to
  save tokens), brief bloat, context flooding, rubber-stamp review,
  parallelism theater, team-for-the-sake-of-it.
- **A communication standard between agents** — adapts ASD-STE100 Simplified
  Technical English for machine readers and adds what STE lacks: evidence
  attribution, confidence marking, and referent precision. It binds every
  channel (briefs, reports, spawn prompts, teammate messages, workflow
  prompts, task-list entries); `orchestrate/tools/comms-lint.py` partially
  scores the rules a regex can check, and several rules stay judgment calls
  no linter settles.

## Layout

- `orchestrate/SKILL.md` — the kernel, loaded on every invocation. Kept lean
  on purpose: a skill about token conservation shouldn't be fat.
- `orchestrate/references/dispatch.md` — read once per session at first
  dispatch: the brief skeleton, a verbatim standing-orders + report-shape
  block to paste into every dispatch prompt, the context-packet shape recon
  delivers to implementers, and the refute-oriented verifier brief.
- `orchestrate/references/routing.md` — read once per session at first
  dispatch: model dossiers, the offload doctrine, gateway mechanics
  (thinking control via per-agent `effort`), cross-family verifier pairings.
- `orchestrate/references/teams.md` — read before the first teammate spawn:
  when a team beats fan-out, lead discipline, spawn-prompt shape, task-list
  and plan-approval rules.
- `orchestrate/references/comms.md` — read once per session: the inter-agent
  communication standard and its pasteable comms block.
- `orchestrate/tools/codemap.py` — deterministic signature maps and
  token-priced file trees (stdlib Python, no dependencies); the model-free
  scaffold recon starts from. Ported from RepoPrompt's CodeMaps idea.
- `orchestrate/tools/comms-lint.py` — mechanical compliance scoring for the
  comms standard (`test_comms_lint.py` beside it); lives inside the skill
  tree so installs carry it.
- `swarm/` — an optional tmux launcher for a three-window workflow whose
  third window runs a lead agent under this skill: `start_workflow.sh`
  builds the session (set `REMOTE_USER`/`REMOTE_HOST` for the ssh window),
  and `swarm_instructions.txt` is the lead's standing orders — vehicle
  selection via the skill's strategy gate, tmux confinement, team lifecycle
  when a team is chosen, and measured harness facts about spawned-agent
  report delivery.
- `agents/` — subagent definitions that pin the gateway routes (`ds-flash`,
  `ds-flash-lite`, `ds-pro`, `ds-pro-max`, `glm`, `kimi`). Installed
  separately (see below);
  the Agent tool's `model` param only accepts Claude aliases, so third-party
  routing happens through these agent types.

## Install

Personal (all your projects):

```bash
git clone https://github.com/aschanken/orchestrate-skill
mkdir -p ~/.claude/skills ~/.claude/agents
cp -r orchestrate-skill/orchestrate ~/.claude/skills/
cp orchestrate-skill/agents/*.md ~/.claude/agents/
```

Per-project (checked into a repo, applies to anyone using Claude Code there):

```bash
cp -r orchestrate-skill/orchestrate <your-repo>/.claude/skills/
cp orchestrate-skill/agents/*.md <your-repo>/.claude/agents/   # optional
```

Claude Code picks it up automatically; type `/orchestrate` to invoke. The
skill degrades gracefully if the gateway agents aren't installed — it falls
back to Claude tiers and says so.

## Requirements

- Claude Code with the Agent tool available (subagent dispatch).
- Python 3 on PATH for `tools/codemap.py` (stdlib only; the skill degrades
  gracefully without it — recon just loses the free deterministic scaffold).
- A git repo if you want worktree-isolated implementers (recommended).
- Works best when the session model is a higher tier than the subagent models
  — that asymmetry is the entire point.
- For third-party routing: an Anthropic-compatible gateway
  (`ANTHROPIC_BASE_URL`) serving the model IDs referenced in `agents/*.md` —
  edit those frontmatter `model:` fields to match your gateway's IDs.
- For agent teams: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your
  environment or settings; teams are experimental and the skill falls back
  to fan-out subagents without them.
- Optional: the Workflow tool for N-item sweeps and adversarial verify panels
  (the skill treats its own invocation as the opt-in).

## Customizing

Everything is plain markdown — edit the routing table and dossiers in
`orchestrate/references/routing.md` to match your gateway's model catalog,
the brief skeleton and standing orders in `references/dispatch.md` to match
your team's conventions, and the `agents/*.md` frontmatter (`model:`,
`effort:`) to pin different models or thinking budgets. The skill
deliberately tells the main agent to restate project workflow rules inside
every subagent brief rather than assume them.

## License

MIT — see [LICENSE](LICENSE).
