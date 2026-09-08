/*
  NeuroPrice — API Service

  The only file in the frontend that calls fetch() against the backend.
  It does exactly three things: build the request, call POST /analyze,
  and classify the response/error into a shape the UI can render. It does
  NOT interpret, recompute, or second-guess anything in the response body
  -- that stays exactly as the backend returned it.

  Base URL comes from an environment variable so production never has
  localhost baked into the built bundle. Vite only exposes env vars
  prefixed VITE_ to client code, and only at build time.
*/

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class NeuroPriceApiError extends Error {
  constructor(kind, message, detail) {
    super(message);
    this.kind = kind; // 'network' | 'validation' | 'server' | 'malformed'
    this.detail = detail;
  }
}

/**
 * inputs: the exact request payload the backend's AnalyzeRequest expects
 *   (current_price, variable_cost, conversion_rate, estimated_market_size,
 *   price_elasticity, customer_segment, psychology_weight, marketing_copy).
 *
 * Returns the CoreResult exactly as the backend produced it -- callers
 * read result.ok, result.psychology, result.financials, result.error_message
 * directly. This function does not add, remove, or reshape any field.
 */
export async function analyzePricing(inputs, { signal } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inputs),
      signal,
    });
  } catch (err) {
    if (err.name === 'AbortError') throw err; // let callers handle cancellation themselves
    throw new NeuroPriceApiError(
      'network',
      'Could not reach the analysis server. Check your connection and try again.',
      err.message,
    );
  }

  if (response.status === 400 || response.status === 422) {
    let detail = null;
    try {
      const body = await response.json();
      detail = body.detail;
    } catch {
      // response body wasn't JSON -- fall through with detail=null
    }
    throw new NeuroPriceApiError(
      'validation',
      typeof detail === 'string' ? detail : 'The submitted inputs were rejected by the server.',
      detail,
    );
  }

  if (response.status >= 500) {
    throw new NeuroPriceApiError(
      'server',
      'The analysis server encountered an error. Please try again shortly.',
      response.status,
    );
  }

  if (!response.ok) {
    throw new NeuroPriceApiError(
      'server',
      `Unexpected response from the server (status ${response.status}).`,
      response.status,
    );
  }

  let body;
  try {
    body = await response.json();
  } catch (err) {
    throw new NeuroPriceApiError(
      'malformed',
      'The server returned a response that could not be read.',
      err.message,
    );
  }

  // Minimal shape check -- NOT re-validating business content, just
  // confirming the response is at least the shape the UI expects before
  // handing it off. A response missing `ok` entirely is not a valid
  // CoreResult regardless of HTTP status.
  if (typeof body?.ok !== 'boolean') {
    throw new NeuroPriceApiError(
      'malformed',
      'The server returned an unexpected response format.',
      body,
    );
  }

  return body;
}
