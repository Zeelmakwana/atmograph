"""
Database initialization script for multi-tenant AtmoGraph.

Creates all tables including the new users table and user_id FK columns.
"""

from app.core.database import Base, engine
from app.models.user import User
from app.models.business_supply_chain import (
    Company,
    BusinessSupplier,
    Plant,
    BusinessProduct,
    Component,
    Warehouse,
    SupplyAllocation,
    Inventory,
    Capacity,
    Demand,
    Route,
    Dependency,
)


def init_database():
    """
    Create all database tables.

    This will create:
    - users table (multi-tenant authentication)
    - All supply chain tables with user_id FK
    """
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("✓ Database tables created successfully")
    print("Tables created:")
    print("  - users (authentication)")
    print("  - sc_companies")
    print("  - sc_suppliers")
    print("  - sc_plants")
    print("  - sc_products")
    print("  - sc_components")
    print("  - sc_warehouses")
    print("  - sc_supply_allocations")
    print("  - sc_inventory")
    print("  - sc_capacity")
    print("  - sc_demand")
    print("  - sc_routes")
    print("  - sc_dependencies")


if __name__ == "__main__":
    init_database()
