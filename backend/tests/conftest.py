from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# ATMO GRAPH TEST PATH
# ============================================================
#
# Tests import application modules like:
#
#     from app.core.database import SessionLocal
#
# When pytest is launched through the Windows pytest.exe
# wrapper, the backend directory is not always inserted into
# sys.path correctly.
#
# This makes test discovery deterministic.
# ============================================================

BACKEND_ROOT = (
    Path(__file__).resolve().parents[1]
)

backend_root_string = str(
    BACKEND_ROOT
)

if backend_root_string not in sys.path:
    sys.path.insert(
        0,
        backend_root_string,
    )