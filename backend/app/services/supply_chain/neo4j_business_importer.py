from __future__ import annotations

from typing import Any

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

from app.services.neo4j_service import Neo4jService


class SupplyChainNeo4jImporter:
    """
    Synchronize the business supply-chain SQL model into Neo4j.

    SQL
      ↓
    Business Supply Chain Graph

    Neo4j business labels:

        SCEntity
        SCCompany
        SCSupplier
        SCPlant
        SCProduct
        SCComponent
        SCWarehouse

    Relationships:

        OWNS_PLANT
        SUPPLIES
        USED_AT
        STORES
        PRODUCES_CAPACITY
        DEMANDS
        SHIPS_TO
        DEPENDS_ON

    Supply allocation properties:

        allocation_pct
        capacity_units
        spare_capacity_units
        lead_time_days
        criticality

    Dependency properties:

        dependency_type
        required_quantity
        criticality

    Existing Event/NLP graph is intentionally preserved.
    """

    def __init__(
        self,
        db,
        user_id: int | None = None,
    ):
        self.db = db
        self.user_id = user_id
        self.neo4j = Neo4jService()

    def _get_rows(self, model):
        query = self.db.query(model)
        if self.user_id is not None:
            query = query.filter(model.user_id == self.user_id)
        return query.all()

    # =========================================================
    # PUBLIC
    # =========================================================

    def sync(self) -> dict[str, Any]:

        if not self.neo4j.verify_connection():
            return {
                "success": False,
                "stage": (
                    "neo4j_business_graph"
                ),
                "counts": {},
                "graph": {},
                "errors": [
                    "Unable to connect to Neo4j."
                ],
            }

        try:

            with self.neo4j.driver.session() as session:

                self._create_constraints(
                    session
                )

                counts = {
                    "companies": (
                        self._sync_companies(
                            session
                        )
                    ),
                    "suppliers": (
                        self._sync_suppliers(
                            session
                        )
                    ),
                    "plants": (
                        self._sync_plants(
                            session
                        )
                    ),
                    "products": (
                        self._sync_products(
                            session
                        )
                    ),
                    "components": (
                        self._sync_components(
                            session
                        )
                    ),
                    "warehouses": (
                        self._sync_warehouses(
                            session
                        )
                    ),
                    "allocations": (
                        self._sync_allocations(
                            session
                        )
                    ),
                    "inventory": (
                        self._sync_inventory(
                            session
                        )
                    ),
                    "capacity": (
                        self._sync_capacity(
                            session
                        )
                    ),
                    "demand": (
                        self._sync_demand(
                            session
                        )
                    ),
                    "routes": (
                        self._sync_routes(
                            session
                        )
                    ),
                    "dependencies": (
                        self._sync_dependencies(
                            session
                        )
                    ),
                }

                node_result = session.run(
                    """
                    MATCH (n:SCEntity)
                    WHERE ($user_id IS NULL OR n.user_id = $user_id)
                    RETURN count(n) AS count
                    """,
                    user_id=self.user_id if self.user_id is not None else 0,
                ).single()

                relationship_result = session.run(
                    """
                    MATCH (:SCEntity)-[r]->(:SCEntity)
                    WHERE ($user_id IS NULL OR r.user_id = $user_id)
                    RETURN count(r) AS count
                    """,
                    user_id=self.user_id if self.user_id is not None else 0,
                ).single()

                nodes = (
                    int(
                        node_result["count"]
                    )
                    if node_result
                    else 0
                )

                relationships = (
                    int(
                        relationship_result[
                            "count"
                        ]
                    )
                    if relationship_result
                    else 0
                )

                return {
                    "success": True,
                    "stage": (
                        "neo4j_business_graph"
                    ),
                    "counts": counts,
                    "graph": {
                        "nodes": nodes,
                        "relationships": relationships,
                    },
                    "errors": [],
                }

        except Exception as exc:

            return {
                "success": False,
                "stage": (
                    "neo4j_business_graph"
                ),
                "counts": {},
                "graph": {},
                "errors": [
                    str(exc)
                ],
            }

    # =========================================================
    # CONSTRAINTS & INDEXES
    # =========================================================

    @staticmethod
    def _create_constraints(
        session,
    ) -> None:

        queries = [
            """
            CREATE INDEX sc_company_lookup IF NOT EXISTS
            FOR (n:SCCompany)
            ON (n.company_id, n.user_id)
            """,
            """
            CREATE INDEX sc_supplier_lookup IF NOT EXISTS
            FOR (n:SCSupplier)
            ON (n.supplier_id, n.user_id)
            """,
            """
            CREATE INDEX sc_plant_lookup IF NOT EXISTS
            FOR (n:SCPlant)
            ON (n.plant_id, n.user_id)
            """,
            """
            CREATE INDEX sc_product_lookup IF NOT EXISTS
            FOR (n:SCProduct)
            ON (n.product_id, n.user_id)
            """,
            """
            CREATE INDEX sc_component_lookup IF NOT EXISTS
            FOR (n:SCComponent)
            ON (n.component_id, n.user_id)
            """,
            """
            CREATE INDEX sc_warehouse_lookup IF NOT EXISTS
            FOR (n:SCWarehouse)
            ON (n.warehouse_id, n.user_id)
            """,
        ]

        for query in queries:
            try:
                session.run(query)
            except Exception:
                pass

    # =========================================================
    # COMPANIES
    # =========================================================

    def _sync_companies(
        self,
        session,
    ) -> int:

        rows = self._get_rows(Company)

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            session.run(
                """
                MERGE (n:SCEntity:SCCompany {
                    company_id: $id,
                    user_id: $user_id
                })
                SET
                    n.name = $name,
                    n.industry = $industry
                """,
                id=row.company_id,
                user_id=user_id,
                name=row.company_name,
                industry=row.industry,
            )

        return len(rows)

    # =========================================================
    # SUPPLIERS
    # =========================================================

    def _sync_suppliers(
        self,
        session,
    ) -> int:

        rows = self._get_rows(BusinessSupplier)

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            session.run(
                """
                MERGE (n:SCEntity:SCSupplier {
                    supplier_id: $id,
                    user_id: $user_id
                })
                SET
                    n.name = $name,
                    n.country = $country,
                    n.city = $city,
                    n.location_known =
                        $location_known
                """,
                id=row.supplier_id,
                user_id=user_id,
                name=row.supplier_name,
                country=row.country,
                city=row.city,
                location_known=bool(
                    row.location_known
                ),
            )

        return len(rows)

    # =========================================================
    # PLANTS
    # =========================================================

    def _sync_plants(
        self,
        session,
    ) -> int:

        rows = self._get_rows(Plant)

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            location = ", ".join(
                x
                for x in [
                    row.city,
                    row.country,
                ]
                if x
            )

            session.run(
                """
                MERGE (n:SCEntity:SCPlant {
                    plant_id: $id,
                    user_id: $user_id
                })
                SET
                    n.name = $name,
                    n.company_id = $company_id,
                    n.city = $city,
                    n.country = $country,
                    n.location = $location
                """,
                id=row.plant_id,
                user_id=user_id,
                name=row.plant_name,
                company_id=row.company_id,
                city=row.city,
                country=row.country,
                location=location,
            )

            session.run(
                """
                MATCH (c:SCCompany {
                    company_id: $company_id,
                    user_id: $user_id
                })

                MATCH (p:SCPlant {
                    plant_id: $plant_id,
                    user_id: $user_id
                })

                MERGE (c)-[r:OWNS_PLANT {user_id: $user_id}]->(p)
                """,
                company_id=row.company_id,
                plant_id=row.plant_id,
                user_id=user_id,
            )

        return len(rows)

    # =========================================================
    # PRODUCTS
    # =========================================================

    def _sync_products(
        self,
        session,
    ) -> int:

        rows = self._get_rows(BusinessProduct)

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            session.run(
                """
                MERGE (n:SCEntity:SCProduct {
                    product_id: $id,
                    user_id: $user_id
                })
                SET
                    n.name = $name,
                    n.category = $category
                """,
                id=row.product_id,
                user_id=user_id,
                name=row.product_name,
                category=row.category,
            )

        return len(rows)

    # =========================================================
    # COMPONENTS
    # =========================================================

    def _sync_components(
        self,
        session,
    ) -> int:

        rows = self._get_rows(Component)

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            session.run(
                """
                MERGE (n:SCEntity:SCComponent {
                    component_id: $id,
                    user_id: $user_id
                })
                SET
                    n.name = $name,
                    n.category = $category
                """,
                id=row.component_id,
                user_id=user_id,
                name=row.component_name,
                category=row.category,
            )

        return len(rows)

    # =========================================================
    # WAREHOUSES
    # =========================================================

    def _sync_warehouses(
        self,
        session,
    ) -> int:

        rows = self._get_rows(Warehouse)

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            location = ", ".join(
                x
                for x in [
                    row.city,
                    row.country,
                ]
                if x
            )

            session.run(
                """
                MERGE (n:SCEntity:SCWarehouse {
                    warehouse_id: $id,
                    user_id: $user_id
                })
                SET
                    n.name = $name,
                    n.city = $city,
                    n.country = $country,
                    n.location = $location
                """,
                id=row.warehouse_id,
                user_id=user_id,
                name=row.warehouse_name,
                city=row.city,
                country=row.country,
                location=location,
            )

        return len(rows)

    # =========================================================
    # SUPPLY ALLOCATIONS
    # =========================================================

    def _sync_allocations(
        self,
        session,
    ) -> int:

        rows = self._get_rows(SupplyAllocation)

        count = 0

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            spare_capacity_units = (
                self._number(
                    getattr(
                        row,
                        "spare_capacity_units",
                        0.0,
                    )
                )
            )

            result = session.run(
                """
                MATCH (s:SCSupplier {
                    supplier_id:
                        $supplier_id,
                    user_id:
                        $user_id
                })

                MATCH (c:SCComponent {
                    component_id:
                        $component_id,
                    user_id:
                        $user_id
                })

                MATCH (p:SCPlant {
                    plant_id:
                        $plant_id,
                    user_id:
                        $user_id
                })

                MERGE (s)-[
                    r:SUPPLIES
                {
                    allocation_key:
                        $allocation_key,
                    user_id:
                        $user_id
                }]->(c)

                SET
                    r.allocation_pct =
                        $allocation_pct,
                    r.capacity_units =
                        $capacity_units,
                    r.spare_capacity_units =
                        $spare_capacity_units,
                    r.lead_time_days =
                        $lead_time_days,
                    r.criticality =
                        $criticality,
                    r.plant_id =
                        $plant_id

                MERGE (c)-[
                    sp:USED_AT
                {
                    allocation_key:
                        $allocation_key,
                    user_id:
                        $user_id
                }]->(p)

                SET
                    sp.allocation_pct =
                        $allocation_pct,
                    sp.capacity_units =
                        $capacity_units,
                    sp.spare_capacity_units =
                        $spare_capacity_units

                RETURN 1 AS created
                """,
                supplier_id=row.supplier_id,
                component_id=row.component_id,
                plant_id=row.plant_id,
                user_id=user_id,
                allocation_key=(
                    f"{row.supplier_id}:"
                    f"{row.component_id}:"
                    f"{row.plant_id}"
                ),
                allocation_pct=row.allocation_pct,
                capacity_units=row.capacity_units,
                spare_capacity_units=(
                    spare_capacity_units
                ),
                lead_time_days=row.lead_time_days,
                criticality=row.criticality,
            )

            if result.single():
                count += 1

        return count

    # =========================================================
    # INVENTORY
    # =========================================================

    def _sync_inventory(
        self,
        session,
    ) -> int:

        rows = self._get_rows(Inventory)

        count = 0

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            location_id = str(
                row.location_id
            )

            location_type = str(
                row.location_type
            ).lower()

            if location_type == "warehouse":

                result = session.run(
                    """
                    MATCH (w:SCWarehouse {
                        warehouse_id:
                            $location_id,
                        user_id:
                            $user_id
                    })

                    MATCH (c:SCComponent {
                        component_id:
                            $component_id,
                        user_id:
                            $user_id
                    })

                    MERGE (w)-[
                        r:STORES
                    {
                        inventory_id:
                            $inventory_id,
                        user_id:
                            $user_id
                    }]->(c)

                    SET
                        r.quantity_units =
                            $quantity_units

                    RETURN 1 AS created
                    """,
                    location_id=location_id,
                    user_id=user_id,
                    component_id=(
                        row.component_id
                    ),
                    inventory_id=(
                        row.inventory_id
                    ),
                    quantity_units=(
                        row.quantity_units
                    ),
                )

                if result.single():
                    count += 1

        return count

    # =========================================================
    # CAPACITY
    # =========================================================

    def _sync_capacity(
        self,
        session,
    ) -> int:

        rows = self._get_rows(Capacity)

        count = 0

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            location_type = str(
                row.location_type
            ).lower()

            if location_type == "plant":

                result = session.run(
                    """
                    MATCH (p:SCPlant {
                        plant_id:
                            $location_id,
                        user_id:
                            $user_id
                    })

                    MATCH (c:SCComponent {
                        component_id:
                            $component_id,
                        user_id:
                            $user_id
                    })

                    MERGE (p)-[
                        r:PRODUCES_CAPACITY
                    {
                        capacity_id:
                            $capacity_id,
                        user_id:
                            $user_id
                    }]->(c)

                    SET
                        r.units_per_day =
                            $capacity_units_per_day

                    RETURN 1 AS created
                    """,
                    location_id=str(
                        row.location_id
                    ),
                    user_id=user_id,
                    component_id=(
                        row.component_id
                    ),
                    capacity_id=(
                        row.capacity_id
                    ),
                    capacity_units_per_day=(
                        row.capacity_units_per_day
                    ),
                )

                if result.single():
                    count += 1

        return count

    # =========================================================
    # DEMAND
    # =========================================================

    def _sync_demand(
        self,
        session,
    ) -> int:

        rows = self._get_rows(Demand)

        count = 0

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            result = session.run(
                """
                MATCH (p:SCPlant {
                    plant_id:
                        $plant_id,
                    user_id:
                        $user_id
                })

                MATCH (prod:SCProduct {
                    product_id:
                        $product_id,
                    user_id:
                        $user_id
                })

                MERGE (p)-[
                    r:DEMANDS
                {
                    demand_id:
                        $demand_id,
                    user_id:
                        $user_id
                }]->(prod)

                SET
                    r.units_per_day =
                        $units_per_day

                RETURN 1 AS created
                """,
                plant_id=row.plant_id,
                product_id=row.product_id,
                user_id=user_id,
                demand_id=row.demand_id,
                units_per_day=(
                    row.daily_demand_units
                ),
            )

            if result.single():
                count += 1

        return count

    # =========================================================
    # ROUTES
    # =========================================================

    def _sync_routes(
        self,
        session,
    ) -> int:

        rows = self._get_rows(Route)

        count = 0

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            source_type = str(
                row.source_type
            ).lower()

            destination_type = str(
                row.destination_type
            ).lower()

            source_label = (
                self._location_label(
                    source_type
                )
            )

            destination_label = (
                self._location_label(
                    destination_type
                )
            )

            if (
                not source_label
                or not destination_label
            ):
                continue

            source_field = (
                self._id_field(
                    source_type
                )
            )

            destination_field = (
                self._id_field(
                    destination_type
                )
            )

            if (
                not source_field
                or not destination_field
            ):
                continue

            query = f"""
            MATCH (source:{source_label} {{user_id: $user_id}})
            MATCH (destination:{destination_label} {{user_id: $user_id}})
            WHERE
                source.{source_field}
                    = $source_id
                AND
                destination.{destination_field}
                    = $destination_id

            MERGE (source)-[
                r:SHIPS_TO
            {{
                route_id:
                    $route_id,
                user_id:
                    $user_id
            }}]->(destination)

            SET
                r.transit_days =
                    $transit_days,
                r.route_status =
                    $route_status

            RETURN 1 AS created
            """

            result = session.run(
                query,
                source_id=str(
                    row.source_id
                ),
                destination_id=str(
                    row.destination_id
                ),
                route_id=row.route_id,
                transit_days=row.transit_days,
                route_status=row.route_status,
                user_id=user_id,
            )

            if result.single():
                count += 1

        return count

    # =========================================================
    # DEPENDENCIES
    # =========================================================

    def _sync_dependencies(
        self,
        session,
    ) -> int:

        rows = self._get_rows(Dependency)

        count = 0

        for row in rows:
            user_id = row.user_id if row.user_id is not None else 0

            source_type = str(
                row.source_type
            ).lower()

            target_type = str(
                row.target_type
            ).lower()

            source_label = (
                self._entity_label(
                    source_type
                )
            )

            target_label = (
                self._entity_label(
                    target_type
                )
            )

            source_field = (
                self._id_field(
                    source_type
                )
            )

            target_field = (
                self._id_field(
                    target_type
                )
            )

            if (
                not source_label
                or not target_label
                or not source_field
                or not target_field
            ):
                continue

            required_quantity = (
                getattr(
                    row,
                    "required_quantity",
                    1.0,
                )
            )

            try:
                required_quantity = float(
                    required_quantity
                    or 1.0
                )
            except (
                TypeError,
                ValueError,
            ):
                required_quantity = 1.0

            if required_quantity <= 0:
                required_quantity = 1.0

            query = f"""
            MATCH (source:{source_label} {{user_id: $user_id}})
            MATCH (target:{target_label} {{user_id: $user_id}})
            WHERE
                source.{source_field}
                    = $source_id
                AND
                target.{target_field}
                    = $target_id

            MERGE (source)-[
                r:DEPENDS_ON
            {{
                dependency_id:
                    $dependency_id,
                user_id:
                    $user_id
            }}]->(target)

            SET
                r.dependency_type =
                    $dependency_type,
                r.required_quantity =
                    $required_quantity,
                r.criticality =
                    $criticality

            RETURN 1 AS created
            """

            result = session.run(
                query,
                source_id=str(
                    row.source_id
                ),
                target_id=str(
                    row.target_id
                ),
                dependency_id=(
                    row.dependency_id
                ),
                dependency_type=(
                    row.dependency_type
                ),
                required_quantity=(
                    required_quantity
                ),
                criticality=(
                    row.criticality
                ),
                user_id=user_id,
            )

            if result.single():
                count += 1

        return count

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _location_label(
        entity_type: str,
    ) -> str | None:

        mapping = {
            "company": "SCCompany",
            "supplier": "SCSupplier",
            "plant": "SCPlant",
            "warehouse": "SCWarehouse",
        }

        return mapping.get(
            entity_type
        )

    @staticmethod
    def _entity_label(
        entity_type: str,
    ) -> str | None:

        mapping = {
            "company": "SCCompany",
            "supplier": "SCSupplier",
            "plant": "SCPlant",
            "product": "SCProduct",
            "component": "SCComponent",
            "warehouse": "SCWarehouse",
        }

        return mapping.get(
            entity_type
        )

    @staticmethod
    def _id_field(
        entity_type: str,
    ) -> str | None:

        mapping = {
            "company": "company_id",
            "supplier": "supplier_id",
            "plant": "plant_id",
            "product": "product_id",
            "component": "component_id",
            "warehouse": "warehouse_id",
        }

        return mapping.get(
            entity_type
        )

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
    "SupplyChainNeo4jImporter",
]