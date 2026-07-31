# Routing reference — model dossiers, offload doctrine, mechanics

Read once per session, at first dispatch.

## Mechanics — how routing actually happens

- **Claude tiers** route via the Agent tool's `model` param (`haiku` /
  `sonnet` / `opus`) or Workflow `opts.model`.
- **Gateway models** (DeepSeek, GLM, Kimi) are NOT in the Agent tool's model
  enum — they route via agent types: subagent definitions in
  `~/.claude/agents/` whose frontmatter pins `model:` to a gateway ID and
  `effort:` to a thinking budget. Dispatch with
  `Agent(subagent_type: "ds-flash", ...)` etc. The definitions ship in this
  repo's `agents/` directory; if a dispatch fails with an unknown agent type,
  they aren't installed — fall back to Claude tiers and note it.
- **Thinking control:** the per-agent `effort` frontmatter field is the
  thinking-budget knob (`low` ≈ thinking off, `max` ≈ max thinking); the
  gateway maps effort to the third-party thinking parameter. This is why
  `ds-pro` and `ds-pro-max` are two agent types over one model.
- **Teams caveat:** a teammate honors a definition's `model` but follows the
  LEAD's effort, not the definition's. The thinking distinction between
  `ds-pro` and `ds-pro-max` therefore only holds for subagents. When a
  DeepSeek teammate's thinking mode matters, prefer subagent dispatch, or
  compensate in the spawn prompt ("reason step-by-step before each edit" /
  "answer directly, no deliberation").
- Model self-reports are unreliable (open models routinely misidentify
  themselves) — never "verify" routing by asking an agent what it is; trust
  the agent-type definition.

## The routing table

Ordered top (most capable, most expensive) to bottom. "Session model" =
whatever runs this session; routing to your own tier buys parallelism, not
capability.

| Agent type | Model / thinking | Cost class | Slot |
|---|---|---|---|
| `opus` | Claude Opus | premium (Anthropic budget) | correctness-critical judgment implementation |
| `glm` | GLM 5.2 | cheap (~1/5 of premium) | default implementation workhorse |
| `kimi` | Kimi K3 | mid (pricey output, slow) | large-context / vision / synthesis specialist |
| `sonnet` | Claude Sonnet | mid (Anthropic budget) | judgment recon + judgment verification |
| `ds-pro-max` | DeepSeek V4 Pro, max thinking | very cheap | budget engineer |
| `ds-pro` | DeepSeek V4 Pro, thinking off | very cheap, fast | instruct executor + distiller |
| `ds-flash` | DeepSeek V4 Flash, max thinking | near-free | utility workhorse |
| `haiku` | Claude Haiku | cheap (Anthropic budget) | template-mechanical sweeps |

## Dossiers — what each route is FOR

**`glm` — GLM 5.2.** The strongest open coding/agentic model; frontend
output ranks at the very top of human-preference arenas, terminal-driving
near Opus level, built for long-running agentic jobs, 1M context. The
default substitute for the Opus slot on implementation. Route: frontend/UI
builds (its standout), multi-file feature implementation, terminal-heavy
work (build/CI wrangling, environment surgery), repo-scale refactors, any
long agentic run where premium tokens would bleed. Pair its judgment-heavy
output with a cross-family verifier. Keep `opus` for: safety-adjacent
changes, subtle concurrency/API-design taste, and work where a review cycle
costs more than the model delta.

**`kimi` — Kimi K3.** 1M context with huge output ceiling, native vision,
frontier-level agentic knowledge work, strong long-horizon repo navigation.
Caveats that shape routing: slow, verbose, priciest of the gateway set, and
overly proactive on ambiguous tasks — tight scope fences and the
standing-orders block are mandatory, and its reports need an explicit length
cap. Route: the large-context delegate slot (whole-repo digests, giant logs,
cross-cutting audits that fit nowhere else), screenshot-in-the-loop UI
verification (it reads images — the only gateway route that does),
long-horizon multi-file campaigns, research/knowledge-work synthesis.
Prefer it as analyst/verifier over bulk implementer.

**GLM vs Kimi — the overlap.** Both excel at frontend engineering and
long-horizon agentic coding over big repos. Tie-breakers: building → `glm`
(cheaper, faster, terminal-native). Needs vision, a truly giant read, or a
synthesis/verdict deliverable → `kimi`. They are also each other's ideal
adversarial pair: `glm` implements the UI, `kimi` refutes it from
screenshots — different families, uncorrelated blind spots.

**`ds-pro-max` — DeepSeek V4 Pro, max thinking.** Highly technical,
solidly engineering-minded. The budget engineer: backend implementation with
real design content — algorithms, data-structure work, invariant-preserving
refactors, debugging from logs and stack traces, perf work against
measurements, technical verification of backend done-claims. Below
`glm`/`opus` in breadth and taste; above everything cheaper in depth. If a
task needs thinking AND taste, split it: taste into the brief, thinking to
`ds-pro-max`.

**`ds-pro` — DeepSeek V4 Pro, thinking disabled.** A cheap, incredibly
competent instruct model — crisp instruction-following with no deliberation
latency. Route: mechanical recon (file maps, symbol traces, config
inventories), distillation duty (see offload doctrine), doc drafts from an
outline, format conversions, commit/PR prose, high-volume single-concern
sweeps, first-draft duty. The workhorse for "do exactly this, quickly".

**`ds-flash` — DeepSeek V4 Flash, max thinking.** Near-free and
surprisingly competent — but ONLY under granular, well-formulated
instructions. The skill's brief discipline is exactly what makes this route
safe: fix-point map, worked example, runnable acceptance criteria, scope
fences. Route: backend/utility lifting — glue code, scripts, test
scaffolding and fixture generation, data munging, log parsing, bulk
semi-mechanical edits one notch above template work, churn (lint fixes,
deprecation sweeps). Hard precondition: errors must be mechanically
detectable (tests/linters/type-checks), because at this price the loop is
dispatch → check → amended retry, not careful first passes. Never: ambiguous
scope, judgment-surfaced errors, anything where the brief says "use your
judgment".

**`sonnet` / `haiku` / `opus` — where Anthropic tiers still win.**
`sonnet`: recon that requires judgment about what MATTERS (architecture
assessment, risk triage), verifier duty on judgment claims, single-concern
fixes needing taste. `haiku`: template-mechanical edits with a worked
example where speed beats everything. `opus`: the escalation tier — subtle
multi-file correctness, security-sensitive diffs, UI fidelity where GLM's
attempt missed, arbitration-grade second opinions.

## Offload doctrine — spend Anthropic tokens on judgment only

The gateway pool is cheap enough that the question inverts: not "is this
task cheap enough to route down?" but "what, exactly, justifies routing this
UP?" Anthropic session/weekly budget is reserved for judgment; everything
retryable defaults to the gateway. Patterns:

1. **Default-down, verify, escalate.** When errors are mechanically
   detectable, start one tier below instinct. A failed `ds-flash` attempt
   plus an amended retry still costs a fraction of one premium first-pass —
   the escalation ladder is the safety net, so use it as the plan, not the
   exception.
2. **Draft-then-polish.** `ds-pro`/`ds-flash` writes the first draft
   (code, doc, test suite); a higher tier reviews and patches the DELTA.
   Reviewing a 90%-right draft spends a fraction of the tokens that
   authoring from scratch does — the premium model's output is a diff, not
   a file.
3. **Speculative N-way drafts.** At near-free prices, dispatch 2–3 parallel
   `ds-flash`/`ds-pro` attempts with differently-angled briefs on a hard-ish
   task; a cheap judge (or the acceptance battery) picks the survivor.
   Escalate to premium only if all fail. Sampling beats escalating.
4. **The distillation shield.** NOTHING bulky enters the main context raw.
   Oversized reads, verbose logs, giant diffs route through `ds-pro` (or
   `kimi` when >`ds-pro`-practical) with a report-shape mandate; the main
   agent reads the digest. This converts main-context input tokens — the
   most expensive tokens in the session — into near-free gateway tokens.
5. **Cheap verifier panels for mechanical claims.** Three `ds-flash`
   refuters with different attack angles cost less than one Sonnet verifier
   and are harder to rubber-stamp past. Reserve Sonnet/`kimi` verification
   for judgment claims (design fidelity, UX, security posture).
6. **Battery-and-churn duty.** Test runs, lint sweeps, fixture regeneration,
   rebase mechanics, changelog assembly: `ds-flash`, always, no deliberation.
7. **Brief-prep pre-digestion.** `ds-pro` assembles the RAW MATERIAL for
   briefs — candidate fix-point tables, current-state inventories — which
   the main agent then curates and decides over. The lead spends judgment,
   not transcription.

The quality floor is non-negotiable: offloading rides on verification, so a
cheap implementation is only "done" when its acceptance battery and (for
judgment work) cross-family refutation pass — the same bar premium output
faces. If a route's failure rate on a task class makes the retry loop cost
more than the tier above, that's evidence, not doctrine — up-tier and note
it in the ledger.

## Cross-family verification pairings

Same-family review shares training biases; route verifiers across families:

| Implementer | Preferred refuter |
|---|---|
| `glm` (frontend/UI) | `kimi` with screenshots |
| `glm` (backend/feature) | `ds-pro-max` or `sonnet` |
| `ds-pro-max` / `ds-flash` (backend) | `sonnet`, or `glm` for terminal-verifiable claims |
| `opus` (critical) | `kimi` or `glm` second-read + main-agent spot-check |
| `kimi` (analysis/synthesis) | `ds-pro` fact-check against sources, main agent arbitrates |
