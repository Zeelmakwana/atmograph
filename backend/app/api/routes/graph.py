"""
AtmoGraph Graph API.

Neo4j graph intelligence endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.services.neo4j_service import neo4j_service
from app.services.graph_sync_service import GraphSyncService


router = APIRouter(
    prefix="/graph",
    tags=["Graph"],
)


# ============================================================
# STATUS
# ============================================================

@router.get("/status")
def graph_status():
    """Check Neo4j connection."""

    connected = neo4j_service.verify_connection()

    return {
        "success": True,
        "neo4j": {
            "connected": connected,
            "uri": neo4j_service.uri,
        },
    }


# ============================================================
# SYNC
# ============================================================

@router.post("/sync")
def sync_graph(
    db: Session = Depends(get_db),
):
    """Synchronize SQL database with Neo4j."""

    service = GraphSyncService(
        db=db,
        neo4j=neo4j_service,
    )

    try:

        result = service.sync_all()

        return {
            "success": True,
            "message": "Supply-chain graph synchronized successfully.",
            "data": result,
        }

    except ConnectionError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Graph synchronization failed: {exc}",
        ) from exc


# ============================================================
# STATISTICS
# ============================================================

@router.get("/statistics")
def graph_statistics(
    db: Session = Depends(get_db),
):
    """Return Neo4j graph statistics, or fallback to SQLite supply chain dataset if offline."""

    if neo4j_service.verify_connection():
        try:
            statistics = neo4j_service.get_graph_statistics()
            total_n = int(statistics.get("total_nodes", 0) or 0)
            if total_n > 0:
                return {
                    "success": True,
                    "source": "neo4j",
                    "data": statistics,
                }
        except Exception:
            pass

    # SQLite fallback
    try:
        from app.models.business_supply_chain import (
            Company,
            BusinessSupplier,
            Plant,
            BusinessProduct,
            Component,
            Warehouse,
            SupplyAllocation,
            Dependency,
            Route,
        )
        total_nodes = (
            db.query(Company).count()
            + db.query(BusinessSupplier).count()
            + db.query(Plant).count()
            + db.query(BusinessProduct).count()
            + db.query(Component).count()
            + db.query(Warehouse).count()
        )
        total_relationships = (
            db.query(SupplyAllocation).count() * 2
            + db.query(Dependency).count()
            + db.query(Route).count()
        )
        return {
            "success": True,
            "source": "sqlite_fallback",
            "data": {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
            },
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve graph statistics: {exc}",
        ) from exc


# ============================================================
# EVENT DETAILS
# ============================================================

@router.get("/event/{event_id}")
def get_event_graph(
    event_id: int,
    depth: int = Query(
        default=4,
        ge=1,
        le=6,
    ),
):
    """Return graph surrounding an event."""

    if not neo4j_service.verify_connection():

        raise HTTPException(
            status_code=503,
            detail="Neo4j is not available.",
        )

    try:

        details = neo4j_service.get_event_details(
            event_id
        )

        if not details:

            raise HTTPException(
                status_code=404,
                detail=f"Event {event_id} not found in Neo4j.",
            )

        graph = neo4j_service.get_event_graph(
            event_id=event_id,
            max_depth=depth,
        )

        return {
            "success": True,
            "event_id": event_id,
            "depth": depth,
            "event": details[0],
            "graph": graph,
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve event graph: {exc}",
        ) from exc


# ============================================================
# AFFECTED SUPPLIERS
# ============================================================

@router.get("/event/{event_id}/suppliers")
def get_affected_suppliers(
    event_id: int,
):
    """Return suppliers affected by an event."""

    if not neo4j_service.verify_connection():

        raise HTTPException(
            status_code=503,
            detail="Neo4j is not available.",
        )

    try:

        suppliers = (
            neo4j_service.get_affected_suppliers(
                event_id
            )
        )

        return {
            "success": True,
            "event_id": event_id,
            "count": len(suppliers),
            "suppliers": suppliers,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve affected suppliers: {exc}",
        ) from exc


# ============================================================
# AFFECTED PRODUCTS
# ============================================================

@router.get("/event/{event_id}/products")
def get_affected_products(
    event_id: int,
):
    """Return products affected by an event."""

    if not neo4j_service.verify_connection():

        raise HTTPException(
            status_code=503,
            detail="Neo4j is not available.",
        )

    try:

        products = (
            neo4j_service.get_affected_products(
                event_id
            )
        )

        return {
            "success": True,
            "event_id": event_id,
            "count": len(products),
            "products": products,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve affected products: {exc}",
        ) from exc


# ============================================================
# RIPPLE PATHS
# ============================================================

@router.get("/event/{event_id}/ripple")
def get_ripple_paths(
    event_id: int,
    depth: int = Query(
        default=5,
        ge=1,
        le=6,
    ),
):
    """Return downstream ripple paths."""

    if not neo4j_service.verify_connection():

        raise HTTPException(
            status_code=503,
            detail="Neo4j is not available.",
        )

    try:

        paths = neo4j_service.get_ripple_paths(
            event_id=event_id,
            max_depth=depth,
        )

        return {
            "success": True,
            "event_id": event_id,
            "depth": depth,
            "path_count": len(paths),
            "paths": paths,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to calculate ripple paths: {exc}",
        ) from exc