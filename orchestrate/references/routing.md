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
  they aren't installed — fall back to Claude tiers and note it. Passing a
  Claude tier name (e.g. `sonnet`) as `subagent_type` fails with
  "Agent type not found" — Claude tiers are `model` values, not agent types.
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
| `opus` | Claude Opus | prepaid (Anthropic) | correctness-critical judgment implementation |
| `glm` | GLM 5.2 | marginal cash | frontend/UI ceiling, long agentic runs, repo-scale refactors |
| `kimi` | Kimi K3 | marginal cash | large-context / vision / synthesis specialist |
| `sonnet` | Claude Sonnet | prepaid (Anthropic) | DEFAULT: recon, context building, distillation, single-concern fixes, verification |
| `ds-pro-max` | DeepSeek V4 Pro, max thinking | marginal cash | technical authoring, engineering critique, fresh-perspective seat |
| `ds-pro` | DeepSeek V4 Pro, thinking off | marginal cash — RESERVE | bulk instruct work under Anthropic quota pressure |
| `ds-flash` | DeepSeek V4 Flash, max thinking | marginal cash — RESERVE | high-volume mechanical work under Anthropic quota pressure |
| `haiku` | Claude Haiku | prepaid (Anthropic) | template-mechanical sweeps |

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
`ds-pro-max`. Named strength: authoring technical code and supplying a
fresh, engineering-focused perspective — including critiquing a design
authored by another model BEFORE implementation begins. A different
lineage catches what same-family review cannot; this is its clearest case
for a gateway dispatch over a prepaid Sonnet.

**`ds-pro` — DeepSeek V4 Pro, thinking disabled.** A cheap, incredibly
competent instruct model — crisp instruction-following with no deliberation
latency. Route: mechanical recon (file maps, symbol traces, config
inventories), distillation duty, doc drafts from an outline, format
conversions, commit/PR prose, high-volume single-concern sweeps, first-draft
duty. The workhorse for "do exactly this, quickly". RESERVE under the
corrected economics (see spend doctrine): this default-recon and
distillation duty now belongs to prepaid Sonnet; dispatch `ds-pro` only when
Anthropic quota is under pressure.

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
judgment". RESERVE under the corrected economics (see spend doctrine): its
mechanical-churn duty defaults to prepaid Sonnet; dispatch `ds-flash` only
when Anthropic quota is under pressure.

**`sonnet` / `haiku` / `opus` — where Anthropic tiers still win.**
`sonnet`: recon that requires judgment about what MATTERS (architecture
assessment, risk triage), verifier duty on judgment claims, single-concern
fixes needing taste. `haiku`: template-mechanical edits with a worked
example where speed beats everything. `opus`: the escalation tier — subtle
multi-file correctness, security-sensitive diffs, UI fidelity where GLM's
attempt missed, arbitration-grade second opinions.

## Spend doctrine — three currencies

Three budgets, not one: **prepaid Anthropic capacity** (Sonnet/Opus draw on
session and weekly limits already paid for — unspent capacity is wasted
capacity, and the marginal cost of using Sonnet to read files or build
context is zero); **the Fable weekly allowance** (the genuinely scarce
Anthropic resource, conserved for the lead/judgment seat); **marginal cash**
(DeepSeek, GLM, and Kimi bill real dollars per token through the gateway).

**Commodity work goes to prepaid capacity. Cash buys differentiation, never
volume.** The test for every gateway dispatch: what does this route provide
that a prepaid Sonnet does not? Valid answers: a different engineering
lineage that produces different solutions and different failure modes
(`ds-pro-max`); a frontend/UI ceiling above the prepaid tier (`glm`); 1M
context or vision (`kimi`); uncorrelated blind spots in an adversarial
panel; throughput when Anthropic rate limits are the binding constraint.
Invalid answer: "it is cheaper" — cheaper than free is not a thing.

**State-dependent clause.** When Anthropic session or weekly limits ARE
under pressure, the old offload logic reactivates: gateway models absorb
volume until pressure eases. This doctrine is conditional on quota state,
not absolute — check quota state before assuming the default holds.

Patterns that remain valid, re-anchored to the corrected economics:

1. **Draft-then-polish.** A lower tier writes the first draft (code, doc,
   test suite); a higher tier reviews and patches the DELTA. Reviewing a
   90%-right draft spends a fraction of the tokens that authoring from
   scratch does — the reviewing model's output is a diff, not a file.
2. **The distillation shield.** NOTHING bulky enters the main context raw.
   Oversized reads, verbose logs, giant diffs route through Sonnet (prepaid,
   the new default) with a report-shape mandate — `kimi` when the material
   exceeds Sonnet-practical (giant logs, whole-repo digests). This converts
   main-context input tokens — the most expensive tokens in the session —
   into tokens already paid for.
3. **Cross-family sampling for diversity.** Dispatch 2–3 parallel attempts
   on a hard-ish task, each from a DIFFERENT model family, with
   differently-angled briefs; a verifier (or the acceptance battery) picks
   the survivor. The point is diversity of failure mode, not price — three
   same-family attempts buy nothing a single attempt didn't already risk.
4. **Mixed-family verifier panels.** Refuters from a different family than
   the implementer, and from each other, catch what same-family review
   rubber-stamps past. Cross-family disagreement is the high-signal event;
   agreement ACROSS families is far stronger evidence than agreement within
   one.
5. **Battery-and-churn duty.** Test runs, lint sweeps, fixture regeneration,
   rebase mechanics, changelog assembly: Sonnet by default (prepaid, no
   deliberation needed); `ds-flash` only when Anthropic quota is under
   pressure.
6. **Brief-prep pre-digestion.** Sonnet assembles the RAW MATERIAL for
   briefs — candidate fix-point tables, current-state inventories — which
   the main agent then curates and decides over; `ds-pro` only when quota is
   under pressure. The lead spends judgment, not transcription.

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
