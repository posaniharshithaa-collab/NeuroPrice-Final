# NeuroPrice — Phase 1 LOCKED (Engine v2)
*No further changes to formulas, validation, or scenario logic without reopening this document.*

## Locked formulas

```
psych_norm            = composite_score / 10
effective_elasticity  = price_elasticity × (1 − psychology_weight × psych_norm)

Scenario prices (FIXED, independent of psychology):
  Conservative = current_price
  Base         = current_price × 1.05
  Aggressive   = current_price × 1.10

D0                     = estimated_market_size × conversion_rate
demand(P)              = D0 × (P / current_price) ^ effective_elasticity
revenue(P)             = P × demand(P)
contribution(P)        = (P − variable_cost) × demand(P)
conversion(P)          = demand(P) / estimated_market_size
```

## Locked validation rules
- `variable_cost >= current_price` → reject
- `conversion_rate` outside (0, 1] → reject
- `estimated_market_size <= 0` → reject
- `price_elasticity >= 0` → reject (no Veblen-good handling in v1)
- `psychology_weight` outside [0, 1] → reject
- `customer_segment` is descriptive context only — never silently overrides a user-supplied `price_elasticity` (verified by integration test)

## Locked labels
- No "optimal price" field, anywhere. Output is a `modeled_range` (low/high) plus three named, labeled scenarios.
- "Risk" → `adjustment_level` (`None` / `Moderate` / `High`), tied directly to the fixed scenario band, not derived from psychology or elasticity.

## Sensitivity sweep — findings (25-point grid: psychology_weight ∈ [0, 0.8], price_elasticity ∈ [−2.0, −0.4])

| Finding | Detail |
|---|---|
| Aggressive wins in 22/25 cells | The recommendation is robust across most of the plausible elasticity range |
| Recommendation flips only at high elasticity magnitude + low psychology weight | At `elasticity ≤ −1.6` combined with `psychology_weight ≤ 0.2`, the winner shifts to Conservative or Base — i.e., for genuinely price-sensitive categories with weak persuasive copy, the model correctly pulls back from recommending a price increase |
| Two flip points identified in the base grid | `psychology_weight=0.0`: Conservative→Base at elasticity −2.0→−1.6, then Base→Aggressive at −1.6→−1.2. `psychology_weight=0.2`: Conservative→Aggressive at −2.0→−1.6 |

**Interview line:** *"Before introducing AI, I tested how sensitive the financial recommendation was to the assumptions driving it — the model only recommends caution in the specific region where elasticity is high and persuasion signal is weak, which matches economic intuition rather than just always pushing price up."*

## Explicitly out of scope for v1 (unchanged from data contract)
- No elasticity estimation from real data
- No competitor reaction or demand saturation modeling
- No validation of psychology scores against real behavioral outcomes
- No downward-pricing scenarios (negative psychology signal → price decrease)

## What's NOT locked yet (Phase 2+)
- Gemini prompt design and evidence enforcement
- FastAPI request/response wiring
- Frontend

Phase 1 is closed. Nothing above changes without a documented reason.
