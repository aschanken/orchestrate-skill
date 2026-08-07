# Comms standard

The comms standard is a controlled-language specification that governs every
message an agent sends to another agent in an orchestrate session. It exists
because agents act on messages immediately and without human review — a missing
file path, a vague referent, or an unqualified claim propagates through a
dispatch chain and compounds. The standard makes every message precise enough
that a machine reader can act on it without asking for clarification.

## Why STE, and what it does not cover

The standard adapts ASD-STE100 Simplified Technical English, the controlled-
language specification used in aerospace maintenance manuals since 1986. STE
was designed for a human reader — a technician who can see the aircraft, the
manual page, and the part they are holding. The slop-source experiment tested
whether STE's mechanical rules reduce "AI slop" in human-facing prose (READMEs,
PR descriptions, error messages) and confirmed they cut violations by 50-74%
across models.

That experiment addressed prose quality for human readers. It did NOT address
agent-to-agent communication. An agent reader differs from a human reader in
three ways: (a) it acts on words immediately with no chance to ask follow-up
questions; (b) it cannot resolve referents from shared physical context — there
is no "aircraft" an agent can look at; (c) it truncates messages, often reading
only the first sentence. The comms standard adapts STE for this reader:
keeping the rules that reduce ambiguity between machines, dropping rules that
cost tokens without removing ambiguity, and adding rules that make claims
verifiable.

### What we keep from STE, what we drop, what we add

| Category | Rule | Rationale |
|---|---|---|
| KEEP | One name for one thing | Prevents a reader from treating one entity as two |
| KEEP | Active voice with named actor | Removes ambiguity about who or what acts |
| KEEP | One instruction per sentence, 20-word cap | Longer sentences hide multiple commands |
| KEEP | Plain verbs over nominalizations | "Analyze" is unambiguous; "perform an analysis" is four words for one verb |
| KEEP | No phrasal verbs | "Spin up" has no machine-parseable meaning |
| KEEP | Condition before command | The reader must evaluate the condition before acting |
| KEEP | Numbered vertical lists for steps | Encodes ordered procedure; bullet lists do not |
| KEEP | No marketing adjectives | Carries zero information for a machine reader |
| KEEP | No hedge openers | Carries zero information; wastes tokens |
| DROP | Contraction ban | Expanding "don't" spends a token and removes no ambiguity between machines |
| DROP | ~900-word approved dictionary | Too narrow for technical domains; keep only the common-word substitution habit |
| DROP | Em-dash policing | A human aesthetic concern; em-dashes create no referential ambiguity |
| DROP | Semicolon ban | Semicolons create no referential ambiguity for a machine reader |
| ADD | Referent precision (rule 5) | STE assumes shared physical context; an agent has none — every referent must resolve |
| ADD | Evidence attribution (rule 6) | STE governs form, not truth; a claim without an origin is unusable |
| ADD | Confidence marking (rule 7) | The highest-value addition — unmarked uncertainty propagates and compounds |
| ADD | Explicit unknowns (rule 8) | A stated gap is actionable; a hidden gap is a trap |
| ADD | Conclusion-first ordering (rule 9) | Agents truncate; STE assumes a document read in full |
| ADD | No brief echo and length caps (rules 11-12) | Token economy — STE has no concept of it |

## The comms block (paste verbatim)

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

## Where it binds

**Subagent briefs.** Briefs are instructions from orchestrator to subagent.
This is a two-layer design: the comms block is baked into the gateway agent
definitions in `agents/*.md`, so agents routed through them comply by
default, AND the block is pasted into every brief as reinforcement. The
paste is not redundant — a Claude-tier subagent dispatched via `model:` on
a generic agent type has no `agents/*.md` definition, so the pasted block
is its only source of the standard. Write the brief body to the standard.

**Subagent reports.** Every subagent final message is a report. The comms
standard governs its form: open with the conclusion, state confidence, cite
evidence at file:line granularity, never echo the brief.

**Decision Requests.** Escalated forks are a bound message type: the
request is governed by the comms standard and shaped per
`references/dispatch.md` (BLOCKED ON / SITUATION / OPTIONS / IMPACT).

**Teammate spawn prompts and SendMessage.** Agent() prompts and SendMessage
bodies are the highest-volume inter-agent channel. Every word here is a word
every teammate must read. The standard binds hardest on this channel.

**Workflow agent() prompts and schema outputs.** When a workflow step calls
agent() and expects structured output, both the prompt and the output schema
conform to the standard. Schema fields carry CONFIRMED/UNCERTAIN/REFUTED
markers where a downstream step acts on the result.

**Shared task-list entries.** Task subject and description fields are read by
every teammate picking up work. Subjects are imperative; descriptions cite
file:line anchors and acceptance criteria — no background narration.

## Worked example

A subagent brief: "Fix the intermittent `TestAuthFlow` failure in the auth
middleware test suite. The test fails roughly 6 out of 20 runs."

**Before** (slop-shaped report):

```
I dug into the TestAuthFlow issue and it turns out the problem was
a tricky race condition in how tokens were being cached. The test
was failing intermittently because stale tokens from previous tests
were leaking into the TestAuthFlow run. I added a cleanup step in
the teardown to flush the cache, which should take care of it. I
ran the tests a bunch of times and they all passed, so I think
we're good now.
```

**After** (comms standard):

```
CONFIRMED: `TestAuthFlow` intermittent failure root cause found
and fixed.

Root cause: the auth middleware cached tokens in a module-level
`Map`, surviving across test cases. When `TestAuthFlow` ran after
`TestTokenRefresh`, the stale token from the prior test triggered
a 401 instead of the expected 403.
File: `src/auth/middleware.ts:47` — `const cache = new Map();`
declared at module scope.

Fix: added `cache.clear()` to `beforeEach` in
`src/auth/__tests__/middleware.test.ts:12`.

Verification: `npx jest TestAuthFlow --repeat=20` passes 20/20
(was 14/20 passing before the fix).
UNCERTAIN: whether other test suites have the same
module-scoped-cache pattern.
```

## Enforcement

A companion tool, `tools/comms-lint.py`, scores agent messages against the
mechanical subset of these rules (violations per 100 words), across seven
rule-backed categories, each mapped one-to-one to a numbered rule above:
long_sentence, passive_voice, nominalization, phrasal_verb,
marketing_adjective, hedge_opener, vague_referent. Covered by a 59-test
suite. It is not yet wired into the orchestrate dispatch pipeline as an
automated gate — run it by hand against a message or brief before sending.

## Limits

The comms standard governs form, not truth. A perfectly compliant report can
still be wrong — a CONFIRMED claim can be false, a cited file:line can be
stale, a 20-word sentence can lie. The standard never replaces verification.
The reader must still check the claim against the evidence.
