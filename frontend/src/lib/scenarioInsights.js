/*
  NeuroPrice — Scenario Insights (presentation layer only)

  Everything in this file operates on numbers and decisions the backend
  ALREADY produced. Nothing here calculates revenue, elasticity, demand,
  or selects which scenario is recommended -- that selection is the
  backend's decision (max contribution), returned directly on each
  scenario and on financials.recommended_scenario. This file only
  formats and describes what's already there.
*/

const TRIGGER_LABELS = {
  scarcity: 'Scarcity',
  social_proof: 'Social proof',
  authority: 'Authority',
  reciprocity: 'Reciprocity',
  liking: 'Liking',
  commitment_consistency: 'Commitment & consistency',
};

export function formatMargin(scenario) {
  if (!scenario.revenue) return null;
  return (scenario.contribution / scenario.revenue) * 100;
}

/**
 * Fractional deltas (e.g. -0.084 for -8.4%) comparing the recommended
 * scenario against the Conservative (current-price) baseline. Division
 * of two numbers the backend already returned -- the same category as
 * formatMargin above, not a new financial calculation.
 */
export function computeFinancialImpact(recommended, baseline) {
  const delta = (recommendedValue, baselineValue) =>
    baselineValue !== 0 ? (recommendedValue - baselineValue) / baselineValue : 0;

  return {
    demand: delta(recommended.demand, baseline.demand),
    revenue: delta(recommended.revenue, baseline.revenue),
    contribution: delta(recommended.contribution, baseline.contribution),
  };
}

/**
 * "↑ 8.4%" / "↓ 2.7%" / "→ 0.0%" -- formats a fractional delta (as
 * produced by computeFinancialImpact) for display. Pure formatting,
 * no calculation.
 */
export function formatDelta(fraction, decimals = 1) {
  const pct = Number((fraction * 100).toFixed(decimals));
  const arrow = pct > 0 ? '↑' : pct < 0 ? '↓' : '→';
  return `${arrow} ${Math.abs(pct).toFixed(decimals)}%`;
}

/**
 * "high scarcity + moderate social proof" -- qualifies up to the two
 * strongest nonzero trigger scores with an intensity word. Purely a
 * copy-formatting function over scores the backend already returned.
 */
function getTriggerIntensityPhrase(scores) {
  const qualify = (score) => {
    if (score >= 8) return 'high';
    if (score >= 5) return 'moderate';
    return 'slight';
  };

  const ranked = Object.entries(scores)
    .filter(([, score]) => score > 0)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 2);

  if (ranked.length === 0) return null;

  return ranked
    .map(([trigger, score]) => `${qualify(score)} ${(TRIGGER_LABELS[trigger] || trigger).toLowerCase()}`)
    .join(' + ');
}

export function getScenarioTradeoff(scenario, allScenarios) {
  const prices = allScenarios.map((s) => s.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);

  if (scenario.price === minPrice) {
    return 'Higher conversion, lower margin per unit';
  }
  if (scenario.price === maxPrice) {
    return 'Higher margin per unit, more demand risk';
  }
  return 'Balances conversion and margin';
}

export function generateWhatMovedText(psychology, financials, recommended) {
  const { price_elasticity_used: baseElasticity, effective_elasticity: effectiveElasticity } =
    financials.assumptions;

  const isConservative = recommended.name === 'Conservative';
  const dampeningPct = baseElasticity !== 0
    ? ((1 - effectiveElasticity / baseElasticity) * 100).toFixed(1)
    : '0.0';

  const triggerPhrase = getTriggerIntensityPhrase(psychology.scores);

  if (isConservative || !triggerPhrase) {
    return (
      'The model held at the current price. Detected persuasion signals were not ' +
      'strong enough, relative to the assumed price sensitivity, to justify moving ' +
      'off the conservative scenario.'
    );
  }

  // Deliberately "reduced the magnitude of modeled price elasticity," not
  // "increased price sensitivity" -- elasticity is negative, so phrasing
  // this in terms of sensitivity risks getting the sign backwards.
  const capitalized = triggerPhrase[0].toUpperCase() + triggerPhrase.slice(1);
  return (
    `${capitalized} reduced the magnitude of modeled price elasticity by ${dampeningPct}%, ` +
    `meaning the model assumes less demand sensitivity to the price increase.`
  );
}

export { TRIGGER_LABELS };
