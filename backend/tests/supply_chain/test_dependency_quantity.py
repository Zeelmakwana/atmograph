from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.services.supply_chain.excel_importer import (
    SupplyChainExcelImporter,
)


def _write_workbook(
    path: Path,
    dependency_quantity=2.0,
):
    sheets = {
        "Companies": pd.DataFrame(
            [
                {
                    "company_id": "COMP001",
                    "company_name": "Test Company",
                    "industry": "Electronics",
                }
            ]
        ),
        "Suppliers": pd.DataFrame(
            [
                {
                    "supplier_id": "SUP001",
                    "supplier_name": "Test Supplier",
                    "country": "Germany",
                    "city": "Hamburg",
                    "location_known": True,
                }
            ]
        ),
        "Plants": pd.DataFrame(
            [
                {
                    "plant_id": "PLANT001",
                    "plant_name": "Test Plant",
                    "company_id": "COMP001",
                    "country": "India",
                    "city": "Pune",
                }
            ]
        ),
        "Products": pd.DataFrame(
            [
                {
                    "product_id": "PROD001",
                    "product_name": "Test Product",
                    "category": "Electronics",
                }
            ]
        ),
        "Components": pd.DataFrame(
            [
                {
                    "component_id": "CMP001",
                    "component_name": "Test Component",
                    "category": "IC",
                }
            ]
        ),
        "Warehouses": pd.DataFrame(
            [
                {
                    "warehouse_id": "WH001",
                    "warehouse_name": "Test Warehouse",
                    "country": "India",
                    "city": "Pune",
                }
            ]
        ),
        "Supply_Allocations": pd.DataFrame(
            [
                {
                    "supplier_id": "SUP001",
                    "component_id": "CMP001",
                    "plant_id": "PLANT001",
                    "allocation_pct": 100,
                    "capacity_units": 1000,
                    "lead_time_days": 10,
                    "criticality": "high",
                }
            ]
        ),
        "Inventory": pd.DataFrame(
            [
                {
                    "inventory_id": "INV001",
                    "location_type": "warehouse",
                    "location_id": "WH001",
                    "component_id": "CMP001",
                    "quantity_units": 1000,
                }
            ]
        ),
        "Capacity": pd.DataFrame(
            [
                {
                    "capacity_id": "CAP001",
                    "location_type": "plant",
                    "location_id": "PLANT001",
                    "component_id": "CMP001",
                    "capacity_units_per_day": 100,
                }
            ]
        ),
        "Demand": pd.DataFrame(
            [
                {
                    "demand_id": "DEM001",
                    "plant_id": "PLANT001",
                    "product_id": "PROD001",
                    "daily_demand_units": 100,
                }
            ]
        ),
        "Routes": pd.DataFrame(
            [
                {
                    "route_id": "ROUTE001",
                    "source_type": "supplier",
                    "source_id": "SUP001",
                    "destination_type": "plant",
                    "destination_id": "PLANT001",
                    "transit_days": 10,
                    "route_status": "active",
                }
            ]
        ),
        "Dependencies": pd.DataFrame(
            [
                {
                    "dependency_id": "DEP001",
                    "source_type": "product",
                    "source_id": "PROD001",
                    "target_type": "component",
                    "target_id": "CMP001",
                    "dependency_type": "requires",
                    "required_quantity": dependency_quantity,
                    "criticality": "high",
                }
            ]
        ),
    }

    with pd.ExcelWriter(
        path,
        engine="openpyxl",
    ) as writer:
        for sheet_name, dataframe in sheets.items():
            dataframe.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )


def test_dependency_required_quantity_is_imported(
    tmp_path,
):
    workbook = (
        tmp_path
        / "dependency_quantity.xlsx"
    )

    _write_workbook(
        workbook,
        dependency_quantity=3.0,
    )

    importer = SupplyChainExcelImporter()

    result = importer.import_file(
        workbook
    )

    assert result.success is True

    dependencies = result.records[
        "Dependencies"
    ]

    assert len(dependencies) == 1

    assert (
        dependencies[0][
            "required_quantity"
        ]
        == 3.0
    )


def test_dependency_quantity_must_be_positive(
    tmp_path,
):
    workbook = (
        tmp_path
        / "invalid_dependency.xlsx"
    )

    _write_workbook(
        workbook,
        dependency_quantity=0,
    )

    importer = SupplyChainExcelImporter()

    result = importer.import_file(
        workbook
    )

    assert result.success is False

    assert any(
        "required_quantity must be greater than 0"
        in error
        for error in result.errors
    )


def test_dependency_quantity_supports_fractional_values(
    tmp_path,
):
    workbook = (
        tmp_path
        / "fractional_dependency.xlsx"
    )

    _write_workbook(
        workbook,
        dependency_quantity=0.5,
    )

    importer = SupplyChainExcelImporter()

    result = importer.import_file(
        workbook
    )

    assert result.success is True

    assert (
        result.records["Dependencies"][0][
            "required_quantity"
        ]
        == 0.5
    )