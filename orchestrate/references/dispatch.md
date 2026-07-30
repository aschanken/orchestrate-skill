# Dispatch reference — brief skeleton + standing-orders block

Read once per session, at first dispatch. The skeleton is a starting shape,
not a form to fill — drop sections that don't apply, never pad. The
standing-orders block is pasted VERBATIM at the end of every dispatch prompt.

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

## Worked example
<For repetitive/mechanical work: one input→output case done fully.
This section is what makes Haiku routing safe.>

## Scope fences
- Files owned by sibling agents (do not touch): <paths>
- Out of scope entirely: <paths / concerns>
- Known pre-existing flakes — do not chase: <names>

## Workflow rules for this repo
<Branch naming, commit convention (test in same commit), PR flow, how to run
the verification battery, baseline numbers: test counts, lint state.>

## Acceptance criteria (runnable)
- [ ] `<command>` → <expected output>
- [ ] ...

<PASTE STANDING-ORDERS BLOCK HERE>
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

## Verifier brief (Tier 1) — shape

Dispatch a DIFFERENT agent than the implementer. Core instruction:

```
Your job is to REFUTE the following done-claim, not to confirm it:
<claim + branch/PR>. Actively look for: acceptance criteria that don't
actually pass, edge cases from the brief's table left unhandled, scope-fence
violations, tests that assert less than they appear to. Run the battery
yourself; do not trust the implementer's pasted output. Verdict: CONFIRMED or
REFUTED with evidence (verbatim output, file:line). If uncertain, say
uncertain — do not round up to confirmed.
```
