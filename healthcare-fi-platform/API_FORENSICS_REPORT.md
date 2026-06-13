# API FORENSICS REPORT

**ERP-1 Phase 4 — API Forensics**
**Date:** 2026-06-12
**Routes Audited:** 127+ across 11 files

---

## Executive Summary

| Category | Routes | % |
|----------|--------|---|
| **REAL DB-backed** | 44 | 35% |
| **MOCK/STUB** | 60 | 47% |
| **STATIC reference data** | 6 | 5% |
| **UNMOUNTED (never registered)** | ~15 | 12% |
| **Total** | ~125 | 100% |

---

## V1 API — Production Quality (33 routes)

All V1 routes are REAL, DB-backed, with proper error handling.

| File | Routes | Status | Data |
|------|--------|--------|------|
| auth.py | 4 | ✅ REAL | PostgreSQL via raw SQL |
| kpi.py | 6 | ✅ REAL | KPIEngine → DB |
| insights.py | 5 | ✅ REAL | InsightsEngine → DB |
| forecasts.py | 4 | ✅ REAL | ForecastingEngine → DB |
| scenarios.py | 8 | ✅ REAL | ScenarioSimulator → DB |
| alerts.py | 6 | ✅ REAL | SQLAlchemy ORM |

---

## V2 API — Mixed (92+ routes)

### REAL DB-backed (44 routes)

| File | Routes | What Works |
|------|--------|------------|
| analytics.py | 10 | Metrics CRUD, Dimensions CRUD |
| collaboration.py | 7 | Comments CRUD, Threads CRUD |
| ai_cfo.py | 15 | Profiles, Questions, Briefings, Workspaces, Alerts |
| dashboards.py | 10 | Full dashboard CRUD + widgets |
| exports.py | 9 | Export jobs, scheduling, subscriptions |
| strategic_planning.py | 13 | Scenarios, driver trees, Monte Carlo, what-if |
| vector_memory.py | 10 | Memory records, search, cluster, decay |
| institutional_knowledge.py | 12 | Knowledge nodes, edges, pathways |
| forecasting.py | 11 | Models, train, forecast, evaluate, drift |
| advanced_currency.py | 4 | FX rates, conversion, consolidation |
| financial.py | 2 | FX rate lookup |
| nl_analytics.py | 2 | Query history |
| performance.py | 3 | Materialized views |
| workspace.py | 7 | Layout, briefings |
| visualization.py | 4 | Chart specs |
| governance.py | 4 | Dashboard versions |
| executive_center.py | 3 | Decisions |
| copilot.py | 4 | Conversations |

### MOCK/STUB (60 routes)

| File | Routes | What's Fake |
|------|--------|-------------|
| **api.py** | **35** | ALL metrics, quality, imports, lineage endpoints return hardcoded `[]` |
| **query_engine.py** | **7** | ALL query execution, SQL generation, saved queries return stubs |
| **embedded.py** | **7** | ALL embed CRUD, tokens, audit return hardcoded data |
| collaboration.py | 8 | Assignments (4 routes) + Watchlists (4 routes) — no persistence |
| analytics.py | 3 | Query execution, saved reports, templates |
| performance.py | 10 | Cache operations (in-memory), background tasks, query analysis |
| governance.py | 4 | Certifications, approvals, usage — static/echo |
| workspace.py | 2 | Notification config |
| visualization.py | 3 | Chart types, color schemes, config — static |
| executive_center.py | 9 | KPIs, alerts, forecasts, risks, briefing — domain service (in-memory) |
| nl_analytics.py | 2 | Intents, visualization types — static enum |
| financial.py | 2 | Currency list — static dict |
| advanced_currency.py | 1 | Currency list — static dict |

### UNMOUNTED (never registered in router)

| File | Routes | Impact |
|------|--------|--------|
| **intelligence.py** | **~15** | **ENTIRE intelligence UI is dead — all 6 sub-components get 404** |

---

## Critical API Issues

### P0 — Intelligence Router Never Mounted

`intelligence.py` defines 15+ routes but is **NOT imported** in `v2/endpoints/__init__.py`. Every frontend call to `/api/v2/intelligence/*` returns 404. The entire intelligence feature (insights, anomalies, opportunities, recommendations, briefings, graph) is inaccessible.

### P0 — 38 Routes in api.py Are All Mock

`v2/endpoints/api.py` (828 LOC) defines metrics, quality, imports, lineage, and health endpoints — all returning hardcoded empty arrays or zero values. These are scaffolding, not production code. Frontend pages that call these endpoints get fake empty data.

### P1 — Frontend-Backend Contract Mismatches

| Page | Frontend Sends | Backend Expects | Result |
|------|---------------|-----------------|--------|
| `/collaboration` | JSON body | Query params | 422 |
| `/performance` | No tenant_id | tenant_id required | 422 |
| `/memory` | `{embedding}` | `{query_embedding}` | 422 |
| `/memory/addRecord` | No embedding field | embedding required | 422 |
| `/dashboards` | `/templates/prebuilt` | `/prebuilt/templates` | 404 |
| `/exports` | `{name, report_type}` | `{query_id, query_plan}` | 422 |
| `/copilot` | `{query}` | `{user_query}` | 400 |
| `/embedded` | JSON body | Query params | 422 |
| `/metric-studio` | `{formula}` | `{formula_id}` | 422 |

### P1 — Raw fetch() Without Auth

8 pages use raw `fetch()` instead of the axios API client, meaning no Authorization header is sent:
- `/deployments`
- `/semantic`
- `/metric-studio`
- `/currency`
- `/formulas`
- `/copilot`
- `/nl-query`
- `/auth`
