"""
Regression Part 2:
- Entity checks with correct routes
- Neo4j full integrity (all 9 node types, all relationship types)
- Graph explorer additional routes
- Mock data check
- Backend log inspection
"""
import json, time, sys
import urllib.request, urllib.error

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

# ── 1. Neo4j full integrity via graph/overview ─────────────────────────────
print("=" * 60)
print("NEO4J DATA INTEGRITY CHECK")
print("=" * 60)

sc, body, ms = get(f"{BASE}/api/v1/graph/overview")
data = json.loads(body)
gdata = data.get("data", {})
node_counts = gdata.get("node_counts", {})
rel_counts = gdata.get("relationship_counts", {})

EXPECTED_NODES = {
    "Country": 12,
    "Company": 30,
    "Supplier": 100,
    "Manufacturer": 20,
    "Warehouse": 25,
    "Port": 15,
    "Product": 60,
    "DisruptionEvent": 20,
}

print("\nNode counts:")
neo4j_pass = True
for label, expected in EXPECTED_NODES.items():
    actual = node_counts.get(label, "MISSING")
    ok = actual == expected
    if not ok: neo4j_pass = False
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:20s} expected={expected}  actual={actual}")

total_expected_rels = 429
total_actual_rels = sum(rel_counts.values())
rel_ok = total_actual_rels == total_expected_rels
if not rel_ok: neo4j_pass = False
print(f"\nRelationship total:")
print(f"  [{'PASS' if rel_ok else 'FAIL'}] Expected={total_expected_rels}  Actual={total_actual_rels}")
print(f"\nRelationship breakdown:")
for rtype, cnt in sorted(rel_counts.items()):
    print(f"  {rtype:30s} {cnt}")

# Check for unexpected relationship types
EXPECTED_RELS = {
    "SUPPLIES_TO", "LOCATED_IN", "AFFECTS", "HAS_WAREHOUSE",
    "SHIPS_THROUGH", "OPERATES_IN", "SOURCES_FROM",
    "MANUFACTURES", "CONNECTS_TO", "DISRUPTS", "PART_OF",
    "SUPPLIED_BY", "STORED_AT", "TRANSITS_VIA",
}
unexpected = [r for r in rel_counts if r not in EXPECTED_RELS]
print(f"\nUnexpected relationship types: {unexpected if unexpected else 'None'}")

# ── 2. Entity checks with correct routes ──────────────────────────────────
print("\n" + "=" * 60)
print("REAL ENTITY CHECKS")
print("=" * 60)

entity_tests = [
    ("co-abb",  [
        f"{BASE}/api/v1/companies/co-abb",
        f"{BASE}/api/v1/companies/co-abb/risk-summary",
    ]),
    ("sup-048", [
        f"{BASE}/api/v1/companies/sup-048",
        f"{BASE}/api/v1/suppliers/sup-048",
        f"{BASE}/api/v1/graph/node/sup-048",
    ]),
    ("evt-020", [
        f"{BASE}/api/v1/events/evt-020",
        f"{BASE}/api/v1/disruption-events/evt-020",
        f"{BASE}/api/v1/graph/node/evt-020",
    ]),
]

entity_results = {}
for eid, urls in entity_tests:
    found = False
    for url in urls:
        sc, resp_body, ms = get(url)
        if sc == 200:
            entity_results[eid] = {"pass": True, "url": url, "ms": ms, "snippet": resp_body[:400]}
            print(f"  [PASS] {eid:12s} HTTP {sc} {ms}ms  {url}")
            try:
                node_data = json.loads(resp_body)
                node_inner = node_data.get("data", node_data)
                print(f"         id={node_inner.get('id','?')} name={node_inner.get('name','?')} type={node_inner.get('labels', node_inner.get('type','?'))}")
            except:
                print(f"         {resp_body[:200]}")
            found = True
            break
        elif sc != 404:
            print(f"  [INFO] {eid} @ {url} -> HTTP {sc}: {resp_body[:100]}")
    if not found:
        entity_results[eid] = {"pass": False, "tried": urls}
        print(f"  [FAIL] {eid:12s} Not found on correct routes: {urls}")

# Also check the company list to confirm co-abb exists in data
print(f"\n  Checking company list for 'abb'...")
sc, body, ms = get(f"{BASE}/api/v1/companies?search=abb&limit=5")
if sc == 200:
    print(f"  [PASS] companies?search=abb HTTP {sc} {ms}ms")
    print(f"         {body[:400]}")
else:
    sc2, body2, ms2 = get(f"{BASE}/api/v1/companies?limit=10")
    print(f"  [INFO] companies list HTTP {sc2} {ms2}ms: {body2[:500]}")

# ── 3. Backend runtime error check ────────────────────────────────────────
print("\n" + "=" * 60)
print("BACKEND RUNTIME ERROR CHECK")
print("=" * 60)
# Test all 500-returning endpoints individually with extra routes
error_routes = [
    f"{BASE}/api/v1/graph/snapshot",
    f"{BASE}/api/v1/reports/formats",
    f"{BASE}/api/v1/companies",
]
for url in error_routes:
    sc, body, ms = get(url)
    print(f"  HTTP {sc} {ms}ms  {url}")
    print(f"         {body[:300]}")

# Try alternate graph routes
graph_alts = [
    f"{BASE}/api/v1/graph/nodes?limit=5",
    f"{BASE}/api/v1/graph/edges?limit=5",
    f"{BASE}/api/v1/graph/nodes",
    f"{BASE}/api/v1/graph/search?q=ABB",
    f"{BASE}/api/v1/graph/overview",
]
print("\n  Testing alternate graph routes:")
for url in graph_alts:
    sc, body, ms = get(url)
    flag = "PASS" if sc == 200 else "FAIL"
    print(f"  [{flag}] HTTP {sc} {ms}ms  {url}")
    if sc == 200:
        print(f"          {body[:200]}")

# ── 4. Mock data check ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("MOCK DATA CHECK")
print("=" * 60)
sc, body, ms = get(f"{BASE}/api/v1/companies?limit=30")
mock_flags = []
if sc == 200:
    try:
        d = json.loads(body)
        companies = d.get("data", [])
        if isinstance(companies, list):
            ids   = [c.get("id","") for c in companies]
            names = [c.get("name","") for c in companies]
            print(f"  Companies returned: {len(companies)}")
            print(f"  Sample IDs: {ids[:10]}")
            print(f"  Sample names: {names[:5]}")
            for n in names:
                if any(kw in str(n).lower() for kw in ["mock","test","lorem","dummy","fake","placeholder"]):
                    mock_flags.append(f"Suspicious name: {n}")
            if mock_flags:
                print(f"  [WARN] Mock indicators: {mock_flags}")
            else:
                print(f"  [PASS] No mock/test names detected")
        else:
            print(f"  [INFO] Unexpected shape: {body[:300]}")
    except Exception as ex:
        print(f"  [WARN] Parse error: {ex}: {body[:200]}")
else:
    print(f"  [FAIL] /api/v1/companies returned HTTP {sc}: {body[:200]}")

# Check analytics for real data
sc2, body2, ms2 = get(f"{BASE}/api/v1/analytics/summary")
if sc2 == 200:
    d2 = json.loads(body2)
    sumdata = d2.get("data", {})
    print(f"\n  Analytics summary: total_nodes={sumdata.get('total_nodes')} avg_risk={sumdata.get('avg_risk_score')} active_events={sumdata.get('active_events')}")
    if sumdata.get("total_nodes", 0) == 0:
        mock_flags.append("total_nodes=0 in analytics summary")

print(f"\n  Mock data introduced: {'YES - ' + str(mock_flags) if mock_flags else 'NO'}")

# ── 5. Frontend build check  (tsc) ───────────────────────────────────────
print("\n" + "=" * 60)
print("CURRENT TYPESCRIPT STATUS (vs baseline)")
print("=" * 60)
import subprocess, os
fe_dir = r"c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\atmograph-ai\frontend"
tsc = os.path.join(fe_dir, "node_modules", ".bin", "tsc.cmd")
if os.path.exists(tsc):
    result = subprocess.run([tsc, "--noEmit", "--project", os.path.join(fe_dir, "tsconfig.json")],
                            capture_output=True, text=True, cwd=fe_dir, timeout=120)
    tsc_out = result.stdout + result.stderr
    lines = [l for l in tsc_out.splitlines() if "error TS" in l]
    print(f"  TypeScript errors found: {len(lines)}")
    for l in lines:
        print(f"    {l}")
    with open(r"c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\tsc_current.txt", "w") as f:
        f.write(tsc_out)
    print(f"  [SAVED] tsc output -> tsc_current.txt")
else:
    print(f"  [SKIP] tsc.cmd not found at {tsc}")
    # Try npx
    result = subprocess.run(["npx", "--yes", "tsc", "--noEmit"],
                            capture_output=True, text=True, cwd=fe_dir, timeout=120)
    tsc_out = result.stdout + result.stderr
    lines = [l for l in tsc_out.splitlines() if "error TS" in l]
    print(f"  TypeScript errors (via npx): {len(lines)}")
    for l in lines[:30]:
        print(f"    {l}")

# ── Save all results ──────────────────────────────────────────────────────
final = {
    "neo4j_node_counts": node_counts,
    "neo4j_rel_counts": rel_counts,
    "neo4j_total_rels": total_actual_rels,
    "neo4j_pass": neo4j_pass,
    "unexpected_rel_types": unexpected,
    "entity_results": entity_results,
    "mock_flags": mock_flags,
}
with open(r"c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\regression_part2_results.json", "w") as f:
    json.dump(final, f, indent=2)
print(f"\n[SAVED] Part 2 results written.")
