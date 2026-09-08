# NeuroPrice

AI-assisted pricing scenario analysis: it separates what marketing copy signals about persuasion from what the underlying economics can actually support, then shows the financial consequences of both together.

## Problem

Pricing decisions are often made with marketing psychology and unit economics considered separately: a growth team reads persuasive copy and calls it a signal to raise price, while a finance team models elasticity and margin with no visibility into what the copy is doing. NeuroPrice puts both in the same model, but doesn't let either one dominate the other's role.

## Solution

```
Marketing copy → persuasion signals (Gemini, evidence-gated)
              → dampens the magnitude of modeled price elasticity
              → three fixed pricing scenarios (Conservative / Base / Aggressive)
              → modeled demand, revenue, and contribution per scenario
              → the scenario with the highest modeled contribution is recommended
```

The system deliberately does **not** ask an LLM to output a price. Gemini's only job is scoring six persuasion signals in marketing copy, each with required evidence. That score can only ever make the deterministic pricing engine's demand curve *less price-sensitive* — it never sets a price directly.

## Architecture

```
Marketing copy + economic inputs
        │
        ▼
Gemini (psychology_prompt.py) ── generates six 0–10 scores + evidence
        │
        ▼
Schema validation (psychology_schema.py) ── structural checks
        │
        ▼
Evidence validation (evidence_validation.py) ── every nonzero score
        │                                        must have real, grounded evidence
        ▼
Retry orchestrator (orchestrator.py) ── max 2 Gemini attempts, both
        │                                validated, no bypass on retry
        ▼
Deterministic pricing engine (pricing_engine.py) ── zero AI, zero randomness
        │
        ▼
FastAPI (api.py) ── thin HTTP layer, no business logic
        │
        ▼
React dashboard (ScenarioComparison + children)
```

Gemini is treated as an **untrusted probabilistic component**. A strict, deterministic validator — not the prompt — decides whether its output is ever allowed to reach the pricing engine. If validation fails twice, the pipeline returns a controlled error; it never falls back to a default or partial psychology score.

## Key design decision

Persuasive copy does not set price. It reduces the **magnitude of modeled price elasticity** — the pricing engine's demand curve becomes less sensitive to a price increase, which is the economically defensible interpretation of "persuasive copy earns pricing power." Scenario prices themselves are a fixed band (current price, +5%, +10%), independent of the psychology score, specifically to avoid the same signal doing two jobs at once (an earlier design iteration let psychology both dampen elasticity *and* set the price lift — that double-counting was deliberately removed).

## Financial model

```
psych_norm            = composite_score / 10
effective_elasticity  = price_elasticity × (1 − psychology_weight × psych_norm)

D0        = estimated_market_size × conversion_rate
D(P)      = D0 × (P / current_price) ^ effective_elasticity
revenue(P)      = P × D(P)
contribution(P) = (P − variable_cost) × D(P)

recommended scenario = the one with the highest contribution(P)
```

All of this is plain Python with no AI involvement — testable and auditable independent of any Gemini call.

## Validation

Gemini's raw output must pass, in order:
1. **Schema validation** — six required trigger keys, each an integer 0–10, evidence entries reference a known trigger with a non-empty reason.
2. **Evidence validation** — a nonzero score requires matching evidence (completeness); the evidence's wording must contain trigger-appropriate vocabulary (plausibility); the evidence must share real content with the submitted copy (grounding, catches hallucination).

All three evidence checks are heuristic, not proof of truth — a fluent hallucination reusing the right vocabulary and quoting real words out of context could pass. That's a documented limitation, not a hidden one.

## Retry strategy

Maximum two Gemini attempts per analysis. The second attempt receives a constrained repair prompt containing the exact validation failure. **Both** attempts go through full validation with no special-casing for the last attempt. If both fail, the API returns `ok: false` with a controlled error message — the pricing engine is never called with unvalidated data.

## Sensitivity analysis

For every successful analysis, a small grid sweep (elasticity × psychology weight, centered on the actual request's own values) re-runs the deterministic engine to show how fragile the recommendation is to its own assumptions. This is a scenario sweep, explicitly **not** a statistical confidence interval or a probability estimate — the dashboard states this directly.

## Limitations

- Price elasticity is user-supplied or a documented segment-level default, not empirically estimated.
- Persuasion-signal scores are heuristic and evidence-gated, not validated behavioral measurements.
- Evidence grounding/plausibility checks are keyword and overlap heuristics, not semantic verification.
- No causal claim is made between copy and actual buyer behavior.
- Competitor response, cross-price effects, and market saturation are not modeled.
- Only upward pricing scenarios are modeled in this version.
- Scenario price bands (0%, +5%, +10%) are fixed modeling assumptions, not derived from data.

## Tech stack

React + Vite · FastAPI · Python · Gemini API (`google-genai`) · Pytest

## Running locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY
uvicorn api:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env.local   # set VITE_API_BASE_URL if not localhost:8000
npm run dev
```

## Environment variables

| Variable | Where | Required | Notes |
|---|---|---|---|
| `GEMINI_API_KEY` | backend | Yes | App fails fast at startup if missing |
| `NEUROPRICE_CORS_ORIGINS` | backend | No | Comma-separated allowed origins; defaults to `http://localhost:5173` |
| `VITE_API_BASE_URL` | frontend | No (dev) / Yes (prod) | Defaults to `http://localhost:8000` for local dev only |

## API

**`POST /analyze`**

Request:
```json
{
  "current_price": 999,
  "variable_cost": 400,
  "conversion_rate": 0.05,
  "estimated_market_size": 10000,
  "price_elasticity": -1.2,
  "customer_segment": "price_sensitive",
  "psychology_weight": 0.4,
  "marketing_copy": "Only 5 seats remaining! Join 50,000+ customers. Offer ends tonight."
}
```

Response (`ok: true` case, abbreviated):
```json
{
  "ok": true,
  "attempts_used": 1,
  "psychology": { "scores": {...}, "composite_score": 5.1, "dominant_triggers": [...], "evidence": [...] },
  "financials": {
    "scenarios": [{ "name": "Aggressive", "price": 1098.9, "contribution": 319041.19, "recommended": true, ... }],
    "recommended_scenario": "Aggressive",
    "assumptions": {...},
    "modeled_range": { "low": 999, "high": 1098.9 },
    "sensitivity": { "grid": [...], "winner_flips": [...] }
  }
}
```

A failed Gemini analysis (both attempts exhausted) returns HTTP 200 with `ok: false` and an `error_message` — this is a legitimate pipeline outcome, not a server error. `price_elasticity` omitted entirely falls back to a documented segment default. `variable_cost >= current_price`, invalid ranges, etc. return HTTP 400.

**`GET /health`** — liveness check, returns `{"status": "ok"}`.

## Testing

Backend: **67/67 passing** (`pytest`), covering the pricing engine, schema/evidence validation (including a full adversarial suite: malformed JSON, out-of-range scores, missing/unsupported evidence, hallucinated evidence, wrong-trigger evidence), retry orchestration, the Gemini↔pricing bridge, the sensitivity summary, and the FastAPI layer (success, retry recovery, persistent failure, invalid input, fail-fast startup).

Frontend: production build verified clean; component tree verified via actual server-side React rendering (not just source inspection) across idle form, submitting form, successful result (with and without sensitivity data), error result, and manual-elasticity input mode — checked for runtime errors, `NaN`, and `undefined` in rendered output.

## Portfolio positioning

NeuroPrice is a decision-support tool, not a statistically validated price optimizer. It does not claim to know the optimal price, predict actual customer behavior, or prove a causal link between marketing copy and revenue. What it demonstrates is a specific architectural discipline: an LLM is useful for extracting structured signal from unstructured text, but should never be the thing deciding the number — that stays in a deterministic, auditable, independently-tested engine, with the LLM's output validated by strict, evidence-gated rules before it's ever allowed to influence a financial calculation.


## Repository structure

```text
backend/
  api.py
  core.py
  pricing_engine.py
  sensitivity.py
  psychology_prompt.py
  psychology_schema.py
  evidence_validation.py
  orchestrator.py
  gemini_adapter.py
  test_*.py

frontend/
  index.html
  package.json
  src/
    App.jsx
    components/
    api/
    lib/
    styles/
```

## Local development

### Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Create .env from .env.example and set GEMINI_API_KEY
uvicorn api:app --reload --port 8000
```

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

For local development, the frontend defaults to `http://localhost:8000`. For deployment, set `VITE_API_BASE_URL` to the live backend URL at frontend build time.

## Deployment

See `DEPLOYMENT.md`. The backend must receive `GEMINI_API_KEY` and `NEUROPRICE_CORS_ORIGINS`. The frontend only needs `VITE_API_BASE_URL`. Never expose the Gemini key through Vite or frontend source.

## Status

The repository is deployment-ready. Live hosting and production browser end-to-end verification require external hosting accounts and credentials.

## Premium dashboard UI
The frontend is designed as a dark fintech-style decision dashboard. It includes an editorial marketing-copy input, compact economics controls, an AI signal layer with evidence, an explicit psychology-to-elasticity model trace, scenario cards, real response-driven revenue/contribution visualizations, financial-impact deltas, a sensitivity map, assumptions, and methodology limitations. Charts are rendered from backend-returned scenario values without adding a second financial model in the browser.
