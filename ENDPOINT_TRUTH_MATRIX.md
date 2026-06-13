# ENDPOINT TRUTH MATRIX

Generated: Runtime probe — no trust in source code

**Results: 36 PASS | 15 PARTIAL | 4 FAIL | 55 TOTAL**

**Pass Rate: 36/55 = 65%**

| Endpoint | HTTP | Data | Rows | Verdict | Error |
|----------|------|------|------|---------|-------|
| `GET /api/v2/executive/kpis` | 200 | Y | 6 | PASS |  |
| `GET /api/v2/executive/alerts` | 200 | Y | 8 | PASS |  |
| `GET /api/v2/executive/summary` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/executive/forecasts/revenue` | 200 | Y | 6 | PASS |  |
| `GET /api/v2/executive/forecasts/cost` | 200 | Y | 6 | PASS |  |
| `GET /api/v2/executive/risks` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/executive/decisions` | 200 | Y | 0 | PASS |  |
| `POST /api/v2/executive/briefing` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/analytics/health` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/analytics/metrics` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/analytics/dimensions` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/analytics/templates` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/analytics/reports/saved` | 200 | Y | 0 | PASS |  |
| `POST /api/v2/analytics/query` | 200 | Y | 13 | PASS |  |
| `GET /api/v2/intelligence/recommendations` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/intelligence/anomalies` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/intelligence/opportunities` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/intelligence/insights` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/intelligence/briefings` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/intelligence/root-causes` | 200 | Y | 0 | PASS |  |
| `GET /api/v1/kpis/executive-summary` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/kpis/revenue` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/kpis/occupancy` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/kpis/claims` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/kpis/profitability` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/insights/comprehensive` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/insights/trends` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/insights/anomalies` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/insights/opportunities` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/forecasts/historical/revenue` | 200 | Y | 24 | PASS |  |
| `GET /api/v1/alerts/list` | 0 | N | 0 | CONN_ERROR | 'list' object has no attribute 'get' |
| `GET /api/v1/alerts/stats/summary` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v2/ai-cfo/profiles` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/ai-cfo/briefings` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/ai-cfo/alerts` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/ai-cfo/workspaces` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/strategic/risks` | 405 | N | 0 | HTTP_405 | {"detail":"Method Not Allowed"} |
| `GET /api/v2/strategic/scenarios` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/strategic/driver-trees` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/copilot/capabilities` | 200 | Y | 15 | PASS |  |
| `GET /api/v2/memory/executive-summary/test-user` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v1/auth/users` | 401 | N | 0 | HTTP_401 | {"detail":"Not authenticated"} |
| `GET /api/v1/auth/me` | 401 | N | 0 | HTTP_401 | {"detail":"Not authenticated"} |
| `GET /api/v2/visualization/chart-types` | 200 | Y | 19 | PASS |  |
| `GET /api/v2/visualization/color-schemes` | 200 | Y | 5 | PASS |  |
| `GET /api/v2/semantic/dimensions` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v2/semantic/fact-tables` | 200 | N | 0 | NO_DATA |  |
| `GET /api/v2/workspace/briefings` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/quality/rules` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/quality/scores` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/admin/audit-log` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/query/saved` | 200 | Y | 0 | PASS |  |
| `GET /api/v2/query/templates` | 200 | Y | 0 | PASS |  |
| `GET /health` | 200 | N | 0 | NO_DATA |  |
| `GET /health/detailed` | 200 | N | 0 | NO_DATA |  |

## FAILURES

