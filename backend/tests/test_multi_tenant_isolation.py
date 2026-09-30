from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.main import app
from app.models.business_supply_chain import (
    BusinessProduct,
    BusinessSupplier,
    Company,
    Component,
    Plant,
    SupplyAllocation,
)
from app.models.user import User
from app.services.auth_service import create_access_token


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_a(db: Session):
    # Setup test user A (Mohilya Couture)
    user = db.query(User).filter(User.email == "mohilya_test@example.com").first()
    if not user:
        user = User(
            email="mohilya_test@example.com",
            password_hash="mockhashedpassword123",
            company_name="Mohilya Couture Pvt Ltd",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def user_b(db: Session):
    # Setup test user B (New User with empty dataset)
    user = db.query(User).filter(User.email == "new_user_b@example.com").first()
    if not user:
        user = User(
            email="new_user_b@example.com",
            password_hash="mockhashedpassword123",
            company_name="Brand New Logistics Ltd",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def token_a(user_a: User):
    return create_access_token({"sub": str(user_a.id)})


@pytest.fixture
def token_b(user_b: User):
    return create_access_token({"sub": str(user_b.id)})


def test_new_registered_user_has_empty_isolated_catalog(client: TestClient, token_b: str, user_b: User, db: Session):
    """
    Ensure a newly registered user sees 0 suppliers, 0 plants, 0 components,
    and does NOT leak the demo AdilQadri or Mohilya datasets.
    """
    # Clean any leftover records for user_b
    for model in [SupplyAllocation, Component, BusinessProduct, Plant, BusinessSupplier, Company]:
        db.query(model).filter(model.user_id == user_b.id).delete()
    db.commit()

    headers = {"Authorization": f"Bearer {token_b}"}
    response = client.get("/api/supply-chain/catalog", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert len(data["suppliers"]) == 0
    assert len(data["plants"]) == 0
    assert len(data["components"]) == 0
    assert len(data["products"]) == 0


def test_new_user_receives_clean_empty_business_graph(client: TestClient, token_b: str, user_b: User, db: Session):
    """
    Ensure newly registered user gets an empty graph payload instead of demo nodes.
    """
    for model in [SupplyAllocation, Component, BusinessProduct, Plant, BusinessSupplier, Company]:
        db.query(model).filter(model.user_id == user_b.id).delete()
    db.commit()

    headers = {"Authorization": f"Bearer {token_b}"}
    response = client.get("/api/supply-chain/business-graph", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["nodes"] == []
    assert data["relationships"] == []


def test_tenant_data_isolation_between_users(client: TestClient, token_a: str, token_b: str, user_a: User, user_b: User, db: Session):
    """
    Create custom entities for User A, and verify User B cannot see them.
    """
    # Clean previous
    for model in [SupplyAllocation, Component, BusinessProduct, Plant, BusinessSupplier, Company]:
        db.query(model).filter(model.user_id.in_([user_a.id, user_b.id])).delete()
    db.commit()

    # Create supplier for User A
    supp_a = BusinessSupplier(
        supplier_id="SUP_MOHILYA_01",
        supplier_name="Surat Ring Road Fabric Mills",
        country="India",
        city="Surat",
        user_id=user_a.id,
    )
    db.add(supp_a)
    db.commit()

    # User A requests suppliers -> should see 1 supplier
    headers_a = {"Authorization": f"Bearer {token_a}"}
    res_a = client.get("/api/supply-chain/suppliers", headers=headers_a)
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert len(data_a["suppliers"]) == 1
    assert data_a["suppliers"][0]["supplier_id"] == "SUP_MOHILYA_01"

    # User B requests suppliers -> should see 0 suppliers
    headers_b = {"Authorization": f"Bearer {token_b}"}
    res_b = client.get("/api/supply-chain/suppliers", headers=headers_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert len(data_b["suppliers"]) == 0

    # User B cannot simulate User A's supplier
    sim_res_b = client.post(
        "/api/supply-chain/simulate",
        json={"supplier_id": "SUP_MOHILYA_01"},
        headers=headers_b,
    )
    assert sim_res_b.status_code == 404
    assert "not found" in sim_res_b.json()["detail"].lower()
