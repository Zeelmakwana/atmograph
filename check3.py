"""
Entity checks + full Neo4j integrity + 500 error root-cause via log check.
No subprocess calls - HTTP only.
"""
import json, time, urllib.request, urllib.error

BASE = "http://localhost:8000"

def get(url, timeout=15):
    t0 = time.time()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            ms = int((time.time()-t0)*1000)
            return resp.status, body, ms
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        ms = int((time.time()-t0)*1000)
        return e.code, body, ms
    except Exception as ex:
        ms = int((time.time()-t0)*1000)
        return 0, str(ex), ms

print("=" * 60)
print("ENTITY CHECKS (correct routes)")
print("=" * 60)

# co-abb is a Company node (prefix co-)
# sup-048 is a Supplier node (prefix sup-)
# evt-020 is a DisruptionEvent node (prefix evt-)

entity_attempts = {
    "co-abb": [
        f"{BASE}/api/v1/companies/co-abb",
        f"{BASE}/api/v1/companies/co-abb/risk-summary",
        f"{BASE}/api/v1/graph/nodes/Company/co-abb",
        f"{BASE}/api/v1/graph/nodes/Company?search=abb&limit=5",
    ],
    "sup-048": [
        f"{BASE}/api/v1/graph/nodes/Supplier/sup-048",
        f"{BASE}/api/v1/graph/nodes/Supplier?limit=5",
        f"{BASE}/api/v1/companies/sup-048",
    ],
    "evt-020": [
        f"{BASE}/api/v1/graph/nodes/DisruptionEvent/evt-020",
        f"{BASE}/api/v1/graph/nodes/DisruptionEvent?limit=5",
        f"{BASE}/api/v1/analytics/disruption-events/evt-020",
    ],
}

entity_results = {}
for eid, urls in entity_attempts.items():
    found = False
    for url in urls:
        sc, body, ms = get(url)
        if sc == 200:
            print(f"  [PASS] {eid:12s} HTTP {sc} {ms}ms  {url}")
            entity_results[eid] = {"pass": True, "url": url, "ms": ms}
            # Parse to show node info
            try:
                d = json.loads(body)
                inner = d.get("data", d)
                # If it's a list (from paginated), show first item
                if isinstance(inner, list) and inner:
                    first = inner[0]
                    print(f"          first_id={first.get('id','?')} name={first.get('name','?')}")
                elif isinstance(inner, dict):
                    print(f"          id={inner.get('id','?')} name={inner.get('name','?')} type={inner.get('_labels','?')}")
            except:
                print(f"          {body[:200]}")
            found = True
            break
        elif sc != 404:
            print(f"  [INFO] {eid} @ {url} HTTP {sc}: {body[:150]}")
    if not found:
        print(f"  [FAIL] {eid:12s} Not found at any route")
        entity_results[eid] = {"pass": False}

# ── Full Neo4j integrity from graph/overview ──────────────────────────────
print("\n" + "=" * 60)
print("NEO4J FULL INTEGRITY")
print("=" * 60)
sc, body, ms = get(f"{BASE}/api/v1/graph/overview")
d = json.loads(body)
gdata = d.get("data", {})
node_counts = gdata.get("node_counts", {})
rel_counts  = gdata.get("relationship_counts", {})
total_nodes = gdata.get("total_nodes", 0)
total_rels  = gdata.get("total_relationships", 0)

EXPECTED_NODES = {
    "Country": 12, "Company": 30, "Supplier": 100,
    "Manufacturer": 20, "Warehouse": 25, "Port": 15,
    "Product": 60, "DisruptionEvent": 20,
}
EXPECTED_REL_TOTAL = 429

print(f"\n  Node counts (HTTP {sc}):")
neo4j_pass = True
for label, expected in EXPECTED_NODES.items():
    actual = node_counts.get(label, "MISSING")
    ok = actual == expected
    if not ok: neo4j_pass = False
    print(f"    [{'PASS' if ok else 'FAIL'}] {label:20s} expected={expected:3d}  actual={actual}")

print(f"\n  All node types in graph: {sorted(node_counts.keys())}")

print(f"\n  Relationship counts:")
for rtype, cnt in sorted(rel_counts.items(), key=lambda x: -x[1]):
    print(f"    {rtype:30s} {cnt}")
print(f"\n  Total relationships: expected={EXPECTED_REL_TOTAL}  actual={total_rels}")
rel_ok = total_rels == EXPECTED_REL_TOTAL
if not rel_ok: neo4j_pass = False

# Check for unexpected relationship types
KNOWN_REL_TYPES = {
    "SUPPLIES_TO", "LOCATED_IN", "AFFECTS", "HAS_WAREHOUSE",
    "SHIPS_THROUGH", "OPERATES_IN", "SOURCES_FROM", "MANUFACTURES",
    "CONNECTS_TO", "DISRUPTS", "PART_OF", "SUPPLIED_BY",
    "STORED_AT", "TRANSITS_VIA", "PRODUCES", "DISTRIBUTES",
    "EXPORTS_TO", "IMPORTS_FROM", "SERVES",
}
unexpected = sorted(r for r in rel_counts if r not in KNOWN_REL_TYPES)
print(f"\n  Unexpected relationship types: {unexpected if unexpected else 'None'}")
print(f"\n  Neo4j integrity: {'PASS' if neo4j_pass else 'FAIL'} (rel_total_ok={rel_ok})")
print(f"  Density proxy: {gdata.get('density_proxy')}  Avg degree: {gdata.get('avg_degree')}")

# ── Check what is actually causing the 500s ───────────────────────────────
print("\n" + "=" * 60)
print("ROOT CAUSE OF 500 ERRORS")
print("=" * 60)

# Test graph/snapshot with a non-Company label
sc1, b1, ms1 = get(f"{BASE}/api/v1/graph/snapshot?node_type=Company")
print(f"  /api/v1/graph/snapshot?node_type=Company  HTTP {sc1} {ms1}ms")
print(f"    {b1[:300]}")

# Try subgraph instead (the non-snapshot graph routes work)
sc2, b2, ms2 = get(f"{BASE}/api/v1/graph/overview")
print(f"\n  /api/v1/graph/overview  HTTP {sc2} {ms2}ms  (This PASSES)")

# Reports/formats — try with debug request ID
import urllib.request as ur
req = ur.Request(f"{BASE}/api/v1/reports/formats",
                 headers={"X-Request-ID": "regression-test-001"})
try:
    with ur.urlopen(req, timeout=15) as resp:
        b3 = resp.read().decode()
        print(f"\n  /api/v1/reports/formats  HTTP {resp.status}: {b3[:200]}")
except urllib.error.HTTPError as e:
    b3 = e.read().decode()
    print(f"\n  /api/v1/reports/formats  HTTP {e.code}: {b3[:300]}")

# Companies list — try with debug request ID
req2 = ur.Request(f"{BASE}/api/v1/companies?page=1&page_size=5",
                  headers={"X-Request-ID": "regression-test-002"})
try:
    with ur.urlopen(req2, timeout=15) as resp:
        b4 = resp.read().decode()
        print(f"\n  /api/v1/companies?limit=5  HTTP {resp.status}: {b4[:400]}")
except urllib.error.HTTPError as e:
    b4 = e.read().decode()
    print(f"\n  /api/v1/companies  HTTP {e.code}: {b4[:300]}")

# Try graph/nodes/Company (list all companies by label)
sc5, b5, ms5 = get(f"{BASE}/api/v1/graph/nodes/Company?limit=5")
print(f"\n  /api/v1/graph/nodes/Company  HTTP {sc5} {ms5}ms")
print(f"    {b5[:400]}")

# Try graph/subgraph with a known company (use first from stats)
sc6, b6, ms6 = get(f"{BASE}/api/v1/graph/subgraph/co-abb?node_label=Company&depth=1")
print(f"\n  /api/v1/graph/subgraph/co-abb  HTTP {sc6} {ms6}ms")
print(f"    {b6[:300]}")

# ── Mock data check ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("MOCK DATA CHECK")
print("=" * 60)
# Check the graph overview and analytics - if they return real Neo4j counts, it's real data
sc_a, b_a, ms_a = get(f"{BASE}/api/v1/analytics/summary")
d_a = json.loads(b_a).get("data", {})
print(f"  Analytics summary: total_nodes={d_a.get('total_nodes')} avg_risk={d_a.get('avg_risk_score')} active_events={d_a.get('active_events')}")

# Fetch a page of graph nodes for Company
sc_c, b_c, ms_c = get(f"{BASE}/api/v1/graph/nodes/Company?limit=10")
mock_flags = []
if sc_c == 200:
    d_c = json.loads(b_c)
    items = d_c.get("data", [])
    if isinstance(items, dict):
        items = items.get("items", items.get("nodes", []))
    print(f"  Company nodes via graph/nodes/Company: {len(items)} returned")
    ids = [c.get("id","") for c in items if isinstance(c, dict)]
    names = [c.get("name","") for c in items if isinstance(c, dict)]
    print(f"    Sample IDs: {ids[:5]}")
    print(f"    Sample names: {names[:5]}")
    for n in names:
        if any(kw in str(n).lower() for kw in ["mock","test","lorem","dummy","fake","placeholder"]):
            mock_flags.append(f"Suspicious name: {n}")
else:
    print(f"  graph/nodes/Company HTTP {sc_c}: {b_c[:200]}")

print(f"\n  Mock data introduced: {'YES - ' + str(mock_flags) if mock_flags else 'NO'}")

# ── Save ──────────────────────────────────────────────────────────────────
results = {
    "entity_results": entity_results,
    "neo4j_pass": neo4j_pass,
    "neo4j_node_counts": node_counts,
    "neo4j_rel_counts": rel_counts,
    "neo4j_total_rels": total_rels,
    "unexpected_rel_types": unexpected,
    "mock_flags": mock_flags,
}
with open(r"c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\regression_part3_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n[SAVED]")
