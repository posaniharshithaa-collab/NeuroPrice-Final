import pytest
from core import run_full_analysis, CoreResult
from pricing_engine import ProductEconomics, ModelingControl
from test_orchestrator import FakeGeminiClient, VALID_RESPONSE, MALFORMED_JSON_RESPONSE, MISSING_EVIDENCE_RESPONSE

COPY = "Only 5 seats remaining! Join 50,000+ customers. Offer ends tonight."


def _reference_econ() -> ProductEconomics:
    return ProductEconomics(
        current_price=999, variable_cost=400, conversion_rate=0.05,
        estimated_market_size=10000, price_elasticity=-1.2,
    )


def test_full_chain_marketing_copy_to_financial_result():
    """The complete arrow from your diagram, proven in one test:
    Marketing Copy -> Gemini -> Validated Psychology -> Effective Elasticity
    -> Scenarios -> Revenue/Contribution."""
    client = FakeGeminiClient([VALID_RESPONSE])
    econ = _reference_econ()
    control = ModelingControl(psychology_weight=0.40)

    result = run_full_analysis(COPY, econ, control, client)

    assert result.ok is True
    assert result.attempts_used == 1

    # Psychology actually came through
    assert result.psychology["scores"]["scarcity"] == 8
    assert result.psychology["composite_score"] == round((8 + 7) / 6, 2)

    # And it actually drove the financial numbers -- not a coincidence,
    # cross-check against the hand-verified reference case from Phase 1.
    assert result.financials["assumptions"]["composite_score"] == result.psychology["composite_score"]
    by_name = {s["name"]: s for s in result.financials["scenarios"]}
    assert by_name["Conservative"]["revenue"] == 999 * 500
    assert by_name["Aggressive"]["price"] == round(999 * 1.10, 2)


def test_full_chain_recovers_through_retry_and_still_reaches_financials():
    client = FakeGeminiClient([MALFORMED_JSON_RESPONSE, VALID_RESPONSE])
    econ = _reference_econ()
    control = ModelingControl(psychology_weight=0.40)

    result = run_full_analysis(COPY, econ, control, client)

    assert result.ok is True
    assert result.attempts_used == 2
    assert result.financials is not None


def test_full_chain_hard_stops_before_pricing_engine_on_persistent_failure():
    """The rule that matters most: two failed attempts must produce a
    result with NO financials at all -- not zeros, not defaults, not a
    'fallback' scenario. Absent entirely."""
    client = FakeGeminiClient([MALFORMED_JSON_RESPONSE, MISSING_EVIDENCE_RESPONSE])
    econ = _reference_econ()
    control = ModelingControl(psychology_weight=0.40)

    result = run_full_analysis(COPY, econ, control, client)

    assert result.ok is False
    assert result.financials is None
    assert result.psychology is None
    assert "No financial calculation was performed" in result.error_message


def test_different_psychology_scores_produce_genuinely_different_financials():
    """Not a coincidence check -- proves the bridge is load-bearing.
    Two different (but both valid) Gemini responses must produce two
    different financial outcomes, not the same numbers regardless of input."""
    weak_response = """{
      "psychology": {"scarcity": 1, "social_proof": 0, "authority": 0,
                      "reciprocity": 0, "liking": 0, "commitment_consistency": 0},
      "evidence": [{"trigger": "scarcity", "reason": "mentions only a few left"}]
    }"""
    strong_response = """{
      "psychology": {"scarcity": 9, "social_proof": 8, "authority": 0,
                      "reciprocity": 0, "liking": 0, "commitment_consistency": 0},
      "evidence": [
        {"trigger": "scarcity", "reason": "Only 5 seats remaining"},
        {"trigger": "social_proof", "reason": "Join 50,000+ customers"}
      ]
    }"""

    econ = _reference_econ()
    control = ModelingControl(psychology_weight=0.40)

    weak_result = run_full_analysis(COPY, econ, control, FakeGeminiClient([weak_response]))
    strong_result = run_full_analysis(COPY, econ, control, FakeGeminiClient([strong_response]))

    weak_aggressive = next(s for s in weak_result.financials["scenarios"] if s["name"] == "Aggressive")
    strong_aggressive = next(s for s in strong_result.financials["scenarios"] if s["name"] == "Aggressive")

    # Stronger psychology -> flatter effective elasticity -> less demand lost
    # at the same +10% price point, exactly as proven in Phase 1's sweep.
    assert strong_aggressive["demand"] > weak_aggressive["demand"]
    assert strong_aggressive["contribution"] > weak_aggressive["contribution"]


def test_recommended_scenario_amendment_flows_through_the_bridge():
    """The recommended/recommended_scenario amendment to pricing_engine.py
    must reach the CoreResult unmodified -- core.py does not strip, rename,
    or recompute anything from the engine's output."""
    client = FakeGeminiClient([VALID_RESPONSE])
    econ = _reference_econ()
    control = ModelingControl(psychology_weight=0.40)

    result = run_full_analysis(COPY, econ, control, client)

    assert "recommended_scenario" in result.financials
    assert any("recommended" in s for s in result.financials["scenarios"])
    flagged = next(s for s in result.financials["scenarios"] if s["recommended"])
    assert result.financials["recommended_scenario"] == flagged["name"]


def test_sensitivity_summary_present_and_uses_actual_request_elasticity():
    """The sensitivity grid must be built around the SAME resolved
    elasticity actually used for the main scenarios -- not an arbitrary
    range disconnected from what the user submitted."""
    client = FakeGeminiClient([VALID_RESPONSE])
    econ = _reference_econ()  # price_elasticity=-1.2
    control = ModelingControl(psychology_weight=0.40)

    result = run_full_analysis(COPY, econ, control, client)
    sensitivity = result.financials["sensitivity"]

    assert -1.2 in sensitivity["elasticity_tested"]
    assert 0.4 in sensitivity["psychology_weight_tested"]
    # Reference case verified by hand in this conversation: at
    # psychology_weight=0.4, elasticity=-1.2, Aggressive wins.
    matching_cell = next(
        c for c in sensitivity["grid"]
        if c["psychology_weight"] == 0.4 and c["price_elasticity"] == -1.2
    )
    assert matching_cell["winner"] == "Aggressive"


def test_sensitivity_reuses_sweep_without_reimplementing_it():
    """The sensitivity summary's grid values must exactly match calling
    sensitivity.sweep() directly with the same parameters -- proving core.py
    delegates rather than reimplements the sweep logic."""
    from sensitivity import sweep as direct_sweep

    econ = _reference_econ()
    control = ModelingControl(psychology_weight=0.40)

    client = FakeGeminiClient([VALID_RESPONSE])
    result = run_full_analysis(COPY, econ, control, client)
    sensitivity = result.financials["sensitivity"]
    composite_score = result.psychology["composite_score"]  # derived, not hardcoded

    direct_results = direct_sweep(
        econ, composite_score,
        sensitivity["psychology_weight_tested"],
        sensitivity["elasticity_tested"],
    )
    direct_winners = {(r.psychology_weight, r.price_elasticity): r.winner for r in direct_results}
    bridge_winners = {(c["psychology_weight"], c["price_elasticity"]): c["winner"] for c in sensitivity["grid"]}

    assert direct_winners == bridge_winners


def test_sensitivity_not_computed_on_analysis_failure():
    """The hard rule extends to sensitivity too: if Gemini analysis fails,
    there is no financials object at all, so there can be no sensitivity
    grid either -- nothing partial leaks through."""
    client = FakeGeminiClient([MALFORMED_JSON_RESPONSE, MISSING_EVIDENCE_RESPONSE])
    econ = _reference_econ()
    control = ModelingControl(psychology_weight=0.40)

    result = run_full_analysis(COPY, econ, control, client)

    assert result.ok is False
    assert result.financials is None
