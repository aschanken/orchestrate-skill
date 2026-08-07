# Routing reference — model dossiers, offload doctrine, mechanics

Read once per session, at first dispatch.

## Benchmark anchors (Artificial Analysis Intelligence Index v4.1, read 2026-08-01)

One scale, one date, so dossier claims stay calibrated. Re-verify when a
listed model ships a new checkpoint — dated observations rot.

| Model (route) | AA Index | Cash price in/out per 1M | Notes |
|---|---|---|---|
| Claude Opus 5 (`opus`) | 61 | subscription | top of the pool |
| Claude Fable 5 (session) | 60 | weekly allowance | the judgment seat |
| Kimi K3 (`kimi`) | 57 | real rates | top open-weights; vision; slow |
| Claude Sonnet 5 (`sonnet`) | 53 | subscription | |
| GLM 5.2 (`glm`) | 51 | real rates | frontend/agentic arena strength |
| DeepSeek V4 Flash 0731 (`ds-flash`) | 50 | $0.14 / $0.28; cache hit $0.003 | 1M ctx; text-only; verbose (~2× median output tokens) |
| DeepSeek V4 Pro (`ds-pro-max`) | 44 | $0.435 / $0.87 | outbenchmarked by Flash 0731 at 3× its price |
| Claude Haiku 4.5 (`haiku`) | 24 | subscription | fast (≈88 t/s), 200k ctx |

The load-bearing fact: **Flash 0731 (released 2026-07-31) benchmarks at
GLM level, three points under Sonnet 5, double Haiku — at 1/35th of
Sonnet's output price and with near-free cache reads.** The index measures
reasoning benchmarks, not taste, agentic reliability, or instruction
economy — treat it as a floor-raiser for CHECKABLE work, not a license to
route taste or safety work down.

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
  `ds-pro`/`ds-pro-max` and `ds-flash-lite`/`ds-flash` are pairs of agent
  types over one model each.
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

Ordered by budget tier: the pennies pool first (the volume default since
Flash 0731), then subscription capacity (finite weekly headroom, reserved
for what the pennies pool cannot hold), then the DELIBERATE SPEND routes
bought only when they earn their cash cost. "Session model" = whatever runs
this session; routing to your own tier buys parallelism, not capability.

| Agent type | Model / thinking | Cost class | Slot |
|---|---|---|---|
| `ds-flash` | DeepSeek V4 Flash 0731, max thinking | pennies (cash) | DEFAULT for checkable work, specified OR judgment-adjacent: implementation under an exact brief, recon, distillation shield, refute-verification, campaign mid-orchestration |
| `ds-flash-lite` | DeepSeek V4 Flash 0731, thinking off | pennies (cash) | grunt tier: fast instruct sweeps, format conversions, fixture generation, report collection — no deliberation latency |
| `sonnet` | Claude Sonnet | subscription (finite weekly headroom) | taste-bearing judgment: ambiguity resolution, UX/API-surface taste, creative work, arbitration support; first escalation when flash fails |
| `opus` | Claude Opus | subscription (finite weekly headroom) | correctness-critical or safety-adjacent implementation; arbitration-grade second opinions |
| `haiku` | Claude Haiku | subscription (finite weekly headroom) | speed-critical mechanical sweeps (≈88 t/s beats flash wall-clock); grunt duty when preserving cash spend matters more than preserving headroom |
| `glm` | GLM 5.2 | real cash — DELIBERATE SPEND | frontend/UI ceiling, long agentic runs, repo-scale refactors |
| `kimi` | Kimi K3 | real cash — DELIBERATE SPEND | large-context / vision / synthesis specialist |
| `ds-pro-max` | DeepSeek V4 Pro, max thinking | real cash — DELIBERATE SPEND | knowledge-heavy or robustness-sensitive technical work where 49B-active depth beats Flash's 13B; intra-family second opinion |
| `ds-pro` | DeepSeek V4 Pro, thinking off | real cash — DELIBERATE SPEND | legacy instruct seat — `ds-flash-lite` supersedes it at a third of the price; keep for instruct robustness when flash-lite output disappoints |

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
throughput — not as a default implementer; `ds-flash` (checkable) and
Sonnet (taste) split that duty now.

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

**`ds-pro-max` — DeepSeek V4 Pro, max thinking.** Demoted by its own
sibling: Flash 0731 outbenchmarks it (50 vs 44) at a third of the price,
so "budget engineer" is no longer its case — `ds-flash` is. What survives:
1.6T total / 49B active parameters against Flash's 284B/13B, which buys
world knowledge, robustness, and depth the index underweights. Route:
knowledge-heavy technical work (unfamiliar protocols, obscure APIs,
domain-dense debugging), an intra-DeepSeek second opinion when a flash
attempt looks subtly off, and design critique where parameter depth beats
reasoning-benchmark parity. Deliberate spend, and a shrinking one — when
in doubt, flash first.

**`ds-pro` — DeepSeek V4 Pro, thinking disabled.** Legacy seat.
`ds-flash-lite` now covers the fast-instruct duty band at a third of the
price. Keep `ds-pro` as the fallback when flash-lite's instruct quality
disappoints on a task class (bigger active parameters, steadier
instruction-following) — a targeted substitution, never a default.

**`ds-flash` — DeepSeek V4 Flash 0731, max thinking.** Re-promoted on the
0731 checkpoint (released 2026-07-31): AA Index 50 — GLM-level, three
points under Sonnet 5, double Haiku — at $0.14/$0.28 per 1M and $0.003
cache hits. The old dossier's "no judgment ever" rule is obsolete; the new
boundary is **checkability, not judgment**. Flash now holds two duty bands:

1. *Specified execution (unchanged):* glue code, scripts, test scaffolding,
   data munging, bulk semi-mechanical edits, churn — under the full brief
   discipline (fix-point map, worked example, runnable acceptance criteria).
2. *Checkable judgment duty (new):* recon with judgment about what matters,
   context-packet assembly for implementers (start from `tools/codemap.py`
   output — deterministic signatures beat model paraphrase),
   distillation-shield passes, refute-verification of done-claims,
   first-draft authoring for a higher tier to polish, and mid-orchestration
   of campaigns (see SKILL.md, Delegated campaigns) — any judgment work
   whose OUTPUT the lead or a battery can check cheaply.

Its cache pricing is a structural advantage for long agentic loops: each
turn re-reads the whole context at 98% off, so a flash mid-orchestrator
iterating twenty times costs cents. Known costs: verbose (~2× median
output tokens — enforce hard report caps), reasoning latency (wall-clock
slow; use `haiku` or `ds-flash-lite` when speed matters), text-only (no
screenshots — vision verification stays on Anthropic tiers or `kimi`).
Hard limits that survive the promotion: taste, creativity, and
safety-adjacent correctness stay on Anthropic tiers — the index measures
reasoning, not aesthetics or alignment; and errors that only surface under
HUMAN judgment (UX feel, API ergonomics) are exactly the errors flash
cannot self-detect. Given a checkable deliverable it performs at
subscription-tier quality for pennies; given taste work it produces
plausible-looking wrongness.

**`ds-flash-lite` — DeepSeek V4 Flash 0731, thinking off.** The grunt
tier: same weights, no deliberation, same pennies. Route: template edits
with a worked example, format conversions, fixture generation, report
collection inside campaigns, high-volume single-concern sweeps — the duty
band `ds-pro` used to hold, at a third of its price. Escalate to full
`ds-flash` when a grunt's task turns out to need actual reasoning.
Instruct-mode quality is less benchmarked than the reasoning variant —
first failures route up to `ds-flash`, not sideways to retries.

**`sonnet` / `haiku` / `opus` — where Anthropic tiers still win.** The
subscription is finite weekly headroom, not an infinite pool — since Flash
0731, its job is the work flash structurally cannot hold, not "all
judgment". `sonnet`: taste and ambiguity — UX/API-surface judgment,
creative and user-facing writing, risk triage where what MATTERS is the
question, arbitration support, first escalation on flash failures, and any
vision-in-the-loop check (flash is text-only). `haiku`: speed-critical
mechanical sweeps — at ≈88 t/s it beats flash's reasoning latency on
wall-clock, and grunt duty on it preserves cash instead of headroom.
`opus`: the apex — safety-adjacent diffs, subtle multi-file correctness,
UI fidelity rescues, arbitration-grade second opinions.

## Spend doctrine — the budget hierarchy

Four levels, and since Flash 0731 the middle two have swapped roles:

1. **The Fable weekly allowance** — the premium resource. Lead and judgment
   seat only. Never spent on execution.
2. **The pennies pool** (`ds-flash`, `ds-flash-lite`) — the volume default.
   Bills cash, but so little that cost stops being a routing input: Index-50
   quality at 1/35th of Sonnet's output price, cache reads at 98% off. Its
   job: absorb ALL checkable work — specified execution and
   judgment-adjacent duty alike (recon, distillation, refute-verification,
   campaign mid-orchestration) — so subscription headroom survives the week.
3. **Anthropic subscription capacity** (Opus, Sonnet, Haiku) — finite
   weekly headroom, the conserved resource. Reserved for what the pennies
   pool structurally cannot hold: taste, creativity, vision,
   safety-adjacent correctness, ambiguity resolution, arbitration — and as
   the escalation tier when flash fails twice. Not hoarded to zero:
   capacity that would expire unspent is fair game for anything. But
   burning headroom on work flash does identically is the new named waste.
4. **`glm`, `kimi`, `ds-pro`, `ds-pro-max`** — real money at real rates.
   Deliberate occasional spends, NOT defaults: `glm` for its frontend and
   long-agentic ceiling, `kimi` for 1M-context/vision/synthesis,
   `ds-pro-max` for parameter-depth knowledge, `ds-pro` as a legacy
   instruct fallback.

**If its output is checkable, send it to flash; if it needs taste, vision,
or safety judgment, spend headroom on Anthropic; pay the others only when
they are genuinely the point.**

The second key idea: brief specificity is the lever that moves work onto
the pennies route — and Flash 0731 widened what the route can catch. A
fully-specified brief lands on `ds-flash-lite` or `haiku`; a
decisions-made-but-checkable brief lands on `ds-flash`; only taste-bearing
or vision work must land on Anthropic at all. The guardrail is absolute —
where work genuinely needs creativity or taste, specifying harder is the
WRONG move; route it to an Anthropic tier and keep the output quality.
Invalid answer for reaching past the pennies pool into DELIBERATE SPEND
territory: "it is cheaper" — cheaper-than-Anthropic-cash is not a reason
to skip the pennies route.

Patterns that remain valid, re-anchored to the corrected hierarchy:

1. **Draft-then-polish.** `ds-flash` drafts the first pass (code, doc, test
   suite) from a fully-specified brief; an Anthropic tier reviews and
   patches the DELTA. Reviewing a 90%-right draft spends a fraction of the
   tokens that authoring from scratch does — the reviewing model's output is
   a diff, not a file.
2. **The distillation shield.** NOTHING bulky enters the main context raw.
   Oversized reads, verbose logs, giant diffs route through `ds-flash`
   (1M context, pennies, the default since 0731) with a report-shape
   mandate and a hard length cap — Sonnet when the distillation itself
   needs taste about what matters, `kimi` when vision or a
   synthesis-grade verdict is the deliverable. This converts
   main-context input tokens — the most expensive tokens in the
   session — into pennies. Structure is even cheaper than pennies:
   `tools/codemap.py` extracts signature maps and per-file token prices
   deterministically — run it before any model reads bodies.
3. **Speculative N-way sampling.** `ds-flash` is cheap enough that
   dispatching several parallel attempts at one fully-specified task is now
   routine, not a splurge — a verifier or the acceptance battery picks the
   survivor. Reserve cross-family N-way sampling (2-3 attempts from
   DIFFERENT model families, differently-angled briefs) for when diversity
   of failure mode across training lineages is the actual point; that
   variant is a deliberate cash spend, not the routine case.
4. **Mixed-family verifier panels.** Refuters from a different family than
   the implementer, and from each other, catch what same-family review
   rubber-stamps past. Since 0731 the single-refuter case is FREE in
   practice: a `ds-flash` refuter on any Anthropic-implemented, textually
   checkable claim costs pennies — make it the default, not a splurge.
   Multi-seat panels adding `kimi`/`glm`/`ds-pro-max` remain deliberate
   spends, justified when cross-family disagreement is the actual signal
   sought; agreement ACROSS families is far stronger evidence than
   agreement within one.
5. **Battery-and-churn duty.** Test runs, lint sweeps, fixture regeneration,
   rebase mechanics, changelog assembly are fully-specifiable and
   mechanically checkable — `ds-flash-lite` profile (no reasoning needed),
   `ds-flash` when a run needs interpretation, Sonnet only when the run
   needs taste about what changed.
6. **Brief-prep pre-digestion.** `ds-flash` assembles the RAW MATERIAL for
   briefs — candidate fix-point tables, current-state inventories — which
   the main agent then curates and decides over. The output is checkable
   (the lead verifies fix-points before dispatch anyway), so it belongs on
   the pennies pool; Sonnet when the assembly itself is the judgment. The
   lead spends judgment, not transcription.
7. **Delegated campaigns.** For high-volume, boundable work-programs
   (research sweeps, N-file audits, corpus collection), a `ds-flash`
   mid-orchestrator runs the dispatch loop over grunt agents and returns
   ONE distilled deliverable — the main context receives a single report
   instead of N, and the whole subtree bills pennies. Doctrine and the
   campaign-brief protocol live in SKILL.md and dispatch.md; prefer a
   Workflow script instead when the loop structure is fully known upfront
   (deterministic beats model-managed where no adaptation is needed).

The quality floor is non-negotiable: offloading rides on verification, so a
cheap implementation is only "done" when its acceptance battery and (for
judgment work) cross-family refutation pass — the same bar premium output
faces. If a route's failure rate on a task class makes the retry loop cost
more than the tier above, that's evidence, not doctrine — up-tier and note
it in the ledger.

## Cross-family verification pairings

Same-family review shares training biases, so a verifier from a DIFFERENT
model family than the implementer is the PREFERRED default for judgment
work. Flash 0731 removed the cost argument: an Index-50 cross-family
refuter now costs pennies, so every textually-checkable judgment claim
gets one by default. Only vision claims and multi-seat panels still route
through cash-billed specialists:

| Implementer | Preferred refuter |
|---|---|
| `sonnet` / `opus` / `haiku` (any text-checkable claim) | `ds-flash` by default — cross-family at pennies; add `sonnet` as a second refuter on critical claims (double refutation still costs ~nothing) |
| `opus` (safety-adjacent / critical) | `ds-flash` + `kimi` or `glm` (deliberate spend) — two independent non-Anthropic lineages; main-agent spot-check on top |
| `ds-flash` / `ds-flash-lite` (execution) | the acceptance battery for mechanical claims; `sonnet` (cross-family, subscription) for judgment-adjacent output |
| `glm` (frontend/UI) | `sonnet` with screenshots by default (flash is text-only); `kimi` (deliberate spend) when independence from BOTH lineages on a UI-fidelity claim is the point |
| `glm` (backend/feature) | `ds-flash` by default; `ds-pro-max` (deliberate spend) when parameter-depth critique is the point |
| `kimi` (analysis/synthesis) | `ds-flash` fact-check against sources by default; main agent arbitrates disagreements |
