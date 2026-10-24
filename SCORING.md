# VentureRadar Scoring

Deterministic Python only. LLMs draft factor scores; they never emit the final numbers.

Founder-market fit is a **separate** score and ranking mode. It is never blended into market scores.

## Factor weights (`scoring_version=2`)

| Criterion | Weight |
|---|---:|
| Problem severity | 0.20 |
| Willingness to pay | 0.20 |
| Market potential | 0.15 |
| Existing solution dissatisfaction | 0.10 |
| Competitive opportunity | 0.10 |
| Customer accessibility | 0.10 |
| Growing demand | 0.10 |
| MVP feasibility | 0.05 |

Sum = 1.00.

Each factor: `score` 1–5 or `null`, `status` scored | unresearched | unknown, evidence, contradictions, confidence, missing, explanation. Unknown stays `null`. Never impute 3.

## Rubrics (1–5)

**Problem severity** — 1 rare annoyance; 2 mild friction; 3 recurring pain that people work around; 4 stated hours/money lost; 5 blocking or urgent buyer language. Score only from stated evidence.

**Willingness to pay** — 1 no budget / refuse to pay; 2 unspecified complaint; 3 named paid tools or “too expensive”; 4 looking to buy/switch; 5 committed spend. Do not treat upvotes as WTP.

**Market potential** — Requires source-backed research (Tavily). Otherwise `unresearched`. Never invent TAM.

**Existing solution dissatisfaction** — 1 current tools work; 2 mixed; 3 workarounds dominate; 4 explicit hate/switch intent; 5 abandoned alternatives. Negative evidence lowers the score.

**Competitive opportunity** — Requires named alternatives plus gaps, or Tavily sources. Otherwise `unresearched`. No invented prices.

**Customer accessibility** — 1 unreachable; 2 obscure; 3 identifiable communities; 4 public buyer-dense communities; 5 clear outbound path. Social presence alone is not distribution proof.

**Growing demand** — Uses normalized `observation_rate` on comparable periods only. If incomparable: `unknown`, not 3.

**MVP feasibility** — 1 research-heavy; 3 standard SaaS; 5 tiny script/wrapper for the default founder profile. This is implementation difficulty, not founder fit.

## Three stored metrics

```
known = factors with score != null
known_weight = sum(weights of known)
research_completeness = known_weight / 1.00

if known_weight == 0:
    observed_quality_score = null
    conservative_score = null
else:
    observed_quality_score = sum((score_i/5)*w_i for known) / known_weight * 100
    conservative_score = sum((score_i/5)*w_i for known) * 100
```

- **Observed quality** — normalized weighted average of evaluated factors.
- **Research completeness** — percent of total weight that was scored.
- **Conservative score** — non-renormalized sum; unknowns contribute 0. This is a **heuristic**, not a statistically established lower bound (`conservative_score_kind=heuristic`).

Also store separately: `evidence_confidence` (0–1), `founder_fit_score` (0–100), `research_status`.

## Ranking

**Verified** (“Highest opportunity”) requires all of:

- `research_completeness >= 0.70`
- `evidence_confidence >= 0.60`
- quality status `passed` or `passed_with_limitations`
- not rejected

**Provisional** opportunities remain discoverable in all-ideas, provisional, and recently-discovered views. Missing research does not discard them.

Other modes: highest confidence, best founder fit, fastest-growing (comparable trends only), recently discovered, strongest commercial evidence.

## Founder fit (separate)

Default profile: software engineer, Python/TS, AI/LLM, SaaS/agents/automation/B2B, India-based with global customers. Score 0–100 from overlap with target customer, stack, and domain. Display beside market scores; never add it into them.
