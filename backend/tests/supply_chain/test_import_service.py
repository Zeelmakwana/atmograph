from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.supply_chain_import_service import (
    SupplyChainImportService,
)


def test_import_service_instantiation():
    mock_db = MagicMock(spec=Session)
    service = SupplyChainImportService(db=mock_db)

    assert service is not None
    assert service.excel_importer is not None
    assert service.database_importer is not None
    assert service.neo4j_importer is not None


def test_validate_file_delegation(tmp_path: Path):
    mock_db = MagicMock(spec=Session)
    service = SupplyChainImportService(db=mock_db)

    test_file = tmp_path / "non_existent.xlsx"
    result = service.validate_file(test_file)

    assert result["success"] is False
    assert result["stage"] == "validation"
    assert "File not found" in result["errors"][0]


def test_import_to_database_delegation():
    mock_db = MagicMock(spec=Session)
    service = SupplyChainImportService(db=mock_db)

    with patch.object(
        service.database_importer,
        "import_workbook",
        return_value={"success": True, "rows": 100},
    ) as mock_import:
        result = service.import_to_database("dummy.xlsx")

        assert result["success"] is True
        mock_import.assert_called_once_with("dummy.xlsx")


def test_sync_to_neo4j_delegation():
    mock_db = MagicMock(spec=Session)
    service = SupplyChainImportService(db=mock_db)

    with patch.object(
        service.neo4j_importer,
        "sync",
        return_value={"success": True, "nodes": 50},
    ) as mock_sync:
        result = service.sync_to_neo4j()

        assert result["success"] is True
        mock_sync.assert_called_once()


def test_import_and_sync_full_pipeline_success():
    mock_db = MagicMock(spec=Session)
    service = SupplyChainImportService(db=mock_db)

    with patch.object(
        service.database_importer,
        "import_workbook",
        return_value={
            "success": True,
            "filename": "template.xlsx",
            "inserted": 25,
            "updated": 5,
        },
    ), patch.object(
        service.neo4j_importer,
        "sync",
        return_value={
            "success": True,
            "nodes": 40,
            "relationships": 60,
        },
    ):
        result = service.import_and_sync("template.xlsx", sync_graph=True)

        assert result["success"] is True
        assert result["stage"] == "completed"
        assert result["filename"] == "template.xlsx"
        assert result["database"]["inserted"] == 25
        assert result["neo4j_sync"]["nodes"] == 40


def test_import_and_sync_database_failure():
    mock_db = MagicMock(spec=Session)
    service = SupplyChainImportService(db=mock_db)

    with patch.object(
        service.database_importer,
        "import_workbook",
        return_value={
            "success": False,
            "stage": "validation",
            "filename": "broken.xlsx",
            "errors": ["Missing sheet: Companies"],
        },
    ):
        result = service.import_and_sync("broken.xlsx", sync_graph=True)

        assert result["success"] is False
        assert result["stage"] == "validation"
        assert "Missing sheet: Companies" in result["errors"]
