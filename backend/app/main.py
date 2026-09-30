from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    events_router,
    graph_router,
    graph_intelligence_router,
    predictions_router,
    ripple_router,
    analysis_router,
    dashboard_router,
    impact_graph_router,
    event_analytics_router,
    news_intelligence_router,
    supply_chain_router,
    news_router,
    historical_intelligence_router,
    health_router,
    risk_router,
    relationships_router,
    nlp_graph_router,
    auth_router,
)

from app.api.routes.nlp import router as nlp_router
from app.api.routes.websocket import router as websocket_router
from app.services.live_news_monitor import live_news_monitor


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.

    Startup:
        - Start live news monitoring.

    Shutdown:
        - Stop live news monitoring cleanly.
    """

    # --------------------------------------------------------
    # STARTUP
    # --------------------------------------------------------

    live_news_monitor.start()

    try:
        yield

    finally:

        # ----------------------------------------------------
        # SHUTDOWN
        # ----------------------------------------------------

        await live_news_monitor.stop()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AtmoGraph API",
    description=(
        "AI-powered supply chain "
        "ripple-effect prediction and intelligence platform."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH & DIAGNOSTICS
# ============================================================

app.include_router(health_router)
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


# ============================================================
# CORE API ROUTES
# ============================================================

app.include_router(
    events_router,
    prefix="/api",
)

app.include_router(
    graph_router,
    prefix="/api",
)

app.include_router(
    predictions_router,
    prefix="/api",
)

app.include_router(
    ripple_router,
    prefix="/api",
)

app.include_router(
    analysis_router,
    prefix="/api",
)

app.include_router(
    dashboard_router,
    prefix="/api",
)

app.include_router(
    impact_graph_router,
    prefix="/api",
)

app.include_router(
    event_analytics_router,
    prefix="/api",
)

app.include_router(
    news_intelligence_router,
    prefix="/api",
)

app.include_router(
    news_router,
    prefix="/api",
)


# ============================================================
# GRAPH INTELLIGENCE
#
# graph_intelligence.py already provides:
#
# /features/{graph_id}
# /gnn-graph/{graph_id}
# /gnn-predict/{graph_id}
# /hybrid-predict/{event_id}/{graph_id}
#
# Final URLs:
#
# /api/graph-intelligence/...
# ============================================================

app.include_router(
    graph_intelligence_router,
    prefix="/api",
)


# ============================================================
# NLP
# ============================================================

app.include_router(
    nlp_router,
    prefix="/api",
)


# ============================================================
# SUPPLY CHAIN
# ============================================================

app.include_router(
    supply_chain_router,
    prefix="/api",
)

app.include_router(
    historical_intelligence_router,
    prefix="/api",
)

app.include_router(
    risk_router,
    prefix="/api",
)

app.include_router(
    relationships_router,
    prefix="/api",
)

app.include_router(
    nlp_graph_router,
    prefix="/api",
)


# ============================================================
# WEBSOCKET
#
# websocket.py:
#
# prefix = /ws
# route   = /updates
#
# Final:
#
# ws://127.0.0.1:8000/ws/updates
# ============================================================

app.include_router(
    websocket_router,
)


# ============================================================
# ROOT
# ============================================================

@app.get(
    "/",
    tags=["Health"],
)
def root():
    return {
        "service": "AtmoGraph",
        "status": "online",
        "docs": "/docs",
        "health": "/health",
        "diagnostics": "/api/diagnostics",
        "nlp": "/api/nlp/analyze",
        "graph_intelligence": "/api/graph-intelligence",
        "news": "/api/news",
        "rss_ingestion": "/api/news/ingest-rss",
        "news_monitor": "/api/news/monitor-status",
        "historical_intelligence": "/api/historical-intelligence",
        "supply_chain": "/api/supply-chain",
        "websocket": "/ws/updates",
    }

