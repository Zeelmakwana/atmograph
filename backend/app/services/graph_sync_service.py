"""
AtmoGraph Graph Synchronization Service

Synchronizes the existing relational supply-chain data
into Neo4j.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.supply_chain import Supplier, Product
from app.models.supply_chain_link import SupplyChainLink

from app.services.neo4j_service import Neo4jService


class GraphSyncService:
    """Synchronize SQL supply-chain data with Neo4j."""

    def __init__(
        self,
        db: Session,
        neo4j: Neo4jService,
    ) -> None:

        self.db = db
        self.neo4j = neo4j

    def sync_events(self) -> int:
        """Sync all events."""

        events = self.db.query(Event).all()

        for event in events:

            self.neo4j.create_event(
                event_id=event.id,
                title=event.title,
                event_type=event.event_type,
                severity=event.severity,
                location=event.location,
            )

        return len(events)

    def sync_suppliers(self) -> int:
        """Sync all suppliers."""

        suppliers = self.db.query(Supplier).all()

        for supplier in suppliers:

            self.neo4j.create_supplier(
                supplier_id=supplier.id,
                name=supplier.name,
                country=supplier.country,
                industry=supplier.industry,
            )

        return len(suppliers)

    def sync_products(self) -> int:
        """Sync all products."""

        products = self.db.query(Product).all()

        for product in products:

            self.neo4j.create_product(
                product_id=product.id,
                name=product.name,
                category=product.category,
            )

        return len(products)

    def sync_relationships(self) -> int:
        """Sync Event → Supplier and Supplier → Product relationships."""

        links = self.db.query(
            SupplyChainLink
        ).all()

        relationship_count = 0

        for link in links:

            if link.event_id and link.supplier_id:

                self.neo4j.create_event_supplier_relationship(
                    event_id=link.event_id,
                    supplier_id=link.supplier_id,
                    relationship_type=link.relationship_type,
                    impact_level=link.impact_level,
                    estimated_delay_days=link.estimated_delay_days,
                )

                relationship_count += 1

            if link.supplier_id and link.product_id:

                self.neo4j.create_supplier_product_relationship(
                    supplier_id=link.supplier_id,
                    product_id=link.product_id,
                )

        return relationship_count

    def sync_all(self) -> dict[str, int]:
        """Run complete SQL → Neo4j synchronization."""

        if not self.neo4j.verify_connection():
            raise ConnectionError(
                "Unable to connect to Neo4j."
            )

        events = self.sync_events()
        suppliers = self.sync_suppliers()
        products = self.sync_products()
        relationships = self.sync_relationships()

        return {
            "events": events,
            "suppliers": suppliers,
            "products": products,
            "relationships": relationships,
        }