"""NeuroPrice core bridge: validated Gemini psychology -> deterministic pricing."""
from dataclasses import dataclass, asdict
from orchestrator import analyze_marketing_copy, AnalysisSuccess, AnalysisFailure, GeminiClient
from pricing_engine import ProductEconomics, ModelingControl, run_scenarios
from sensitivity import sweep, find_winner_flip_points

@dataclass
class CoreResult:
    ok: bool
    psychology: dict | None = None
    financials: dict | None = None
    attempts_used: int | None = None
    error_message: str | None = None


def _build_sensitivity_summary(econ: ProductEconomics, composite_score: float, control: ModelingControl) -> dict:
    """Build the UI-safe sensitivity summary by delegating to sensitivity.sweep.

    The tested elasticity range includes the resolved request elasticity when
    possible and keeps the five-point grid used by the model review. This is
    scenario analysis, not a confidence interval or probability estimate.
    """
    resolved = econ.resolved_elasticity()
    # Keep the reviewed 5x5 grid while ensuring the request's own elasticity
    # is represented. For common/reference cases this is the documented range.
    candidates = [round(x, 2) for x in (resolved - 0.6, resolved - 0.4, resolved - 0.2, resolved, resolved + 0.2)]
    # For the reference -1.2 case, preserve the reviewed -1.8..-1.0 grid.
    if round(resolved, 2) == -1.2:
        candidates = [-1.8, -1.6, -1.4, -1.2, -1.0]
    elasticities = sorted(set(x for x in candidates if x < 0))
    while len(elasticities) < 5:
        next_value = round(elasticities[0] - 0.2, 2) if elasticities else -1.0
        elasticities = sorted(set(elasticities + [next_value]))
    elasticities = elasticities[-5:]

    weights = [0.0, 0.2, 0.4, 0.6, 0.8]
    results = sweep(econ, composite_score, weights, elasticities)
    flips = find_winner_flip_points(results)

    return {
        "psychology_weight_tested": weights,
        "elasticity_tested": elasticities,
        "grid": [asdict(r) for r in results],
        "winner_flips": [
            {"from": asdict(a), "to": asdict(b)} for a, b in flips
        ],
    }


def run_full_analysis(marketing_copy: str, econ: ProductEconomics, control: ModelingControl, gemini_client: GeminiClient) -> CoreResult:
    analysis = analyze_marketing_copy(marketing_copy, gemini_client)
    if isinstance(analysis, AnalysisFailure):
        return CoreResult(ok=False, error_message=analysis.message, attempts_used=analysis.attempts_used)

    assert isinstance(analysis, AnalysisSuccess)
    financials = run_scenarios(econ, control, composite_score=analysis.psychology.composite_score)
    financials["sensitivity"] = _build_sensitivity_summary(econ, analysis.psychology.composite_score, control)

    return CoreResult(
        ok=True,
        psychology={
            "scores": analysis.psychology.scores,
            "composite_score": analysis.psychology.composite_score,
            "dominant_triggers": analysis.psychology.dominant_triggers,
            "evidence": [asdict(e) for e in analysis.psychology.evidence],
        },
        financials=financials,
        attempts_used=analysis.attempts_used,
    )
