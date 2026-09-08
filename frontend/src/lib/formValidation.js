/*
  NeuroPrice — Form Validation (UX layer only)

  These checks exist so the user gets immediate inline feedback instead of
  waiting for a round trip to the server. They mirror the backend's own
  validation rules (ProductEconomics.__post_init__, ModelingControl) in
  spirit, but the backend remains the authoritative source of truth --
  this function's only job is to catch obvious mistakes before submission
  and disable the Analyze button until they're fixed. It computes no
  pricing, elasticity, or financial figures.
*/

export function validateForm(values) {
  const errors = {};

  if (!values.marketing_copy || !values.marketing_copy.trim()) {
    errors.marketing_copy = 'Marketing copy is required.';
  } else if (values.marketing_copy.length > 2000) {
    errors.marketing_copy = 'Marketing copy must be 2000 characters or fewer.';
  }

  const currentPrice = Number(values.current_price);
  if (!values.current_price || Number.isNaN(currentPrice) || currentPrice <= 0) {
    errors.current_price = 'Current price must be greater than 0.';
  }

  const variableCost = Number(values.variable_cost);
  if (values.variable_cost === '' || Number.isNaN(variableCost) || variableCost < 0) {
    errors.variable_cost = 'Variable cost must be 0 or greater.';
  } else if (!errors.current_price && variableCost >= currentPrice) {
    errors.variable_cost = 'Variable cost must be less than current price.';
  }

  const conversionPct = Number(values.conversion_rate_pct);
  if (values.conversion_rate_pct === '' || Number.isNaN(conversionPct) || conversionPct <= 0 || conversionPct > 100) {
    errors.conversion_rate_pct = 'Conversion rate must be between 0 and 100%.';
  }

  const marketSize = Number(values.estimated_market_size);
  if (!values.estimated_market_size || Number.isNaN(marketSize) || !Number.isInteger(marketSize) || marketSize <= 0) {
    errors.estimated_market_size = 'Market size must be a whole number greater than 0.';
  }

  if (values.elasticity_mode === 'manual') {
    const elasticity = Number(values.price_elasticity);
    if (values.price_elasticity === '' || Number.isNaN(elasticity) || elasticity >= 0) {
      errors.price_elasticity = 'Price elasticity must be a negative number.';
    }
  } else if (!values.customer_segment) {
    errors.customer_segment = 'Select a customer segment to use its default elasticity.';
  }

  const psychWeightPct = Number(values.psychology_weight_pct);
  if (values.psychology_weight_pct === '' || Number.isNaN(psychWeightPct) || psychWeightPct < 0 || psychWeightPct > 100) {
    errors.psychology_weight_pct = 'Psychology weight must be between 0 and 100%.';
  }

  return { errors, isValid: Object.keys(errors).length === 0 };
}

/**
 * Converts the form's display-friendly values (percentages, strings) into
 * the exact payload shape POST /analyze expects. Unit conversion (percent
 * -> fraction) is presentation-layer formatting, not business logic -- no
 * pricing, elasticity, or financial calculation happens here.
 */
export function buildAnalyzeRequest(values) {
  return {
    current_price: Number(values.current_price),
    variable_cost: Number(values.variable_cost),
    conversion_rate: Number(values.conversion_rate_pct) / 100,
    estimated_market_size: Number(values.estimated_market_size),
    price_elasticity: values.elasticity_mode === 'manual' ? Number(values.price_elasticity) : null,
    customer_segment: values.customer_segment || 'neutral',
    psychology_weight: Number(values.psychology_weight_pct) / 100,
    marketing_copy: values.marketing_copy.trim(),
  };
}

export const DEFAULT_FORM_VALUES = {
  marketing_copy: '',
  current_price: '',
  variable_cost: '',
  conversion_rate_pct: '',
  estimated_market_size: '',
  elasticity_mode: 'segment', // 'segment' | 'manual'
  price_elasticity: '',
  customer_segment: 'neutral',
  psychology_weight_pct: '40',
};

/**
 * Reverse of buildAnalyzeRequest -- reconstructs form-shaped values from an
 * already-submitted API payload, so "modify and re-analyze" can prefill
 * the form instead of making the user retype everything. Pure formatting,
 * the inverse of a unit conversion already performed on the way in.
 */
export function formValuesFromRequest(payload) {
  return {
    marketing_copy: payload.marketing_copy,
    current_price: String(payload.current_price),
    variable_cost: String(payload.variable_cost),
    conversion_rate_pct: String(payload.conversion_rate * 100),
    estimated_market_size: String(payload.estimated_market_size),
    elasticity_mode: payload.price_elasticity != null ? 'manual' : 'segment',
    price_elasticity: payload.price_elasticity != null ? String(payload.price_elasticity) : '',
    customer_segment: payload.customer_segment,
    psychology_weight_pct: String(payload.psychology_weight * 100),
  };
}
