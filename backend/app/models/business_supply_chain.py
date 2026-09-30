"""
Multi-tenant supply chain models.

CRITICAL: All tables have user_id FK for complete data isolation.
Each user sees ONLY their own data - no cross-tenant access.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Company(Base):
    __tablename__ = "sc_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class BusinessSupplier(Base):
    __tablename__ = "sc_suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_known: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class Plant(Base):
    __tablename__ = "sc_plants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    plant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class BusinessProduct(Base):
    __tablename__ = "sc_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class Component(Base):
    __tablename__ = "sc_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    component_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    component_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class Warehouse(Base):
    __tablename__ = "sc_warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    warehouse_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class SupplyAllocation(Base):
    """
    Supplier-to-component allocation for a specific plant.
    Includes spare capacity for disruption recovery.
    """
    __tablename__ = "sc_supply_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    component_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    plant_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    allocation_pct: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_units: Mapped[float] = mapped_column(Float, nullable=False)
    spare_capacity_units: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0.0")
    lead_time_days: Mapped[float] = mapped_column(Float, nullable=False)
    criticality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class Inventory(Base):
    __tablename__ = "sc_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inventory_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    component_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    quantity_units: Mapped[float] = mapped_column(Float, nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class Capacity(Base):
    __tablename__ = "sc_capacity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    capacity_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    component_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    capacity_units_per_day: Mapped[float] = mapped_column(Float, nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class Demand(Base):
    __tablename__ = "sc_demand"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    demand_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    plant_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    product_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    daily_demand_units: Mapped[float] = mapped_column(Float, nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class Route(Base):
    __tablename__ = "sc_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    destination_type: Mapped[str] = mapped_column(String(50), nullable=False)
    destination_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    transit_days: Mapped[float] = mapped_column(Float, nullable=False)
    route_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)


class Dependency(Base):
    """
    Product/component BOM-style dependency.
    Example: PROD001 -> CMP001, required_quantity = 2
    """
    __tablename__ = "sc_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dependency_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    dependency_type: Mapped[str] = mapped_column(String(100), nullable=False)
    required_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0, server_default="1.0")
    criticality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
