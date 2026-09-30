from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    Event,
    Product,
    Supplier,
    SupplyChainLink,
)
from app.schemas.supply_chain_link import (
    SupplyChainLinkCreate,
    SupplyChainLinkResponse,
)


router = APIRouter(
    prefix="/relationships",
    tags=["Supply Chain Relationships"],
)


@router.post(
    "/",
    response_model=SupplyChainLinkResponse,
)
def create_relationship(
    data: SupplyChainLinkCreate,
    db: Session = Depends(get_db),
):
    event = (
        db.query(Event)
        .filter(Event.id == data.event_id)
        .first()
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found.",
        )

    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == data.supplier_id)
        .first()
    )

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found.",
        )

    product = (
        db.query(Product)
        .filter(Product.id == data.product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    if product.supplier_id != supplier.id:
        raise HTTPException(
            status_code=400,
            detail="Product does not belong to this supplier.",
        )

    existing = (
        db.query(SupplyChainLink)
        .filter(
            SupplyChainLink.event_id == data.event_id,
            SupplyChainLink.supplier_id == data.supplier_id,
            SupplyChainLink.product_id == data.product_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This supply-chain relationship already exists.",
        )

    link = SupplyChainLink(
        event_id=data.event_id,
        supplier_id=data.supplier_id,
        product_id=data.product_id,
        relationship_type=data.relationship_type,
        impact_level=data.impact_level,
        estimated_delay_days=data.estimated_delay_days,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    return link


@router.get(
    "/",
    response_model=list[SupplyChainLinkResponse],
)
def get_relationships(
    db: Session = Depends(get_db),
):
    return (
        db.query(SupplyChainLink)
        .order_by(SupplyChainLink.id.desc())
        .all()
    )


@router.get(
    "/event/{event_id}",
    response_model=list[SupplyChainLinkResponse],
)
def get_event_relationships(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found.",
        )

    return (
        db.query(SupplyChainLink)
        .filter(
            SupplyChainLink.event_id == event_id
        )
        .order_by(SupplyChainLink.id.desc())
        .all()
    )


@router.get(
    "/supplier/{supplier_id}",
    response_model=list[SupplyChainLinkResponse],
)
def get_supplier_relationships(
    supplier_id: int,
    db: Session = Depends(get_db),
):
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id)
        .first()
    )

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found.",
        )

    return (
        db.query(SupplyChainLink)
        .filter(
            SupplyChainLink.supplier_id == supplier_id
        )
        .order_by(SupplyChainLink.id.desc())
        .all()
    )


@router.get(
    "/product/{product_id}",
    response_model=list[SupplyChainLinkResponse],
)
def get_product_relationships(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    return (
        db.query(SupplyChainLink)
        .filter(
            SupplyChainLink.product_id == product_id
        )
        .order_by(SupplyChainLink.id.desc())
        .all()
    )