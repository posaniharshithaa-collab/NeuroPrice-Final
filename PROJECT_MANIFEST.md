# NeuroPrice Clean Project

This is the consolidated clean project assembled from the uploaded NeuroPrice source archives.

## Deployable structure

- `backend/` — FastAPI API, Gemini adapter, validation/orchestration, deterministic pricing engine, sensitivity analysis, and tests.
- `frontend/` — React + Vite application, including the analysis form, scenario dashboard, psychology signals/evidence, assumptions, sensitivity, and limitations.
- `README.md` — project overview, architecture, formulas, local setup, and deployment notes.
- `DEPLOYMENT.md` — deployment runbook.
- `Procfile` is inside `backend/` because the backend is the deployable PaaS service.

## Consolidation rules

The clean project uses the most complete/latest versions represented in the uploaded archives:

- Final FastAPI/core/frontend integration files from the latest complete application archive.
- Psychology UI and scenario insight refinements from the psychology/UI archive.
- Scenario card, assumptions styling, and locked pricing-engine implementation from the later UI/model archive.
- Validation, orchestration, sensitivity, and locked Phase 1 artifacts from their respective archives.
- Minimal Vite project scaffolding (`package.json`, `vite.config.js`, `index.html`, `main.jsx`, and global `App.css`) was added where the uploaded incremental archives did not contain the required scaffold.

## Important

- `GEMINI_API_KEY` belongs only in the backend environment.
- `VITE_API_BASE_URL` is the only frontend runtime/build configuration variable.
- Do not commit real `.env` files or API keys.
- The financial formulas and scenario logic are preserved from the locked implementation.

### UI refresh
- Premium dark fintech dashboard visual system
- SVG hero visual with model/network motif; no external image dependency
- Real-data scenario bar visualizations for revenue and contribution
- Psychology signal meters and evidence cards
- Explicit AI signal -> base elasticity -> effective elasticity trace
- Sensitivity winner map from backend sensitivity output
- Mobile-responsive layout
