# Dispatch reference — brief skeleton + standing-orders block

Read once per session, at first dispatch. The skeleton is a starting shape,
not a form to fill — drop sections that don't apply, never pad. The
standing-orders block is pasted VERBATIM at the end of every dispatch prompt,
and the comms block is pasted alongside it in every dispatch.

The same skeleton serves subagent briefs and teammate spawn prompts alike —
teammates also get the team appendix from `teams.md`. Model choice
per brief comes from `routing.md`; note in the brief's Context line which
route it was written for, since brief granularity is what makes cheap routes
safe (`ds-flash` needs the fix-point map and worked example filled; `opus`
can tolerate gaps that would sink a gateway model).

## Brief skeleton

```
# Brief: <one-line goal>

## Context
<Why this exists. 3 lines max — the agent doesn't need the saga.>

## Decisions (already made — do not relitigate)
- <decision> — <one-line rationale>
- ...

## Fix-point map (verified at <commit/date> — re-verify before editing)
| file:line | what's there now | change to make |
|---|---|---|

## The hard parts, pre-solved
<Signatures, invariants, edge-case table, pseudocode for the tricky
algorithm — whatever judgment the executing model shouldn't have to supply.>

## Worked example (for mechanical work)
<One input→output case done fully. This is what makes `ds-flash` routing safe:
it converts a rule the agent must interpret into a pattern it can match.>

## Scope fences
- Files owned by sibling agents (do not touch): <paths>
- Out of scope entirely: <paths / concerns>
- Known pre-existing flakes — do not chase: <names>
- Git: <who owns commits. When the orchestrator owns them, write "read-only
  git only (status, log, diff); no add, commit, branch, or checkout" — a bare
  "no git commands" fence contradicts any acceptance criterion that asks the
  agent to run `git status`, and a careful agent will stop to report it.>

## Self-contradiction check (author's pass before dispatch)
<Re-read the brief as the agent will: do any two instructions conflict? The
common pairs are a scope fence versus an acceptance command, and a
"reproduce verbatim" payload versus a `grep` criterion the payload's own line
wrapping defeats. A well-briefed agent stops and reports the fork, which
costs a full dispatch cycle — cheaper to catch here.>

## Workflow rules for this repo
<Branch naming, commit convention (test in same commit), PR flow, how to run
the verification battery, baseline numbers: test counts, lint state.>

## Acceptance criteria (runnable)
- [ ] `<command>` → <expected output>
- [ ] ...

<PASTE STANDING-ORDERS BLOCK HERE>
<PASTE COMMS BLOCK HERE>
```

## Standing-orders block (paste verbatim)

```
## Standing orders (non-negotiable)
- Smallest correct change. No drive-by refactors or unrequested improvements
  — note them in your report instead.
- Re-verify every fix-point (file:line) in this brief before editing. If
  reality disagrees with the brief, STOP and report the discrepancy — do not
  improvise around it.
- If you hit a decision fork this brief doesn't resolve, stop and send a
  Decision Request (shape below) — do not choose.
- Never fabricate output to appear done. Dependency unavailable → report
  blocked. No unearned numbers: never state a figure you didn't measure.
- TDD: failing test → minimal implementation → verify pass → commit, with the
  test in the same commit as the code.
- Deviations from this brief are listed in your final report with reasons —
  never silently reconciled.

## Required final report shape (keep it under ~60 lines)
1. Status: done / blocked / partial — one line.
2. Files changed: paths only.
3. Verification: verbatim command + output; test counts compared to the
   baseline given above.
4. Branch / PR URL, if applicable.
5. Deviations & discoveries, or "none".
6. Decision forks encountered, or "none".
No raw diffs, no file dumps, no restating the brief back.

## Decision Requests — how to escalate a fork
A decision fork, a contradicted fix-point, or a blocker your brief does not
resolve is manager work. Stop that item. Do not choose. Send a Decision
Request in this shape, hard cap 15 lines:
1. BLOCKED ON: the decision you need, one sentence.
2. SITUATION: what you found, each claim with file:line or verbatim output.
   Give decision-relevant context only — your manager holds more context
   than your brief shows, so do not re-explain the task.
3. OPTIONS: 2-3 viable paths. One line each on what it entails, one line on
   its tradeoff or risk. Mark exactly one RECOMMENDED, with one sentence why.
4. IMPACT: what stays blocked awaiting the answer; what you continue with
   meanwhile. Then continue with it.
Channel: teammates send this to the lead by SendMessage and keep working
non-blocked items. Solo subagents end the run with the Decision Request as
the final report, status blocked. Campaign grunts send it to their
mid-orchestrator, which answers only from its own brief or stops the
campaign and forwards the request unchanged.
```

## Comms block (paste verbatim)

```
## Comms standard (governs every message you send)

Write for a machine reader that will act on your words with no chance to ask
you what you meant.

PRECISION
1. One name for one thing. Reuse the exact identifier the brief uses. Never
   introduce a synonym for something already named.
2. Name the actor. Write "the parser reads the file", not "the file is read".
3. One instruction per sentence, 20 words maximum. Put the condition first,
   then the command.
4. Use plain verbs. Write "analyze the log", not "perform an analysis of the
   log". No phrasal verbs: spin up, circle back, dive into, reach out.
5. Make every referent resolvable: a path, a file:line, a symbol, a command, a
   task id, or an agent name. Never "the file", "it", "as mentioned above".

EVIDENCE
6. Attach an origin to every claim: verbatim command output, a file:line, or
   the word "inferred".
7. Mark confidence with CONFIRMED, UNCERTAIN, or REFUTED. Never round
   UNCERTAIN up to CONFIRMED.
8. Report unknowns as unknowns. A hidden gap costs the reader more than a
   stated one.

SIGNAL
9. Lead with the conclusion. Your reader may stop after the first line.
10. Delete marketing adjectives (seamless, robust, powerful, elegant,
    best-in-class) and hedge openers ("it is important to note", "it is worth
    noting"). They carry no information.
11. Never restate the brief back. Report only what you found and what changed.
12. Respect the length cap the brief gives you.
```

## Context packet — the recon deliverable that never transits the lead

Ported from RepoPrompt's context-builder discipline (tiered render modes,
token-priced composition; verified against repoprompt-ce source,
2026-08-07). Recon produces TWO artifacts, not one:

1. **Decision brief** — into the lead's context, standard report shape:
   conclusions, file:line evidence, open questions, and the packet's path
   plus its price line.
2. **Context packet** — a file at an exact scratchpad path, handed to
   implementers BY PATH. The lead never reads it. It moves recon's bulk
   directly into implementer contexts.

Packet shape — XML-tagged sections in this fixed order, each tag carrying
its own token estimate:

```
<file_map tokens="~2.1k">
  indented tree of the relevant area with per-file "~N tok" prices
  (tools/codemap.py --tree emits exactly this)
</file_map>
<code_maps tokens="~4.8k">
  signature-level maps (tools/codemap.py output) for the RING: files an
  implementer must know the shape of but not read — callers, interfaces,
  siblings of the target
</code_maps>
<file_contents tokens="~11k">
  TARGET files only — full text, or slices annotated
  "File: path (lines 40-95: the handler being changed)"
</file_contents>
<git_diff tokens="~1.2k">
  unified diff, only when "what changed recently" is itself context
</git_diff>
<open_questions>
  unresolved recon questions an implementer must NOT silently answer —
  these become Decision Requests if hit
</open_questions>
```

**Tiering rule (the packet's whole economics):** TARGET files — the ones
the brief's fix-point map names — get contents; the RING gets code maps
only; everything else stays in the file map. Promotion between tiers is
the lead's call, priced by the token column.

**Budgets and honesty:** default packet cap ~30k tokens; the decision
brief states the per-section split. Token estimates use the codemap
heuristic (bytes/4 × 1.05). An unknown count is written "pending" —
NEVER 0 and never a guess; an invented count corrupts the lead's budget
arithmetic.

**Consumption:** the implementer brief's Context section points at the
packet path — "Read <path> first; its <file_contents> section replaces
your own exploration of the target files." The brief's fix-point map
cites the same file:line the packet shows, so the two artifacts
cross-check each other.

## Campaign appendix (paste into mid-orchestrator briefs only)

For delegated campaigns (SKILL.md, Delegated campaigns): the campaign brief
is a normal brief PLUS this protocol block, filled in. The harness allows
three delegation layers below the lead; campaigns use ONE by rule. Consider
`maxTurns` in the mid-orchestrator's dispatch as a runaway guard on long
loops.

```
## Delegation protocol
- You may dispatch subagents with the Agent tool for the item work below.
  Depth limit: your grunts must not spawn agents.
- Grunt route: <agent type per item class — ds-flash-lite / haiku / ds-flash>.
- Grunt brief template: <template with <slots>>. Paste the standing-orders
  block and the comms block from YOUR brief into EVERY grunt prompt.
- Per-grunt report shape: <shape>, hard cap <N> lines.
- Concurrency: at most <N> grunts in flight.
- Iteration ceiling: <N> dispatch rounds. At the ceiling, stop and report
  progress plus the remainder — never push past the ceiling.
- Escalation: grunts send Decision Requests to the mid-orchestrator, which
  answers only from its own brief or stops the campaign and forwards the
  request unchanged. If a grunt fails after one amended retry, stop the
  campaign and report. Never re-scope.
- Your deliverable: ONE report in the shape below, hard cap <N> lines.
  Never forward grunt reports raw; distill and attribute (grunt id +
  claim + its evidence).
```

## Verifier brief (Tier 1) — shape

Dispatch a DIFFERENT agent than the implementer. Core instruction:

```
Your job is to REFUTE the following done-claim, not to confirm it:
<claim + branch/PR>. Actively look for: acceptance criteria that don't
actually pass, edge cases from the brief's table left unhandled, scope-fence
violations, tests that assert less than they appear to. Run the battery
yourself; do not trust the implementer's pasted output. Verdict: CONFIRMED or
REFUTED with evidence (verbatim output, file:line). If uncertain, say
uncertain — do not round up to confirmed. The verdict must be marked
CONFIRMED, REFUTED, or UNCERTAIN, and UNCERTAIN is never rounded up.
```
