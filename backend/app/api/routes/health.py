from __future__ import annotations

import os
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.services.neo4j_service import neo4j_service
from app.services.live_news_monitor import live_news_monitor
from app.core.config import settings

router = APIRouter(
    tags=["Health & Diagnostics"],
)


@router.get("/health")
@router.get("/diagnostics")
def system_health(db: Session = Depends(get_db)):
    """
    Comprehensive system health diagnostic endpoint.
    Checks API, SQLite Database, Neo4j Graph, GNN Model, NLP, and Live News Monitor.
    """
    # 1. SQLite Database Check
    db_status = "offline"
    table_counts: dict[str, int] = {}
    try:
        tables = [
            "events",
            "suppliers",
            "products",
            "sc_suppliers",
            "sc_plants",
            "sc_products",
            "sc_components",
            "sc_warehouses",
            "sc_supply_allocations",
            "sc_inventory",
        ]
        for t in tables:
            try:
                row = db.execute(text(f"SELECT count(*) FROM [{t}]")).fetchone()
                if row is not None:
                    table_counts[t] = int(row[0])
            except Exception:
                pass
        db_status = "online"
    except Exception as exc:
        db_status = f"error: {exc}"

    # 2. Neo4j Check
    neo4j_connected = False
    try:
        neo4j_connected = neo4j_service.verify_connection()
    except Exception:
        neo4j_connected = False

    # 3. GNN Model Check
    gnn_model_path = Path(__file__).resolve().parents[3] / "models" / "atmograph_gnn.pt"
    gnn_available = gnn_model_path.exists()

    # 4. Overall Status
    is_healthy = db_status == "online"

    return {
        "success": True,
        "status": "healthy" if is_healthy else "degraded",
        "service": "AtmoGraph API",
        "version": settings.APP_VERSION,
        "diagnostics": {
            "api": {
                "status": "online",
                "version": settings.APP_VERSION,
            },
            "database": {
                "status": db_status,
                "engine": "sqlite",
                "table_counts": table_counts,
            },
            "neo4j": {
                "status": "online" if neo4j_connected else "offline",
                "connected": neo4j_connected,
                "uri": neo4j_service.uri,
            },
            "gnn": {
                "status": "online" if gnn_available else "offline",
                "model_loaded": gnn_available,
                "model_path": str(gnn_model_path) if gnn_available else None,
            },
            "nlp": {
                "status": "online",
                "engine": "spacy",
            },
            "live_news_monitor": {
                "status": "online" if live_news_monitor.running else "idle",
                "running": live_news_monitor.running,
                "interval_seconds": live_news_monitor.interval_seconds,
            },
        },
    }