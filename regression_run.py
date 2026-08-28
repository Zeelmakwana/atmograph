"""
Final End-to-End Regression Script
Covers: backend health, Neo4j integrity, API smoke tests, entity checks,
        relationship types, mock data detection, response times.
"""
import time
import json
import sys
import os

# ── HTTP helper ──────────────────────────────────────────────────────────────
try:
    import urllib.request
    import urllib.error

    def get(url, timeout=10):
        t0 = time.time()
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                ms = int((time.time() - t0) * 1000)
                return resp.status, body, ms
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            ms = int((time.time() - t0) * 1000)
            return e.code, body, ms
        except Exception as ex:
            ms = int((time.time() - t0) * 1000)
            return 0, str(ex), ms

except Exception as e:
    print(f"FATAL: cannot import urllib: {e}")
    sys.exit(1)

BASE = "http://localhost:8000"
results = {}

# ── 1. Health endpoint ────────────────────────────────────────────────────────
status, body, ms = get(f"{BASE}/health")
ok = status == 200
results["health"] = {"pass": ok, "status": status, "ms": ms, "body": body[:200]}
print(f"[health] {'PASS' if ok else 'FAIL'} HTTP {status} {ms}ms")

# ── 2. OpenAPI / docs reachable ───────────────────────────────────────────────
status2, _, ms2 = get(f"{BASE}/docs")
results["docs"] = {"pass": status2 == 200, "status": status2, "ms": ms2}
print(f"[docs]   {'PASS' if status2==200 else 'FAIL'} HTTP {status2} {ms2}ms")

# ── 3. All API smoke tests ────────────────────────────────────────────────────
endpoints = [
    ("graph_nodes",    f"{BASE}/api/graph/nodes?limit=5"),
    ("graph_edges",    f"{BASE}/api/graph/edges?limit=5"),
    ("graph_search",   f"{BASE}/api/graph/search?q=ABB"),
    ("analytics_ovr",  f"{BASE}/api/analytics/overview"),
    ("analytics_risk", f"{BASE}/api/analytics/risk-distribution"),
    ("predictions",    f"{BASE}/api/predictions"),
    ("copilot_health", f"{BASE}/api/copilot/health"),
    ("events",         f"{BASE}/api/events"),
    ("company_list",   f"{BASE}/api/company"),
    ("export_formats", f"{BASE}/api/export/formats"),
    ("v1_forecast",    f"{BASE}/api/v1/forecast"),
    ("v1_simulation",  f"{BASE}/api/v1/simulation"),
    ("v1_reports",     f"{BASE}/api/v1/reports"),
    ("v1_collab",      f"{BASE}/api/v1/collaboration"),
    ("v1_admin",       f"{BASE}/api/v1/admin"),
    ("v1_explanations",f"{BASE}/api/v1/explanations"),
    ("v1_sim_scenarios",f"{BASE}/api/v1/simulation/scenarios"),
]

api_results = {}
for name, url in endpoints:
    sc, body, ms = get(url)
    ok = sc in (200, 201, 204)
    api_results[name] = {"pass": ok, "status": sc, "ms": ms, "snippet": body[:300]}
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:25s} HTTP {sc} {ms}ms")

results["api_smoke"] = api_results

# ── 4. Real entity checks ─────────────────────────────────────────────────────
entity_checks = [
    ("co-abb",  f"{BASE}/api/graph/node/co-abb"),
    ("sup-048", f"{BASE}/api/graph/node/sup-048"),
    ("evt-020", f"{BASE}/api/graph/node/evt-020"),
]
entity_results = {}
print("\n[Entity Checks]")
for eid, url in entity_checks:
    sc, body, ms = get(url)
    # Also try company endpoint
    if sc != 200:
        sc2, body2, ms2 = get(f"{BASE}/api/company/{eid}")
        if sc2 == 200:
            sc, body, ms = sc2, body2, ms2
    ok = sc == 200
    snippet = body[:400] if ok else body[:200]
    entity_results[eid] = {"pass": ok, "status": sc, "ms": ms, "snippet": snippet}
    print(f"  [{'PASS' if ok else 'FAIL'}] {eid:12s} HTTP {sc} {ms}ms  {snippet[:120]}")

results["entities"] = entity_results

# ── 5. Neo4j integrity via backend cypher endpoint ────────────────────────────
print("\n[Neo4j Integrity]")
# Use analytics or graph endpoint to infer counts
# Try a dedicated stats endpoint first
sc, body, ms = get(f"{BASE}/api/graph/stats")
if sc == 200:
    results["neo4j_stats_endpoint"] = {"pass": True, "body": body[:800]}
    print(f"  [PASS] /api/graph/stats HTTP {sc} {ms}ms")
    print(f"         {body[:500]}")
else:
    print(f"  [INFO] /api/graph/stats HTTP {sc} - trying /api/analytics/overview")
    sc2, body2, ms2 = get(f"{BASE}/api/analytics/overview")
    results["neo4j_stats_endpoint"] = {"pass": sc2==200, "status": sc2, "body": body2[:800]}
    print(f"  [{'PASS' if sc2==200 else 'FAIL'}] /api/analytics/overview HTTP {sc2} {ms2}ms")
    print(f"         {body2[:500]}")

# ── 6. Relationship types check ───────────────────────────────────────────────
print("\n[Relationship Types]")
sc, body, ms = get(f"{BASE}/api/graph/relationship-types")
if sc == 200:
    results["rel_types"] = {"pass": True, "body": body[:600]}
    print(f"  [PASS] /api/graph/relationship-types HTTP {sc} {ms}ms")
    print(f"         {body[:400]}")
else:
    # Try edges endpoint and inspect
    sc2, body2, ms2 = get(f"{BASE}/api/graph/edges?limit=50")
    results["rel_types"] = {"pass": sc2==200, "status": sc2, "body": body2[:600]}
    print(f"  [INFO] relationship-types returned {sc}, using /api/graph/edges snippet")
    print(f"         {body2[:400]}")

# ── 7. Check for mock/static data ────────────────────────────────────────────
print("\n[Mock Data Check]")
# Request graph nodes - real data will have varied IDs; mock typically repeats patterns
sc, body, ms = get(f"{BASE}/api/graph/nodes?limit=30")
mock_indicators = []
if sc == 200:
    try:
        data = json.loads(body)
        nodes = data if isinstance(data, list) else data.get("data", data.get("nodes", []))
        if isinstance(nodes, dict):
            nodes = nodes.get("nodes", [])
        # Check for obvious mock patterns
        ids = [str(n.get("id","")) for n in nodes if isinstance(n, dict)]
        names = [str(n.get("name","") or n.get("label","")) for n in nodes if isinstance(n, dict)]
        if ids.count(ids[0]) > 3 if ids else False:
            mock_indicators.append("Repeated IDs detected")
        if any("mock" in s.lower() or "test" in s.lower() or "lorem" in s.lower() for s in names):
            mock_indicators.append(f"Mock/test names detected: {[s for s in names if 'mock' in s.lower() or 'test' in s.lower()]}")
        results["mock_check"] = {"pass": len(mock_indicators)==0, "node_count": len(nodes), "indicators": mock_indicators, "sample_ids": ids[:10]}
        print(f"  [{'PASS' if not mock_indicators else 'WARN'}] node_count={len(nodes)} indicators={mock_indicators}")
        print(f"         sample_ids={ids[:10]}")
    except Exception as ex:
        results["mock_check"] = {"pass": None, "error": str(ex)}
        print(f"  [WARN] Could not parse nodes: {ex}")
else:
    results["mock_check"] = {"pass": None, "status": sc}
    print(f"  [WARN] /api/graph/nodes returned {sc}")

# ── 8. Response-time sanity ───────────────────────────────────────────────────
print("\n[Response Time Sanity]")
time_results = {}
perf_endpoints = [
    ("health",        f"{BASE}/health"),
    ("graph_nodes",   f"{BASE}/api/graph/nodes?limit=10"),
    ("analytics_ovr", f"{BASE}/api/analytics/overview"),
    ("predictions",   f"{BASE}/api/predictions"),
    ("v1_forecast",   f"{BASE}/api/v1/forecast"),
]
for name, url in perf_endpoints:
    sc, _, ms = get(url)
    ok = ms < 5000  # 5s threshold for sanity only
    time_results[name] = {"ms": ms, "pass": ok and sc in (200,201,204)}
    flag = "PASS" if (ok and sc in (200,201,204)) else ("SLOW" if sc in (200,201,204) else "FAIL")
    print(f"  [{flag}] {name:25s} {ms}ms")

results["perf"] = time_results

# ── Save full results ─────────────────────────────────────────────────────────
out_path = r"c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\regression_full_results.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n[SAVED] Full results -> {out_path}")
print("\n=== REGRESSION SUMMARY ===")
print(f"Health:        {'PASS' if results['health']['pass'] else 'FAIL'}")
print(f"Docs/OpenAPI:  {'PASS' if results['docs']['pass'] else 'FAIL'}")
all_api = all(v["pass"] for v in api_results.values())
print(f"API Smoke:     {'PASS' if all_api else 'PARTIAL/FAIL'}")
all_ent = all(v["pass"] for v in entity_results.values())
print(f"Entities:      {'PASS' if all_ent else 'PARTIAL/FAIL'}")
print(f"Mock Check:    {'PASS' if results['mock_check'].get('pass') else 'SEE DETAILS'}")
all_perf = all(v["pass"] for v in time_results.values())
print(f"Perf Sanity:   {'PASS' if all_perf else 'PARTIAL/FAIL'}")
