from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# ROUTE IMPACT
# ============================================================


class IntelligenceRouteImpact(BaseModel):
    """
    Canonical route intelligence.

    Timing semantics:

        normal_transit_days
            = normal route transit.

        additional_disruption_delay_days
            = delay caused by the disruption.

        effective_route_time_days
            = normal transit + disruption delay.
    """

    routes_known: bool = False
    location_match: bool = False

    routes_analyzed: int = 0
    disrupted_routes: int = 0

    normal_transit_days: float = 0.0
    additional_disruption_delay_days: float = 0.0
    effective_route_time_days: float = 0.0

    route_delay_days: float = 0.0
    effective_delay_days: float = 0.0


# ============================================================
# BUSINESS IMPACT
# ============================================================


class IntelligenceBusinessImpact(BaseModel):
    """
    Canonical business-level supply-chain impact.
    """

    affected_components: int = 0
    affected_products: int = 0
    affected_plants: int = 0

    gross_lost_supply: float = 0.0
    alternative_recovery: float = 0.0
    gross_shortage: float = 0.0
    net_shortage: float = 0.0

    products_buffered: int = 0
    products_route_delayed: int = 0
    products_with_shortage: int = 0

    production_stop: bool = False

    max_delay_days: float = 0.0
    max_risk_score: float = 0.0


# ============================================================
# SUPPLIER EXPOSURE
# ============================================================


class IntelligenceSupplierExposure(BaseModel):
    """
    Supplier exposure produced by event-to-business matching.
    """

    matched_count: int = 0
    affected_count: int = 0

    matched_suppliers: list[dict[str, Any]] = Field(
        default_factory=list
    )

    affected_suppliers: list[dict[str, Any]] = Field(
        default_factory=list
    )


# ============================================================
# RESILIENCE
# ============================================================


class IntelligenceResilience(BaseModel):
    """
    Deterministic supplier resilience information.

    This is business-capacity analysis, not an ML prediction.
    """

    available: bool = False

    recovery_units: float = 0.0
    unrecovered_units: float = 0.0
    recovery_percentage: float = 0.0

    resilience_score: float = 0.0
    resilience_level: str = "unknown"

    alternative_supplier_count: int = 0

    supplier_id: str | None = None
    supplier_name: str | None = None


# ============================================================
# RISK
# ============================================================


class IntelligenceRisk(BaseModel):
    """
    Unified risk interpretation.
    """

    score: float = 0.0
    level: str = "low"

    production_stop: bool = False

    confidence: float | None = None

    basis: list[str] = Field(
        default_factory=list
    )


# ============================================================
# PREDICTION
# ============================================================


class IntelligencePrediction(BaseModel):
    """
    Existing prediction/GNN/hybrid prediction summary.

    Full raw prediction remains available in the legacy
    top-level `prediction` field.
    """

    available: bool = False

    risk_score: float = 0.0
    risk_level: str = "unknown"

    estimated_delay_days: float = 0.0

    model: str | None = None
    model_loaded: bool | None = None


# ============================================================
# EVENT
# ============================================================


class IntelligenceEvent(BaseModel):
    """
    Canonical event understanding.
    """

    event_id: int | None = None
    title: str = ""
    description: str = ""
    source: str = ""

    event_type: str = "unknown"
    location: str | None = None
    severity: str = "unknown"
    status: str = "active"

    confidence: float | None = None


# ============================================================
# UNIFIED INTELLIGENCE
# ============================================================


class UnifiedIntelligence(BaseModel):
    """
    Stable frontend-facing AtmoGraph intelligence contract.

    Raw/legacy pipeline output is intentionally preserved
    separately for backward compatibility.
    """

    version: str = "1.0"

    event: IntelligenceEvent = Field(
        default_factory=IntelligenceEvent
    )

    supplier_exposure: IntelligenceSupplierExposure = Field(
        default_factory=IntelligenceSupplierExposure
    )

    business_impact: IntelligenceBusinessImpact = Field(
        default_factory=IntelligenceBusinessImpact
    )

    route_impact: IntelligenceRouteImpact = Field(
        default_factory=IntelligenceRouteImpact
    )

    resilience: IntelligenceResilience = Field(
        default_factory=IntelligenceResilience
    )

    risk: IntelligenceRisk = Field(
        default_factory=IntelligenceRisk
    )

    prediction: IntelligencePrediction = Field(
        default_factory=IntelligencePrediction
    )

    recommendations: list[str] = Field(
        default_factory=list
    )


__all__ = [
    "IntelligenceRouteImpact",
    "IntelligenceBusinessImpact",
    "IntelligenceSupplierExposure",
    "IntelligenceResilience",
    "IntelligenceRisk",
    "IntelligencePrediction",
    "IntelligenceEvent",
    "UnifiedIntelligence",
]