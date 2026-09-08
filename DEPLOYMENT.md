# NeuroPrice Deployment Runbook

This repository is intentionally organized as two deployable applications:

```text
NeuroPrice/
├── backend/        # FastAPI + deterministic pricing engine + Gemini adapter
├── frontend/       # React + Vite dashboard
├── README.md
└── DEPLOYMENT.md
```

Deploy the `backend/` directory as the API service and the `frontend/` directory as the static web application.

Code is deployment-ready and locally verified (67/67 backend tests, clean
frontend production build). Everything below is the external hosting
action that only you can perform — account creation and credential
configuration aren't things this environment has access to.

## 1. Push to GitHub
Standard `git init` / commit / push. `.gitignore` is already in place for
both `backend/` and `frontend/` so `.env` files and `node_modules/` won't
be committed.

## 2. Deploy the backend first
Any Python-friendly host works (Render, Railway, Fly.io, etc.). Point it
at `backend/`.

- Build: `pip install -r requirements.txt`
- Start: `uvicorn api:app --host 0.0.0.0 --port $PORT` (already in `Procfile`
  for platforms that read one, e.g. Railway/Heroku-style hosts)
- Required env var: `GEMINI_API_KEY` — the app **fails to start** if this
  is missing, by design (see `api.py`'s `lifespan` handler). That's the
  correct behavior to see if you forget to set it.
- Optional env var: `NEUROPRICE_CORS_ORIGINS` — leave unset for now if the
  frontend URL isn't known yet; set it once step 3 gives you that URL.

**Verify before moving on:**
```bash
curl https://your-backend-url/health
# expect: {"status":"ok"}
```
If this fails, the frontend deployment can't be meaningfully tested yet —
fix this first.

## 3. Deploy the frontend
Any static host works (Vercel, Netlify, Cloudflare Pages).

- Build command: `npm run build`
- Output directory: `dist`
- Required env var: `VITE_API_BASE_URL=https://your-backend-url` (set
  this in the host's dashboard, not committed to a file — Vite bakes it
  into the build at build time)

**Do not set `GEMINI_API_KEY` here.** Anything prefixed `VITE_` ships to
every visitor's browser in plain text. The key belongs only on the
backend host from step 2. (Verified in this codebase: `GEMINI_API_KEY`
does not appear anywhere under a `VITE_` name in frontend source.)

## 4. Close the loop on CORS
Now that the frontend has a real URL, go back to the backend host and set:
```
NEUROPRICE_CORS_ORIGINS=https://your-frontend-url
```
Redeploy the backend for this to take effect.

## 5. Real end-to-end verification
This is the step that actually earns "100%" — not the deploy button
succeeding, but a real browser session completing the full chain:

1. Open the deployed frontend URL
2. Enter real marketing copy and economics
3. Submit — confirm the loading state appears
4. Confirm a real Gemini call completes (this is the one thing that was
   never testable inside this sandbox — no network route to Gemini here)
5. Confirm the recommended scenario, financial impact, psychology
   signals + evidence, assumptions, and sensitivity table all render
   with real (not mock) data
6. Try an intentionally bad input (e.g., variable cost above price) —
   confirm a clean validation message, not a raw error
7. Run a second analysis without reloading the page — confirm the reset
   flow works and no stale data bleeds through

If all seven pass, that's the genuine, verified 100% — not "the code
compiles," but "a real person can use the real product end to end."

## Do not, while deploying
- Do not change any formula in `pricing_engine.py`, `sensitivity.py`, or
  `evidence_validation.py`. The 67/67 test suite exists specifically so
  deployment stays plumbing, not a second chance to relitigate the model.
- Do not add a fake/default Gemini key anywhere "to make it work" if the
  real one isn't set yet — the fail-fast startup check is intentional.
- Do not skip step 5. A live URL that 500s on first real request is not
  a finished product.
