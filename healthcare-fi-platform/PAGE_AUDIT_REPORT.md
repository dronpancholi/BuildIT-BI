# PAGE AUDIT REPORT

**ERP-1 Phase 2 — Page-by-Page Functional Audit**
**Date:** 2026-06-12
**Pages Audited:** 38

---

## Summary

| Status | Count | Pages |
|--------|-------|-------|
| **WORKING** | 20 | dashboard, insights, forecasting, strategic, alerts, executive-center, ai-cfo, causal, knowledge-system, knowledge-graph, workspace, multi-currency, login, register, visualization, deployments, semantic, learning, auth, root |
| **PARTIAL** | 13 | forecasts, scenarios, analytics, analytics/query, dashboards, exports, collaboration, performance, currency, formulas, metric-studio, embedded, memory, governance |
| **DISCONNECTED** | 3 | intelligence, decisions, nl-query |
| **FAKE** | 2 | revenue, settings |

---

## Detailed Results

### WORKING (20 pages)

| # | Route | LOC | Data | Notes |
|---|-------|-----|------|-------|
| 1 | `/` | 5 | N/A | Redirect to /dashboard |
| 2 | `/dashboard` | 279 | REAL | Promise.allSettled, empty KPI fallback |
| 3 | `/login` | 113 | REAL | Proper auth flow |
| 4 | `/register` | 246 | REAL | Password validation, auto-login |
| 5 | `/insights` | 345 | REAL | Tab-based, AI CFO Chat included |
| 6 | `/forecasting` | 794 | REAL | Full CRUD, promote/demote, drift detection |
| 7 | `/strategic` | 974 | REAL | Monte Carlo, what-if, risk assessment |
| 8 | `/alerts` | 259 | REAL | Filter, mark-read, resolve |
| 9 | `/executive-center` | 957 | REAL | KPIs, alerts, decisions, forecasts, briefing |
| 10 | `/ai-cfo` | 684 | REAL | Questions, briefings, workspaces, alerts |
| 11 | `/causal` | 867 | REAL | Graph building, contribution, counterfactual |
| 12 | `/knowledge-system` | 1164 | REAL | Full CRUD + analysis |
| 13 | `/knowledge-graph` | 11 | REAL | Delegates to KnowledgeGraphExplorer |
| 14 | `/workspace` | 770 | REAL | Layout, briefings, notifications |
| 15 | `/multi-currency` | 738 | REAL | Config, rates, convert, consolidate |
| 16 | `/visualization` | 514 | REAL | Chart types, specs, render |
| 17 | `/deployments` | 383 | REAL | Environments, paths, promote, rollback |
| 18 | `/semantic` | 325 | REAL | Dimensions, facts, relationships |
| 19 | `/learning` | 11 | REAL | Delegates to LearningDashboard |
| 20 | `/auth` | 249 | REAL | Audit log, role display |

### PARTIAL (13 pages)

| # | Route | LOC | Data | Issues |
|---|-------|-----|------|--------|
| 1 | `/forecasts` | 287 | REAL+MOCK | Hardcoded decomposition (trend/seasonality/noise), placeholder charts |
| 2 | `/scenarios` | 446 | REAL | `alert()` for save, no error UI |
| 3 | `/analytics` | 760 | REAL | Frontend expects `items` key, backend uses `metrics`/`dimensions` |
| 4 | `/analytics/query` | 791 | REAL | Calls `execute({type:'list_metrics'})` but execute expects QueryPlan — will 422 |
| 5 | `/dashboards` | 609 | REAL | URL mismatch: `/dashboards/templates/prebuilt` vs backend `/dashboards/prebuilt/templates` — 404 |
| 6 | `/exports` | 853 | REAL | Frontend sends `{name, format, report_type}`, backend expects `{query_id, query_plan, format}` — 422 |
| 7 | `/collaboration` | 989 | REAL | Backend uses Query params, frontend sends JSON body — 422 on all creates |
| 8 | `/performance` | 781 | REAL | All endpoints require `tenant_id` query param, client never sends it — 422 |
| 9 | `/currency` | 315 | MOCK | Raw fetch, hardcoded currency list fallback |
| 10 | `/formulas` | 278 | MOCK | Raw fetch, hardcoded formula templates |
| 11 | `/metric-studio` | 194 | REAL | Frontend sends `formula`, backend expects `formula_id` — 422 on create |
| 12 | `/embedded` | 509 | REAL | Create: frontend JSON body vs backend Query params — 422 |
| 13 | `/memory` | 610 | REAL | `addRecord` requires `embedding` field (frontend never sends), `search` field name mismatches — 422 |
| 14 | `/governance` | 623 | REAL | Approvals tab calls `listUsage()` instead of approvals — always empty |

### DISCONNECTED (3 pages)

| # | Route | LOC | Data | Issues |
|---|-------|-----|------|--------|
| 1 | `/intelligence` | 76 | REAL* | `GET /api/v2/intelligence/feed` endpoint MISSING from backend — IntelligenceFeed gets 404 |
| 2 | `/decisions` | 37 | REAL* | No DashboardLayout wrapper, fully delegated to child components |
| 3 | `/nl-query` | 268 | MOCK | Uses raw fetch without auth headers, hardcoded query examples |

### FAKE (2 pages)

| # | Route | LOC | Data | Issues |
|---|-------|-----|------|--------|
| 1 | `/revenue` | 273 | **MOCK** | Department revenue, payer mix, and insights are ALL hardcoded inline arrays |
| 2 | `/settings` | 209 | **EMPTY** | All forms are decorative — Save buttons have no onClick handlers, no API calls, no persistence |

---

## Cross-Cutting Issues

### 1. Frontend-Backend Contract Mismatches (P0)

| Page | Issue | Impact |
|------|-------|--------|
| `/analytics` | Expects `items` key, backend returns `metrics`/`dimensions` | Data doesn't render |
| `/analytics/query` | Calls `execute({type:'list_metrics'})`, backend expects QueryPlan | 422 error |
| `/dashboards` | URL `/templates/prebuilt` vs `/prebuilt/templates` | 404 error |
| `/exports` | Sends `{name, report_type}`, backend expects `{query_id, query_plan}` | 422 error |
| `/collaboration` | Sends JSON body, backend uses Query params | 422 on all creates |
| `/performance` | Missing `tenant_id` query param on all calls | 422 error |
| `/memory` | Missing `embedding` field, wrong field names | 422 error |
| `/embedded` | JSON body vs Query params on create | 422 error |
| `/metric-studio` | Sends `formula`, backend expects `formula_id` | 422 on create |

### 2. Raw fetch() Bypassing API Client (P1)

| Page | Issue |
|------|-------|
| `/deployments` | Uses raw `fetch()` instead of `deploymentAPI` |
| `/semantic` | Uses raw `fetch()` instead of `semanticLayerAPI` |
| `/metric-studio` | Uses raw `fetch()` instead of `metricStudioAPI` |
| `/currency` | Uses raw `fetch()` instead of `advancedCurrencyAPI` |
| `/formulas` | Uses raw `fetch()` instead of `bflAPI` |
| `/copilot` | Uses raw `fetch()` instead of `copilotAPI` |
| `/nl-query` | Uses raw `fetch()` instead of `nlAnalyticsAPI` |
| `/auth` | Uses raw `fetch()` instead of `enterpriseGovernanceAPI` |

### 3. Missing DashboardLayout (P1)

| Page | Issue |
|------|-------|
| `/intelligence` | No DashboardLayout wrapper |
| `/decisions` | No DashboardLayout wrapper |
| `/learning` | No DashboardLayout wrapper |
| `/knowledge-graph` | No DashboardLayout wrapper (delegates to component) |

### 4. Missing Error State UI (P2)

Pages that only `console.error` on failure, showing stale loading spinner:
- `/revenue`
- `/insights`
- `/forecasts`
- `/scenarios`
- `/alerts`
- `/formulas`
- `/currency`
- `/metric-studio`

### 5. Hardcoded Mock Data (P0)

| Page | What's Mock |
|------|-------------|
| `/revenue` | Department revenue array, payer mix array, insight text |
| `/settings` | All forms (no backend) |
| `/currency` | Currency list fallback |
| `/formulas` | Formula template list |
| `/copilot` | Default suggestions |

### 6. `alert()` for User Feedback (P2)

| Page | Usage |
|------|-------|
| `/forecasting` | Model comparison result |
| `/scenarios` | Save confirmation |
| `/strategic` | Scenario comparison result |

---

## Score Card

| Area | Score | Notes |
|------|-------|-------|
| Core Pages (dashboard, alerts, insights) | 85 | Solid, minor gaps |
| Analytics Pages | 30 | Contract mismatches, stubs |
| Intelligence Pages | 25 | Missing endpoint, disconnected |
| Decision Pages | 35 | Delegation, missing layout |
| Forecasting Pages | 75 | Real data, minor UX issues |
| Strategic Pages | 80 | Full functionality |
| CFO Pages | 80 | Working well |
| Knowledge Pages | 85 | Working well |
| Collaboration Pages | 40 | API contract broken |
| Performance Pages | 20 | Missing tenant_id |
| Settings Pages | 0 | Completely fake |
