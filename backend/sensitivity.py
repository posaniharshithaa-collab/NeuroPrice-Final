"""
NeuroPrice — Sensitivity Sweep (Phase 1, Step 1 of the final sequence)

Answers: "What happens if your elasticity assumption is wrong, or the
psychology weight was set differently?" — by actually running the model
across a grid instead of asserting it's robust.

Still zero AI calls. composite_score is passed in as a plain float,
exactly like the engine expects.
"""

from dataclasses import dataclass
from pricing_engine import ProductEconomics, ModelingControl, run_scenarios


@dataclass
class SweepPoint:
    psychology_weight: float
    price_elasticity: float
    winner: str                  # which scenario has the highest contribution
    conservative_contribution: float
    base_contribution: float
    aggressive_contribution: float


def sweep(
    econ_template: ProductEconomics,
    composite_score: float,
    psychology_weights: list[float],
    elasticities: list[float],
) -> list[SweepPoint]:
    """Full grid sweep over psychology_weight x price_elasticity.

    econ_template's own price_elasticity is ignored here — we override it
    per grid point — everything else (price, cost, conversion, market size)
    stays fixed so the sweep isolates exactly two variables at a time.
    """
    results = []

    for pw in psychology_weights:
        for elas in elasticities:
            econ = ProductEconomics(
                current_price=econ_template.current_price,
                variable_cost=econ_template.variable_cost,
                conversion_rate=econ_template.conversion_rate,
                estimated_market_size=econ_template.estimated_market_size,
                price_elasticity=elas,
                customer_segment=econ_template.customer_segment,
            )
            control = ModelingControl(psychology_weight=pw)
            out = run_scenarios(econ, control, composite_score=composite_score)

            by_name = {s["name"]: s["contribution"] for s in out["scenarios"]}
            winner = max(by_name, key=by_name.get)

            results.append(SweepPoint(
                psychology_weight=pw,
                price_elasticity=elas,
                winner=winner,
                conservative_contribution=by_name["Conservative"],
                base_contribution=by_name["Base"],
                aggressive_contribution=by_name["Aggressive"],
            ))

    return results


def find_winner_flip_points(results: list[SweepPoint]) -> list[tuple[SweepPoint, SweepPoint]]:
    """Within each psychology_weight row, walk elasticities in order and
    report every adjacent pair where the winning scenario changes. This is
    the exact evidence for 'here is where the recommendation flips.'"""
    flips = []
    by_weight: dict[float, list[SweepPoint]] = {}
    for r in results:
        by_weight.setdefault(r.psychology_weight, []).append(r)

    for pw, rows in by_weight.items():
        rows_sorted = sorted(rows, key=lambda r: r.price_elasticity)  # most negative -> least
        for a, b in zip(rows_sorted, rows_sorted[1:]):
            if a.winner != b.winner:
                flips.append((a, b))

    return flips


def print_sweep_table(results: list[SweepPoint]) -> None:
    header = f"{'psych_w':>8} {'elasticity':>11} {'Conservative':>14} {'Base':>12} {'Aggressive':>12}   winner"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r.psychology_weight:>8.2f} {r.price_elasticity:>11.2f} "
              f"{r.conservative_contribution:>14,.0f} {r.base_contribution:>12,.0f} "
              f"{r.aggressive_contribution:>12,.0f}   {r.winner}")
