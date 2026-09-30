from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from app.schemas.supply_chain import SupplyChainImportResult


class SupplyChainExcelImporter:
    """
    Validate and normalize the AtmoGraph supply-chain Excel workbook.

    Excel
      ↓
    Read & Match sheets (supports synonyms: Materials -> Components, BOM -> Dependencies, etc.)
      ↓
    Map & Normalize columns & missing values (UNKNOWN, NaN, numeric strings)
      ↓
    Auto-generate synthetic keys and cross-sheet default references if missing
      ↓
    Validate relational integrity
      ↓
    Return structured records
    """

    # Canonical sheets and their canonical column names
    CANONICAL_SHEETS: dict[str, list[str]] = {
        "Companies": [
            "company_id",
            "company_name",
            "industry",
        ],
        "Suppliers": [
            "supplier_id",
            "supplier_name",
            "country",
            "city",
            "location_known",
        ],
        "Plants": [
            "plant_id",
            "plant_name",
            "company_id",
            "country",
            "city",
        ],
        "Products": [
            "product_id",
            "product_name",
            "category",
        ],
        "Components": [
            "component_id",
            "component_name",
            "category",
        ],
        "Warehouses": [
            "warehouse_id",
            "warehouse_name",
            "country",
            "city",
        ],
        "Supply_Allocations": [
            "supplier_id",
            "component_id",
            "plant_id",
            "allocation_pct",
            "capacity_units",
            "spare_capacity_units",
            "lead_time_days",
            "criticality",
        ],
        "Inventory": [
            "inventory_id",
            "location_type",
            "location_id",
            "component_id",
            "quantity_units",
        ],
        "Capacity": [
            "capacity_id",
            "location_type",
            "location_id",
            "component_id",
            "capacity_units_per_day",
        ],
        "Demand": [
            "demand_id",
            "plant_id",
            "product_id",
            "daily_demand_units",
        ],
        "Routes": [
            "route_id",
            "source_type",
            "source_id",
            "destination_type",
            "destination_id",
            "transit_days",
            "route_status",
        ],
        "Dependencies": [
            "dependency_id",
            "source_type",
            "source_id",
            "target_type",
            "target_id",
            "dependency_type",
            "required_quantity",
            "criticality",
        ],
    }

    # Aliases for matching sheet names in user workbooks
    SHEET_ALIASES: dict[str, list[str]] = {
        "Companies": ["companies", "company", "organisation", "organization", "firm"],
        "Suppliers": ["suppliers", "supplier", "vendors", "vendor", "sellers", "partners"],
        "Plants": ["plants", "plant", "factories", "factory", "manufacturing_units", "units", "manufacturing"],
        "Components": ["components", "component", "materials", "material", "raw_materials", "parts", "items"],
        "Products": ["products", "product", "finished_goods", "goods", "skus", "garments", "apparel"],
        "Warehouses": ["warehouses", "warehouse", "storage", "dc", "distribution_centers", "depots"],
        "Supply_Allocations": ["supply_allocations", "supply_relationships", "supplier_allocations", "allocations", "sourcing", "supplier_matrix"],
        "Inventory": ["inventory", "stock", "stocks", "store_inventory", "warehouse_stock"],
        "Capacity": ["capacity", "capacities", "plant_capacity", "factory_capacity", "manufacturing_relationships"],
        "Demand": ["demand", "demands", "product_demand", "sales_demand", "order_demand"],
        "Routes": ["routes", "route", "logistics", "transport", "lanes", "transit_routes"],
        "Dependencies": ["dependencies", "dependency", "bom", "bill_of_materials", "product_bom", "product_dependencies"],
    }

    NUMERIC_COLUMNS = {
        "allocation_pct",
        "capacity_units",
        "spare_capacity_units",
        "lead_time_days",
        "quantity_units",
        "capacity_units_per_day",
        "daily_demand_units",
        "transit_days",
        "required_quantity",
    }

    BOOLEAN_COLUMNS = {
        "location_known",
    }

    def import_file(
        self,
        file_path: str | Path,
    ) -> SupplyChainImportResult:

        path = Path(file_path)

        if not path.exists():
            return SupplyChainImportResult(
                success=False,
                filename=path.name,
                sheets_found=[],
                sheets_validated=[],
                row_counts={},
                errors=[f"File not found: {path}"],
            )

        if path.suffix.lower() not in {".xlsx", ".xls"}:
            return SupplyChainImportResult(
                success=False,
                filename=path.name,
                sheets_found=[],
                sheets_validated=[],
                row_counts={},
                errors=["Only .xlsx and .xls files are supported."],
            )

        try:
            workbook = pd.ExcelFile(path)
        except Exception as exc:
            return SupplyChainImportResult(
                success=False,
                filename=path.name,
                sheets_found=[],
                sheets_validated=[],
                row_counts={},
                errors=[f"Unable to open Excel workbook: {exc}"],
            )

        sheets_found = workbook.sheet_names
        sheet_map = self._resolve_sheet_names(sheets_found)

        errors: list[str] = []
        warnings: list[str] = []
        validated: list[str] = []
        row_counts: dict[str, int] = {}
        raw_dataframes: dict[str, pd.DataFrame] = {}

        # Check required sheets
        for canonical_name in self.CANONICAL_SHEETS:
            actual_sheet = sheet_map.get(canonical_name)
            if not actual_sheet:
                errors.append(f"Missing required sheet: {canonical_name}")
                continue

            try:
                df = pd.read_excel(path, sheet_name=actual_sheet)
                df.columns = [str(c).strip() for c in df.columns]
                raw_dataframes[canonical_name] = df
            except Exception as exc:
                errors.append(f"{canonical_name} ({actual_sheet}): unable to read sheet: {exc}")

        if errors:
            return SupplyChainImportResult(
                success=False,
                filename=path.name,
                sheets_found=sheets_found,
                sheets_validated=[],
                row_counts={},
                warnings=warnings,
                errors=errors,
                records={},
            )

        # Normalize data sheet-by-sheet with intelligent column mapping & fallback generation
        records = self._normalize_all_sheets(raw_dataframes, errors, warnings)

        for sheet_name, rows in records.items():
            row_counts[sheet_name] = len(rows)
            self._validate_sheet(sheet_name, rows, errors, warnings)
            validated.append(sheet_name)

        if not errors:
            self._validate_references(records, errors, warnings)

        success = not errors

        return SupplyChainImportResult(
            success=success,
            filename=path.name,
            sheets_found=sheets_found,
            sheets_validated=validated if success else [],
            row_counts=row_counts if success else {},
            warnings=warnings,
            errors=errors,
            records=records if success else {},
        )

    # =========================================================
    # SHEET NAME RESOLVER
    # =========================================================

    def _resolve_sheet_names(self, sheet_names: list[str]) -> dict[str, str]:
        """
        Maps canonical sheet names to actual sheet names in the workbook.
        """
        lookup = {s.strip().lower(): s for s in sheet_names}
        resolved: dict[str, str] = {}

        for canonical, aliases in self.SHEET_ALIASES.items():
            # Exact or alias match
            for alias in aliases:
                norm_alias = alias.lower()
                if norm_alias in lookup:
                    resolved[canonical] = lookup[norm_alias]
                    break

        return resolved

    # =========================================================
    # SHEET NORMALIZATION PIPELINE
    # =========================================================

    def _normalize_all_sheets(
        self,
        raw_dfs: dict[str, pd.DataFrame],
        errors: list[str],
        warnings: list[str],
    ) -> dict[str, list[dict[str, Any]]]:
        records: dict[str, list[dict[str, Any]]] = {}

        # 1. Companies
        records["Companies"] = self._normalize_companies(raw_dfs.get("Companies"), errors)
        first_company_id = records["Companies"][0]["company_id"] if records["Companies"] else "C001"

        # 2. Suppliers
        records["Suppliers"] = self._normalize_suppliers(raw_dfs.get("Suppliers"), errors)

        # 3. Plants
        records["Plants"] = self._normalize_plants(raw_dfs.get("Plants"), first_company_id, errors)
        first_plant_id = records["Plants"][0]["plant_id"] if records["Plants"] else "P001"

        # 4. Products
        records["Products"] = self._normalize_products(raw_dfs.get("Products"), errors)

        # 5. Components
        records["Components"] = self._normalize_components(raw_dfs.get("Components"), errors)

        # 6. Warehouses
        records["Warehouses"] = self._normalize_warehouses(raw_dfs.get("Warehouses"), errors)

        # 7. Dependencies (BOM)
        records["Dependencies"] = self._normalize_dependencies(raw_dfs.get("Dependencies"), errors)

        # 8. Supply Allocations
        records["Supply_Allocations"] = self._normalize_supply_allocations(
            raw_dfs.get("Supply_Allocations"),
            first_plant_id,
            records.get("Components", []),
            errors,
        )

        # 9. Inventory
        records["Inventory"] = self._normalize_inventory(
            raw_dfs.get("Inventory"),
            records.get("Plants", []),
            records.get("Warehouses", []),
            errors,
        )

        # 10. Capacity
        records["Capacity"] = self._normalize_capacity(
            raw_dfs.get("Capacity"),
            first_plant_id,
            records.get("Components", []),
            errors,
        )

        # 11. Demand
        records["Demand"] = self._normalize_demand(
            raw_dfs.get("Demand"),
            first_plant_id,
            records.get("Products", []),
            errors,
        )

        # 12. Routes
        records["Routes"] = self._normalize_routes(raw_dfs.get("Routes"), errors)

        return records

    # =========================================================
    # INDIVIDUAL SHEET NORMALIZERS
    # =========================================================

    def _clean_str(self, val: Any, default: str | None = None) -> str | None:
        if val is None or pd.isna(val):
            return default
        s = str(val).strip()
        if not s or s.upper() in {"UNKNOWN", "NAN", "NONE", "NULL", "-"}:
            return default
        return s

    def _clean_float(self, val: Any, default: float = 0.0) -> float:
        if val is None or pd.isna(val):
            return default
        if isinstance(val, (int, float)):
            return float(val) if not math.isnan(val) else default
        s = str(val).strip()
        if not s or s.upper() in {"UNKNOWN", "NAN", "NONE", "NULL", "-", "N/A"}:
            return default
        try:
            return float(s.replace(",", ""))
        except (ValueError, TypeError):
            return default

    def _normalize_companies(self, df: pd.DataFrame | None, errors: list[str]) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return [{"company_id": "C001", "company_name": "Company", "industry": "Manufacturing"}]
        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            cid = self._clean_str(self._find_col(row, ["company_id", "id", "code"]), f"C{i+1:03d}")
            name = self._clean_str(self._find_col(row, ["company_name", "name", "title"]), f"Company {cid}")
            ind = self._clean_str(self._find_col(row, ["industry", "sector", "business_type"]), "Manufacturing")
            rows.append({"company_id": str(cid), "company_name": str(name), "industry": ind})
        return rows

    def _normalize_suppliers(self, df: pd.DataFrame | None, errors: list[str]) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []
        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            sid = self._clean_str(self._find_col(row, ["supplier_id", "id", "code", "vendor_id"]), f"S{i+1:03d}")
            name = self._clean_str(self._find_col(row, ["supplier_name", "name", "title", "vendor_name"]), f"Supplier {sid}")
            city = self._clean_str(self._find_col(row, ["city", "location", "place", "city_name", "town"]), "Surat")
            country = self._clean_str(self._find_col(row, ["country", "nation"]), "India")
            loc_known_raw = self._find_col(row, ["location_known", "is_location_known"])
            loc_known = self._normalize_bool(loc_known_raw, default=True)
            rows.append({
                "supplier_id": str(sid),
                "supplier_name": str(name),
                "city": city,
                "country": country,
                "location_known": loc_known,
            })
        return rows

    def _normalize_plants(self, df: pd.DataFrame | None, default_company_id: str, errors: list[str]) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []
        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            pid = self._clean_str(self._find_col(row, ["plant_id", "id", "code", "unit_id", "factory_id"]), f"P{i+1:03d}")
            name = self._clean_str(self._find_col(row, ["plant_name", "name", "title", "factory_name"]), f"Plant {pid}")
            cid = self._clean_str(self._find_col(row, ["company_id", "company"]), default_company_id)
            city = self._clean_str(self._find_col(row, ["city", "location", "place"]), "Surat")
            country = self._clean_str(self._find_col(row, ["country", "nation"]), "India")
            rows.append({
                "plant_id": str(pid),
                "plant_name": str(name),
                "company_id": str(cid),
                "city": city,
                "country": country,
            })
        return rows

    def _normalize_products(self, df: pd.DataFrame | None, errors: list[str]) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []
        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            pid = self._clean_str(self._find_col(row, ["product_id", "id", "code", "sku", "item_id"]), f"PR{i+1:03d}")
            name = self._clean_str(self._find_col(row, ["product_name", "name", "title", "item_name"]), f"Product {pid}")
            cat = self._clean_str(self._find_col(row, ["category", "type", "group", "product_type"]), "Apparel")
            rows.append({
                "product_id": str(pid),
                "product_name": str(name),
                "category": cat,
            })
        return rows

    def _normalize_components(self, df: pd.DataFrame | None, errors: list[str]) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []
        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            cid = self._clean_str(self._find_col(row, ["component_id", "material_id", "id", "code", "part_id", "item_id"]), f"M{i+1:03d}")
            name = self._clean_str(self._find_col(row, ["component_name", "material_name", "name", "title", "item_name"]), f"Component {cid}")
            cat = self._clean_str(self._find_col(row, ["category", "material_type", "type", "group"]), "Raw Material")
            rows.append({
                "component_id": str(cid),
                "component_name": str(name),
                "category": cat,
            })
        return rows

    def _normalize_warehouses(self, df: pd.DataFrame | None, errors: list[str]) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []
        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            wid = self._clean_str(self._find_col(row, ["warehouse_id", "id", "code"]), f"W{i+1:03d}")
            name = self._clean_str(self._find_col(row, ["warehouse_name", "name", "title"]), f"Warehouse {wid}")
            city = self._clean_str(self._find_col(row, ["city", "location", "place"]), "Surat")
            country = self._clean_str(self._find_col(row, ["country", "nation"]), "India")
            rows.append({
                "warehouse_id": str(wid),
                "warehouse_name": str(name),
                "city": city,
                "country": country,
            })
        return rows

    def _normalize_dependencies(self, df: pd.DataFrame | None, errors: list[str]) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []
        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            dep_id = self._clean_str(self._find_col(row, ["dependency_id", "id"]), f"DEP_{i+1:03d}")

            # Check if this is a BOM format (product_id, material_id, quantity_required)
            prod_id = self._clean_str(self._find_col(row, ["product_id", "source_id", "parent_id"]))
            mat_id = self._clean_str(self._find_col(row, ["material_id", "component_id", "target_id", "child_id"]))

            # Default canonical orientation: Product (source) depends on Component (target)
            s_type = self._clean_str(self._find_col(row, ["source_type"]), "product")
            s_id = self._clean_str(self._find_col(row, ["source_id"]), prod_id)
            t_type = self._clean_str(self._find_col(row, ["target_type"]), "component")
            t_id = self._clean_str(self._find_col(row, ["target_id"]), mat_id)

            dep_type = self._clean_str(self._find_col(row, ["dependency_type", "type"]), "bom")
            raw_qty = self._find_col(row, ["required_quantity", "quantity_required", "quantity", "qty"])
            if raw_qty is not None and not pd.isna(raw_qty) and str(raw_qty).strip() != "":
                qty = self._clean_float(raw_qty, default=0.0)
            else:
                qty = 1.0
            crit = self._clean_str(self._find_col(row, ["criticality", "priority"]), "high")

            if not s_id or not t_id:
                continue

            rows.append({
                "dependency_id": str(dep_id),
                "source_type": s_type,
                "source_id": str(s_id),
                "target_type": t_type,
                "target_id": str(t_id),
                "dependency_type": dep_type,
                "required_quantity": qty,
                "criticality": crit,
            })
        return rows

    def _normalize_supply_allocations(
        self,
        df: pd.DataFrame | None,
        default_plant_id: str,
        components: list[dict[str, Any]],
        errors: list[str],
    ) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []

        raw_rows: list[dict[str, Any]] = []
        comp_supplier_counts: dict[str, int] = {}

        for i, row in df.iterrows():
            sid = self._clean_str(self._find_col(row, ["supplier_id", "from_id", "vendor_id"]))
            cid = self._clean_str(self._find_col(row, ["component_id", "material_id", "item_id"]))
            pid = self._clean_str(self._find_col(row, ["plant_id", "to_id", "destination_id"]), default_plant_id)

            if not sid or not cid:
                continue

            comp_supplier_counts[cid] = comp_supplier_counts.get(cid, 0) + 1

            alloc_val = self._clean_float(self._find_col(row, ["allocation_pct", "allocation_percent", "allocation", "share"]), default=-1.0)
            cap_val = self._clean_float(self._find_col(row, ["capacity_units", "monthly_capacity", "capacity"]), default=1000.0)
            spare_val = self._clean_float(self._find_col(row, ["spare_capacity_units", "spare_capacity"]), default=0.0)
            lead_val = self._clean_float(self._find_col(row, ["lead_time_days", "lead_time"]), default=2.0)
            crit = self._clean_str(self._find_col(row, ["criticality", "priority"]), "high")

            raw_rows.append({
                "supplier_id": str(sid),
                "component_id": str(cid),
                "plant_id": str(pid),
                "allocation_pct": alloc_val,
                "capacity_units": cap_val,
                "spare_capacity_units": spare_val,
                "lead_time_days": lead_val,
                "criticality": crit,
            })

        # Resolve allocation percent: if unknown or negative, evenly divide among suppliers of that component
        resolved_rows: list[dict[str, Any]] = []
        for item in raw_rows:
            cid = item["component_id"]
            alloc = item["allocation_pct"]
            if alloc < 0 or alloc > 100:
                count = max(1, comp_supplier_counts.get(cid, 1))
                alloc = round(100.0 / count, 2)
            item["allocation_pct"] = alloc
            resolved_rows.append(item)

        return resolved_rows

    def _normalize_inventory(
        self,
        df: pd.DataFrame | None,
        plants: list[dict[str, Any]],
        warehouses: list[dict[str, Any]],
        errors: list[str],
    ) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []

        plant_ids = {p["plant_id"] for p in plants}
        warehouse_ids = {w["warehouse_id"] for w in warehouses}

        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            inv_id = self._clean_str(self._find_col(row, ["inventory_id", "id"]), f"INV_{i+1:03d}")
            loc_id = self._clean_str(self._find_col(row, ["location_id", "plant_id", "warehouse_id"]), "P001")

            # Infer location_type
            loc_type = self._clean_str(self._find_col(row, ["location_type"]))
            if not loc_type:
                if loc_id in plant_ids or str(loc_id).startswith("P"):
                    loc_type = "plant"
                else:
                    loc_type = "warehouse"

            comp_id = self._clean_str(self._find_col(row, ["component_id", "material_id", "item_id", "product_id"]))
            qty = self._clean_float(self._find_col(row, ["quantity_units", "quantity", "stock", "qty"]), default=500.0)

            if not comp_id:
                continue

            rows.append({
                "inventory_id": str(inv_id),
                "location_type": str(loc_type).lower(),
                "location_id": str(loc_id),
                "component_id": str(comp_id),
                "quantity_units": qty,
            })
        return rows

    def _normalize_capacity(
        self,
        df: pd.DataFrame | None,
        default_plant_id: str,
        components: list[dict[str, Any]],
        errors: list[str],
    ) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []

        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            cap_id = self._clean_str(self._find_col(row, ["capacity_id", "id"]), f"CAP_{i+1:03d}")
            loc_id = self._clean_str(self._find_col(row, ["location_id", "plant_id"]), default_plant_id)
            loc_type = self._clean_str(self._find_col(row, ["location_type"]), "plant")
            comp_id = self._clean_str(self._find_col(row, ["component_id", "item_id", "material_id", "product_id"]))
            cap_units = self._clean_float(self._find_col(row, ["capacity_units_per_day", "capacity_per_day", "daily_capacity", "units_per_day"]), default=100.0)

            if not comp_id:
                continue

            rows.append({
                "capacity_id": str(cap_id),
                "location_type": str(loc_type).lower(),
                "location_id": str(loc_id),
                "component_id": str(comp_id),
                "capacity_units_per_day": cap_units,
            })
        return rows

    def _normalize_demand(
        self,
        df: pd.DataFrame | None,
        default_plant_id: str,
        products: list[dict[str, Any]],
        errors: list[str],
    ) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []

        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            dem_id = self._clean_str(self._find_col(row, ["demand_id", "id"]), f"DEM_{i+1:03d}")
            plant_id = self._clean_str(self._find_col(row, ["plant_id"]), default_plant_id)
            prod_id = self._clean_str(self._find_col(row, ["product_id", "item_id", "sku"]))
            demand_units = self._clean_float(self._find_col(row, ["daily_demand_units", "daily_demand", "demand", "demand_units"]), default=25.0)

            if not prod_id:
                continue

            rows.append({
                "demand_id": str(dem_id),
                "plant_id": str(plant_id),
                "product_id": str(prod_id),
                "daily_demand_units": demand_units,
            })
        return rows

    def _normalize_routes(self, df: pd.DataFrame | None, errors: list[str]) -> list[dict[str, Any]]:
        if df is None or df.empty:
            return []

        rows: list[dict[str, Any]] = []
        for i, row in df.iterrows():
            rid = self._clean_str(self._find_col(row, ["route_id", "id", "code"]), f"R_{i+1:03d}")
            src_id = self._clean_str(self._find_col(row, ["source_id", "from_id", "origin_id"]))
            dest_id = self._clean_str(self._find_col(row, ["destination_id", "to_id", "dest_id"]))

            if not src_id or not dest_id:
                continue

            # Infer source & dest types
            src_type = self._clean_str(self._find_col(row, ["source_type"]))
            if not src_type:
                src_type = "supplier" if str(src_id).startswith("S") else "plant" if str(src_id).startswith("P") else "warehouse"

            dest_type = self._clean_str(self._find_col(row, ["destination_type"]))
            if not dest_type:
                dest_type = "plant" if str(dest_id).startswith("P") else "warehouse" if str(dest_id).startswith("W") else "customer"

            transit = self._clean_float(self._find_col(row, ["transit_days", "lead_time_days", "lead_time"]), default=1.0)
            status = self._clean_str(self._find_col(row, ["route_status", "status"]), "active")

            rows.append({
                "route_id": str(rid),
                "source_type": str(src_type).lower(),
                "source_id": str(src_id),
                "destination_type": str(dest_type).lower(),
                "destination_id": str(dest_id),
                "transit_days": transit,
                "route_status": status,
            })
        return rows

    # =========================================================
    # HELPERS
    # =========================================================

    def _find_col(self, row: pd.Series | dict[str, Any], candidates: list[str]) -> Any:
        """
        Case-insensitive search for the first matching column name in a row.
        """
        row_dict = row.to_dict() if isinstance(row, pd.Series) else row
        lower_keys = {str(k).strip().lower(): k for k in row_dict.keys()}

        for cand in candidates:
            c_low = cand.strip().lower()
            if c_low in lower_keys:
                return row_dict[lower_keys[c_low]]
        return None

    def _normalize_bool(self, val: Any, default: bool = True) -> bool:
        if val is None or pd.isna(val):
            return default
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        if s in {"true", "yes", "y", "1"}:
            return True
        if s in {"false", "no", "n", "0"}:
            return False
        return default

    # =========================================================
    # RELATIONAL INTEGRITY VALIDATIONS
    # =========================================================

    def _validate_sheet(
        self,
        sheet_name: str,
        rows: list[dict[str, Any]],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        id_columns = {
            "Companies": "company_id",
            "Suppliers": "supplier_id",
            "Plants": "plant_id",
            "Products": "product_id",
            "Components": "component_id",
            "Warehouses": "warehouse_id",
            "Supply_Allocations": None,
            "Inventory": "inventory_id",
            "Capacity": "capacity_id",
            "Demand": "demand_id",
            "Routes": "route_id",
            "Dependencies": "dependency_id",
        }

        id_column = id_columns.get(sheet_name)
        if id_column:
            seen: set[str] = set()
            for index, row in enumerate(rows, start=2):
                value = row.get(id_column)
                if not value:
                    errors.append(f"{sheet_name} row {index}: {id_column} is required.")
                    continue
                value_str = str(value)
                if value_str in seen:
                    errors.append(f"{sheet_name} row {index}: duplicate {id_column} '{value_str}'.")
                seen.add(value_str)

        if sheet_name == "Dependencies":
            for index, row in enumerate(rows, start=2):
                quantity = row.get("required_quantity")
                if quantity is None:
                    errors.append(f"{sheet_name} row {index}: required_quantity is required.")
                elif quantity <= 0:
                    errors.append(f"{sheet_name} row {index}: required_quantity must be greater than 0.")

        if not rows:
            warnings.append(f"{sheet_name}: sheet is empty.")

    def _validate_references(
        self,
        records: dict[str, list[dict[str, Any]]],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        def ids(sheet: str, column: str) -> set[str]:
            return {
                str(row[column])
                for row in records.get(sheet, [])
                if row.get(column) is not None
            }

        supplier_ids = ids("Suppliers", "supplier_id")
        plant_ids = ids("Plants", "plant_id")
        product_ids = ids("Products", "product_id")
        component_ids = ids("Components", "component_id")

        # Supply allocations
        for index, row in enumerate(records.get("Supply_Allocations", []), start=2):
            sid = row.get("supplier_id")
            cid = row.get("component_id")
            pid = row.get("plant_id")

            if sid and str(sid) not in supplier_ids:
                errors.append(f"Supply_Allocations row {index}: unknown supplier_id '{sid}'.")
            if cid and str(cid) not in component_ids:
                errors.append(f"Supply_Allocations row {index}: unknown component_id '{cid}'.")
            if pid and str(pid) not in plant_ids:
                errors.append(f"Supply_Allocations row {index}: unknown plant_id '{pid}'.")

        # Dependencies
        for index, row in enumerate(records.get("Dependencies", []), start=2):
            st = str(row.get("source_type") or "").strip().lower()
            sid = row.get("source_id")
            tt = str(row.get("target_type") or "").strip().lower()
            tid = row.get("target_id")

            if st == "component" and sid and str(sid) not in component_ids:
                warnings.append(f"Dependencies row {index}: component source_id '{sid}' not found in Components sheet.")
            if tt == "product" and tid and str(tid) not in product_ids:
                warnings.append(f"Dependencies row {index}: product target_id '{tid}' not found in Products sheet.")

    @staticmethod
    def validate_file_size(
        file_path: str | Path,
        max_size_mb: int = 25,
    ) -> tuple[bool, str | None]:
        path = Path(file_path)
        if not path.exists():
            return False, "File does not exist."
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"File exceeds {max_size_mb} MB limit."
        return True, None
