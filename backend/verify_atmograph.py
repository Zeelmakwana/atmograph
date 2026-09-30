"""
AtmoGraph Backend Smoke Test

Checks the currently running AtmoGraph backend without creating
or modifying application data.

Run from:
backend/

Command:
python verify_atmograph.py
"""

from __future__ import annotations

import json
import sys
from typing import Any

import requests


BASE_URL = "http://127.0.0.1:8000"
TEST_EVENT_ID = 25
TEST_GRAPH_ID = f"event_{TEST_EVENT_ID}"

TIMEOUT = 20


passed = 0
failed = 0
skipped = 0


def check(
    name: str,
    condition: bool,
    detail: str = "",
) -> None:
    global passed, failed

    if condition:
        passed += 1
        print(f"[PASS] {name}")
        if detail:
            print(f"       {detail}")
    else:
        failed += 1
        print(f"[FAIL] {name}")
        if detail:
            print(f"       {detail}")


def skip(
    name: str,
    detail: str = "",
) -> None:
    global skipped

    skipped += 1
    print(f"[SKIP] {name}")
    if detail:
        print(f"       {detail}")


def get_json(path: str) -> tuple[int, Any]:
    response = requests.get(
        BASE_URL + path,
        timeout=TIMEOUT,
    )

    try:
        data = response.json()
    except Exception:
        data = response.text

    return response.status_code, data


def unwrap(data: Any) -> Any:
    if isinstance(data, dict) and "data" in data:
        return data["data"]

    return data


def main() -> int:
    print()
    print("=" * 72)
    print(" AT M O G R A P H   BACKEND   SMOKE   TEST")
    print("=" * 72)
    print(f"API      : {BASE_URL}")
    print(f"Event ID : {TEST_EVENT_ID}")
    print(f"Graph ID : {TEST_GRAPH_ID}")
    print("=" * 72)
    print()

    # ---------------------------------------------------------
    # 1. ROOT
    # ---------------------------------------------------------

    try:
        status, data = get_json("/")

        check(
            "Root endpoint",
            status == 200,
            f"HTTP {status}",
        )

    except Exception as exc:
        check(
            "Root endpoint",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 2. HEALTH
    # ---------------------------------------------------------

    try:
        status, data = get_json("/health")

        body = unwrap(data)

        check(
            "FastAPI health",
            status == 200,
            f"HTTP {status}",
        )

        if isinstance(body, dict):
            check(
                "Health reports healthy",
                body.get("status") == "healthy",
                json.dumps(body),
            )

    except Exception as exc:
        check(
            "FastAPI health",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 3. EVENTS
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            "/api/events?limit=5"
        )

        body = unwrap(data)

        check(
            "Events API",
            status == 200,
            f"HTTP {status}",
        )

        if isinstance(body, list):
            events = body

        elif isinstance(body, dict):
            events = (
                body.get("events")
                or body.get("items")
                or []
            )

        else:
            events = []

        check(
            "Events response is usable",
            isinstance(events, list),
            f"{len(events)} events returned",
        )

        if events:
            latest = events[0]

            print()
            print(
                "       Latest event:"
            )
            print(
                f"       ID    : "
                f"{latest.get('id', latest.get('event_id'))}"
            )
            print(
                f"       Title : "
                f"{latest.get('title', 'N/A')}"
            )
            print()

    except Exception as exc:
        check(
            "Events API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 4. GRAPH STATUS
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            "/api/graph/status"
        )

        body = unwrap(data)

        check(
            "Neo4j status API",
            status == 200,
            f"HTTP {status}",
        )

        connected = False

        if isinstance(body, dict):
            connected = (
                body.get("connected") is True
                or body.get("status") == "connected"
                or body.get("success") is True
            )

        check(
            "Neo4j connected",
            connected,
            json.dumps(body),
        )

    except Exception as exc:
        check(
            "Neo4j status API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 5. GRAPH STATISTICS
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            "/api/graph/statistics"
        )

        body = unwrap(data)

        check(
            "Graph statistics API",
            status == 200,
            f"HTTP {status}",
        )

        if isinstance(body, dict):
            nodes = body.get(
                "total_nodes",
                body.get("nodes", 0),
            )

            relationships = body.get(
                "total_relationships",
                body.get("relationships", 0),
            )

            print(
                f"       Neo4j nodes         : {nodes}"
            )

            print(
                f"       Neo4j relationships : {relationships}"
            )

            check(
                "Graph contains nodes",
                int(nodes or 0) > 0,
                f"{nodes} nodes",
            )

            check(
                "Graph contains relationships",
                int(relationships or 0) > 0,
                f"{relationships} relationships",
            )

    except Exception as exc:
        check(
            "Graph statistics API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 6. GNN GRAPH
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            f"/api/graph-intelligence/"
            f"gnn-graph/{TEST_GRAPH_ID}?max_depth=3"
        )

        body = unwrap(data)

        check(
            "GNN graph API",
            status == 200,
            f"HTTP {status}",
        )

        node_count = 0
        edge_count = 0

        if isinstance(body, dict):

            if isinstance(
                body.get("node_names"),
                list,
            ):
                node_count = len(
                    body["node_names"]
                )

            elif isinstance(
                body.get("nodes"),
                list,
            ):
                node_count = len(
                    body["nodes"]
                )

            if isinstance(
                body.get("relationships"),
                list,
            ):
                edge_count = len(
                    body["relationships"]
                )

            elif isinstance(
                body.get("edges"),
                list,
            ):
                edge_count = len(
                    body["edges"]
                )

        print(
            f"       GNN graph nodes : {node_count}"
        )

        print(
            f"       GNN graph edges : {edge_count}"
        )

        check(
            "GNN graph has nodes",
            node_count > 0,
            f"{node_count} nodes",
        )

        check(
            "GNN graph has edges",
            edge_count > 0,
            f"{edge_count} edges",
        )

    except Exception as exc:
        check(
            "GNN graph API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 7. GNN PREDICTION
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            f"/api/graph-intelligence/"
            f"gnn-predict/{TEST_GRAPH_ID}"
        )

        body = unwrap(data)

        check(
            "GNN prediction API",
            status == 200,
            f"HTTP {status}",
        )

        check(
            "GNN prediction response exists",
            body is not None,
            "Inference response received",
        )

    except Exception as exc:
        check(
            "GNN prediction API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 8. HYBRID PREDICTION
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            f"/api/graph-intelligence/"
            f"hybrid-predict/"
            f"{TEST_EVENT_ID}/"
            f"{TEST_GRAPH_ID}"
        )

        body = unwrap(data)

        check(
            "Hybrid prediction API",
            status == 200,
            f"HTTP {status}",
        )

        hybrid_score = None

        if isinstance(body, dict):

            hybrid_score = (
                body.get("hybrid_risk")
                or body.get("hybrid_score")
                or body.get("risk_score")
                or body.get("score")
            )

        if hybrid_score is not None:
            print(
                f"       Hybrid risk : {hybrid_score}"
            )

            check(
                "Hybrid risk is numeric",
                isinstance(
                    hybrid_score,
                    (int, float),
                ),
                str(hybrid_score),
            )
        else:
            check(
                "Hybrid response exists",
                body is not None,
                "Response received",
            )

    except Exception as exc:
        check(
            "Hybrid prediction API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 9. GRAPH EVENT
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            f"/api/graph/event/"
            f"{TEST_EVENT_ID}"
        )

        body = unwrap(data)

        check(
            "Event graph API",
            status == 200,
            f"HTTP {status}",
        )

        check(
            "Event graph response exists",
            body is not None,
            "Response received",
        )

    except Exception as exc:
        check(
            "Event graph API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 10. SUPPLIERS
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            f"/api/graph/event/"
            f"{TEST_EVENT_ID}/suppliers"
        )

        body = unwrap(data)

        check(
            "Affected suppliers API",
            status == 200,
            f"HTTP {status}",
        )

        print(
            f"       Response: "
            f"{str(body)[:300]}"
        )

    except Exception as exc:
        check(
            "Affected suppliers API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 11. PRODUCTS
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            f"/api/graph/event/"
            f"{TEST_EVENT_ID}/products"
        )

        body = unwrap(data)

        check(
            "Affected products API",
            status == 200,
            f"HTTP {status}",
        )

        print(
            f"       Response: "
            f"{str(body)[:300]}"
        )

    except Exception as exc:
        check(
            "Affected products API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 12. RIPPLE
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            f"/api/graph/event/"
            f"{TEST_EVENT_ID}/ripple?max_depth=5"
        )

        body = unwrap(data)

        check(
            "Ripple API",
            status == 200,
            f"HTTP {status}",
        )

        check(
            "Ripple response exists",
            body is not None,
            "Response received",
        )

    except Exception as exc:
        check(
            "Ripple API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 13. NLP
    # ---------------------------------------------------------

    try:
        response = requests.post(
            BASE_URL + "/api/nlp/analyze",
            json={
                "title": "Supply chain health check",
                "description": (
                    "A logistics disruption may cause "
                    "shipment delays."
                ),
            },
            timeout=TIMEOUT,
        )

        check(
            "NLP API",
            response.status_code == 200,
            f"HTTP {response.status_code}",
        )

        if response.ok:
            body = response.json()

            check(
                "NLP returned analysis",
                body is not None,
                "NLP response received",
            )

    except Exception as exc:
        check(
            "NLP API",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # 14. OPENAPI ROUTES
    # ---------------------------------------------------------

    try:
        status, data = get_json(
            "/openapi.json"
        )

        check(
            "OpenAPI",
            status == 200,
            f"HTTP {status}",
        )

        paths = (
            data.get("paths", {})
            if isinstance(data, dict)
            else {}
        )

        required_paths = [
            "/api/events",
            "/api/graph/status",
            "/api/graph/statistics",
            "/api/graph-intelligence/gnn-graph/{graph_id}",
            "/api/graph-intelligence/gnn-predict/{graph_id}",
            "/api/graph-intelligence/hybrid-predict/{event_id}/{graph_id}",
            "/api/news-intelligence/analyze",
        ]

        for path in required_paths:
            check(
                f"Route exists: {path}",
                path in paths,
            )

    except Exception as exc:
        check(
            "OpenAPI route inspection",
            False,
            str(exc),
        )

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    print()
    print("=" * 72)
    print(" TEST RESULT")
    print("=" * 72)

    print(
        f"PASSED  : {passed}"
    )

    print(
        f"FAILED  : {failed}"
    )

    print(
        f"SKIPPED : {skipped}"
    )

    print("=" * 72)

    if failed == 0:
        print()
        print(
            "ATMO GRAPH BACKEND STATUS: HEALTHY"
        )
        print(
            "Core API + Neo4j + GNN + NLP pipeline "
            "passed the smoke test."
        )
        print()
        return 0

    print()
    print(
        "ATMO GRAPH BACKEND STATUS: NEEDS ATTENTION"
    )
    print(
        "Fix the failed checks before moving "
        "to deployment."
    )
    print()

    return 1


if __name__ == "__main__":
    sys.exit(main())