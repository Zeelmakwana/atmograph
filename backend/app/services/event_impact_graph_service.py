from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.supply_chain_link import SupplyChainLink

from app.models.supply_chain import (
    Supplier,
    Product,
)

from app.models.business_supply_chain import (
    BusinessSupplier,
    BusinessProduct,
    Plant,
    Component,
    SupplyAllocation,
    Dependency,
)


class EventImpactGraphService:
    """
    Canonical operational impact graph.

    Event
      ↓
    Supplier
      ↓
    Component
      ↓
    Plant
      ↓
    Product

    This is an operational graph overlay.

    It is intentionally separate from the GNN graph.
    """

    VERSION = "1.0"

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ========================================================
    # BUILD
    # ========================================================

    def build(
        self,
        event_id: int,
    ) -> dict[str, Any]:

        event = (
            self.db.query(Event)
            .filter(
                Event.id == event_id
            )
            .first()
        )

        if event is None:

            return {
                "success": False,
                "event_id": event_id,
                "message": "Event not found.",
            }

        # ----------------------------------------------------
        # Legacy event links
        # ----------------------------------------------------

        links = (
            self.db.query(
                SupplyChainLink
            )
            .filter(
                SupplyChainLink.event_id
                == event_id
            )
            .all()
        )

        legacy_supplier_ids = {
            int(link.supplier_id)
            for link in links
            if link.supplier_id is not None
        }

        legacy_product_ids = {
            int(link.product_id)
            for link in links
            if link.product_id is not None
        }

        legacy_suppliers = (
            self.db.query(Supplier)
            .filter(
                Supplier.id.in_(
                    legacy_supplier_ids
                )
            )
            .all()
            if legacy_supplier_ids
            else []
        )

        legacy_products = (
            self.db.query(Product)
            .filter(
                Product.id.in_(
                    legacy_product_ids
                )
            )
            .all()
            if legacy_product_ids
            else []
        )

        # ----------------------------------------------------
        # Match legacy suppliers to business suppliers
        # ----------------------------------------------------

        legacy_supplier_names = {
            self._normalize(
                supplier.name
            )
            for supplier in legacy_suppliers
        }

        business_suppliers = []

        for supplier in (
            self.db.query(
                BusinessSupplier
            ).all()
        ):

            if (
                self._normalize(
                    supplier.supplier_name
                )
                in legacy_supplier_names
            ):

                business_suppliers.append(
                    supplier
                )

        # ----------------------------------------------------
        # If legacy links did not resolve suppliers,
        # use event title/location matching as a fallback.
        #
        # No arbitrary supplier is selected.
        # ----------------------------------------------------

        if not business_suppliers:

            event_text = self._normalize(
                " ".join(
                    [
                        str(
                            event.title
                            or ""
                        ),
                        str(
                            event.description
                            or ""
                        ),
                    ]
                )
            )

            event_location = self._normalize(
                event.location
            )

            for supplier in (
                self.db.query(
                    BusinessSupplier
                ).all()
            ):

                supplier_name = self._normalize(
                    supplier.supplier_name
                )

                city = self._normalize(
                    supplier.city
                )

                country = self._normalize(
                    supplier.country
                )

                if (
                    supplier_name
                    and supplier_name in event_text
                ):
                    business_suppliers.append(
                        supplier
                    )

                elif (
                    event_location
                    and (
                        event_location == city
                        or event_location == country
                    )
                ):
                    business_suppliers.append(
                        supplier
                    )

        # Deduplicate
        business_suppliers = self._unique(
            business_suppliers,
            "supplier_id",
        )

        business_supplier_ids = {
            str(
                supplier.supplier_id
            )
            for supplier in business_suppliers
        }

        # ----------------------------------------------------
        # Allocations
        # ----------------------------------------------------

        allocations = (
            self.db.query(
                SupplyAllocation
            )
            .filter(
                SupplyAllocation.supplier_id.in_(
                    business_supplier_ids
                )
            )
            .all()
            if business_supplier_ids
            else []
        )

        component_ids = {
            str(
                allocation.component_id
            )
            for allocation in allocations
            if allocation.component_id
            is not None
        }

        plant_ids = {
            str(
                allocation.plant_id
            )
            for allocation in allocations
            if allocation.plant_id
            is not None
        }

        # ----------------------------------------------------
        # Components
        # ----------------------------------------------------

        components = (
            self.db.query(
                Component
            )
            .filter(
                Component.component_id.in_(
                    component_ids
                )
            )
            .all()
            if component_ids
            else []
        )

        # ----------------------------------------------------
        # Plants
        # ----------------------------------------------------

        plants = (
            self.db.query(
                Plant
            )
            .filter(
                Plant.plant_id.in_(
                    plant_ids
                )
            )
            .all()
            if plant_ids
            else []
        )

        # ----------------------------------------------------
        # Dependency graph
        #
        # Actual model:
        #
        # Product(source_id)
        #       ↓
        # Component(target_id)
        # ----------------------------------------------------

        dependencies = (
            self.db.query(
                Dependency
            )
            .all()
        )

        relevant_dependencies = []

        for dependency in dependencies:

            source_type = self._normalize(
                dependency.source_type
            )

            target_type = self._normalize(
                dependency.target_type
            )

            source_id = self._normalize(
                dependency.source_id
            )

            target_id = self._normalize(
                dependency.target_id
            )

            if (
                source_type == "product"
                and target_type == "component"
                and target_id in {
                    self._normalize(
                        component_id
                    )
                    for component_id
                    in component_ids
                }
            ):

                relevant_dependencies.append(
                    dependency
                )

        dependency_product_ids = {
            str(
                dependency.source_id
            )
            for dependency
            in relevant_dependencies
        }

        # ----------------------------------------------------
        # Business products from dependencies
        # ----------------------------------------------------

        business_products = (
            self.db.query(
                BusinessProduct
            )
            .filter(
                BusinessProduct.product_id.in_(
                    dependency_product_ids
                )
            )
            .all()
            if dependency_product_ids
            else []
        )

        # ----------------------------------------------------
        # Add legacy directly affected products too
        # ----------------------------------------------------

        legacy_product_names = {
            self._normalize(
                product.name
            )
            for product in legacy_products
        }

        if legacy_product_names:

            for product in (
                self.db.query(
                    BusinessProduct
                ).all()
            ):

                if (
                    self._normalize(
                        product.product_name
                    )
                    in legacy_product_names
                    and product
                    not in business_products
                ):

                    business_products.append(
                        product
                    )

        business_products = self._unique(
            business_products,
            "product_id",
        )

        # ----------------------------------------------------
        # NODE CREATION
        # ----------------------------------------------------

        nodes: list[dict[str, Any]] = []

        event_node_id = (
            f"event:{event.id}"
        )

        nodes.append(
            {
                "id": event_node_id,
                "type": "Event",
                "name": event.title,
                "affected": True,
                "failed": True,
                "properties": {
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "location": event.location,
                    "status": event.status,
                },
            }
        )

        for supplier in business_suppliers:

            nodes.append(
                {
                    "id": (
                        "supplier:"
                        + str(
                            supplier.supplier_id
                        )
                    ),
                    "type": "Supplier",
                    "name": supplier.supplier_name,
                    "affected": True,
                    "failed": True,
                    "properties": {
                        "supplier_id": (
                            supplier.supplier_id
                        ),
                        "country": supplier.country,
                        "city": supplier.city,
                    },
                }
            )

        for component in components:

            nodes.append(
                {
                    "id": (
                        "component:"
                        + str(
                            component.component_id
                        )
                    ),
                    "type": "Component",
                    "name": component.component_name,
                    "affected": True,
                    "failed": False,
                    "properties": {
                        "component_id": (
                            component.component_id
                        ),
                        "category": component.category,
                    },
                }
            )

        for plant in plants:

            nodes.append(
                {
                    "id": (
                        "plant:"
                        + str(
                            plant.plant_id
                        )
                    ),
                    "type": "Plant",
                    "name": plant.plant_name,
                    "affected": True,
                    "failed": False,
                    "properties": {
                        "plant_id": plant.plant_id,
                        "company_id": plant.company_id,
                        "country": plant.country,
                        "city": plant.city,
                    },
                }
            )

        for product in business_products:

            nodes.append(
                {
                    "id": (
                        "product:"
                        + str(
                            product.product_id
                        )
                    ),
                    "type": "Product",
                    "name": product.product_name,
                    "affected": True,
                    "failed": False,
                    "properties": {
                        "product_id": (
                            product.product_id
                        ),
                        "category": product.category,
                    },
                }
            )

        # ----------------------------------------------------
        # RELATIONSHIPS
        # ----------------------------------------------------

        relationships: list[
            dict[str, Any]
        ] = []

        # Event → Supplier
        for supplier in business_suppliers:

            supplier_node = (
                "supplier:"
                + str(
                    supplier.supplier_id
                )
            )

            relationships.append(
                {
                    "source": event_node_id,
                    "target": supplier_node,
                    "relationship": "AFFECTS",
                    "affected": True,
                    "properties": {
                        "severity": event.severity,
                        "event_type": event.event_type,
                    },
                }
            )

        # Supplier → Component
        for allocation in allocations:

            supplier_node = (
                "supplier:"
                + str(
                    allocation.supplier_id
                )
            )

            component_node = (
                "component:"
                + str(
                    allocation.component_id
                )
            )

            plant_node = (
                "plant:"
                + str(
                    allocation.plant_id
                )
            )

            relationships.append(
                {
                    "source": supplier_node,
                    "target": component_node,
                    "relationship": "SUPPLIES",
                    "affected": True,
                    "properties": {
                        "allocation_pct": self._number(
                            allocation.allocation_pct
                        ),
                        "capacity_units": self._number(
                            allocation.capacity_units
                        ),
                        "spare_capacity_units": (
                            self._number(
                                getattr(
                                    allocation,
                                    "spare_capacity_units",
                                    0,
                                )
                            )
                        ),
                        "lead_time_days": self._number(
                            allocation.lead_time_days
                        ),
                        "criticality": (
                            allocation.criticality
                        ),
                    },
                }
            )

            relationships.append(
                {
                    "source": component_node,
                    "target": plant_node,
                    "relationship": "USED_AT",
                    "affected": True,
                    "properties": {},
                }
            )

        # Product → Component
        for dependency in relevant_dependencies:

            product_node = (
                "product:"
                + str(
                    dependency.source_id
                )
            )

            component_node = (
                "component:"
                + str(
                    dependency.target_id
                )

            )

            relationships.append(
                {
                    "source": product_node,
                    "target": component_node,
                    "relationship": "DEPENDS_ON",
                    "affected": True,
                    "properties": {
                        "required_quantity": (
                            self._number(
                                getattr(
                                    dependency,
                                    "required_quantity",
                                    1.0,
                                ),
                                1.0,
                            )
                        ),
                        "dependency_type": (
                            dependency.dependency_type
                        ),
                        "criticality": (
                            dependency.criticality
                        ),
                    },
                }
            )

        # ----------------------------------------------------
        # IDs
        # ----------------------------------------------------

        affected_node_ids = [
            node["id"]
            for node in nodes
            if node.get("affected")
        ]

        failed_node_ids = [
            node["id"]
            for node in nodes
            if node.get("failed")
        ]

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {
            "success": True,
            "version": self.VERSION,
            "event_id": event.id,

            "event": {
                "id": event.id,
                "title": event.title,
                "event_type": event.event_type,
                "location": event.location,
                "severity": event.severity,
                "status": event.status,
            },

            "counts": {
                "nodes": len(nodes),
                "relationships": len(
                    relationships
                ),
                "suppliers": len(
                    business_suppliers
                ),
                "components": len(
                    components
                ),
                "plants": len(
                    plants
                ),
                "products": len(
                    business_products
                ),
            },

            "affected_node_ids": (
                affected_node_ids
            ),

            "failed_node_ids": (
                failed_node_ids
            ),

            "nodes": nodes,

            "relationships": relationships,
        }

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _normalize(
        value: Any,
    ) -> str:

        return (
            str(value or "")
            .strip()
            .lower()
            .replace("-", " ")
            .replace("_", " ")
        )

    _normalize_name = _normalize

    @staticmethod
    def _number(
        value: Any,
        default: float = 0.0,
    ) -> float:

        try:

            if value is None:
                return default

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    @staticmethod
    def _unique(
        rows: list[Any],
        attribute: str,
    ) -> list[Any]:

        result = []
        seen = set()

        for row in rows:

            value = getattr(
                row,
                attribute,
                None,
            )

            key = str(value)

            if key in seen:
                continue

            seen.add(key)
            result.append(row)

        return result


__all__ = [
    "EventImpactGraphService",
]
