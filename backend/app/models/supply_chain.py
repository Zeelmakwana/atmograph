from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Supplier(Base):
    """
    Represents a supplier in the supply chain.
    """

    __tablename__ = "suppliers"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    country = Column(
        String(255),
        nullable=True,
    )

    industry = Column(
        String(255),
        nullable=True,
    )

    products = relationship(
        "Product",
        back_populates="supplier",
        cascade="all, delete-orphan",
    )

    supply_chain_links = relationship(
        "SupplyChainLink",
        back_populates="supplier",
        cascade="all, delete-orphan",
    )


class Product(Base):
    """
    Represents a product supplied by a supplier.
    """

    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
        index=True,
    )

    category = Column(
        String(255),
        nullable=True,
    )

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )

    supplier = relationship(
        "Supplier",
        back_populates="products",
    )

    supply_chain_links = relationship(
        "SupplyChainLink",
        back_populates="product",
        cascade="all, delete-orphan",
    )