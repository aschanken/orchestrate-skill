# orchestrate — a Claude Code skill

Turn your top-tier Claude model into the **brains of the operation**: it plans,
routes, and verifies, while cheaper model-routed subagents (Opus / Sonnet /
Haiku) do all the implementation lifting — each in an isolated git worktree,
each delivering a branch/PR with evidence.

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
carefully-written briefs. In practice the main agent's token spend concentrates
in recon synthesis, plan authorship, and evidence review, while multi-hundred-
tool-call implementation runs happen on Opus or Sonnet.

## What the mode enforces

- **Division of labor** — the main agent never implements features directly.
  Its only hands-on exceptions: trivial one-liners where dispatching costs more
  than the fix, and knowledge-distillation writing where the main conversation
  context is the source material.
- **Model routing by task weight** — Haiku for menial sweeps, Sonnet for recon
  and well-specified single-concern fixes, Opus for multi-file implementation.
- **A four-step flow** — cheap parallel recon (file:line briefs) → a plan with
  decisions already made → worktree-isolated dispatch with disjoint file
  ownership and `git merge-tree` dry-runs between sibling branches → skeptical
  evidence review (verbatim test output or it didn't happen).
- **Brief quality** — subagents start cold, so every dispatch prompt carries
  the doctrine, the verified fix-point map, scope fences, the repo's workflow
  rules, and integrity rules (never fabricate outputs; report blocked instead;
  deviations listed, never silently reconciled).

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
- A git repo if you want worktree-isolated implementers (recommended).
- Works best when the session model is a higher tier than the subagent models —
  that asymmetry is the entire point.

## Customizing

`orchestrate/SKILL.md` is plain markdown — edit the routing table, the flow, or
the brief checklist to match your team's conventions (e.g. squash vs merge
commits, your CI battery, a reviewer bot workflow). The skill deliberately
tells the main agent to restate project workflow rules inside every subagent
brief rather than assume them.

## License

MIT — see [LICENSE](LICENSE).
