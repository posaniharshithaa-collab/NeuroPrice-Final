"""
NeuroPrice — FastAPI Layer (Phase 3)

This file is deliberately thin. It does exactly three things:
  1. Validate the SHAPE of the incoming HTTP request (types, required
     fields) via Pydantic.
  2. Hand off to the already-tested orchestrator/core pipeline.
  3. Translate the result into an HTTP response.

It does NOT re-validate business rules (that's ProductEconomics /
ModelingControl's job), does NOT touch Gemini directly (that's the
adapter's job), and does NOT compute anything financial (that's
pricing_engine's job). If you find yourself writing a formula in this
file, that's a sign it belongs somewhere else.
"""

import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from functools import lru_cache
from typing import Literal

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pricing_engine import ProductEconomics, ModelingControl
from core import run_full_analysis, GeminiClient
from gemini_adapter import RealGeminiClient, GeminiAdapterConfigError


@lru_cache
def _real_client_singleton() -> RealGeminiClient:
    return RealGeminiClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast: construct the real client once at boot. If GEMINI_API_KEY
    # is missing, GeminiAdapterConfigError propagates out of here and the
    # app refuses to start at all -- not "starts fine, breaks on first
    # request." A misconfigured deployment should never reach a healthy
    # state in the first place.
    _real_client_singleton()
    yield


app = FastAPI(title="NeuroPrice API", version="1.0", lifespan=lifespan)

# CORS: default covers local Vite dev. Production deployments must set
# NEUROPRICE_CORS_ORIGINS to the real deployed frontend origin(s) --
# comma-separated for multiple. There is no wildcard default.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("NEUROPRICE_CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Request / response shape (structural validation only -- no business rules
# duplicated here; those live in ProductEconomics.__post_init__)
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    current_price: float
    variable_cost: float
    conversion_rate: float
    estimated_market_size: int
    price_elasticity: float | None = None
    customer_segment: Literal["price_sensitive", "neutral", "price_insensitive"] = "neutral"
    psychology_weight: float = Field(default=0.40)
    marketing_copy: str


# ---------------------------------------------------------------------------
# Gemini client as a FastAPI dependency, not a bare module-level global --
# this is what lets tests swap in FakeGeminiClient with dependency_overrides
# without touching this file at all. Configuration failure is no longer a
# concern HERE: by the time any request reaches this dependency, lifespan()
# has already guaranteed the real client constructs successfully.
# ---------------------------------------------------------------------------

def get_gemini_client() -> GeminiClient:
    return _real_client_singleton()


# ---------------------------------------------------------------------------
# The one endpoint
# ---------------------------------------------------------------------------

@app.post("/analyze")
def analyze(request: AnalyzeRequest, client: GeminiClient = Depends(get_gemini_client)):
    try:
        econ = ProductEconomics(
            current_price=request.current_price,
            variable_cost=request.variable_cost,
            conversion_rate=request.conversion_rate,
            estimated_market_size=request.estimated_market_size,
            price_elasticity=request.price_elasticity,
            customer_segment=request.customer_segment,
        )
        control = ModelingControl(psychology_weight=request.psychology_weight)
    except ValueError as e:
        # ProductEconomics/ModelingControl's own validation rejected the
        # input -- this is the ONE place business validation errors are
        # translated into an HTTP status, not re-implemented.
        raise HTTPException(status_code=400, detail=str(e))

    result = run_full_analysis(request.marketing_copy, econ, control, client)

    # A Gemini analysis failure (both attempts exhausted) is a well-defined,
    # legitimate outcome of the pipeline -- not a server error. It returns
    # HTTP 200 with ok=false so the frontend can render the "unavailable"
    # state directly from the response body, exactly as designed upstream.
    return asdict(result)
