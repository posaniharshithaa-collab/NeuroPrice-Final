# NeuroPrice

### AI-assisted pricing scenario analysis with an evidence-gated AI signal layer and deterministic financial modeling.

NeuroPrice analyzes persuasion signals in marketing copy, translates those signals into a controlled elasticity adjustment, and evaluates predefined pricing scenarios using a deterministic financial model.

The central design principle is simple:

> **AI extracts the signal. The financial engine decides the numbers.**

NeuroPrice is a decision-support system, not a statistically validated price optimizer.

---

## Problem

Pricing decisions often separate marketing psychology from financial modeling.

A marketing team may see scarcity, social proof, authority, or other persuasive signals and interpret them as pricing power. A finance team may model elasticity, revenue, and contribution without considering what the marketing copy is communicating.

NeuroPrice brings these two perspectives into one pipeline without allowing either layer to take over the other's responsibility.

---

## Solution

```text
Marketing copy
      ↓
AI-assisted persuasion signal extraction
      ↓
Strict schema + evidence validation
      ↓
Validated psychology signal
      ↓
Controlled elasticity adjustment
      ↓
Three fixed pricing scenarios
      ↓
Deterministic demand and financial modeling
      ↓
Revenue / contribution / margin analysis
      ↓
Sensitivity analysis
      ↓
Decision-support recommendation

```

The AI does not directly recommend a price.

Instead, it extracts six persuasion signals from the marketing copy:

- Scarcity
- Social proof
- Authority
- Reciprocity
- Liking
- Commitment / consistency

Each signal receives a score from 0–10 and must be supported by evidence from the submitted copy.

---

## Key Design Decision

**Persuasive copy does not set price.**

An earlier design allowed psychology to both:

- increase modeled pricing power, and
- directly increase the scenario price.

That created a double-counting problem.

The final design deliberately removes that behavior.

Psychology affects only the magnitude of modeled price elasticity:

```text
psych_norm = composite_score / 10

effective_elasticity =
    price_elasticity ×
    (1 − psychology_weight × psych_norm)

```

The pricing scenarios themselves remain fixed:

- **Conservative** = current price
- **Base** = current price × 1.05
- **Aggressive** = current price × 1.10

Therefore: **the AI signal changes elasticity, not price.**

This keeps the AI influence narrow, explicit, and auditable.

---

## Architecture

```text
                 Marketing Copy
                       │
                       ▼
             ┌──────────────────┐
             │   OpenAI API      │
             │ Signal Extraction │
             └────────┬─────────┘
                      │
                      ▼
             Raw structured JSON
                      │
                      ▼
             ┌──────────────────┐
             │ Schema Validation │
             └────────┬─────────┘
                      │
                      ▼
             ┌──────────────────┐
             │ Evidence          │
             │ Validation        │
             └────────┬─────────┘
                      │
                Validated signal
                      │
                      ▼
             ┌──────────────────┐
             │ Retry Orchestrator│
             │ Max 2 attempts    │
             └────────┬─────────┘
                      │
                      ▼
             ┌──────────────────┐
             │ Deterministic     │
             │ Pricing Engine    │
             └────────┬─────────┘
                      │
                      ▼
             ┌──────────────────┐
             │ Sensitivity       │
             │ Analysis          │
             └────────┬─────────┘
                      │
                      ▼
                 FastAPI API
                      │
                      ▼
             React + Vite Dashboard

```

The AI is treated as an untrusted probabilistic component.

A deterministic validator decides whether its output is allowed to influence the pricing engine.

If validation fails twice, the pipeline returns a controlled error.

It never passes partial or unvalidated psychology data into the financial model.

---

## Production Architecture

```text
GitHub
   │
   ├───────────────┐
   ▼               ▼
Render           Render
Frontend         Backend
   │               │
React/Vite       FastAPI
   │               │
   └───────┬───────┘
           ▼
       OpenAI API

```

The frontend communicates with the production FastAPI backend through the configured `VITE_API_BASE_URL`.

The backend keeps the API key server-side.

The OpenAI API key is never exposed to the browser.

---

## Financial Model

The financial engine is completely deterministic.

**Initial demand**

```text
D0 = estimated_market_size × conversion_rate

```

**Price-sensitive demand**

```text
D(P) =
    D0 ×
    (P / current_price) ^ effective_elasticity

```

**Revenue**

```text
revenue(P) = P × D(P)

```

**Contribution**

```text
contribution(P) =
    (P − variable_cost) × D(P)

```

**Recommended scenario**

```text
recommended scenario =
    scenario with the highest modeled contribution

```

This recommendation is a model-based scenario selection, not a claim about the statistically optimal real-world price.

---

## Why the Model Uses Fixed Price Bands

The system evaluates three predefined scenarios:

| Scenario | Price Change |
|---|---:|
| Conservative | 0% |
| Base | +5% |
| Aggressive | +10% |

These price bands are modeling assumptions.

They are intentionally independent of the psychology score.

This prevents the AI from effectively saying:

> "The copy is persuasive, therefore increase the price by whatever I think is appropriate."

Instead, the AI produces a bounded signal and the deterministic engine evaluates the consequences.

---

## AI Responsibility

OpenAI is responsible only for:

- reading the marketing copy
- identifying persuasion signals
- assigning six 0–10 heuristic scores
- providing evidence for non-zero scores
- identifying dominant triggers

OpenAI does **not**:

- calculate price elasticity
- calculate demand
- calculate revenue
- calculate contribution
- calculate margin
- recommend a price
- estimate willingness to pay
- claim causal behavioral effects

All financial calculations happen outside the LLM.

---

## Validation

AI output passes through multiple deterministic checks.

**1. Schema validation**

The response must contain:

- all six required trigger keys
- integer scores from 0–10
- valid evidence structures
- supported trigger names
- non-empty evidence reasons

**2. Evidence completeness**

Every non-zero psychology score must have corresponding evidence.

For example: `scarcity = 8` requires evidence explaining why the submitted copy contains scarcity.

**3. Evidence plausibility**

Evidence is checked for trigger-appropriate vocabulary.

**4. Evidence grounding**

Evidence must share real content with the submitted marketing copy. This helps catch unsupported or hallucinated evidence.

**Important limitation:** these checks are heuristics, not proof of truth. A fluent hallucination that reuses appropriate vocabulary or real words out of context could still pass. That limitation is explicitly documented rather than hidden.

---

## Retry Strategy

The AI pipeline allows a maximum of two attempts.

```text
Attempt 1
   ↓
Validation
   │
   ├── Pass → continue
   │
   └── Fail
         ↓
   Constrained repair prompt
         ↓
Attempt 2
   ↓
Validation
   │
   ├── Pass → continue
   │
   └── Fail → controlled error

```

The second attempt receives the exact validation failure.

Both attempts pass through the same validation pipeline.

There is no validator bypass on the final attempt.

If both attempts fail, `ok = false` and the pricing engine is never called with unvalidated AI output.

---

## Sensitivity Analysis

For every successful analysis, NeuroPrice performs a small deterministic grid sweep across:

- price elasticity
- psychology weight

The sweep is centered around the actual request's values.

It re-runs the pricing engine across the grid and identifies whether the recommended scenario changes.

This helps answer: *"How sensitive is this recommendation to the model's own assumptions?"*

The sensitivity grid is **not**:

- a statistical confidence interval
- a probability estimate
- a forecast distribution

It is a scenario-based robustness check.

---

## Example Inputs

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

If price elasticity is omitted, NeuroPrice uses the documented segment-level default.

Available segments:

- `price_sensitive`
- `neutral`
- `price_insensitive`

Segment defaults are assumptions, not empirical estimates.

---

## API

### `POST /analyze`

**Accepts:**

- product economics
- customer segment
- optional elasticity
- psychology weighting
- marketing copy

**Returns:**

- AI psychology signals
- composite score
- dominant triggers
- evidence
- effective elasticity
- pricing scenarios
- modeled demand
- revenue
- contribution
- margin
- recommended scenario
- sensitivity analysis
- assumptions
- model trace

### `GET /health`

Returns:

```json
{
  "status": "ok"
}

```

Used as a production liveness check.

---

## Technology Stack

**Frontend**

- React
- Vite
- JavaScript
- Custom CSS
- SVG-based visualization

**Backend**

- Python
- FastAPI
- Pydantic
- OpenAI API

**Modeling**

- Deterministic Python pricing engine
- Elasticity modeling
- Scenario analysis
- Sensitivity analysis

**Testing**

- Pytest
- Adversarial validation tests
- API-layer tests
- Retry orchestration tests
- Pricing-engine tests
- Frontend production-build verification

**Deployment**

- GitHub
- Render
- Production FastAPI backend
- Production React frontend

---

## Testing

### Backend

**67/67 tests passing**

The test suite covers:

- pricing engine behavior
- schema validation
- evidence validation
- malformed JSON
- out-of-range scores
- missing evidence
- unsupported evidence
- hallucinated evidence
- wrong-trigger evidence
- retry recovery
- persistent AI failure
- AI-to-pricing bridge
- sensitivity analysis
- FastAPI success responses
- invalid inputs
- fail-fast startup behavior

### Frontend

Production build verified successfully.

The component tree was also checked through actual server-side React rendering across:

- idle form
- submitting state
- successful analysis
- successful analysis with sensitivity data
- error state
- manual elasticity input mode

The rendered output was checked for:

- runtime errors
- NaN
- undefined
- invalid component output

---

## Limitations

NeuroPrice intentionally does not claim more than the model can support.

1. **Elasticity is not empirically estimated** — Price elasticity is user-supplied or comes from a documented segment-level assumption.
2. **Psychology scores are heuristic** — The six persuasion signals are structured heuristics, not validated behavioral measurements.
3. **Evidence validation is heuristic** — Keyword and content-overlap checks are not semantic proof.
4. **No causal claims** — The system does not claim that persuasive copy causes higher prices, conversion, or revenue.
5. **No competitor modeling** — Competitor response and competitive pricing are not modeled.
6. **No cross-price effects** — Substitution between products is not modeled.
7. **No market saturation model** — Market saturation is outside the current model.
8. **Upward scenarios only** — The current version evaluates 0%, +5%, +10%. It does not currently model price reductions.
9. **Fixed price bands** — The scenario bands are explicit modeling assumptions rather than data-derived recommendations.

---

## Portfolio Positioning

NeuroPrice should be presented as:

> An AI-assisted financial decision-support system that extracts structured persuasion signals from marketing copy, validates those signals with deterministic evidence rules, and passes only validated information into an independently tested pricing engine.

It should **not** be presented as:

- a statistically validated price optimizer
- a willingness-to-pay predictor
- a customer behavior predictor
- an autonomous pricing agent
- proof that marketing psychology causes revenue changes

The interesting part of NeuroPrice is not simply that an LLM is involved. The interesting part is the boundary between probabilistic AI and deterministic finance.

```text
Unstructured text
       ↓
Probabilistic AI
       ↓
Strict validation
       ↓
Structured signal
       ↓
Deterministic financial model
       ↓
Auditable decision support

```

---

## Repository Structure

```text
NeuroPrice/
│
├── backend/
│   ├── api.py
│   ├── core.py
│   ├── pricing_engine.py
│   ├── sensitivity.py
│   ├── psychology_prompt.py
│   ├── psychology_schema.py
│   ├── evidence_validation.py
│   ├── orchestrator.py
│   ├── gemini_adapter.py
│   ├── requirements.txt
│   └── test_*.py
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── public/
│   │   └── favicon.png
│   └── src/
│       ├── App.jsx
│       ├── api/
│       ├── components/
│       ├── lib/
│       └── styles/
│
├── .gitignore
├── DEPLOYMENT.md
└── README.md

```

> **Note:** `gemini_adapter.py` retains its historical filename and compatibility class names from the original architecture, but the current implementation uses the OpenAI API internally.

---

## Local Development

### Backend

```bash
cd backend

python -m venv .venv

```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1

```

Install dependencies:

```bash
pip install -r requirements.txt

```

Create the backend environment file from the provided example and configure:

- `OPENAI_API_KEY`
- `NEUROPRICE_CORS_ORIGINS`

Start the API:

```bash
uvicorn api:app --reload --port 8000

```

The local API runs on: `http://localhost:8000`

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev

```

The Vite development server runs on: `http://localhost:5173`

For local development, the frontend defaults to the local FastAPI backend.

For deployment, configure `VITE_API_BASE_URL` with the production backend address.

---

## Environment Variables

| Variable | Location | Required | Purpose |
|---|---|---:|---|
| `OPENAI_API_KEY` | Backend | Yes | Authenticates the OpenAI API |
| `NEUROPRICE_CORS_ORIGINS` | Backend | Yes in production | Allows the deployed frontend origin |
| `VITE_API_BASE_URL` | Frontend | Yes in production | Points the frontend to the production API |

The OpenAI API key must remain server-side. It must never be placed in:

- React source code
- Vite client environment variables
- browser-visible configuration
- GitHub

---

## Production Deployment

The deployed architecture uses separate frontend and backend services.

```text
GitHub
   │
   ├── Render Static Site
   │       └── React + Vite frontend
   │
   └── Render Web Service
           └── FastAPI backend
                    │
                    ▼
                OpenAI API

```

The frontend is configured with the production backend URL.

The backend is configured with:

- `OPENAI_API_KEY`
- `NEUROPRICE_CORS_ORIGINS`

The production application also exposes:

- `GET /health`
- `POST /analyze`

---

## UI / Product Design

NeuroPrice uses a dark fintech-style interface designed around decision support rather than generic AI chat.

The dashboard includes:

- editorial marketing-copy input
- product economics controls
- customer segment selection
- psychology weighting
- AI signal scores
- evidence for detected signals
- psychology-to-elasticity model trace
- scenario comparison
- revenue and contribution analysis
- financial-impact deltas
- sensitivity visualization
- assumptions
- methodology limitations

The visual system intentionally separates:

```text
MARKETING SIGNALS
        ↓
ELASTICITY
        ↓
FINANCIAL SCENARIOS

```

The charts are rendered from backend-returned values. The browser does not implement a second financial model.

---

## Example Decision Flow

A marketing message containing strong scarcity and social proof may produce:

| Trigger Score  |      |
| -------------- | ---- |
| Scarcity       | 8/10 |
| Social Proof   | 7/10 |
| Authority      | 2/10 |
| Reciprocity    | 1/10 |
| Liking         | 3/10 |
| Commitment     | 2/10 |

The scores are validated first.

The composite signal is then used to adjust the magnitude of price elasticity.

The pricing engine independently evaluates: Conservative, Base, Aggressive.

The system compares modeled contribution across those scenarios.

The highest-contribution scenario becomes the recommendation.

**The AI never directly chooses the price.**

---

## Why This Project Matters

NeuroPrice demonstrates a practical pattern for combining LLMs with financial systems:

> Use AI where unstructured language needs interpretation. Use deterministic code where financial consequences need calculation.

That separation makes the system:

- easier to test
- easier to audit
- easier to explain
- safer to reason about
- less dependent on LLM consistency
- more defensible in a finance context

---

## Project Status

**Production deployed.**

| Component Status     |                 |
| -------------------- | --------------- |
| Frontend             | ✓ Live          |
| Backend              | ✓ Live          |
| Production API       | ✓ Connected     |
| OpenAI integration   | ✓ Implemented   |
| CORS                 | ✓ Configured    |
| Deterministic engine | ✓ Implemented   |
| AI validation        | ✓ Implemented   |
| Retry handling       | ✓ Implemented   |
| Sensitivity analysis | ✓ Implemented   |
| Backend tests        | ✓ 67/67 passing |
| Frontend build       | ✓ Verified      |
| Premium dashboard    | ✓ Implemented   |

---

## Author

**Harshitha**

MBA Finance | Information Technology

**Interests:**

- Financial Modeling
- FinTech
- AI-assisted Decision Support
- Business Analytics
- Data-driven Finance
- Technology + Finance