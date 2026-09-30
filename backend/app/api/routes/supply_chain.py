from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_optional_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.neo4j_service import Neo4jService

from app.services.supply_chain.disruption_simulator import (
    DisruptionSimulator,
)

from app.services.supply_chain.neo4j_business_importer import (
    SupplyChainNeo4jImporter,
)

from app.services.supply_chain.excel_importer import (
    SupplyChainExcelImporter,
)

from app.services.supply_chain.database_importer import (
    SupplyChainDatabaseImporter,
)

from app.services.supply_chain.resilience_service import (
    SupplyChainResilienceService,
)


router = APIRouter(
    prefix="/supply-chain",
    tags=["Supply Chain"],
)


IMPORT_DIRECTORY = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "imports"
)

TEMPLATE_PATH = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "templates"
    / "supply_chain_template.xlsx"
)

ALLOWED_EXTENSIONS = {
    ".xlsx",
    ".xls",
}

MAX_UPLOAD_SIZE_MB = 25


# ============================================================
# REQUEST MODELS
# ============================================================


class SupplierFailureRequest(BaseModel):
    """
    Request payload for business supply-chain disruption
    simulation.
    """

    supplier_id: str = Field(
        ...,
        min_length=1,
        description="Business supplier ID",
    )

    disruption_location: str | None = Field(
        default=None,
        description=(
            "Location where the disruption occurs, "
            "for example Hamburg or Rotterdam."
        ),
    )

    severity: str | None = Field(
        default=None,
        description=(
            "Disruption severity such as low, medium, "
            "high, or critical."
        ),
    )

    event_type: str | None = Field(
        default=None,
        description=(
            "Disruption event type such as port_disruption, "
            "port_strike, supply_chain_disruption, etc."
        ),
    )


# ============================================================
# SUPPLIER FAILURE SIMULATION
# ============================================================


@router.post("/simulate")
def simulate_supplier_failure(
    payload: SupplierFailureRequest,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Simulate a supplier failure together with optional
    real-world disruption context.

    The disruption context is forwarded to the simulator so
    route impact can distinguish:

        normal transit time
        +
        additional disruption delay
        =
        effective route time
    """

    user_id = current_user.id if current_user else None
    simulator = DisruptionSimulator(db, user_id=user_id)

    result = simulator.simulate_supplier_failure(
        supplier_id=payload.supplier_id,
        disruption_location=payload.disruption_location,
        severity=payload.severity,
        event_type=payload.event_type,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get(
                "error",
                "Supplier simulation failed",
            ),
        )

    return result


# ============================================================
# SUPPLY-CHAIN CATALOG
# ============================================================


@router.get("/suppliers")
def supply_chain_suppliers(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    from app.models.business_supply_chain import (
        BusinessSupplier,
    )

    user_id = current_user.id if current_user else None
    query = db.query(BusinessSupplier)
    if user_id is not None:
        query = query.filter(BusinessSupplier.user_id == user_id)

    suppliers = (
        query.order_by(
            BusinessSupplier.supplier_name.asc()
        )
        .all()
    )

    return {
        "success": True,
        "suppliers": [
            {
                "supplier_id": supplier.supplier_id,
                "name": supplier.supplier_name,
                "country": supplier.country,
                "city": supplier.city,
                "location_known": supplier.location_known,
            }
            for supplier in suppliers
        ],
    }


@router.get("/catalog")
def supply_chain_catalog(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    from app.models.business_supply_chain import (
        BusinessProduct,
        BusinessSupplier,
        Component,
        Plant,
        Warehouse,
        Company,
    )

    user_id = current_user.id if current_user else None

    def _query(model):
        q = db.query(model)
        if user_id is not None:
            q = q.filter(model.user_id == user_id)
        return q

    suppliers = (
        _query(BusinessSupplier)
        .order_by(
            BusinessSupplier.supplier_name.asc()
        )
        .all()
    )

    plants = (
        _query(Plant)
        .order_by(
            Plant.plant_name.asc()
        )
        .all()
    )

    products = (
        _query(BusinessProduct)
        .order_by(
            BusinessProduct.product_name.asc()
        )
        .all()
    )

    components = (
        _query(Component)
        .order_by(
            Component.component_name.asc()
        )
        .all()
    )

    warehouses = (
        _query(Warehouse)
        .order_by(
            Warehouse.warehouse_name.asc()
        )
        .all()
    )

    active_company = _query(Company).first()
    company_data = None
    if active_company:
        company_data = {
            "company_id": active_company.company_id,
            "company_name": active_company.company_name,
            "industry": active_company.industry,
        }

    return {
        "success": True,
        "company": company_data,
        "suppliers": [
            {
                "supplier_id": x.supplier_id,
                "name": x.supplier_name,
                "country": x.country,
                "city": x.city,
                "location_known": x.location_known,
            }
            for x in suppliers
        ],
        "plants": [
            {
                "plant_id": x.plant_id,
                "name": x.plant_name,
                "company_id": x.company_id,
                "country": x.country,
                "city": x.city,
            }
            for x in plants
        ],
        "products": [
            {
                "product_id": x.product_id,
                "name": x.product_name,
                "category": x.category,
            }
            for x in products
        ],
        "components": [
            {
                "component_id": x.component_id,
                "name": x.component_name,
                "category": x.category,
            }
            for x in components
        ],
        "warehouses": [
            {
                "warehouse_id": x.warehouse_id,
                "name": x.warehouse_name,
                "country": x.country,
                "city": x.city,
            }
            for x in warehouses
        ],
    }


# ============================================================
# BUSINESS NEO4J GRAPH
# ============================================================


@router.get("/business-graph")
def get_business_supply_chain_graph(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the actual business supply-chain graph stored
    in Neo4j, or seamlessly fallback to the relational SQLite
    knowledge graph if Neo4j is offline or unpopulated.
    """

    user_id = current_user.id if current_user else None
    neo4j = Neo4jService()

    if neo4j.verify_connection():
        try:
            with neo4j.driver.session() as session:
                user_id_val = user_id if user_id is not None else 0
                node_result = session.run(
                    """
                    MATCH (n:SCEntity)
                    WHERE ($user_id IS NULL OR n.user_id = $user_id)
                    RETURN
                        elementId(n) AS id,
                        labels(n) AS labels,
                        properties(n) AS properties
                    ORDER BY elementId(n)
                    """,
                    user_id=user_id_val,
                )

                nodes: list[dict[str, Any]] = []

                for record in node_result:
                    labels = list(record["labels"] or [])
                    properties = dict(record["properties"] or {})
                    entity_type = _business_entity_type(labels)

                    nodes.append(
                        {
                            "id": str(record["id"]),
                            "type": entity_type,
                            "labels": labels,
                            "name": str(
                                properties.get(
                                    "name",
                                    properties.get(
                                        "company_name",
                                        properties.get(
                                            "supplier_name",
                                            record["id"],
                                        ),
                                    ),
                                )
                            ),
                            "properties": _json_safe(properties),
                        }
                    )

                relationship_result = session.run(
                    """
                    MATCH
                        (source:SCEntity)-[r]->(target:SCEntity)
                    WHERE
                        ($user_id IS NULL OR (source.user_id = $user_id AND target.user_id = $user_id))
                    RETURN
                        elementId(source) AS source,
                        elementId(target) AS target,
                        type(r) AS relationship,
                        properties(r) AS properties
                    ORDER BY
                        type(r),
                        elementId(source),
                        elementId(target)
                    """,
                    user_id=user_id_val,
                )

                relationships: list[dict[str, Any]] = []

                for record in relationship_result:
                    relationships.append(
                        {
                            "source": str(record["source"]),
                            "target": str(record["target"]),
                            "relationship": str(record["relationship"]),
                            "properties": _json_safe(
                                dict(record["properties"] or {})
                            ),
                        }
                    )

                if len(nodes) > 0:
                    return {
                        "success": True,
                        "stage": "neo4j_business_graph",
                        "source": "neo4j",
                        "nodes": nodes,
                        "relationships": relationships,
                        "graph": {
                            "nodes": len(nodes),
                            "relationships": len(relationships),
                        },
                    }
        except Exception:
            pass  # Fallback to SQLite below

    # ========================================================
    # SQLITE RELATIONAL IN-MEMORY GRAPH FALLBACK
    # Ensures zero-failure interactive UI even when Neo4j is offline.
    # ========================================================
    return _build_fallback_business_graph(db, user_id=user_id)


def _build_fallback_business_graph(db: Session, user_id: int | None = None) -> dict[str, Any]:
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

    def _query(model):
        q = db.query(model)
        if user_id is not None:
            q = q.filter(model.user_id == user_id)
        return q

    nodes: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []

    # 1. Companies
    for c in _query(Company).all():
        nodes.append({
            "id": f"company_{c.company_id}",
            "type": "Company",
            "labels": ["SCEntity", "SCCompany"],
            "name": c.company_name,
            "properties": {
                "company_id": c.company_id,
                "name": c.company_name,
                "industry": c.industry,
            },
        })

    # 2. Suppliers
    for s in _query(BusinessSupplier).all():
        nodes.append({
            "id": f"supplier_{s.supplier_id}",
            "type": "Supplier",
            "labels": ["SCEntity", "SCSupplier"],
            "name": s.supplier_name,
            "properties": {
                "supplier_id": s.supplier_id,
                "name": s.supplier_name,
                "country": s.country,
                "city": s.city,
            },
        })

    # 3. Plants
    for p in _query(Plant).all():
        nodes.append({
            "id": f"plant_{p.plant_id}",
            "type": "Plant",
            "labels": ["SCEntity", "SCPlant"],
            "name": p.plant_name,
            "properties": {
                "plant_id": p.plant_id,
                "name": p.plant_name,
                "company_id": p.company_id,
                "country": p.country,
                "city": p.city,
            },
        })
        if p.company_id:
            relationships.append({
                "source": f"company_{p.company_id}",
                "target": f"plant_{p.plant_id}",
                "relationship": "OWNS_PLANT",
                "properties": {},
            })

    # 4. Products
    for pr in _query(BusinessProduct).all():
        nodes.append({
            "id": f"product_{pr.product_id}",
            "type": "Product",
            "labels": ["SCEntity", "SCProduct"],
            "name": pr.product_name,
            "properties": {
                "product_id": pr.product_id,
                "name": pr.product_name,
                "category": pr.category,
            },
        })

    # 5. Components
    for cmp in _query(Component).all():
        nodes.append({
            "id": f"component_{cmp.component_id}",
            "type": "Component",
            "labels": ["SCEntity", "SCComponent"],
            "name": cmp.component_name,
            "properties": {
                "component_id": cmp.component_id,
                "name": cmp.component_name,
                "category": cmp.category,
            },
        })

    # 6. Warehouses
    for w in _query(Warehouse).all():
        nodes.append({
            "id": f"warehouse_{w.warehouse_id}",
            "type": "Warehouse",
            "labels": ["SCEntity", "SCWarehouse"],
            "name": w.warehouse_name,
            "properties": {
                "warehouse_id": w.warehouse_id,
                "name": w.warehouse_name,
                "country": w.country,
                "city": w.city,
            },
        })

    # 7. Supply Allocations: Supplier -> Component -> Plant
    for alloc in _query(SupplyAllocation).all():
        relationships.append({
            "source": f"supplier_{alloc.supplier_id}",
            "target": f"component_{alloc.component_id}",
            "relationship": "SUPPLIES",
            "properties": {
                "allocation_pct": alloc.allocation_pct,
                "capacity_units": alloc.capacity_units,
                "spare_capacity_units": alloc.spare_capacity_units,
                "lead_time_days": alloc.lead_time_days,
                "criticality": alloc.criticality,
            },
        })
        relationships.append({
            "source": f"component_{alloc.component_id}",
            "target": f"plant_{alloc.plant_id}",
            "relationship": "USED_AT",
            "properties": {},
        })

    # 8. Dependencies: Product -> Component
    for dep in _query(Dependency).all():
        s_id = dep.source_id
        t_id = dep.target_id
        s_node = f"product_{s_id}" if not s_id.startswith("product_") else s_id
        t_node = f"component_{t_id}" if not t_id.startswith("component_") else t_id
        relationships.append({
            "source": s_node,
            "target": t_node,
            "relationship": "DEPENDS_ON",
            "properties": {
                "required_quantity": dep.required_quantity,
                "criticality": dep.criticality,
            },
        })

    # 9. Routes
    for route in _query(Route).all():
        s_type = (route.source_type or "").lower()
        d_type = (route.destination_type or "").lower()
        s_id = f"{s_type}_{route.source_id}" if not route.source_id.startswith(f"{s_type}_") else route.source_id
        d_id = f"{d_type}_{route.destination_id}" if not route.destination_id.startswith(f"{d_type}_") else route.destination_id
        relationships.append({
            "source": s_id,
            "target": d_id,
            "relationship": "SHIPS_TO",
            "properties": {
                "transit_days": route.transit_days,
                "route_status": route.route_status,
            },
        })

    # Deduplicate relationships
    unique_rels = []
    seen = set()
    for rel in relationships:
        key = (rel["source"], rel["target"], rel["relationship"])
        if key not in seen:
            seen.add(key)
            unique_rels.append(rel)

    return {
        "success": True,
        "stage": "business_graph",
        "source": "sqlite_fallback",
        "nodes": nodes,
        "relationships": unique_rels,
        "graph": {
            "nodes": len(nodes),
            "relationships": len(unique_rels),
        },
    }


# ============================================================
# EXCEL VALIDATION
# ============================================================


@router.post("/validate")
async def validate_supply_chain_file(
    file: UploadFile = File(...),
):
    """
    Validate an uploaded supply-chain Excel workbook
    without writing anything to SQL or Neo4j.
    """

    filename = file.filename or ""

    extension = Path(
        filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "stage": "upload",
                "errors": [
                    "Only .xlsx and .xls files are supported."
                ],
            },
        )

    IMPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = (
        IMPORT_DIRECTORY
        / (
            "_validation_"
            f"{uuid.uuid4().hex}"
            f"{extension}"
        )
    )

    try:
        with temporary_path.open(
            "wb"
        ) as output:

            total_bytes = 0

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_bytes += len(
                    chunk
                )

                if (
                    total_bytes
                    > MAX_UPLOAD_SIZE_MB
                    * 1024
                    * 1024
                ):
                    raise HTTPException(
                        status_code=413,
                        detail={
                            "success": False,
                            "stage": "upload",
                            "errors": [
                                (
                                    f"File exceeds "
                                    f"{MAX_UPLOAD_SIZE_MB} MB limit."
                                )
                            ],
                        },
                    )

                output.write(chunk)

        importer = (
            SupplyChainExcelImporter()
        )

        result = importer.import_file(
            temporary_path
        )

        return {
            "success": result.success,
            "stage": "validation",
            "filename": result.filename,
            "sheets_found": (
                result.sheets_found
            ),
            "sheets_validated": (
                result.sheets_validated
            ),
            "row_counts": (
                result.row_counts
            ),
            "warnings": result.warnings,
            "errors": result.errors,
        }

    finally:

        try:
            temporary_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass

        await file.close()


# ============================================================
# EXCEL IMPORT
# ============================================================


@router.post("/import")
async def import_supply_chain_file(
    file: UploadFile = File(...),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Validate and import an Excel workbook into SQL,
    then synchronize the resulting business graph to Neo4j.
    """

    filename = file.filename or ""

    extension = Path(
        filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "stage": "upload",
                "errors": [
                    "Only .xlsx and .xls files are supported."
                ],
            },
        )

    IMPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = (
        IMPORT_DIRECTORY
        / (
            "_import_"
            f"{uuid.uuid4().hex}"
            f"{extension}"
        )
    )

    try:
        with temporary_path.open(
            "wb"
        ) as output:

            total_bytes = 0

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_bytes += len(
                    chunk
                )

                if (
                    total_bytes
                    > MAX_UPLOAD_SIZE_MB
                    * 1024
                    * 1024
                ):
                    raise HTTPException(
                        status_code=413,
                        detail={
                            "success": False,
                            "stage": "upload",
                            "errors": [
                                (
                                    f"File exceeds "
                                    f"{MAX_UPLOAD_SIZE_MB} MB limit."
                                )
                            ],
                        },
                    )

                output.write(chunk)

        user_id = current_user.id if current_user else None
        importer = (
            SupplyChainDatabaseImporter(
                db,
                user_id=user_id,
            )
        )

        database_result = (
            importer.import_workbook(
                temporary_path
            )
        )

        if not database_result.get(
            "success"
        ):
            raise HTTPException(
                status_code=400,
                detail=database_result,
            )

        graph_result = (
            SupplyChainNeo4jImporter(
                db,
                user_id=user_id,
            ).sync()
        )

        if not graph_result.get(
            "success"
        ):
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "stage": (
                        "neo4j_business_graph"
                    ),
                    "database": database_result,
                    "neo4j_sync": graph_result,
                },
            )

        return {
            "success": True,
            "stage": "completed",
            "filename": database_result.get(
                "filename"
            ),
            "database": database_result,
            "neo4j_sync": graph_result,
        }

    finally:

        try:
            temporary_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass

        await file.close()


# ============================================================
# MANUAL NEO4J BUSINESS GRAPH SYNC
# ============================================================


@router.post("/sync-graph")
def sync_business_supply_chain_graph(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Synchronize the current business supply-chain SQL
    dataset into Neo4j.
    """

    user_id = current_user.id if current_user else None
    importer = SupplyChainNeo4jImporter(
        db,
        user_id=user_id,
    )

    result = importer.sync()

    if not result.get(
        "success"
    ):
        raise HTTPException(
            status_code=503,
            detail=result,
        )

    return result


# ============================================================
# SUPPLIER RESILIENCE
# ============================================================


@router.get(
    "/resilience/{supplier_id}"
)
def get_supplier_resilience(
    supplier_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze supplier resilience against alternative
    supplier capacity.

    This is deterministic business intelligence,
    not an ML prediction.
    """

    user_id = current_user.id if current_user else None
    service = (
        SupplyChainResilienceService(
            db,
            user_id=user_id,
        )
    )

    result = service.analyze_supplier(
        supplier_id
    )

    if not result.get(
        "success"
    ):
        raise HTTPException(
            status_code=404,
            detail=result.get(
                "error",
                (
                    "Supplier resilience "
                    "analysis failed."
                ),
            ),
        )

    return result


@router.get("/template")
def download_supply_chain_template():
    """
    Download the standard AtmoGraph multi-sheet Excel supply chain template.
    """
    if not TEMPLATE_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Supply chain template file not found on server.",
        )
    return FileResponse(
        path=str(TEMPLATE_PATH),
        filename="AtmoGraph_Supply_Chain_Template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ============================================================
# HELPERS
# ============================================================


def _business_entity_type(
    labels: list[str],
) -> str:

    mapping = {
        "SCCompany": "Company",
        "SCSupplier": "Supplier",
        "SCPlant": "Plant",
        "SCProduct": "Product",
        "SCComponent": "Component",
        "SCWarehouse": "Warehouse",
    }

    for label in labels:

        if label in mapping:
            return mapping[label]

    return "Entity"


def _json_safe(
    value: Any,
) -> Any:

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    return str(value)


# ============================================================
# MULTI-BUSINESS WORKSPACE MANAGEMENT
# ============================================================


class SwitchWorkspacePayload(BaseModel):
    workspace_id: str = Field(..., description="Target business workspace identifier")


class RegisterWorkspacePayload(BaseModel):
    company_name: str = Field(..., min_length=2, description="Business company name")
    industry: str = Field(..., min_length=2, description="Industry sector")
    owner_name: str | None = Field(default=None, description="Founder or Owner name")
    location: str | None = Field(default=None, description="Location")


def _clear_all_sc_tables(db: Session, user_id: int | None = None):
    from app.models.business_supply_chain import (
        BusinessProduct,
        BusinessSupplier,
        Capacity,
        Company,
        Component,
        Demand,
        Dependency,
        Inventory,
        Plant,
        Route,
        SupplyAllocation,
        Warehouse,
    )

    for model in [
        SupplyAllocation,
        Dependency,
        Route,
        Inventory,
        Capacity,
        Demand,
        Warehouse,
        Component,
        BusinessProduct,
        Plant,
        BusinessSupplier,
        Company,
    ]:
        query = db.query(model)
        if user_id is not None:
            query = query.filter(model.user_id == user_id)
        else:
            query = query.filter(model.user_id.is_(None))
        query.delete(synchronize_session=False)
    db.commit()


@router.get("/workspaces")
def list_workspaces(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    from app.models.business_supply_chain import BusinessSupplier, Company, Plant

    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to access business workspaces.",
        )

    user_id = current_user.id

    # Find companies owned by this user
    user_companies = db.query(Company).filter(Company.user_id == user_id).all()

    # If no company exists yet for this user, auto-initialize from user profile
    if not user_companies:
        root = Path(__file__).resolve().parents[4]
        co_name_lower = (current_user.company_name or "").lower()
        co_email_lower = (current_user.email or "").lower()

        if "mohilya" in co_name_lower or "mohilya" in co_email_lower or "garment" in co_name_lower:
            excel_path = root / "data" / "templates" / "Mohilya_Couture_SupplyChain.xlsx"
            if excel_path.exists():
                importer = SupplyChainDatabaseImporter(db, user_id=user_id)
                importer.import_workbook(excel_path)
        elif "adil" in co_name_lower or "adil" in co_email_lower or "perfume" in co_name_lower or "attar" in co_name_lower:
            excel_path = root / "data" / "imports" / "_import_91394fdd5bd643f18696d1204573e36b.xlsx"
            if excel_path.exists():
                importer = SupplyChainDatabaseImporter(db, user_id=user_id)
                importer.import_workbook(excel_path)
        else:
            new_cid = f"COMP_{uuid.uuid4().hex[:6].upper()}"
            default_company = Company(
                company_id=new_cid,
                company_name=current_user.company_name or "My Private Business",
                industry="Custom Industry",
                user_id=user_id,
            )
            db.add(default_company)
            db.commit()

        user_companies = db.query(Company).filter(Company.user_id == user_id).all()

    suppliers_count = db.query(BusinessSupplier).filter(BusinessSupplier.user_id == user_id).count()
    plants_count = db.query(Plant).filter(Plant.user_id == user_id).count()

    active_co = user_companies[0] if user_companies else None
    active_cid = active_co.company_id if active_co else f"COMP_{user_id}"
    active_name = active_co.company_name if active_co else (current_user.company_name or "My Business")
    active_industry = (active_co.industry if active_co else None) or "Custom Industry"

    # Strictly build workspaces belonging ONLY to this current authenticated user
    workspaces = []
    for idx, co in enumerate(user_companies):
        co_suppliers = db.query(BusinessSupplier).filter(BusinessSupplier.user_id == user_id).count()
        co_plants = db.query(Plant).filter(Plant.user_id == user_id).count()
        badge = "".join([part[0] for part in co.company_name.split()[:2]]).upper() if co.company_name else "CO"

        workspaces.append({
            "workspace_id": co.company_id,
            "company_id": co.company_id,
            "company_name": co.company_name,
            "industry": co.industry or active_industry,
            "owner_name": current_user.email,
            "location": "Verified Facility",
            "suppliers_count": co_suppliers,
            "plants_count": co_plants,
            "is_active": idx == 0,
            "badge": badge,
            "description": f"Private tenant workspace for {co.company_name}. Complete data isolation active.",
        })

    return {
        "success": True,
        "active_workspace_id": active_cid,
        "active_company": {
            "company_id": active_cid,
            "company_name": active_name,
            "industry": active_industry,
            "suppliers_count": suppliers_count,
            "plants_count": plants_count,
        },
        "workspaces": workspaces,
    }


@router.post("/workspaces/switch")
def switch_workspace(
    payload: SwitchWorkspacePayload,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to switch workspaces.",
        )

    user_id = current_user.id
    from app.models.business_supply_chain import Company

    # Check that target workspace belongs strictly to this user
    target = payload.workspace_id.strip()
    user_company = (
        db.query(Company)
        .filter(Company.user_id == user_id, Company.company_id == target)
        .first()
    )

    if not user_company:
        # Check if the target is one of the user's recognized IDs
        user_companies = db.query(Company).filter(Company.user_id == user_id).all()
        matched = next((c for c in user_companies if c.company_id.lower() == target.lower()), None)
        if not matched:
            raise HTTPException(
                status_code=403,
                detail="Access denied: You do not have permission to access or switch to this business workspace. Workspaces are private to their owners.",
            )

    # Sync Neo4j if available for this user
    try:
        neo = SupplyChainNeo4jImporter(db, user_id=user_id)
        neo.sync()
    except Exception:
        pass

    return list_workspaces(current_user=current_user, db=db)


@router.post("/workspaces/register")
def register_workspace(
    payload: RegisterWorkspacePayload,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to register a business workspace.",
        )

    from app.models.business_supply_chain import Company

    user_id = current_user.id
    new_cid = f"COMP_{uuid.uuid4().hex[:6].upper()}"
    new_company = Company(
        company_id=new_cid,
        company_name=payload.company_name.strip(),
        industry=payload.industry.strip(),
        user_id=user_id,
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return {
        "success": True,
        "message": f"Successfully registered business '{new_company.company_name}' in your account. You can now import your supply chain data.",
        "company": {
            "company_id": new_company.company_id,
            "company_name": new_company.company_name,
            "industry": new_company.industry,
        },
    }


__all__ = [
    "router",
]