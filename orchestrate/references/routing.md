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

Ordered by budget tier: the two DEFAULT routes first (subscription capacity
for judgment, `ds-flash` for fully-specifiable execution), then the
DELIBERATE SPEND routes bought only when they earn their cash cost.
"Session model" = whatever runs this session; routing to your own tier buys
parallelism, not capability.

| Agent type | Model / thinking | Cost class | Slot |
|---|---|---|---|
| `sonnet` | Claude Sonnet | expendable (Anthropic subscription) | DEFAULT: judgment-bearing work — recon, context building, distillation, single-concern fixes, verification |
| `ds-flash` | DeepSeek V4 Flash, max thinking | pennies (cash) | DEFAULT for fully-specifiable work: high-volume mechanical work under a granular, exact brief |
| `opus` | Claude Opus | expendable (Anthropic subscription) | correctness-critical judgment implementation |
| `haiku` | Claude Haiku | expendable (Anthropic subscription) | template-mechanical sweeps |
| `glm` | GLM 5.2 | real cash — DELIBERATE SPEND | frontend/UI ceiling, long agentic runs, repo-scale refactors |
| `kimi` | Kimi K3 | real cash — DELIBERATE SPEND | large-context / vision / synthesis specialist |
| `ds-pro-max` | DeepSeek V4 Pro, max thinking | real cash — DELIBERATE SPEND | technical authoring, engineering critique, fresh-perspective seat |
| `ds-pro` | DeepSeek V4 Pro, thinking off | real cash — DELIBERATE SPEND | bulk instruct work when subscription capacity is exhausted |

## Dossiers — what each route is FOR

**`glm` — GLM 5.2.** The strongest open coding/agentic model; frontend
output ranks at the very top of human-preference arenas, terminal-driving
near Opus level, built for long-running agentic jobs, 1M context. A capable
substitute for the Opus slot on implementation. Route: frontend/UI builds
(its standout), multi-file feature implementation, terminal-heavy work
(build/CI wrangling, environment surgery), repo-scale refactors, any long
agentic run where the deliverable needs its ceiling. Pair its judgment-heavy
output with a cross-family verifier. Keep `opus` for: safety-adjacent
changes, subtle concurrency/API-design taste, and work where a review cycle
costs more than the model delta. Deliberate spend: pay for `glm` when the
task genuinely needs its frontend/UI ceiling or its long-agentic-run
throughput — not as a default implementer; Sonnet is the default now.

**`kimi` — Kimi K3.** 1M context with huge output ceiling, native vision,
frontier-level agentic knowledge work, strong long-horizon repo navigation.
Caveats that shape routing: slow, verbose, priciest of the gateway set, and
overly proactive on ambiguous tasks — tight scope fences and the
standing-orders block are mandatory, and its reports need an explicit length
cap. Route: the large-context delegate slot (whole-repo digests, giant logs,
cross-cutting audits that fit nowhere else), screenshot-in-the-loop UI
verification (it reads images — the only gateway route that does),
long-horizon multi-file campaigns, research/knowledge-work synthesis.
Prefer it as analyst/verifier over bulk implementer. Deliberate spend: pay
for `kimi` when 1M context, native vision, or a synthesis/verdict
deliverable is the actual requirement — not as a default recon route.

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
for a gateway dispatch over Sonnet. Deliberate spend: pay for `ds-pro-max`
when a different engineering lineage or thinking-heavy technical critique is
the actual requirement — not for routine backend work Sonnet can do.

**`ds-pro` — DeepSeek V4 Pro, thinking disabled.** A cheap, incredibly
competent instruct model — crisp instruction-following with no deliberation
latency. Route: mechanical recon (file maps, symbol traces, config
inventories), distillation duty, doc drafts from an outline, format
conversions, commit/PR prose, high-volume single-concern sweeps, first-draft
duty. The workhorse for "do exactly this, quickly" when the work also needs
some instruction-following judgment `ds-flash` shouldn't be trusted with.
Deliberate spend under the corrected economics (see spend doctrine): this
recon and distillation duty now belongs to Sonnet by default; dispatch
`ds-pro` when subscription capacity is exhausted, not as a routine default.

**`ds-flash` — DeepSeek V4 Flash, max thinking.** Promoted to a DEFAULT
workhorse under the corrected economics (see spend doctrine): near-free and
surprisingly competent, it is the one cash-billed route worth paying for
because it buys enormous throughput for pennies. That promotion has a
precondition, not a suspension, of the old caution — it holds ONLY under
granular, well-formulated instructions. The skill's brief discipline is
exactly what makes this route safe, and is now the precondition for
defaulting to it: fix-point map, worked example, runnable acceptance
criteria, scope fences. Route: backend/utility lifting — glue code, scripts,
test scaffolding and fixture generation, data munging, log parsing, bulk
semi-mechanical edits one notch above template work, churn (lint fixes,
deprecation sweeps). Hard precondition: errors must be mechanically
detectable (tests/linters/type-checks), because at this price the loop is
dispatch → check → amended retry, not careful first passes. Hard limit,
absolute, unchanged by the promotion: it supplies no creativity and no
taste. Never: ambiguous scope, judgment-surfaced errors, anything where the
brief says "use your judgment" — those stay on Sonnet regardless of quota
state. Given granular, completely specified instructions it performs far
above its price; given ambiguity it fails.

**`sonnet` / `haiku` / `opus` — where Anthropic tiers still win.**
`sonnet`: recon that requires judgment about what MATTERS (architecture
assessment, risk triage), verifier duty on judgment claims, single-concern
fixes needing taste. `haiku`: template-mechanical edits with a worked
example where speed beats everything. `opus`: the escalation tier — subtle
multi-file correctness, security-sensitive diffs, UI fidelity where GLM's
attempt missed, arbitration-grade second opinions.

## Spend doctrine — the budget hierarchy

Four levels, not three, and they are not interchangeable:

1. **The Fable weekly allowance** — the premium resource. Lead and judgment
   seat only. Never spent on execution.
2. **Anthropic subscription capacity** (Opus, Sonnet, Haiku) — expendable.
   Already paid for, wasted if unspent, zero marginal cost. The default pool
   for anything needing judgment, taste, or creativity.
3. **`ds-flash`** — the one cash-billed route worth paying for. It bills
   real money but so little that it buys enormous throughput for pennies.
   Its job: absorb fully-specifiable work so subscription capacity stays
   free for what only Anthropic tiers can do. Hard limit: it supplies no
   creativity and no taste. Given granular, completely specified
   instructions it performs far above its price; given ambiguity it fails.
4. **`glm`, `kimi`, `ds-pro`, `ds-pro-max`** — all bill real money at real
   rates. Deliberate occasional spends, NOT defaults. Reach for them when
   subscription capacity is exhausted, or when cross-family adversarial
   diversity is genuinely the point of the task.

**Specify it and send it to flash; judge it and keep it on Anthropic; pay
the others only when they are genuinely the point.**

The second key idea: brief specificity is the lever that moves work onto
the pennies route. Main-agent effort spent making a brief exact converts
expensive execution into cheap execution without touching quality. The
guardrail is absolute — where work genuinely needs creativity or taste,
specifying harder is the WRONG move; route it to an Anthropic tier and keep
the output quality. Invalid answer for reaching past `ds-flash` into
DELIBERATE SPEND territory: "it is cheaper" — cheaper than free (subscription
capacity) is not a thing, and cheaper-than-Anthropic-cash is not a reason to
skip the pennies route either.

Patterns that remain valid, re-anchored to the corrected hierarchy:

1. **Draft-then-polish.** `ds-flash` drafts the first pass (code, doc, test
   suite) from a fully-specified brief; an Anthropic tier reviews and
   patches the DELTA. Reviewing a 90%-right draft spends a fraction of the
   tokens that authoring from scratch does — the reviewing model's output is
   a diff, not a file.
2. **The distillation shield.** NOTHING bulky enters the main context raw.
   Oversized reads, verbose logs, giant diffs route through Sonnet
   (subscription capacity, the default) with a report-shape mandate —
   `kimi` (deliberate spend) when the material exceeds Sonnet-practical
   (giant logs, whole-repo digests). This converts main-context input
   tokens — the most expensive tokens in the session — into tokens already
   paid for.
3. **Speculative N-way sampling.** `ds-flash` is cheap enough that
   dispatching several parallel attempts at one fully-specified task is now
   routine, not a splurge — a verifier or the acceptance battery picks the
   survivor. Reserve cross-family N-way sampling (2-3 attempts from
   DIFFERENT model families, differently-angled briefs) for when diversity
   of failure mode across training lineages is the actual point; that
   variant is a deliberate cash spend, not the routine case.
4. **Mixed-family verifier panels.** Refuters from a different family than
   the implementer, and from each other, catch what same-family review
   rubber-stamps past. Deliberate spend — justified when cross-family
   disagreement is the actual signal sought; agreement ACROSS families is
   far stronger evidence than agreement within one.
5. **Battery-and-churn duty.** Test runs, lint sweeps, fixture regeneration,
   rebase mechanics, changelog assembly are fully-specifiable and
   mechanically checkable — exactly the `ds-flash` profile, so `ds-flash` is
   the default; fall back to Sonnet when the run needs judgment about what
   changed or ambiguity resolution.
6. **Brief-prep pre-digestion.** Sonnet assembles the RAW MATERIAL for
   briefs — candidate fix-point tables, current-state inventories — which
   the main agent then curates and decides over; this is judgment-adjacent
   curation, so it stays on Sonnet by default. `ds-pro` is a deliberate spend
   when subscription capacity is exhausted. The lead spends judgment, not
   transcription.

The quality floor is non-negotiable: offloading rides on verification, so a
cheap implementation is only "done" when its acceptance battery and (for
judgment work) cross-family refutation pass — the same bar premium output
faces. If a route's failure rate on a task class makes the retry loop cost
more than the tier above, that's evidence, not doctrine — up-tier and note
it in the ledger.

## Cross-family verification pairings

Same-family review shares training biases, so a verifier from a DIFFERENT
model family than the implementer is the PREFERRED default for judgment
work — CASH-BILLED SPEND accepted where the implementer is Anthropic-tier.
Fall back to an Anthropic-tier verifier only when cross-family capacity is
unavailable, not as the routine choice:

| Implementer | Preferred refuter |
|---|---|
| `glm` (frontend/UI) | `sonnet` by default; `kimi` with screenshots (deliberate spend) when independence from GLM's lineage on a UI-fidelity claim is the actual point |
| `glm` (backend/feature) | `sonnet` by default; `ds-pro-max` (deliberate spend) when a different engineering lineage is the actual point |
| `ds-pro-max` / `ds-flash` (backend) | `sonnet` by default |
| `opus` (critical) | `kimi` or `glm` refuter by default (cash-billed, deliberate spend) — independence from Opus's Anthropic lineage is the point; `sonnet` second-read + main-agent spot-check as fallback only when cross-family capacity is unavailable |
| `kimi` (analysis/synthesis) | `sonnet` fact-check against sources by default; `ds-pro` (deliberate spend) when independence from Sonnet's lineage is the actual point, main agent arbitrates |
