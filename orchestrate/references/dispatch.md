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
- If you hit a decision fork this brief doesn't resolve, stop and report the
  options with a recommendation — do not choose.
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
- Iteration ceiling: <N> dispatch rounds. On hitting it, stop and report
  progress plus the remainder — never push past the ceiling.
- Escalation: a decision fork, a contradicted fix-point, or a grunt failing
  after one amended retry → stop the campaign and report. Never re-scope.
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
