"""MASTERFIX ULTRA X — Runtime Discovery Probe"""
import json
import urllib.request
import urllib.error
import sys

BASE = "http://localhost:8000"

def test_endpoint(method, path, body=None):
    url = f"{BASE}{path}"
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        if body:
            req.data = json.dumps(body).encode()
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        has_data = "data" in data
        row_count = len(data.get("data", {}).get("rows", [])) if isinstance(data.get("data"), dict) else len(data.get("data", [])) if isinstance(data.get("data"), list) else 0
        return resp.status, has_data, row_count, ""
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()[:100] if e.fp else ""
        return e.code, False, 0, body_text
    except Exception as e:
        return 0, False, 0, str(e)[:80]

# All endpoints the frontend calls
endpoints = [
    # Executive Center
    ("GET", "/api/v2/executive/kpis", None),
    ("GET", "/api/v2/executive/alerts", None),
    ("GET", "/api/v2/executive/summary", None),
    ("GET", "/api/v2/executive/forecasts/revenue", None),
    ("GET", "/api/v2/executive/forecasts/cost", None),
    ("GET", "/api/v2/executive/risks", None),
    ("GET", "/api/v2/executive/decisions", None),
    ("POST", "/api/v2/executive/briefing", {"period": "30d", "period_type": "monthly"}),
    
    # Analytics
    ("GET", "/api/v2/analytics/health", None),
    ("GET", "/api/v2/analytics/metrics", None),
    ("GET", "/api/v2/analytics/dimensions", None),
    ("GET", "/api/v2/analytics/templates", None),
    ("GET", "/api/v2/analytics/reports/saved", None),
    ("POST", "/api/v2/analytics/query", {"metrics": ["revenue"], "dimensions": ["month"]}),
    
    # Intelligence
    ("GET", "/api/v2/intelligence/recommendations", None),
    ("GET", "/api/v2/intelligence/anomalies", None),
    ("GET", "/api/v2/intelligence/opportunities", None),
    ("GET", "/api/v2/intelligence/insights", None),
    ("GET", "/api/v2/intelligence/briefings", None),
    ("GET", "/api/v2/intelligence/root-causes", None),
    
    # V1 KPIs
    ("GET", "/api/v1/kpis/executive-summary", None),
    ("GET", "/api/v1/kpis/revenue", None),
    ("GET", "/api/v1/kpis/occupancy", None),
    ("GET", "/api/v1/kpis/claims", None),
    ("GET", "/api/v1/kpis/profitability", None),
    
    # V1 Insights
    ("GET", "/api/v1/insights/comprehensive", None),
    ("GET", "/api/v1/insights/trends", None),
    ("GET", "/api/v1/insights/anomalies", None),
    ("GET", "/api/v1/insights/opportunities", None),
    
    # V1 Forecasts
    ("GET", "/api/v1/forecasts/historical/revenue", None),
    
    # V1 Alerts
    ("GET", "/api/v1/alerts/list", None),
    ("GET", "/api/v1/alerts/stats/summary", None),
    
    # AI CFO
    ("GET", "/api/v2/ai-cfo/profiles", None),
    ("GET", "/api/v2/ai-cfo/briefings", None),
    ("GET", "/api/v2/ai-cfo/alerts", None),
    ("GET", "/api/v2/ai-cfo/workspaces", None),
    
    # Strategic
    ("GET", "/api/v2/strategic/risks", None),
    ("GET", "/api/v2/strategic/scenarios", None),
    ("GET", "/api/v2/strategic/driver-trees", None),
    
    # Copilot
    ("GET", "/api/v2/copilot/capabilities", None),
    
    # Memory
    ("GET", "/api/v2/memory/executive-summary/test-user", None),
    
    # Auth
    ("GET", "/api/v1/auth/users", None),
    ("GET", "/api/v1/auth/me", None),
    
    # Visualization
    ("GET", "/api/v2/visualization/chart-types", None),
    ("GET", "/api/v2/visualization/color-schemes", None),
    
    # Semantic
    ("GET", "/api/v2/semantic/dimensions", None),
    ("GET", "/api/v2/semantic/fact-tables", None),
    
    # Workspace
    ("GET", "/api/v2/workspace/briefings", None),
    
    # Quality
    ("GET", "/api/v2/quality/rules", None),
    ("GET", "/api/v2/quality/scores", None),
    
    # Admin
    ("GET", "/api/v2/admin/audit-log", None),
    
    # Query
    ("GET", "/api/v2/query/saved", None),
    ("GET", "/api/v2/query/templates", None),
    
    # Health
    ("GET", "/health", None),
    ("GET", "/health/detailed", None),
]

print(f"Testing {len(endpoints)} endpoints...\n")
print(f"{'ENDPOINT':<55} | {'HTTP':>4} | {'DATA':>4} | {'ROWS':>4} | VERDICT")
print("-" * 100)

pass_count = 0
fail_count = 0
partial_count = 0
results = []

for method, path, body in endpoints:
    code, has_data, row_count, error = test_endpoint(method, path, body)
    
    if code == 200 and has_data:
        verdict = "PASS"
        pass_count += 1
    elif code == 200 and not has_data:
        verdict = "NO_DATA"
        partial_count += 1
    elif code == 404:
        verdict = "404_NOT_FOUND"
        fail_count += 1
    elif code == 422:
        verdict = "422_VALIDATION"
        fail_count += 1
    elif code == 500:
        verdict = "500_SERVER_ERROR"
        fail_count += 1
    elif code == 0:
        verdict = f"CONN_ERROR"
        fail_count += 1
    else:
        verdict = f"HTTP_{code}"
        fail_count += 1
    
    label = f"{method} {path}"
    print(f"  {label:<53} | {code:>4} | {'Y' if has_data else 'N':>4} | {row_count:>4} | {verdict}")
    if error:
        print(f"    ERROR: {error[:80]}")
    results.append((label, code, has_data, row_count, verdict, error))

print(f"\n{'='*100}")
print(f"RESULTS: {pass_count} PASS | {partial_count} PARTIAL | {fail_count} FAIL | {len(endpoints)} TOTAL")
print(f"PASS RATE: {pass_count}/{len(endpoints)} = {pass_count*100//len(endpoints)}%")

# Write results to file
with open("/Users/dronpancholi/Developer/BuildIT BI/ENDPOINT_TRUTH_MATRIX.md", "w") as f:
    f.write("# ENDPOINT TRUTH MATRIX\n\n")
    f.write(f"Generated: Runtime probe — no trust in source code\n\n")
    f.write(f"**Results: {pass_count} PASS | {partial_count} PARTIAL | {fail_count} FAIL | {len(endpoints)} TOTAL**\n\n")
    f.write(f"**Pass Rate: {pass_count}/{len(endpoints)} = {pass_count*100//len(endpoints)}%**\n\n")
    f.write("| Endpoint | HTTP | Data | Rows | Verdict | Error |\n")
    f.write("|----------|------|------|------|---------|-------|\n")
    for label, code, has_data, row_count, verdict, error in results:
        err_short = error[:40].replace("|", "/") if error else ""
        f.write(f"| `{label}` | {code} | {'Y' if has_data else 'N'} | {row_count} | {verdict} | {err_short} |\n")
    
    f.write("\n## FAILURES\n\n")
    for label, code, has_data, row_count, verdict, error in results:
        if "FAIL" in verdict or "404" in verdict or "500" in verdict or "422" in verdict:
            f.write(f"### `{label}`\n")
            f.write(f"- HTTP: {code}\n")
            f.write(f"- Error: {error}\n\n")

print("\nResults written to ENDPOINT_TRUTH_MATRIX.md")
