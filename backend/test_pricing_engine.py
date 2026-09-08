"""
Manual sanity tests for the deterministic engine.

These aren't just unit tests — each one is worked out by hand in the
comments first, so you can defend "the model is correct" with pen-and-paper
math, not just "the tests pass."
"""

import math
import pytest
from pricing_engine import (
    ProductEconomics, ModelingControl, effective_elasticity,
    demand_at_price, run_scenarios
)


def test_effective_elasticity_matches_hand_calc():
    # By hand: psych_norm = 5.1/10 = 0.51
    # effective = -1.2 * (1 - 0.40*0.51) = -1.2 * (1 - 0.204) = -1.2*0.796 = -0.9552
    result = effective_elasticity(price_elasticity=-1.2, psychology_weight=0.40, composite_score=5.1)
    assert math.isclose(result, -0.9552, rel_tol=1e-6)


def test_effective_elasticity_zero_psychology_is_a_noop():
    # If Gemini finds nothing persuasive (score=0), elasticity must be untouched.
    result = effective_elasticity(price_elasticity=-1.2, psychology_weight=0.40, composite_score=0)
    assert result == -1.2


def test_effective_elasticity_never_flips_sign_or_overshoots():
    # Even at maximum psychology (score=10) and max weight (1.0), dampening
    # should approach but never exceed -100% of original elasticity, and
    # should never make elasticity positive (that would imply price INCREASES
    # increase demand, which is a different economic claim entirely).
    result = effective_elasticity(price_elasticity=-1.2, psychology_weight=1.0, composite_score=10)
    assert math.isclose(result, 0.0, abs_tol=1e-9)
    assert result <= 0


def test_demand_at_base_price_equals_base_demand():
    # At price == base_price, the ratio is 1, and 1**anything == 1,
    # so demand must exactly equal the input base demand regardless of elasticity.
    d = demand_at_price(price=999, base_price=999, base_demand=500, elasticity=-0.9552)
    assert math.isclose(d, 500.0)


def test_demand_falls_as_price_rises_for_negative_elasticity():
    d_base = demand_at_price(price=999, base_price=999, base_demand=500, elasticity=-0.9552)
    d_higher = demand_at_price(price=1099, base_price=999, base_demand=500, elasticity=-0.9552)
    assert d_higher < d_base


def test_higher_psychology_score_means_smaller_demand_drop_at_same_price():
    # This is the entire economic claim of the model: more persuasive copy
    # -> demand curve is flatter -> a given price increase costs less demand.
    low_psych_elasticity = effective_elasticity(-1.2, 0.40, composite_score=1.0)
    high_psych_elasticity = effective_elasticity(-1.2, 0.40, composite_score=9.0)

    demand_low_psych = demand_at_price(1099, 999, 500, low_psych_elasticity)
    demand_high_psych = demand_at_price(1099, 999, 500, high_psych_elasticity)

    assert demand_high_psych > demand_low_psych


def test_full_scenario_run_reject_bad_input():
    with pytest.raises(ValueError):
        ProductEconomics(current_price=999, variable_cost=1200,  # cost > price
                          conversion_rate=0.05, estimated_market_size=10000,
                          price_elasticity=-1.2)


def test_full_scenario_run_reference_case():
    econ = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.2,
    )
    control = ModelingControl(psychology_weight=0.40)
    result = run_scenarios(econ, control, composite_score=5.1)

    scenarios = {s["name"]: s for s in result["scenarios"]}

    # Conservative scenario = current price, exactly base demand, by construction
    assert scenarios["Conservative"]["price"] == 999
    assert scenarios["Conservative"]["demand"] == 500.0
    assert scenarios["Conservative"]["revenue"] == 999 * 500

    # Base and Aggressive prices are the FIXED bands, not psychology-derived
    assert scenarios["Base"]["price"] == round(999 * 1.05, 2)
    assert scenarios["Aggressive"]["price"] == round(999 * 1.10, 2)

    # Demand must be strictly decreasing as price rises across all 3 scenarios
    assert scenarios["Conservative"]["demand"] > scenarios["Base"]["demand"] > scenarios["Aggressive"]["demand"]

    # Contribution should still be positive in all scenarios given cost=400
    assert all(s["contribution"] > 0 for s in scenarios.values())

    # Recommended flag: exactly one scenario, matching the top-level name,
    # matching the actual max-contribution scenario -- computed here
    # independently to prove the flag isn't just echoing itself.
    recommended_flagged = [name for name, s in scenarios.items() if s["recommended"]]
    assert len(recommended_flagged) == 1
    assert recommended_flagged[0] == result["recommended_scenario"]
    max_contribution_name = max(scenarios, key=lambda n: scenarios[n]["contribution"])
    assert recommended_flagged[0] == max_contribution_name


def test_segment_default_used_only_when_elasticity_not_supplied():
    econ = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=None,
        customer_segment="price_sensitive",
    )
    assert econ.resolved_elasticity() == -1.8  # from SEGMENT_DEFAULT_ELASTICITY

    econ2 = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.2,
        customer_segment="price_sensitive",  # must NOT silently override
    )
    assert econ2.resolved_elasticity() == -1.2


# ---------------------------------------------------------------------------
# Amendment: recommended / recommended_scenario (metadata only, Phase 1
# math unchanged). Adopted per explicit decision -- verified before freeze.
# ---------------------------------------------------------------------------

def test_recommended_flag_matches_highest_contribution():
    econ = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.2,
    )
    control = ModelingControl(psychology_weight=0.40)
    result = run_scenarios(econ, control, composite_score=5.1)

    by_name = {s["name"]: s for s in result["scenarios"]}
    highest_contribution_name = max(by_name, key=lambda n: by_name[n]["contribution"])

    assert by_name[highest_contribution_name]["recommended"] is True


def test_exactly_one_scenario_is_recommended():
    econ = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.2,
    )
    control = ModelingControl(psychology_weight=0.40)
    result = run_scenarios(econ, control, composite_score=5.1)

    recommended_flags = [s["recommended"] for s in result["scenarios"]]
    assert sum(recommended_flags) == 1


def test_recommended_scenario_field_matches_the_flagged_scenario():
    econ = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.2,
    )
    control = ModelingControl(psychology_weight=0.40)
    result = run_scenarios(econ, control, composite_score=5.1)

    flagged = next(s for s in result["scenarios"] if s["recommended"])
    assert result["recommended_scenario"] == flagged["name"]


def test_recommended_flag_shifts_to_conservative_when_it_wins_on_contribution():
    # Extreme elasticity: the large % demand loss from raising price
    # dominates the comparatively small % margin gain, so Conservative
    # genuinely produces the highest contribution -- verified numerically
    # before writing this assertion, not assumed.
    econ = ProductEconomics(
        current_price=999, variable_cost=100, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-10.0,
    )
    control = ModelingControl(psychology_weight=0.40)
    result = run_scenarios(econ, control, composite_score=0.0)  # no psychology dampening

    by_name = {s["name"]: s for s in result["scenarios"]}
    assert by_name["Conservative"]["contribution"] > by_name["Aggressive"]["contribution"]
    assert by_name["Conservative"]["recommended"] is True
    assert result["recommended_scenario"] == "Conservative"
    assert by_name["Base"]["recommended"] is False
    assert by_name["Aggressive"]["recommended"] is False


def test_amendment_does_not_alter_any_financial_calculation():
    """The critical regression check: every number that existed BEFORE the
    amendment (effective_elasticity, demand, revenue, contribution) must be
    byte-for-byte identical to the Phase 1 locked reference case. Only new
    keys (`recommended`, `recommended_scenario`) may appear; nothing else
    may differ."""
    econ = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.2,
        customer_segment="price_sensitive",
    )
    control = ModelingControl(psychology_weight=0.40)
    result = run_scenarios(econ, control, composite_score=5.1)

    # Locked reference values, reproduced exactly from the Phase 1 lock doc
    # and the earlier printed reference-case output in this project.
    assert result["assumptions"]["effective_elasticity"] == -0.9552
    assert result["assumptions"]["price_elasticity_used"] == -1.2
    assert result["assumptions"]["elasticity_source"] == "user_supplied"
    assert result["modeled_range"] == {"low": 999.0, "high": 1098.9}

    by_name = {s["name"]: s for s in result["scenarios"]}

    assert by_name["Conservative"]["price"] == 999.0
    assert by_name["Conservative"]["demand"] == 500.0
    assert by_name["Conservative"]["revenue"] == 499500.0
    assert by_name["Conservative"]["contribution"] == 299500.0

    assert by_name["Base"]["price"] == 1048.95
    assert by_name["Base"]["demand"] == 477.2
    assert by_name["Base"]["revenue"] == 500593.0
    assert by_name["Base"]["contribution"] == 309700.01

    assert by_name["Aggressive"]["price"] == 1098.9
    assert by_name["Aggressive"]["demand"] == 456.5
    assert by_name["Aggressive"]["revenue"] == 501637.37
    assert by_name["Aggressive"]["contribution"] == 319041.19

    # And the new fields are present without disturbing the above
    assert "recommended" in by_name["Aggressive"]
    assert "recommended_scenario" in result


# ---------------------------------------------------------------------------
# Integration tests: elasticity resolution -> full scenario engine
# ---------------------------------------------------------------------------

def test_integration_user_supplied_elasticity_flows_through_scenarios():
    """User gives an explicit elasticity -> it must reach effective_elasticity
    and every scenario's demand calculation unchanged by segment."""
    econ = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.2,
        customer_segment="price_insensitive",  # deliberately mismatched vs elasticity
    )
    control = ModelingControl(psychology_weight=0.40)
    result = run_scenarios(econ, control, composite_score=5.1)

    assert result["assumptions"]["price_elasticity_used"] == -1.2
    assert result["assumptions"]["elasticity_source"] == "user_supplied"
    # Hand-calc from earlier: -1.2 * (1 - 0.4*0.51) = -0.9552
    assert math.isclose(result["assumptions"]["effective_elasticity"], -0.9552, rel_tol=1e-6)

    # Aggressive scenario demand must match the manually-derived value from
    # the reference case (500 * 1.10**-0.9552 ≈ 456.5)
    aggressive = next(s for s in result["scenarios"] if s["name"] == "Aggressive")
    assert math.isclose(aggressive["demand"], 456.5, abs_tol=0.5)


def test_integration_omitted_elasticity_uses_segment_default_end_to_end():
    """No elasticity supplied -> segment default must be the value that
    actually drives effective_elasticity and every downstream number."""
    econ = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=None,
        customer_segment="price_sensitive",  # default = -1.8
    )
    control = ModelingControl(psychology_weight=0.40)
    result = run_scenarios(econ, control, composite_score=5.1)

    assert result["assumptions"]["price_elasticity_used"] == -1.8
    assert result["assumptions"]["elasticity_source"] == "segment_default:price_sensitive"
    # Hand-calc: -1.8 * (1 - 0.4*0.51) = -1.8 * 0.796 = -1.4328
    assert math.isclose(result["assumptions"]["effective_elasticity"], -1.4328, rel_tol=1e-6)

    # Compare against the user-supplied -1.2 case: a MORE negative elasticity
    # (-1.8 vs -1.2) must produce LOWER demand at the Aggressive price, since
    # demand is more sensitive to the price increase.
    econ_explicit = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.2,
    )
    result_explicit = run_scenarios(econ_explicit, control, composite_score=5.1)

    demand_default = next(s for s in result["scenarios"] if s["name"] == "Aggressive")["demand"]
    demand_explicit = next(s for s in result_explicit["scenarios"] if s["name"] == "Aggressive")["demand"]
    assert demand_default < demand_explicit


def test_integration_same_composite_score_different_elasticity_sources_are_independent():
    """Sanity check that elasticity source selection and psychology dampening
    are genuinely independent axes -- changing one must not silently change
    how the other is computed."""
    control = ModelingControl(psychology_weight=0.40)

    econ_a = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.8,  # explicit, same value as segment default
    )
    econ_b = ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=None,
        customer_segment="price_sensitive",  # resolves to -1.8 too
    )

    result_a = run_scenarios(econ_a, control, composite_score=5.1)
    result_b = run_scenarios(econ_b, control, composite_score=5.1)

    # Same resolved elasticity via two different paths must give identical scenarios
    assert result_a["assumptions"]["effective_elasticity"] == result_b["assumptions"]["effective_elasticity"]
    assert result_a["scenarios"] == result_b["scenarios"]
    # But the source label must correctly reflect which path was taken
    assert result_a["assumptions"]["elasticity_source"] == "user_supplied"
    assert result_b["assumptions"]["elasticity_source"] == "segment_default:price_sensitive"
