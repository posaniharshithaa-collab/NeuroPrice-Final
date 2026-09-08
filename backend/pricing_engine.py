"""
NeuroPrice — Deterministic Pricing Engine (v2)

This module contains ZERO calls to any AI model. It takes a psychology
composite score as a plain float input (produced elsewhere, by Gemini)
and does the rest with pure arithmetic. That separation is the point:
this file should be auditable line by line in an interview.

Locked modeling decisions (v2, per review):
  - Option A: psychology dampens elasticity. It does NOT set price.
  - Scenario prices are a FIXED band (0%, +5%, +10%), independent of
    the psychology score, to avoid psychology doing two jobs at once.
  - "Risk" is renamed "adjustment_level" — it labels the magnitude of
    the price change being modeled, not a statistical risk estimate.
"""

from dataclasses import dataclass, asdict
from typing import Literal


# ---------------------------------------------------------------------------
# Fixed, documented assumptions (v2)
# ---------------------------------------------------------------------------

SCENARIO_BANDS = {
    "Conservative": 0.00,
    "Base": 0.05,
    "Aggressive": 0.10,
}

ADJUSTMENT_LEVEL = {
    "Conservative": "None",
    "Base": "Moderate",
    "Aggressive": "High",
}

SEGMENT_DEFAULT_ELASTICITY = {
    "price_sensitive": -1.8,
    "neutral": -1.0,
    "price_insensitive": -0.5,
}


# ---------------------------------------------------------------------------
# Input contracts
# ---------------------------------------------------------------------------

@dataclass
class ProductEconomics:
    current_price: float
    variable_cost: float
    conversion_rate: float          # 0-1, at current price
    estimated_market_size: int      # traffic / addressable leads
    price_elasticity: float | None = None   # if None, use segment default
    customer_segment: Literal["price_sensitive", "neutral", "price_insensitive"] = "neutral"

    def __post_init__(self):
        if self.variable_cost >= self.current_price:
            raise ValueError("variable_cost must be < current_price (negative baseline contribution)")
        if not (0 < self.conversion_rate <= 1):
            raise ValueError("conversion_rate must be in (0, 1]")
        if self.estimated_market_size <= 0:
            raise ValueError("estimated_market_size must be > 0")
        if self.price_elasticity is not None and self.price_elasticity >= 0:
            raise ValueError("price_elasticity must be negative in v1 (no Veblen-good handling)")

    def resolved_elasticity(self) -> float:
        """Segment is descriptive context only — it fills a gap, it never
        silently overrides a user-supplied elasticity."""
        if self.price_elasticity is not None:
            return self.price_elasticity
        return SEGMENT_DEFAULT_ELASTICITY[self.customer_segment]


@dataclass
class ModelingControl:
    psychology_weight: float = 0.40   # 0-1: max fraction elasticity can be dampened

    def __post_init__(self):
        if not (0 <= self.psychology_weight <= 1):
            raise ValueError("psychology_weight must be in [0, 1]")


# ---------------------------------------------------------------------------
# Core formulas
# ---------------------------------------------------------------------------

def effective_elasticity(price_elasticity: float, psychology_weight: float, composite_score: float) -> float:
    """Option A: psychology makes demand LESS price-sensitive.
    composite_score is 0-10 (raw Gemini output); normalized internally."""
    psych_norm = composite_score / 10
    return price_elasticity * (1 - psychology_weight * psych_norm)


def demand_at_price(price: float, base_price: float, base_demand: float, elasticity: float) -> float:
    """Constant-elasticity demand curve."""
    return base_demand * (price / base_price) ** elasticity


@dataclass
class ScenarioResult:
    name: str
    price: float
    demand: float
    conversion: float
    revenue: float
    contribution: float
    adjustment_level: str


def run_scenarios(econ: ProductEconomics, control: ModelingControl, composite_score: float) -> dict:
    elasticity_in = econ.resolved_elasticity()
    eff_elasticity = effective_elasticity(elasticity_in, control.psychology_weight, composite_score)

    base_demand = econ.estimated_market_size * econ.conversion_rate  # D0

    scenarios = []
    for name, lift in SCENARIO_BANDS.items():
        price = econ.current_price * (1 + lift)
        demand = demand_at_price(price, econ.current_price, base_demand, eff_elasticity)
        revenue = price * demand
        contribution = (price - econ.variable_cost) * demand
        conversion = demand / econ.estimated_market_size

        scenarios.append(ScenarioResult(
            name=name,
            price=round(price, 2),
            demand=round(demand, 1),
            conversion=round(conversion, 4),
            revenue=round(revenue, 2),
            contribution=round(contribution, 2),
            adjustment_level=ADJUSTMENT_LEVEL[name],
        ))

    prices = [s.price for s in scenarios]

    winner = max(scenarios, key=lambda s: s.contribution)

    return {
        "assumptions": {
            "price_elasticity_used": elasticity_in,
            "elasticity_source": "user_supplied" if econ.price_elasticity is not None else f"segment_default:{econ.customer_segment}",
            "effective_elasticity": round(eff_elasticity, 4),
            "psychology_weight": control.psychology_weight,
            "composite_score": composite_score,
        },
        "scenarios": [{**asdict(s), "recommended": s.name == winner.name} for s in scenarios],
        "modeled_range": {"low": min(prices), "high": max(prices)},
        "recommended_scenario": winner.name,
    }
