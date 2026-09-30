from app.api.routes.events import router as events_router
from app.api.routes.graph import router as graph_router
from app.api.routes.graph_intelligence import router as graph_intelligence_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.ripple import router as ripple_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.impact_graph import router as impact_graph_router
from app.api.routes.event_analytics import router as event_analytics_router
from app.api.routes.news_intelligence import router as news_intelligence_router
from app.api.routes.news import router as news_router
from app.api.routes.supply_chain import router as supply_chain_router
from app.api.routes.historical_intelligence import router as historical_intelligence_router
from app.api.routes.health import router as health_router
from app.api.routes.risk import router as risk_router
from app.api.routes.relationships import router as relationships_router
from app.api.routes.nlp_graph import router as nlp_graph_router
from app.api.routes.auth import router as auth_router

__all__ = [
    "events_router",
    "graph_router",
    "graph_intelligence_router",
    "predictions_router",
    "ripple_router",
    "analysis_router",
    "dashboard_router",
    "impact_graph_router",
    "event_analytics_router",
    "news_intelligence_router",
    "news_router",
    "supply_chain_router",
    "historical_intelligence_router",
    "health_router",
    "risk_router",
    "relationships_router",
    "nlp_graph_router",
    "auth_router",
]

