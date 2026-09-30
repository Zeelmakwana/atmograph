from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class SupplyChainLink(Base):
    """
    Connects an event with an affected supplier and product.
    """

    __tablename__ = "supply_chain_links"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    relationship_type = Column(
        String(100),
        nullable=False,
        default="affected",
    )

    impact_level = Column(
        String(50),
        nullable=False,
        default="medium",
    )

    estimated_delay_days = Column(
        Integer,
        nullable=False,
        default=0,
    )

    event = relationship(
        "Event",
        back_populates="supply_chain_links",
    )

    supplier = relationship(
        "Supplier",
        back_populates="supply_chain_links",
    )

    product = relationship(
        "Product",
        back_populates="supply_chain_links",
    )