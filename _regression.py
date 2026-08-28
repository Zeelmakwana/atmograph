"""
AtmoGraph AI — Final End-to-End Regression Script
Tests: Neo4j connectivity, all module APIs, cross-module data flow,
real entities, data integrity, performance sanity, and mock data audit.
Never prints passwords or secrets.
"""
import sys, os, asyncio, json, time, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "atmograph-ai", "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.config import get_settings
settings = get_settings()

results = {}
timings = {}

def record(name, passed, detail=""):
    results[name] = (passed, detail)
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")

def tick():
    return time.time()

def elapsed(start):
    return round((time.time() - start) * 1000, 1)

async def main():
    # ── 1. NEO4J + BACKEND STARTUP ────────────────────────────────────────
    print("\n=== 1. NEO4J CONNECTION & BACKEND STARTUP ===")
    t = tick()
    from app.database.neo4j import Neo4jClient
    from app.database.session import SessionManager
    client = Neo4jClient(settings)
    try:
        await client.connect()
        ms = elapsed(t)
        record("neo4j_connection", True, f"connected to {settings.neo4j_uri} in {ms}ms")
        record("neo4j_database", settings.neo4j_database == "neo4j", f"db={settings.neo4j_database}")
        record("neo4j_user", settings.neo4j_user == "neo4j", f"user={settings.neo4j_user}")
    except Exception as e:
        record("neo4j_connection", False, str(e))
        print("  Cannot proceed without Neo4j — aborting.")
        return

    sm = SessionManager(client, settings)

    # ── Verify health endpoint query ──────────────────────────────────
    t = tick()
    from neo4j import AsyncGraphDatabase
    driver = client._driver
    async with driver.session(database=settings.neo4j_database) as sess:
        r = await sess.run("RETURN 1 AS ok")
        rec = await r.single()
        record("neo4j_health_query", rec and rec["ok"] == 1, f"RETURN 1 OK in {elapsed(t)}ms")

    # ── 2. DATA INTEGRITY ─────────────────────────────────────────────────
    print("\n=== 2. DATA INTEGRITY ===")
    from app.repositories.graph_repository import GraphRepository
    from app.repositories.company_repository import CompanyRepository
    from app.repositories.analytics_repository import AnalyticsRepository
    from app.services.graph_service import GraphService
    from app.services.analytics_service import AnalyticsService

    graph_repo     = GraphRepository(sm)
    company_repo   = CompanyRepository(sm)
    analytics_repo = AnalyticsRepository(sm)
    analytics_svc  = AnalyticsService(analytics_repo)
    graph_svc      = GraphService(graph_repo, company_repo)

    t = tick()
    overview = await graph_svc.get_graph_overview()
    nc = overview.get("node_counts", {})
    rc = overview.get("relationship_counts", {})
    ms = elapsed(t)
    timings["graph_overview"] = ms

    expected_nodes = {"Company":30,"Supplier":100,"Manufacturer":20,"Warehouse":25,"Port":15,"Country":12,"Product":60,"DisruptionEvent":20}
    expected_rels  = {"SUPPLIES_TO":149,"LOCATED_IN":90,"AFFECTS":60,"HAS_WAREHOUSE":48,"SHIPS_THROUGH":40,"OPERATES_IN":30,"SOURCES_FROM":12}

    for label, exp in expected_nodes.items():
        record(f"integrity_{label.lower()}", nc.get(label,0)==exp, f"{nc.get(label,0)}/{exp}")

    record("integrity_total_nodes", overview.get("total_nodes")==282, f"total={overview.get('total_nodes')}")
    record("integrity_total_rels",  overview.get("total_relationships")==429, f"total={overview.get('total_relationships')}")

    # Check no unexpected relationship types
    known_rels = set(expected_rels.keys())
    actual_rels = set(rc.keys())
    unexpected = actual_rels - known_rels
    record("integrity_no_unexpected_rels", len(unexpected)==0, f"unexpected={unexpected if unexpected else 'none'}")
    print(f"      Overview fetched in {ms}ms")

    # ── 3. REAL ENTITY TESTS ──────────────────────────────────────────────
    print("\n=== 3. REAL ENTITY TESTS ===")
    t = tick()
    co_abb = await graph_svc.get_node("co-abb", label="Company")
    record("real_entity_co_abb", co_abb.get("id")=="co-abb", f"name={co_abb.get('name')} risk={co_abb.get('current_risk_score')}")
    timings["co_abb_lookup"] = elapsed(t)

    t = tick()
    suppliers = await graph_repo.find_nodes_by_label("Supplier", skip=0, limit=200)
    sup_048 = next((s for s in suppliers if s.get("id")=="sup-048"), None)
    record("real_entity_sup_048", sup_048 is not None, f"name={sup_048.get('name') if sup_048 else 'NOT FOUND'}")
    timings["supplier_lookup"] = elapsed(t)

    t = tick()
    events = await analytics_repo.get_disruption_events(skip=0, limit=25)
    evt_020 = next((e for e in events if e.get("event_id")=="evt-020"), None)
    record("real_entity_evt_020", evt_020 is not None, f"type={evt_020.get('event_type') if evt_020 else 'NOT FOUND'}")
    timings["event_lookup"] = elapsed(t)
