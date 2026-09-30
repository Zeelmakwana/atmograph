from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

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

from app.services.supply_chain.excel_importer import (
    SupplyChainExcelImporter,
)


class SupplyChainDatabaseImporter:
    """
    Import validated AtmoGraph supply-chain Excel data
    into business supply-chain SQL tables.

    Existing rows are updated for the given user_id.
    New rows are inserted with user_id attached.
    """

    def __init__(
        self,
        db: Session,
        user_id: int | None = None,
    ):
        self.db = db
        self.user_id = user_id
        self.validator = (
            SupplyChainExcelImporter()
        )

    # =========================================================
    # PUBLIC
    # =========================================================

    def import_workbook(
        self,
        file_path: str | Path,
    ) -> dict[str, Any]:

        validation = (
            self.validator.import_file(
                file_path
            )
        )

        if not validation.success:
            return {
                "success": False,
                "stage": "validation",
                "filename": validation.filename,
                "errors": validation.errors,
                "warnings": validation.warnings,
            }

        records = validation.records

        try:

            counts: dict[str, int] = {}

            counts["companies"] = (
                self._upsert_companies(
                    records.get(
                        "Companies",
                        [],
                    )
                )
            )

            counts["suppliers"] = (
                self._upsert_suppliers(
                    records.get(
                        "Suppliers",
                        [],
                    )
                )
            )

            counts["plants"] = (
                self._upsert_plants(
                    records.get(
                        "Plants",
                        [],
                    )
                )
            )

            counts["products"] = (
                self._upsert_products(
                    records.get(
                        "Products",
                        [],
                    )
                )
            )

            counts["components"] = (
                self._upsert_components(
                    records.get(
                        "Components",
                        [],
                    )
                )
            )

            counts["warehouses"] = (
                self._upsert_warehouses(
                    records.get(
                        "Warehouses",
                        [],
                    )
                )
            )

            counts["supply_allocations"] = (
                self._upsert_supply_allocations(
                    records.get(
                        "Supply_Allocations",
                        [],
                    )
                )
            )

            counts["inventory"] = (
                self._upsert_inventory(
                    records.get(
                        "Inventory",
                        [],
                    )
                )
            )

            counts["capacity"] = (
                self._upsert_capacity(
                    records.get(
                        "Capacity",
                        [],
                    )
                )
            )

            counts["demand"] = (
                self._upsert_demand(
                    records.get(
                        "Demand",
                        [],
                    )
                )
            )

            counts["routes"] = (
                self._upsert_routes(
                    records.get(
                        "Routes",
                        [],
                    )
                )
            )

            counts["dependencies"] = (
                self._upsert_dependencies(
                    records.get(
                        "Dependencies",
                        [],
                    )
                )
            )

            self.db.commit()

            return {
                "success": True,
                "stage": "database",
                "filename": validation.filename,
                "counts": counts,
                "warnings": validation.warnings,
                "errors": [],
            }

        except Exception as exc:

            self.db.rollback()

            return {
                "success": False,
                "stage": "database",
                "filename": validation.filename,
                "counts": {},
                "warnings": validation.warnings,
                "errors": [
                    (
                        "Database import failed: "
                        f"{exc}"
                    )
                ],
            }

    # =========================================================
    # COMPANIES
    # =========================================================

    def _upsert_companies(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            company_id = str(
                row["company_id"]
            )

            query = self.db.query(Company).filter(Company.company_id == company_id)
            if self.user_id is not None:
                query = query.filter(Company.user_id == self.user_id)
            existing = query.first()

            values = {
                "company_name": row[
                    "company_name"
                ],
                "industry": row.get(
                    "industry"
                ),
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    Company(
                        company_id=company_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # SUPPLIERS
    # =========================================================

    def _upsert_suppliers(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            supplier_id = str(
                row["supplier_id"]
            )

            query = self.db.query(BusinessSupplier).filter(BusinessSupplier.supplier_id == supplier_id)
            if self.user_id is not None:
                query = query.filter(BusinessSupplier.user_id == self.user_id)
            existing = query.first()

            values = {
                "supplier_name": row[
                    "supplier_name"
                ],
                "country": row.get(
                    "country"
                ),
                "city": row.get(
                    "city"
                ),
                "location_known": row.get(
                    "location_known"
                ),
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    BusinessSupplier(
                        supplier_id=supplier_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # PLANTS
    # =========================================================

    def _upsert_plants(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            plant_id = str(
                row["plant_id"]
            )

            query = self.db.query(Plant).filter(Plant.plant_id == plant_id)
            if self.user_id is not None:
                query = query.filter(Plant.user_id == self.user_id)
            existing = query.first()

            values = {
                "plant_name": row[
                    "plant_name"
                ],
                "company_id": str(
                    row["company_id"]
                ),
                "country": row.get(
                    "country"
                ),
                "city": row.get(
                    "city"
                ),
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    Plant(
                        plant_id=plant_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # PRODUCTS
    # =========================================================

    def _upsert_products(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            product_id = str(
                row["product_id"]
            )

            query = self.db.query(BusinessProduct).filter(BusinessProduct.product_id == product_id)
            if self.user_id is not None:
                query = query.filter(BusinessProduct.user_id == self.user_id)
            existing = query.first()

            values = {
                "product_name": row[
                    "product_name"
                ],
                "category": row.get(
                    "category"
                ),
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    BusinessProduct(
                        product_id=product_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # COMPONENTS
    # =========================================================

    def _upsert_components(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            component_id = str(
                row["component_id"]
            )

            query = self.db.query(Component).filter(Component.component_id == component_id)
            if self.user_id is not None:
                query = query.filter(Component.user_id == self.user_id)
            existing = query.first()

            values = {
                "component_name": row[
                    "component_name"
                ],
                "category": row.get(
                    "category"
                ),
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    Component(
                        component_id=component_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # WAREHOUSES
    # =========================================================

    def _upsert_warehouses(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            warehouse_id = str(
                row["warehouse_id"]
            )

            query = self.db.query(Warehouse).filter(Warehouse.warehouse_id == warehouse_id)
            if self.user_id is not None:
                query = query.filter(Warehouse.user_id == self.user_id)
            existing = query.first()

            values = {
                "warehouse_name": row[
                    "warehouse_name"
                ],
                "country": row.get(
                    "country"
                ),
                "city": row.get(
                    "city"
                ),
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    Warehouse(
                        warehouse_id=warehouse_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # SUPPLY ALLOCATIONS
    # =========================================================

    def _upsert_supply_allocations(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            supplier_id = str(
                row["supplier_id"]
            )

            component_id = str(
                row["component_id"]
            )

            plant_id = str(
                row["plant_id"]
            )

            query = self.db.query(SupplyAllocation).filter(
                SupplyAllocation.supplier_id == supplier_id,
                SupplyAllocation.component_id == component_id,
                SupplyAllocation.plant_id == plant_id,
            )
            if self.user_id is not None:
                query = query.filter(SupplyAllocation.user_id == self.user_id)
            existing = query.first()

            spare_capacity_units = (
                self._number(
                    row.get(
                        "spare_capacity_units",
                        0.0,
                    )
                )
            )

            if spare_capacity_units < 0:
                spare_capacity_units = 0.0

            values = {
                "allocation_pct": row[
                    "allocation_pct"
                ],
                "capacity_units": row[
                    "capacity_units"
                ],
                "spare_capacity_units": (
                    spare_capacity_units
                ),
                "lead_time_days": row[
                    "lead_time_days"
                ],
                "criticality": row.get(
                    "criticality"
                ),
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    SupplyAllocation(
                        supplier_id=supplier_id,
                        component_id=component_id,
                        plant_id=plant_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # INVENTORY
    # =========================================================

    def _upsert_inventory(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            inventory_id = str(
                row["inventory_id"]
            )

            query = self.db.query(Inventory).filter(Inventory.inventory_id == inventory_id)
            if self.user_id is not None:
                query = query.filter(Inventory.user_id == self.user_id)
            existing = query.first()

            values = {
                "location_type": row[
                    "location_type"
                ],
                "location_id": str(
                    row["location_id"]
                ),
                "component_id": str(
                    row["component_id"]
                ),
                "quantity_units": row[
                    "quantity_units"
                ],
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    Inventory(
                        inventory_id=inventory_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # CAPACITY
    # =========================================================

    def _upsert_capacity(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            capacity_id = str(
                row["capacity_id"]
            )

            query = self.db.query(Capacity).filter(Capacity.capacity_id == capacity_id)
            if self.user_id is not None:
                query = query.filter(Capacity.user_id == self.user_id)
            existing = query.first()

            values = {
                "location_type": row[
                    "location_type"
                ],
                "location_id": str(
                    row["location_id"]
                ),
                "component_id": str(
                    row["component_id"]
                ),
                "capacity_units_per_day": row[
                    "capacity_units_per_day"
                ],
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    Capacity(
                        capacity_id=capacity_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # DEMAND
    # =========================================================

    def _upsert_demand(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            demand_id = str(
                row["demand_id"]
            )

            query = self.db.query(Demand).filter(Demand.demand_id == demand_id)
            if self.user_id is not None:
                query = query.filter(Demand.user_id == self.user_id)
            existing = query.first()

            values = {
                "plant_id": str(
                    row["plant_id"]
                ),
                "product_id": str(
                    row["product_id"]
                ),
                "daily_demand_units": row[
                    "daily_demand_units"
                ],
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    Demand(
                        demand_id=demand_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # ROUTES
    # =========================================================

    def _upsert_routes(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            route_id = str(
                row["route_id"]
            )

            query = self.db.query(Route).filter(Route.route_id == route_id)
            if self.user_id is not None:
                query = query.filter(Route.user_id == self.user_id)
            existing = query.first()

            values = {
                "source_type": row[
                    "source_type"
                ],
                "source_id": str(
                    row["source_id"]
                ),
                "destination_type": row[
                    "destination_type"
                ],
                "destination_id": str(
                    row["destination_id"]
                ),
                "transit_days": row[
                    "transit_days"
                ],
                "route_status": row.get(
                    "route_status"
                ),
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    Route(
                        route_id=route_id,
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # DEPENDENCIES
    # =========================================================

    def _upsert_dependencies(
        self,
        rows: list[dict[str, Any]],
    ) -> int:

        for row in rows:

            dependency_id = str(
                row["dependency_id"]
            )

            query = self.db.query(Dependency).filter(Dependency.dependency_id == dependency_id)
            if self.user_id is not None:
                query = query.filter(Dependency.user_id == self.user_id)
            existing = query.first()

            required_quantity = (
                self._number(
                    row.get(
                        "required_quantity",
                        1.0,
                    )
                )
            )

            if required_quantity <= 0:
                required_quantity = 1.0

            values = {
                "source_type": row[
                    "source_type"
                ],
                "source_id": str(
                    row["source_id"]
                ),
                "target_type": row[
                    "target_type"
                ],
                "target_id": str(
                    row["target_id"]
                ),
                "dependency_type": row[
                    "dependency_type"
                ],
                "required_quantity": (
                    required_quantity
                ),
                "criticality": row.get(
                    "criticality"
                ),
            }

            if existing:

                for key, value in (
                    values.items()
                ):
                    setattr(
                        existing,
                        key,
                        value,
                    )

            else:

                self.db.add(
                    Dependency(
                        dependency_id=(
                            dependency_id
                        ),
                        user_id=self.user_id,
                        **values,
                    )
                )

        return len(rows)

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _number(
        value: Any,
    ) -> float:

        try:
            return float(
                value or 0.0
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0


__all__ = [
    "SupplyChainDatabaseImporter",
]
