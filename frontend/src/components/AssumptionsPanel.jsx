import './AssumptionsPanel.css';

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatSegment(segment) {
  return segment
    .split('_')
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * inputs: the original request payload the frontend already holds
 *   (current_price, variable_cost, conversion_rate, estimated_market_size,
 *   customer_segment) -- the backend response does not echo these back.
 * assumptions: financials.assumptions from CoreResult (elasticity
 *   resolution details -- the part the backend DOES compute and own).
 *
 * Each item is tagged USER INPUT (submitted directly) or MODEL ASSUMPTION
 * (a segment default or fixed modeling constant) -- this distinction
 * matters because assumptions are not empirically validated.
 */
export default function AssumptionsPanel({ inputs, assumptions }) {
  const elasticityIsDefault = assumptions.elasticity_source.startsWith('segment_default');

  return (
    <div className="assumptions-panel">
      <h2 className="assumptions-panel__heading">Model assumptions</h2>
      <p className="assumptions-panel__subheading">
        This recommendation exists because these assumptions exist.
      </p>

      <div className="assumptions-panel__grid">
        <div className="assumptions-panel__item">
          <span className="assumptions-panel__label">Current price</span>
          <span className="assumptions-panel__value">{formatCurrency(inputs.current_price)}</span>
          <span className="assumptions-panel__tag">User input</span>
        </div>

        <div className="assumptions-panel__item">
          <span className="assumptions-panel__label">Variable cost</span>
          <span className="assumptions-panel__value">{formatCurrency(inputs.variable_cost)}</span>
          <span className="assumptions-panel__tag">User input</span>
        </div>

        <div className="assumptions-panel__item">
          <span className="assumptions-panel__label">Conversion rate</span>
          <span className="assumptions-panel__value">{(inputs.conversion_rate * 100).toFixed(1)}%</span>
          <span className="assumptions-panel__tag">User input</span>
        </div>

        <div className="assumptions-panel__item">
          <span className="assumptions-panel__label">Market size</span>
          <span className="assumptions-panel__value">{inputs.estimated_market_size.toLocaleString()}</span>
          <span className="assumptions-panel__tag">User input</span>
        </div>

        <div className="assumptions-panel__item">
          <span className="assumptions-panel__label">
            Price elasticity{elasticityIsDefault ? ' (segment default)' : ''}
          </span>
          <span className="assumptions-panel__value">
            {assumptions.price_elasticity_used.toFixed(2)}
          </span>
          <span className="assumptions-panel__tag">
            {elasticityIsDefault ? 'Model assumption' : 'User input'}
          </span>
        </div>

        <div className="assumptions-panel__item">
          <span className="assumptions-panel__label">Customer segment</span>
          <span className="assumptions-panel__value">{formatSegment(inputs.customer_segment)}</span>
          <span className="assumptions-panel__tag">User input</span>
        </div>

        <div className="assumptions-panel__item">
          <span className="assumptions-panel__label">Psychology weighting</span>
          <span className="assumptions-panel__value assumptions-panel__value--gold">
            {(assumptions.psychology_weight * 100).toFixed(0)}%
          </span>
          <span className="assumptions-panel__tag">User input</span>
        </div>
      </div>

      <p className="assumptions-panel__disclaimer">
        Segment defaults and psychology weighting are modeling assumptions, not empirically
        validated estimates.
      </p>
    </div>
  );
}
