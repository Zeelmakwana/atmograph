from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.services.supply_chain.excel_importer import (
    SupplyChainExcelImporter,
)
from app.services.supply_chain.database_importer import (
    SupplyChainDatabaseImporter,
)
from app.services.supply_chain.neo4j_business_importer import (
    SupplyChainNeo4jImporter,
)


class SupplyChainImportService:
    """
    Unified orchestrator for AtmoGraph supply chain data ingestion.

    Coordinates:
      1. Excel structure validation (SupplyChainExcelImporter)
      2. Deterministic SQL database ingestion (SupplyChainDatabaseImporter)
      3. Neo4j graph topology synchronization (SupplyChainNeo4jImporter)

    Ensures that business supply chain data remains the deterministic source
    of truth in SQLite/PostgreSQL while projecting the topology into Neo4j
    for GNN feature extraction and multi-hop graph queries.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.excel_importer = SupplyChainExcelImporter()
        self.database_importer = SupplyChainDatabaseImporter(db)
        self.neo4j_importer = SupplyChainNeo4jImporter(db)

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate_file(
        self,
        file_path: str | Path,
    ) -> dict[str, Any]:
        """
        Validate an Excel workbook against the required supply chain schema
        without persisting records to SQL or Neo4j.
        """
        result = self.excel_importer.import_file(file_path)

        return {
            "success": result.success,
            "stage": "validation",
            "filename": result.filename,
            "sheets_found": result.sheets_found,
            "sheets_validated": result.sheets_validated,
            "row_counts": result.row_counts,
            "warnings": result.warnings,
            "errors": result.errors,
        }

    # =========================================================
    # SQL DATABASE IMPORT
    # =========================================================

    def import_to_database(
        self,
        file_path: str | Path,
    ) -> dict[str, Any]:
        """
        Import validated Excel workbook into SQL business tables.
        """
        return self.database_importer.import_workbook(file_path)

    # =========================================================
    # NEO4J GRAPH SYNCHRONIZATION
    # =========================================================

    def sync_to_neo4j(self) -> dict[str, Any]:
        """
        Project current SQL business supply chain state into Neo4j.
        """
        return self.neo4j_importer.sync()

    # =========================================================
    # FULL END-TO-END PIPELINE
    # =========================================================

    def import_and_sync(
        self,
        file_path: str | Path,
        sync_graph: bool = True,
    ) -> dict[str, Any]:
        """
        Execute full end-to-end import:
          1. Validate and write to SQL database
          2. Synchronize business graph to Neo4j (optional, defaults to True)
        """
        db_result = self.import_to_database(file_path)

        if not db_result.get("success"):
            return {
                "success": False,
                "stage": db_result.get("stage", "database_import"),
                "filename": db_result.get("filename"),
                "database": db_result,
                "neo4j_sync": None,
                "errors": db_result.get("errors", []),
            }

        graph_result = None

        if sync_graph:
            graph_result = self.sync_to_neo4j()

        return {
            "success": True,
            "stage": "completed",
            "filename": db_result.get("filename"),
            "database": db_result,
            "neo4j_sync": graph_result,
        }


__all__ = [
    "SupplyChainImportService",
]
