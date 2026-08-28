"""
Fresh-server verification — confirms whether 500s were environment (stale
process) or real code bugs. Tests every previously-failing endpoint plus
all entities and confirms passing ones still pass.
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

results = {}

tests = [
    # Previously failing
    ("companies_list",          f"{BASE}/api/v1/companies"),
    ("graph_snapshot",          f"{BASE}/api/v1/graph/snapshot"),
    ("graph_nodes_company",     f"{BASE}/api/v1/graph/nodes/Company"),
    ("graph_subgraph_co_abb",   f"{BASE}/api/v1/graph/subgraph/co-abb?node_label=Company&depth=1"),
    ("reports_formats",         f"{BASE}/api/v1/reports/formats"),
    # Entity checks
    ("entity_co_abb",           f"{BASE}/api/v1/companies/co-abb"),
    ("entity_co_abb_risk",      f"{BASE}/api/v1/companies/co-abb/risk-summary"),
    ("entity_sup_048_graph",    f"{BASE}/api/v1/graph/nodes/Supplier/sup-048"),
    ("entity_evt_020",          f"{BASE}/api/v1/graph/nodes/DisruptionEvent/evt-020"),
    # Previously passing - regression guard
    ("health",                  f"{BASE}/health"),
    ("graph_overview",          f"{BASE}/api/v1/graph/overview"),
    ("analytics_summary",       f"{BASE}/api/v1/analytics/summary"),
    ("companies_by_country",    f"{BASE}/api/v1/companies/stats/by-country"),
    ("companies_by_risk",       f"{BASE}/api/v1/companies/stats/by-risk"),
    ("admin_dashboard",         f"{BASE}/api/v1/admin/dashboard"),
    ("collaboration_roles",     f"{BASE}/api/v1/collaboration/roles"),
    ("copilot_suggestions",     f"{BASE}/api/v1/copilot/suggestions"),
    ("forecast_models",         f"{BASE}/api/v1/forecast/models"),
    ("simulation_scenario",     f"{BASE}/api/v1/simulation/scenario"),
    ("explainability_node",     f"{BASE}/api/v1/explanations/node/co-abb"),
    # Intentional stubs (expect 501)
    ("predictions_history",     f"{BASE}/api/v1/predictions/history"),
    ("events_list",             f"{BASE}/api/v1/events"),
    ("export_csv",              f"{BASE}/api/v1/export/csv"),
]

print(f"{'Test':<30} {'HTTP':>4}  {'ms':>6}  Result  Snippet")
print("-" * 90)
for name, url in tests:
    sc, body, ms = get(url)
    ok = sc in (200, 201, 204)
    stub = sc == 501
    flag = "PASS " if ok else ("STUB " if stub else "FAIL ")
    snippet = body.replace("\n","")[:80]
    print(f"{name:<30} {sc:>4}  {ms:>6}ms  {flag}  {snippet}")
    results[name] = {"pass": ok, "stub": stub, "status": sc, "ms": ms}

print("\n--- ENTITY DETAIL ---")
for eid, url in [
    ("co-abb",  f"{BASE}/api/v1/companies/co-abb"),
    ("sup-048", f"{BASE}/api/v1/graph/nodes/Supplier/sup-048"),
    ("evt-020", f"{BASE}/api/v1/graph/nodes/DisruptionEvent/evt-020"),
]:
    sc, body, ms = get(url)
    if sc == 200:
        try:
            d = json.loads(body).get("data", {})
            if isinstance(d, list): d = d[0] if d else {}
            print(f"  {eid}: id={d.get('id','?')} name={d.get('name','?')} labels={d.get('_labels','?')}")
        except:
            print(f"  {eid}: HTTP {sc} {body[:120]}")
    else:
        print(f"  {eid}: HTTP {sc} {body[:120]}")

with open(r"c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\fresh_server_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\n[SAVED] fresh_server_results.json")
