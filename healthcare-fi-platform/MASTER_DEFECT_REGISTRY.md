# MASTER DEFECT REGISTRY

**ERP-1 Phase 9 — Defect Registry**
**Date:** 2026-06-12
**Total Defects:** 47

---

## P0 — Platform Unusable (8 defects)

### DEFECT-001
**Title:** Intelligence Router Never Mounted
**Severity:** P0
**Category:** Backend
**File:** `backend/app/api/v2/endpoints/__init__.py`
**Component:** Intelligence API
**Root Cause:** `intelligence.py` router exists but is never imported or included in `v2_router`
**Reproduction:** Call `GET /api/v2/intelligence/insights` → 404
**Impact:** Entire intelligence UI (6 sub-components) is dead. All API calls return 404.
**Fix Effort:** S (add 1 import line)
**Dependencies:** None

### DEFECT-002
**Title:** v2/api.py — 38 Routes Are All Mock Stubs
**Severity:** P0
**Category:** Backend
**File:** `backend/app/api/v2/endpoints/api.py` (828 LOC)
**Component:** Metrics, Quality, Imports, Lineage APIs
**Root Cause:** All handlers return hardcoded `APIResponse(data=[])` with no DB access
**Reproduction:** Call any `/api/v2/metrics/*`, `/api/v2/quality/*`, `/api/v2/imports/*`, `/api/v2/lineage/*` endpoint
**Impact:** 38 endpoints return fake empty data. Frontend pages show empty states.
**Fix Effort:** XL (wire 38 endpoints to real repos/services)
**Dependencies:** None

### DEFECT-003
**Title:** Query Engine — All 8 Routes Are Mock
**Severity:** P0
**Category:** Backend
**File:** `backend/app/api/v2/endpoints/query_engine.py` (262 LOC)
**Component:** Query Engine
**Root Cause:** All handlers return hardcoded stubs (empty rows, null SQL, always-valid validation)
**Reproduction:** Call `POST /api/v2/query/execute` → returns `{rows: [], columns: []}`
**Impact:** Analytics Query page cannot execute any queries
**Fix Effort:** L (implement SQL execution engine)
**Dependencies:** DEFECT-002 (shared query infrastructure)

### DEFECT-004
**Title:** Embedded Analytics — All 7 Routes Are Mock
**Severity:** P0
**Category:** Backend
**File:** `backend/app/api/v2/endpoints/embedded.py` (148 LOC)
**Component:** Embedded Analytics
**Root Cause:** All handlers return hardcoded data. Token validation is string prefix check only.
**Reproduction:** Call `POST /api/v2/embedded` → returns hardcoded dict
**Impact:** Embedded analytics feature completely non-functional
**Fix Effort:** L (implement embed CRUD + token generation + validation)
**Dependencies:** None

### DEFECT-005
**Title:** Revenue Page — Hardcoded Mock Data
**Severity:** P0
**Category:** Frontend
**File:** `frontend/src/app/revenue/page.tsx` (273 LOC)
**Component:** Revenue Page
**Root Cause:** "By Department" and "By Payer" tabs use hardcoded inline arrays. Insights are static text.
**Reproduction:** Navigate to `/revenue` → see fake department/payer data
**Impact:** Executive sees fake revenue data presented as real
**Fix Effort:** M (replace hardcoded data with API calls)
**Dependencies:** None

### DEFECT-006
**Title:** Settings Page — Completely Non-Functional
**Severity:** P0
**Category:** Frontend
**File:** `frontend/src/app/settings/page.tsx` (209 LOC)
**Component:** Settings Page
**Root Cause:** All form buttons have NO onClick handlers. No API calls. No persistence.
**Reproduction:** Navigate to `/settings` → click any Save button → nothing happens
**Impact:** User cannot change any settings
**Fix Effort:** L (implement settings API + wire all forms)
**Dependencies:** None (backend settings API needs creation)

### DEFECT-007
**Title:** Quality Domain — No Persistence Layer
**Severity:** P0
**Category:** Backend
**File:** `backend/app/infrastructure/persistence/models.py`
**Component:** Quality Rules, Issues, Scores
**Root Cause:** No ORM models, no repositories. All quality endpoints return hardcoded `[]`.
**Reproduction:** Call `GET /api/v2/quality/rules` → returns `data: []`
**Impact:** Data quality feature completely non-functional
**Fix Effort:** L (create ORM models, repos, wire endpoints)
**Dependencies:** None

### DEFECT-008
**Title:** Metrics Domain — In-Memory Only
**Severity:** P0
**Category:** Backend
**File:** `backend/app/domain/metric_studio/__init__.py`
**Component:** Metric Studio
**Root Cause:** `MetricStudioService` stores in `self.metrics: dict`. Module-level singleton loses data on restart.
**Reproduction:** Create metric via POST → restart backend → GET returns empty
**Impact:** All metric definitions lost on restart
**Fix Effort:** M (wire to SemanticMetricRepository instead of in-memory dict)
**Dependencies:** None

---

## P1 — Major Functionality Broken (12 defects)

### DEFECT-009
**Title:** Collaboration API — Body vs Query Param Mismatch
**Severity:** P1
**Category:** API Contract
**File:** `frontend/src/app/collaboration/page.tsx` + `backend/app/api/v2/endpoints/collaboration.py`
**Component:** Collaboration Create Operations
**Root Cause:** Frontend sends JSON body, backend uses `Query(...)` parameters
**Reproduction:** Try to create a comment → 422 Unprocessable Entity
**Impact:** Cannot create comments, threads, assignments, or watchlists
**Fix Effort:** M (align frontend/backend contract)
**Dependencies:** None

### DEFECT-010
**Title:** Performance API — Missing tenant_id Query Param
**Severity:** P1
**Category:** API Contract
**File:** `frontend/src/app/performance/page.tsx`
**Component:** Performance Page
**Root Cause:** All backend endpoints require `tenant_id` query param. Frontend never sends it.
**Reproduction:** Navigate to `/performance` → all API calls return 422
**Impact:** Performance monitoring completely broken
**Fix Effort:** S (add tenant_id to all performance API calls)
**Dependencies:** None

### DEFECT-011
**Title:** Memory API — Field Name Mismatches
**Severity:** P1
**Category:** API Contract
**File:** `frontend/src/app/memory/page.tsx`
**Component:** Memory Search, Semantic Search, Add Record
**Root Cause:** Frontend sends `{embedding, query}` but backend expects `{query_embedding, query_text}`
**Reproduction:** Try to add memory record → 422 (missing embedding field)
**Impact:** Cannot add, search, or semantically search memory records
**Fix Effort:** S (align field names)
**Dependencies:** None

### DEFECT-012
**Title:** Copilot — Raw fetch Without Auth Headers
**Severity:** P1
**Category:** Frontend
**File:** `frontend/src/app/copilot/page.tsx`
**Component:** Copilot Chat
**Root Cause:** Uses `fetch('/api/v2/copilot/...')` instead of `copilotAPI` — no Bearer token
**Reproduction:** Send message → request fails without auth
**Impact:** Copilot chat broken in authenticated mode
**Fix Effort:** S (use copilotAPI instead of raw fetch)
**Dependencies:** None

### DEFECT-013
**Title:** 8 Pages Bypass API Client (Raw fetch Without Auth)
**Severity:** P1
**Category:** Frontend
**File:** Multiple pages
**Component:** Deployments, Semantic, Metric Studio, Currency, Formulas, Copilot, NL Query, Auth
**Root Cause:** Pages use raw `fetch()` instead of typed axios client — no Authorization header
**Reproduction:** Any authenticated action on these pages
**Impact:** All write operations fail in authenticated mode
**Fix Effort:** M (replace raw fetch with API client calls)
**Dependencies:** None

### DEFECT-014
**Title:** Dashboards — URL Path Mismatch
**Severity:** P1
**Category:** API Contract
**File:** `frontend/src/app/dashboards/page.tsx`
**Component:** Dashboard Prebuilt Templates
**Root Cause:** Frontend calls `/dashboards/templates/prebuilt`, backend route is `/dashboards/prebuilt/templates`
**Reproduction:** Load dashboards page → templates tab shows error
**Impact:** Prebuilt templates never load
**Fix Effort:** S (fix URL path)
**Dependencies:** None

### DEFECT-015
**Title:** Exports — Request Shape Mismatch
**Severity:** P1
**Category:** API Contract
**File:** `frontend/src/app/exports/page.tsx`
**Component:** Export Job Creation
**Root Cause:** Frontend sends `{name, format, report_type}`, backend expects `{query_id, query_plan, format}`
**Reproduction:** Try to create export → 422
**Impact:** Cannot create export jobs
**Fix Effort:** M (align request shapes)
**Dependencies:** None

### DEFECT-016
**Title:** AICFOChat Component — Fake AI Responses
**Severity:** P1
**Category:** Frontend
**File:** `frontend/src/components/ai/ai-cfo-chat.tsx` (218 LOC)
**Component:** AI CFO Chat
**Root Cause:** `generateAIResponse()` returns hardcoded strings. Confidence is random `0.85 + Math.random() * 0.15`.
**Reproduction:** Ask any question → get canned response with fake confidence
**Impact:** AI CFO chat gives fake answers with fake confidence scores
**Fix Effort:** M (wire to real copilotAPI)
**Dependencies:** None

### DEFECT-017
**Title:** Decision Center — Hardcoded UUIDs
**Severity:** P1
**Category:** Frontend
**File:** `frontend/src/components/decision/decision-center.tsx` (359 LOC)
**Component:** Decision Center
**Root Cause:** `owner_id` and `created_by` hardcoded to `"00000000-0000-0000-0000-000000000000"`
**Reproduction:** Create decision → owner is always the zero UUID
**Impact:** All decisions attributed to phantom user
**Fix Effort:** S (get current user from auth context)
**Dependencies:** None

### DEFECT-018
**Title:** RecommendationCenter — Wrong HTTP Method
**Severity:** P1
**Category:** Frontend
**File:** `frontend/src/components/intelligence/recommendation-center.tsx` (576 LOC)
**Component:** Recommendation Center
**Root Cause:** `handleApprove` and `handleReject` call `intelligenceAPI.getRecommendation(id)` (GET) instead of PUT/PATCH
**Reproduction:** Approve a recommendation → state not actually updated
**Impact:** Approve/reject actions do nothing
**Fix Effort:** S (use correct HTTP method)
**Dependencies:** DEFECT-001 (intelligence router must be mounted first)

### DEFECT-019
**Title:** Analytics Query — Wrong API Call Pattern
**Severity:** P1
**Category:** API Contract
**File:** `frontend/src/app/analytics/query/page.tsx`
**Component:** Analytics Query
**Root Cause:** `fetchMetrics/fetchDimensions` call `queryAPI.execute({type:'list_metrics'})` but execute expects QueryPlan
**Reproduction:** Load analytics query page → metrics list fails with 422
**Impact:** Cannot list available metrics/dimensions for query building
**Fix Effort:** M (fix query call pattern)
**Dependencies:** None

### DEFECT-020
**Title:** Embedded — Body vs Query Param Mismatch
**Severity:** P1
**Category:** API Contract
**File:** `frontend/src/app/embedded/page.tsx`
**Component:** Embedded Create
**Root Cause:** Frontend sends JSON body, backend uses Query params. Field "name" vs "title" mismatch.
**Reproduction:** Try to create embed → 422
**Impact:** Cannot create embedded dashboards
**Fix Effort:** S (align contract)
**Dependencies:** DEFECT-004 (embedded must have real implementation first)

### DEFECT-021
**Title:** Metric Studio — Formula Field Name Mismatch
**Severity:** P1
**Category:** API Contract
**File:** `frontend/src/app/metric-studio/page.tsx`
**Component:** Metric Studio Create
**Root Cause:** Frontend sends `{formula}`, backend expects `{formula_id}`
**Reproduction:** Try to create metric → 422
**Impact:** Cannot create metrics via Metric Studio
**Fix Effort:** S (align field name)
**Dependencies:** DEFECT-008 (metric persistence must be fixed first)

---

## P2 — Works Incorrectly (15 defects)

### DEFECT-022
**Title:** Forecasts — Hardcoded Decomposition Values
**Severity:** P2
**Category:** Frontend
**File:** `frontend/src/app/forecasts/page.tsx`
**Component:** Forecast Decomposition
**Root Cause:** Trend/seasonality/noise sections always show "Increasing / +2.3% monthly", "Moderate / Q4 peak pattern", "Low / High signal-to-noise"
**Reproduction:** Generate forecast → decomposition shows static values
**Impact:** Misleading decomposition data
**Fix Effort:** M (use actual decomposition results)
**Dependencies:** None

### DEFECT-023
**Title:** Analytics — Data Shape Mismatch (items vs metrics)
**Severity:** P2
**Category:** API Contract
**File:** `frontend/src/app/analytics/page.tsx`
**Component:** Analytics Page
**Root Cause:** Frontend expects `response.data?.items`, backend returns `{data: {metrics: [...], total: N}}`
**Reproduction:** Load analytics page → metrics list shows empty
**Impact:** Metrics/dimensions don't render despite being in DB
**Fix Effort:** S (fix data access path)
**Dependencies:** None

### DEFECT-024
**Title:** Governance — Approvals Tab Calls Wrong Endpoint
**Severity:** P2
**Category:** Frontend
**File:** `frontend/src/app/governance/page.tsx`
**Component:** Governance Approvals Tab
**Root Cause:** `governanceAPI.listUsage()` returns usage records, not approval workflows
**Reproduction:** Click Approvals tab → always shows "No Pending Approvals"
**Impact:** Approvals feature broken
**Fix Effort:** S (call correct endpoint or implement listApprovals)
**Dependencies:** None

### DEFECT-025
**Title:** 8 Pages Missing Error State UI
**Severity:** P2
**Category:** Frontend
**File:** Multiple pages
**Component:** Revenue, Insights, Forecasts, Scenarios, Alerts, Formulas, Currency, Metric Studio
**Root Cause:** Errors only logged to `console.error()`, no user-facing error state
**Reproduction:** Trigger API error → user sees stale loading spinner
**Impact:** Users don't know when errors occur
**Fix Effort:** M (add error banners to 8 pages)
**Dependencies:** None

### DEFECT-026
**Title:** 4 Pages Missing DashboardLayout
**Severity:** P2
**Category:** Frontend
**File:** intelligence/page.tsx, decisions/page.tsx, learning/page.tsx, knowledge-graph/page.tsx
**Component:** Page Layout
**Root Cause:** These pages don't wrap in `DashboardLayout` component
**Reproduction:** Navigate to these pages → no sidebar, inconsistent chrome
**Impact:** Inconsistent user experience
**Fix Effort:** S (add DashboardLayout wrapper)
**Dependencies:** None

### DEFECT-027
**Title:** DashboardLayout — Hardcoded localhost:8000
**Severity:** P2
**Category:** Frontend
**File:** `frontend/src/components/layout/dashboard-layout.tsx` (line 149)
**Component:** Dashboard Layout
**Root Cause:** API URL hardcoded as `http://localhost:8000`
**Reproduction:** Deploy to non-localhost → API calls fail
**Impact:** Only works in local development
**Fix Effort:** S (use environment variable)
**Dependencies:** None

### DEFECT-028
**Title:** 3 Dead Components — 1,281 Lines of Unused Code
**Severity:** P2
**Category:** Frontend
**File:** quality-dashboard.tsx, metric-explorer.tsx, lineage-graph.tsx
**Component:** Quality Dashboard, Metric Explorer, Lineage Graph
**Root Cause:** These components are defined but never imported by any page
**Reproduction:** Search for imports → none found
**Impact:** Dead code, maintenance burden
**Fix Effort:** S (delete or wire to pages)
**Dependencies:** None

### DEFECT-029
**Title:** BriefingLibrary — Unreachable Dialog
**Severity:** P2
**Category:** Frontend
**File:** `frontend/src/components/intelligence/briefing-library.tsx` (lines 482-486)
**Component:** Briefing Library
**Root Cause:** `dialogOpen` state exists but `setDialogOpen(true)` is never called
**Reproduction:** Try to view briefing detail → nothing happens
**Impact:** BriefingDetailDialog is dead code
**Fix Effort:** S (add click handler)
**Dependencies:** DEFECT-001

### DEFECT-030
**Title:** Copilot — Field Name Mismatch (query vs user_query)
**Severity:** P2
**Category:** API Contract
**File:** `frontend/src/app/copilot/page.tsx`
**Component:** Copilot
**Root Cause:** Frontend sends `{query}`, backend expects `{user_query}`
**Reproduction:** Send message → backend gets empty user_query → 400
**Impact:** Copilot messages fail
**Fix Effort:** S (align field name)
**Dependencies:** None

### DEFECT-031
**Title:** Copilot — Archive Uses POST Instead of PUT
**Severity:** P2
**Category:** API Contract
**File:** `frontend/src/app/copilot/page.tsx`
**Component:** Copilot Archive
**Root Cause:** Frontend sends `POST` to archive, backend expects `PUT`
**Reproduction:** Try to archive conversation → 405 Method Not Allowed
**Impact:** Cannot archive conversations
**Fix Effort:** S (change POST to PUT)
**Dependencies:** None

### DEFECT-032
**Title:** Copilot — Response Parsing Mismatch
**Severity:** P2
**Category:** API Contract
**File:** `frontend/src/app/copilot/page.tsx`
**Component:** Copilot Response
**Root Cause:** Frontend expects `data.response`, backend returns `{data: {message: {...}}}`
**Reproduction:** Send message → response not displayed
**Impact:** AI responses don't show in chat
**Fix Effort:** S (fix response parsing)
**Dependencies:** None

### DEFECT-033
**Title:** Strategic — alert() for Compare Result
**Severity:** P2
**Category:** UX
**File:** `frontend/src/app/strategic/page.tsx` (line 226)
**Component:** Strategic Planning
**Root Cause:** Uses `alert(JSON.stringify(...))` for scenario comparison
**Reproduction:** Compare scenarios → browser alert popup
**Impact:** Poor UX, unprofessional
**Fix Effort:** S (use toast or inline display)
**Dependencies:** None

### DEFECT-034
**Title:** Forecasting — alert() for Model Comparison
**Severity:** P2
**Category:** UX
**File:** `frontend/src/app/forecasting/page.tsx` (line 226)
**Component:** Forecasting
**Root Cause:** Uses `alert(JSON.stringify(...))` for model comparison
**Reproduction:** Compare models → browser alert popup
**Impact:** Poor UX
**Fix Effort:** S (use toast or inline display)
**Dependencies:** None

### DEFECT-035
**Title:** Semantic — Dimension Field Name Mismatch
**Severity:** P2
**Category:** API Contract
**File:** `frontend/src/app/semantic/page.tsx`
**Component:** Semantic Layer Create Dimension
**Root Cause:** Frontend sends `{source_table, source_column}`, backend expects `{physical_name, key_column}`
**Reproduction:** Try to create dimension → 422
**Impact:** Cannot create dimensions
**Fix Effort:** S (align field names)
**Dependencies:** None

### DEFECT-036
**Title:** IntelligenceFeed — Missing Backend Endpoint
**Severity:** P2
**Category:** Backend
**File:** `backend/app/api/v2/endpoints/intelligence.py`
**Component:** Intelligence Feed
**Root Cause:** `GET /api/v2/intelligence/feed` endpoint not defined
**Reproduction:** IntelligenceFeed component calls this endpoint → 404
**Impact:** Feed tab in intelligence shows error
**Fix Effort:** M (implement feed endpoint)
**Dependencies:** DEFECT-001

---

## P3 — UX Issues (11 defects)

### DEFECT-037
**Title:** No Authentication Guards on Protected Pages
**Severity:** P3
**Category:** Security
**File:** All pages except /login and /register
**Component:** Auth Guard
**Root Cause:** No page checks if user is authenticated before rendering
**Reproduction:** Navigate directly to `/dashboard` without login → page loads
**Impact:** Unauthenticated users can access all pages
**Fix Effort:** M (add auth middleware/guard)
**Dependencies:** None

### DEFECT-038
**Title:** Knowledge Graph — Developer-Facing, Not Executive
**Severity:** P3
**Category:** UX
**File:** `frontend/src/components/knowledge-graph/knowledge-graph-explorer.tsx`
**Component:** Knowledge Graph Explorer
**Root Cause:** Shows UUIDs instead of entity names, requires Node IDs for search, basic SVG circles
**Reproduction:** Open knowledge graph → see generic circles with no labels
**Impact:** Executives cannot use this page
**Fix Effort:** XL (redesign with entity labels, search, interactive viz)
**Dependencies:** None

### DEFECT-039
**Title:** Forecasting — Technical UI for Executives
**Severity:** P3
**Category:** UX
**File:** `frontend/src/app/forecasting/page.tsx`
**Component:** Forecasting
**Root Cause:** Requires choosing model type (Prophet, ARIMA, XGBoost) and entering JSON parameters
**Reproduction:** Open forecasting → see data science interface
**Impact:** Executives cannot use without technical knowledge
**Fix Effort:** L (add simplified "Quick Forecast" mode)
**Dependencies:** None

### DEFECT-040
**Title:** Strategic Planning — Raw Key-Value Input
**Severity:** P3
**Category:** UX
**File:** `frontend/src/app/strategic/page.tsx`
**Component:** Strategic Planning Scenario Creation
**Root Cause:** Assumptions entered as raw key-value pairs without guidance
**Reproduction:** Create scenario → blank key-value fields
**Impact:** Slow scenario creation, confusing for executives
**Fix Effort:** M (pre-populate common healthcare assumptions)
**Dependencies:** None

### DEFECT-041
**Title:** 3 Unused Sparkline Default Values
**Severity:** P3
**Category:** Frontend
**File:** intelligence-feed.tsx, anomaly-center.tsx
**Component:** Intelligence Components
**Root Cause:** Default sparkline data `[10, 12, 11, 14, 13, 16, 18]` used as fallback
**Reproduction:** Component loads with no data → shows generic sparkline
**Impact:** Misleading visual
**Fix Effort:** S (show empty state instead)
**Dependencies:** None

### DEFECT-042
**Title:** Learning Dashboard — Raw JSON.stringify Output
**Severity:** P3
**Category:** UX
**File:** `frontend/src/components/learning/learning-dashboard.tsx` (line 163)
**Component:** Learning Dashboard
**Root Cause:** Dashboard data rendered as `JSON.stringify(data, null, 2)`
**Reproduction:** Open learning page → see raw JSON
**Impact:** Unreadable for executives
**Fix Effort:** M (format as structured cards/charts)
**Dependencies:** None

### DEFECT-043
**Title:** Visualization — Render Result Not Displayed
**Severity:** P3
**Category:** Frontend
**File:** `frontend/src/app/visualization/page.tsx`
**Component:** Visualization
**Root Cause:** `handleRenderSpec` renders server-side but result is never shown in UI
**Reproduction:** Create and render spec → result not visible
**Impact:** Render feature is pointless
**Fix Effort:** M (display rendered chart)
**Dependencies:** None

### DEFECT-044
**Title:** Alert Stats — Manual Local State Manipulation
**Severity:** P3
**Category:** Frontend
**File:** `frontend/src/app/alerts/page.tsx`
**Component:** Alert Center
**Root Cause:** Stats updated by `stats.unread - 1` locally instead of re-fetching
**Reproduction:** Mark alert read → stats may desync from server
**Impact:** Stats can become inaccurate
**Fix Effort:** S (re-fetch stats after mutation)
**Dependencies:** None

### DEFECT-045
**Title:** Dead Imports in Workspace Page
**Severity:** P3
**Category:** Frontend
**File:** `frontend/src/app/workspace/page.tsx` (line 50)
**Component:** Workspace
**Root Cause:** `intelligenceAPI` and `decisionsAPI` imported but never used
**Reproduction:** Check imports → dead references
**Impact:** Dead code
**Fix Effort:** S (remove unused imports)
**Dependencies:** None

### DEFECT-046
**Title:** Missing useEffect Dependencies (8 components)
**Severity:** P3
**Category:** Frontend
**File:** Multiple components
**Component:** Various
**Root Cause:** `useEffect` missing function dependencies (React exhaustive-deps)
**Reproduction:** ESLint warning
**Impact:** Potential stale closures
**Fix Effort:** S (add dependencies or useCallback)
**Dependencies:** None

### DEFECT-047
**Title:** No Route-Level Error Boundaries
**Severity:** P3
**Category:** Frontend
**File:** All pages
**Component:** Error Handling
**Root Cause:** No error boundary components at route level
**Reproduction:** Component throws → entire app crashes
**Impact:** Unhandled errors crash the whole app
**Fix Effort:** M (add error boundaries per route)
**Dependencies:** None
