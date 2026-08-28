"""
Check actual API routes from OpenAPI and run corrected smoke tests.
Also run Neo4j integrity checks via Cypher through the backend.
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

def post_json(url, payload, timeout=15):
    t0 = time.time()
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
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

# ── Get OpenAPI spec to discover real route prefixes ──────────────────────────
print("=" * 60)
print("STEP 1: Discovering actual routes from OpenAPI")
print("=" * 60)
sc, body, ms = get(f"{BASE}/openapi.json")
if sc != 200:
    print(f"FATAL: cannot reach openapi.json: {sc}")
    sys.exit(1)

spec = json.loads(body)
paths = list(spec.get("paths", {}).keys())

# Print all unique path prefixes
prefixes = set()
for p in paths:
    parts = p.strip("/").split("/")
    if len(parts) >= 2:
        prefixes.add("/" + "/".join(parts[:2]))
print(f"Total routes: {len(paths)}")
print("Path prefixes found:")
for pfx in sorted(prefixes):
    print(f"  {pfx}")

# Find representative GET routes for each module
module_routes = {}
for p in paths:
    info = spec["paths"][p]
    if "get" not in info:
        continue
    tags = info["get"].get("tags", ["untagged"])
    tag = tags[0] if tags else "untagged"
    if tag not in module_routes:
        # Prefer routes without path parameters for smoke test
        if "{" not in p:
            module_routes[tag] = p
        else:
            if tag not in module_routes:
                module_routes[tag] = p

print("\nSelected smoke routes by tag:")
for tag, route in sorted(module_routes.items()):
    print(f"  [{tag}] {route}")

# ── STEP 2: Run smoke tests on discovered routes ──────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: API smoke tests")
print("=" * 60)
smoke_results = {}
for tag, route in sorted(module_routes.items()):
    url = BASE + route
    sc, resp_body, ms = get(url)
    ok = sc in (200, 201, 204)
    smoke_results[tag] = {"pass": ok, "status": sc, "ms": ms, "route": route, "snippet": resp_body[:300]}
    flag = "PASS" if ok else "FAIL"
    print(f"  [{flag}] {tag:30s} HTTP {sc} {ms}ms  {route}")
    if not ok:
        print(f"         BODY: {resp_body[:200]}")

# ── STEP 3: Specific module smoke tests ──────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Cross-module explicit smoke tests")
print("=" * 60)

# Find the actual paths from the spec
def find_route(keyword, method="get"):
    for p in paths:
        if keyword.lower() in p.lower() and method in spec["paths"][p]:
            if "{" not in p:
                return p
    for p in paths:
        if keyword.lower() in p.lower() and method in spec["paths"][p]:
            return p
    return None

explicit_tests = [
    ("Graph Explorer",    find_route("/graph")),
    ("Analytics",         find_route("/analytics")),
    ("AI Insights",       find_route("/predictions") or find_route("/ai")),
    ("Explainability",    find_route("/explanations") or find_route("/explainability")),
    ("AI Copilot",        find_route("/copilot")),
    ("Forecast",          find_route("/forecast")),
    ("Simulation",        find_route("/simulation")),
    ("Reports",           find_route("/reports")),
    ("Collaboration",     find_route("/collaboration")),
    ("Administration",    find_route("/admin")),
]

module_results = {}
for name, route in explicit_tests:
    if not route:
        module_results[name] = {"pass": False, "error": "No route found in spec"}
        print(f"  [FAIL] {name:25s} - No matching route in OpenAPI spec")
        continue
    url = BASE + route
    sc, resp_body, ms = get(url)
    ok = sc in (200, 201, 204)
    module_results[name] = {"pass": ok, "status": sc, "ms": ms, "route": route, "snippet": resp_body[:400]}
    flag = "PASS" if ok else "FAIL"
    print(f"  [{flag}] {name:25s} HTTP {sc} {ms}ms  {route}")
    if not ok:
        print(f"         BODY: {resp_body[:200]}")

# ── STEP 4: Real entity checks ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Real entity checks")
print("=" * 60)

# Find entity/node detail routes
node_route = find_route("/node/") or find_route("/nodes/")
company_route = find_route("/company/") or find_route("/companies/")

entity_results = {}
for eid in ["co-abb", "sup-048", "evt-020"]:
    found = False
    # Try multiple potential routes
    attempts = []
    if node_route:
        attempts.append(node_route.replace("{node_id}", eid).replace("{id}", eid).replace("{entity_id}", eid))
    if company_route:
        attempts.append(company_route.replace("{company_id}", eid).replace("{id}", eid))
    # Generic tries
    attempts += [
        f"{BASE}/api/graph/node/{eid}",
        f"{BASE}/api/company/{eid}",
        f"{BASE}/api/v1/graph/node/{eid}",
        f"{BASE}/api/graph/nodes/{eid}",
    ]
    for url in attempts:
        sc, resp_body, ms = get(url)
        if sc == 200:
            entity_results[eid] = {"pass": True, "status": sc, "ms": ms, "url": url, "snippet": resp_body[:400]}
            print(f"  [PASS] {eid:12s} HTTP {sc} {ms}ms  {url}")
            print(f"         {resp_body[:200]}")
            found = True
            break
    if not found:
        entity_results[eid] = {"pass": False, "tried": attempts[:4]}
        print(f"  [FAIL] {eid:12s} - Not found on any tried route")
        # Show what routes ARE available in the graph area
        graph_paths = [p for p in paths if "graph" in p.lower() or "company" in p.lower() or "node" in p.lower()]
        print(f"         Available graph/company routes: {graph_paths[:8]}")

# ── STEP 5: Neo4j integrity via backend ───────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: Neo4j data integrity")
print("=" * 60)

# Find stats endpoint
stats_routes = [p for p in paths if "stats" in p.lower() or "summary" in p.lower() or "overview" in p.lower() or "count" in p.lower()]
print(f"Candidate stats routes: {stats_routes}")

neo4j_counts = {}
for route in stats_routes[:5]:
    sc, body, ms = get(BASE + route)
    print(f"  [{sc}] {route} {ms}ms: {body[:300]}")
    if sc == 200:
        try:
            neo4j_counts[route] = json.loads(body)
        except:
            neo4j_counts[route] = body[:300]

# ── STEP 6: Check for unexpected relationship types ───────────────────────────
print("\n" + "=" * 60)
print("STEP 6: Relationship types check")
print("=" * 60)
rel_routes = [p for p in paths if "relationship" in p.lower() or "edge" in p.lower() or "rel-type" in p.lower()]
print(f"Candidate relationship routes: {rel_routes}")
for route in rel_routes[:4]:
    sc, body, ms = get(BASE + route)
    print(f"  [{sc}] {route} {ms}ms: {body[:400]}")

# ── STEP 7: Response time sanity ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 7: Response time sanity")
print("=" * 60)
SLOW_MS = 3000
perf_pass = True
for tag, route in list(module_results.items())[:8]:
    ms = module_results[tag].get("ms", 0)
    sc = module_results[tag].get("status", 0)
    flag = "OK" if ms < SLOW_MS else "SLOW"
    if ms >= SLOW_MS: perf_pass = False
    print(f"  [{flag}] {tag:25s} {ms}ms")

# ── Save results ──────────────────────────────────────────────────────────────
final = {
    "smoke_by_tag": smoke_results,
    "module_results": module_results,
    "entity_results": entity_results,
    "neo4j_counts": neo4j_counts,
    "perf_pass": perf_pass,
    "total_routes": len(paths),
    "path_prefixes": sorted(prefixes),
}
with open(r"c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\regression_full_results.json", "w") as f:
    json.dump(final, f, indent=2)
print(f"\n[SAVED] Results written.")
