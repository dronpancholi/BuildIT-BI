# SYSTEM REALITY MAP
## BuildIT BI — Healthcare Financial Intelligence Platform
### WAVE-1 FOUNDATION RECONSTRUCTION | Audit Date: 2026-06-13

---

## VERDICT SUMMARY

| Dimension | Status |
|-----------|--------|
| Architecture | ⚠️ SPLIT — Two parallel architectures (v1/v2) with no unification |
| Data Layer | ⚠️ FRAGMENTED — Three separate model files, no single source of truth |
| AI Layer | ✅ DEFINED — Endpoints exist, intelligence engine exists, but not wired to real data |
| Frontend | ⚠️ PARTIAL — 31 pages exist; ~40% render real data, ~60% show placeholders or crash |
| Exports | ⚠️ SKELETON — Excel framework exists via openpyxl; no actual data populates it |
| Executive Layer | ⚠️ DISCONNECTED — Executive Center reads v2 API; v2 API returns mock/empty data |
| UIF | ❌ DOES NOT EXIST — No Unified Intelligence Fabric; pages query independently |

---

## SECTION 1 — FRONTEND ROUTES

### 1.1 Registered Routes (Next.js App Router)

| Route | File | Component | Status |
|-------|------|-----------|--------|
| `/` | `app/page.tsx` | Root redirect | ✅ Redirects to `/login` |
| `/login` | `app/login/page.tsx` | LoginPage | ✅ Works — calls v1 `/auth/login` |
| `/register` | `app/register/page.tsx` | RegisterPage | ✅ Works — calls v1 `/auth/register` |
| `/auth` | `app/auth/page.tsx` | AuthPage | ⚠️ DUPLICATE of `/login` |
| `/dashboard` | `app/dashboard/page.tsx` | CommandCenter | ⚠️ PARTIAL — KPIs load; charts are placeholders |
| `/revenue` | `app/revenue/page.tsx` | RevenuePage | ❌ FAIL — Chart areas are empty placeholders |
| `/insights` | `app/insights/page.tsx` | InsightsPage | ⚠️ PARTIAL — Calls v1 `/insights/comprehensive` |
| `/alerts` | `app/alerts/page.tsx` | AlertsPage | ✅ Works — v1 alerts API wired |
| `/analytics` | `app/analytics/page.tsx` | AnalyticsPage | ⚠️ PARTIAL — v2 metrics API called |
| `/analytics/query` | `app/analytics/query/page.tsx` | QueryPage | ❌ FAIL — No query builder UI |
| `/forecasting` | `app/forecasting/page.tsx` | ForecastingPage | ⚠️ PARTIAL — Model list loads; no chart |
| `/forecasts` | `app/forecasts/page.tsx` | ForecastsPage | ❌ DEAD — Duplicate of forecasting; orphaned |
| `/intelligence` | `app/intelligence/page.tsx` | IntelligencePage | ✅ BEST PAGE — Full tabbed intelligence center |
| `/executive-center` | `app/executive-center/page.tsx` | ExecutiveCenterPage | ⚠️ PARTIAL — KPI grid loads; briefings empty |
| `/ai-cfo` | `app/ai-cfo/page.tsx` | AICFOPage | ⚠️ PARTIAL — Chat interface exists; backend returns generic responses |
| `/copilot` | `app/copilot/page.tsx` | CopilotPage | ⚠️ PARTIAL — Query UI exists; real NLP not wired |
| `/decisions` | `app/decisions/page.tsx` | DecisionsPage | ✅ Works — Full CRUD via v2 decisions API |
| `/scenarios` | `app/scenarios/page.tsx` | ScenariosPage | ⚠️ PARTIAL — v1 scenarios API; no Monte Carlo UI |
| `/strategic` | `app/strategic/page.tsx` | StrategicPage | ✅ Works — Monte Carlo, What-If wired |
| `/dashboards` | `app/dashboards/page.tsx` | DashboardsPage | ⚠️ PARTIAL — List works; widget builder broken |
| `/formulas` | `app/formulas/page.tsx` | FormulasPage | ✅ Works — BFL parse/validate wired |
| `/metric-studio` | `app/metric-studio/page.tsx` | MetricStudioPage | ✅ Works — Full lifecycle management |
| `/semantic` | `app/semantic/page.tsx` | SemanticPage | ✅ Works — Dimensions, hierarchies wired |
| `/knowledge-graph` | `app/knowledge-graph/page.tsx` | KnowledgeGraphPage | ❌ FAIL — Graph explorer renders empty SVG |
| `/governance` | `app/governance/page.tsx` | GovernancePage | ✅ Works — Certifications, approvals wired |
| `/collaboration` | `app/collaboration/page.tsx` | CollaborationPage | ✅ Works — Comments, assignments wired |
| `/exports` | `app/exports/page.tsx` | ExportsPage | ⚠️ PARTIAL — Job creation works; download broken |
| `/visualization` | `app/visualization/page.tsx` | VisualizationPage | ⚠️ PARTIAL — Chart types list works; rendering fails |
| `/workspace` | `app/workspace/page.tsx` | WorkspacePage | ⚠️ PARTIAL — Workspace loads; briefings empty |
| `/learning` | `app/learning/page.tsx` | LearningPage | ✅ Works — Metrics, patterns wired |
| `/settings` | `app/settings/page.tsx` | SettingsPage | ⚠️ PARTIAL — UI only; no save wired |

### 1.2 MISSING Routes (Referenced but non-existent)

| Referenced Route | Source | Status |
|-----------------|--------|--------|
| `/patients` | No route | ❌ DOES NOT EXIST |
| `/claims` | No route | ❌ DOES NOT EXIST |
| `/departments` | No route | ❌ DOES NOT EXIST |
| `/branches` | No route | ❌ DOES NOT EXIST |
| `/payers` | No route | ❌ DOES NOT EXIST |
| `/doctors` | No route | ❌ DOES NOT EXIST |
| `/cash-flow` | No route | ❌ DOES NOT EXIST |
| `/occupancy` | No route | ❌ DOES NOT EXIST |
| `/expenses` | No route | ❌ DOES NOT EXIST |

### 1.3 Orphaned/Dead Routes

| Route | Issue |
|-------|-------|
| `/forecasts` | Duplicate of `/forecasting`; not in nav |
| `/auth` | Duplicate of `/login`; standalone page |

---

## SECTION 2 — FRONTEND COMPONENTS

### 2.1 Component Inventory

| Path | Files | Status |
|------|-------|--------|
| `components/ai/` | `ask-ai-button.tsx`, `ai-cfo-chat.tsx` | ✅ Exists |
| `components/intelligence/` | 6 files (feed, anomaly, opportunity, recommendation, briefing, graph) | ✅ Well-built |
| `components/layout/` | `dashboard-layout.tsx`, `kpi-card.tsx` | ✅ Core layout works |
| `components/charts/` | Unknown — directory exists, no files confirmed | ⚠️ INVESTIGATE |
| `components/dashboard/` | No files found | ❌ EMPTY |
| `components/decision/` | Unknown | ⚠️ INVESTIGATE |
| `components/kpi/` | No files found in root | ❌ EMPTY |
| `components/outcome/` | Unknown | ⚠️ INVESTIGATE |
| `components/ui/` | shadcn/ui components | ✅ Full suite |

### 2.2 Chart Library Status

- **ECharts**: Listed in package.json? **NOT CONFIRMED** — Revenue page says "Connect ECharts to visualize data"
- **Recharts**: Referenced in some components — status unclear
- **Victory/Vega**: Not detected
- **Chart Placeholders**: Revenue page, forecasting page, visualization page all have `h-[300px] flex items-center justify-center bg-muted/50` placeholder divs

### 2.3 Hooks

| Hook Path | Status |
|-----------|--------|
| `lib/hooks/` | ❌ EMPTY DIRECTORY — No custom hooks exist |

**CRITICAL**: Zero shared hooks. Every page manages its own state independently.

---

## SECTION 3 — FRONTEND STORES / CONTEXTS

| Item | Status |
|------|--------|
| React Context | ❌ NONE — No global context providers |
| Zustand/Redux | ❌ NONE — Not detected |
| React Query / SWR | ❌ NONE — Not installed |
| Auth Context | ❌ NONE — Auth stored in `localStorage` directly |
| User Context | ❌ NONE — Each page calls `/auth/me` independently |
| Tenant Context | ❌ NONE — No tenant state management |

**CRITICAL FAILURE**: No shared state layer. Every page re-fetches user identity, re-reads tokens from localStorage, and manages its own loading/error states with `useState`.

---

## SECTION 4 — BACKEND ROUTERS

### 4.1 V1 API (Legacy — `app/api/v1/`)

| Prefix | File | Endpoints | Wired To |
|--------|------|-----------|----------|
| `/api/v1/auth` | `auth.py` | login, register, me, update-me | PostgreSQL users table |
| `/api/v1/kpis` | `kpi.py` | executive-summary, revenue, profitability, occupancy, claims, trend, by-department, by-payer | PostgreSQL revenues/expenses/claims/occupancy |
| `/api/v1/insights` | `insights.py` | comprehensive, anomalies, trends, opportunities, narrative | Computed from revenue/expense data |
| `/api/v1/forecasts` | `forecasts.py` | create, historical, decompose, validate | PostgreSQL forecasts table |
| `/api/v1/scenarios` | `scenarios.py` | simulate, pricing-change, department-expansion, staffing-change, save, list | PostgreSQL scenarios table |
| `/api/v1/alerts` | `alerts.py` | list, get, mark-read, resolve, create, stats | PostgreSQL alerts table |

### 4.2 V2 API (New Architecture — `app/api/v2/`)

| Prefix | File | Status | DB Connected |
|--------|------|--------|-------------|
| `/api/v2/decisions` | `decisions.py` | ✅ Full CRUD | PostgreSQL (persistence models) |
| `/api/v2/outcomes` | `outcomes.py` | ✅ Full CRUD | PostgreSQL (persistence models) |
| `/api/v2/learning` | `learning.py` | ✅ Metrics + patterns | PostgreSQL |
| `/api/v2/financial` | `financial.py` | ✅ FX rates, conversion | In-memory (no DB needed) |
| `/api/v2/analytics` | `analytics.py` | ✅ Metrics, dimensions, query | PostgreSQL (metric models) |
| `/api/v2/dashboards` | `dashboards.py` | ✅ Full CRUD + widgets | PostgreSQL |
| `/api/v2/query` | `query_engine.py` | ✅ Execute, generate-sql | DuckDB + PostgreSQL |
| `/api/v2/exports` | `exports.py` | ⚠️ Jobs created; Excel generation has fallback path | PostgreSQL + openpyxl |
| `/api/v2/collaboration` | `collaboration.py` | ✅ Comments, assignments | PostgreSQL |
| `/api/v2/workspace` | `workspace.py` | ✅ Workspace + briefings | PostgreSQL |
| `/api/v2/visualization` | `visualization.py` | ✅ Chart types, specs | PostgreSQL |
| `/api/v2/governance` | `governance.py` | ✅ Certifications, approvals | PostgreSQL |
| `/api/v2/bfl` | `bfl.py` | ✅ Parse, validate, generate-sql | In-memory |
| `/api/v2/metric-studio` | `metric_studio.py` | ✅ Lifecycle management | PostgreSQL |
| `/api/v2/semantic` | `semantic_layer.py` | ✅ SCD2, hierarchies | PostgreSQL |
| `/api/v2/ai-cfo` | `ai_cfo.py` | ✅ Profiles, questions, briefings | PostgreSQL + OpenAI/NIM |
| `/api/v2/strategic` | `strategic_planning.py` | ✅ Scenarios, Monte Carlo | In-memory computation |
| `/api/v2/forecasting` | `forecasting.py` | ✅ Models, training, forecast | PostgreSQL |
| `/api/v2/executive` | `executive_center.py` | ✅ KPIs, alerts, decisions, summary | PostgreSQL |
| `/api/v2/copilot` | `copilot.py` | ✅ Query, reasoning, conversations | PostgreSQL + LLM |
| `/api/v2/intelligence` | `intelligence.py` | ✅ Full intelligence engine | PostgreSQL (persistence models) |
| `/api/v2/ai` | `ai_everywhere.py` | ✅ Ask AI about anything | LLM + context |

---

## SECTION 5 — BACKEND SERVICES & REPOSITORIES

### 5.1 Service Layer Architecture

```
app/services/          ← V1 services (simple, stateless)
  kpi/engine.py
  forecasting/engine.py
  insights/engine.py
  scenarios/simulator.py

app/domain/services/   ← V2 domain services (DDD pattern)
  kpi_engine.py        ← Authoritative metric computation engine
  metric_registry.py   ← Metric definitions registry

app/domain/intelligence/services/  ← Intelligence engine components
  anomaly_detection_engine.py
  insight_discovery_engine.py
  recommendation_engine.py
  opportunity_engine.py
  briefing_engine.py
  narrative_engine.py
  root_cause_engine.py
  scoring.py
  graph.py
```

### 5.2 Repository Pattern

| Repository | Location | Status |
|-----------|---------|--------|
| IntelligenceInsightRepositoryImpl | `infrastructure/database/repositories/` | ✅ Exists |
| IntelligenceAnomalyRepositoryImpl | `infrastructure/database/repositories/` | ✅ Exists |
| IntelligenceOpportunityRepositoryImpl | `infrastructure/database/repositories/` | ✅ Exists |
| IntelligenceRecommendationRepositoryImpl | `infrastructure/database/repositories/` | ✅ Exists |
| IntelligenceBriefingRepositoryImpl | `infrastructure/database/repositories/` | ✅ Exists |
| DecisionRepositoryImpl | `infrastructure/database/repositories/decision_repository.py` | ✅ Exists |
| OutcomeRepositoryImpl | `infrastructure/database/repositories/outcome_repository.py` | ✅ Exists |
| ForecastingRepositoryImpl | `infrastructure/database/repositories/forecasting_repository.py` | ✅ Exists |
| KnowledgeRepositoryImpl | `infrastructure/database/repositories/knowledge_repository.py` | ✅ Exists |
| MemoryRepositoryImpl | `infrastructure/database/repositories/memory_repository.py` | ✅ Exists |
| General Infrastructure | `infrastructure/persistence/repositories.py` | ✅ 1476 lines |

### 5.3 Infrastructure Services

| Service | Status |
|---------|--------|
| PostgreSQL (pgvector) | ✅ Configured via docker-compose |
| Redis | ✅ Configured — used for caching |
| Temporal | ✅ Configured — workflow orchestration |
| DuckDB | ⚠️ Directory empty — DuckDB referenced in requirements but no .db file seeded |
| NIM/NVIDIA LLM | ⚠️ Configured — API key required; falls back to stub responses |
| OpenAI | ⚠️ Referenced in requirements (openai==2.41.1) — API key unknown |
| pgvector | ✅ Image configured — embedding support ready |

---

## SECTION 6 — DOMAIN MODELS

### 6.1 Model Split — THE CRITICAL PROBLEM

There are **THREE separate model files** defining database entities:

**Model File 1**: `app/models/models.py` (V1 Models — 278 lines)
```
User, Branch, Department, Payer, Doctor, FinancialPeriod,
Revenue, Expense, Claim, Occupancy, KPI, KPIValue, Alert,
Forecast, Scenario
```

**Model File 2**: `app/infrastructure/persistence/models.py` (V2 Models — 2013 lines)
```
TenantModel, HospitalGroupModel, HospitalModel, BranchModel,
DepartmentModel, DoctorModel, PayerModel, PatientModel,
RevenueTransactionModel, ExpenseModel, ClaimModel, OccupancyModel,
KPIDefinitionModel, KPIValueModel,
IntelligenceInsightModel, IntelligenceAnomalyModel,
IntelligenceOpportunityModel, IntelligenceRecommendationModel,
IntelligenceBriefingModel, IntelligenceRootCauseModel,
IntelligenceGraphNodeModel, IntelligenceRelationshipModel,
DecisionModel, OutcomeDefinitionModel, OutcomeMeasurementModel,
FeatureModel, MLModelModel, ForecastModelModel, ForecastRunModel,
MetricDefinitionModel, MetricValueModel, DimensionModel,
FactTableModel, DashboardModel, WidgetModel,
WorkspaceModel, BriefingModel, ExportJobModel, ExportScheduleModel,
CollaborationCommentModel, CollaborationThreadModel, AssignmentModel,
GovernanceVersionModel, MetricStudioModel, SemanticDimensionModel,
AICFOProfileModel, AICFOQuestionModel, CopilotConversationModel,
ScenarioModel, StrategicDriverTreeModel
```

**Model File 3**: `app/schemas/schemas.py` (Pydantic Schemas — 7574 bytes)
```
Pydantic response/request schemas used in V1 endpoints
```

**VERDICT**: Model duplication is severe. V1 models (app/models/models.py) are used only by V1 endpoints. V2 endpoints use V2 persistence models. The two model sets have similar entities (Revenue, Department, etc.) with different schemas, column names, and relationships. There is NO unified domain model.

### 6.2 Database Tables (from Alembic Migrations)

Migration chain: 001 → 002 → 003 → 004 → 005 → 006 → 007

| Migration | Tables Created |
|-----------|---------------|
| 001_initial_schema | users, branches, departments, payers, doctors, financial_periods, revenues, expenses, claims, occupancy, kpis, kpi_values, alerts, forecasts, scenarios |
| 002_intelligence_engine | intelligence_insights, intelligence_anomalies, intelligence_opportunities, intelligence_recommendations, intelligence_briefings, intelligence_root_causes, intelligence_graph_nodes, intelligence_relationships |
| 003_decision_intelligence | decisions, decision_timeline_events, decision_evidence |
| 004_outcome_feature_model | outcome_definitions, outcome_measurements, features, ml_models |
| 005_financial_architecture | tenants, hospital_groups, hospitals, (full tenant hierarchy) |
| 006_phase5_domains | metric_studio_metrics, semantic_dimensions, semantic_hierarchies, dashboard_models, export_jobs, collaboration_comments, etc. |
| 007_core_financial_tables | (Supplemental financial tables) |

### 6.3 Missing Entities (Referenced but No Table)

| Entity | Referenced In | Has Table? |
|--------|--------------|------------|
| Patient | Claim.patient_id (string) | ❌ No dedicated patients table |
| ExecutiveReport | Exports endpoint | ❌ No dedicated table |
| AIBriefing (structured) | Workspace | ⚠️ workspace_briefings table exists |

---

## SECTION 7 — AI LAYER

### 7.1 AI Components Inventory

| Component | Location | Status | Data Source |
|-----------|---------|--------|-------------|
| AI CFO Core | `v2/endpoints/ai_cfo.py` | ✅ 24 endpoints | LLM + PostgreSQL |
| AI CFO Copilot | `v2/endpoints/copilot.py` | ✅ 8 endpoints | LLM + context |
| Intelligence Engine | `v2/endpoints/intelligence.py` | ✅ 1791 lines — most complete | PostgreSQL |
| AI Everywhere (Ask AI) | `v2/endpoints/ai_everywhere.py` | ✅ Single `/ai/ask` endpoint | LLM + page context |
| Anomaly Detection | `domain/intelligence/services/anomaly_detection_engine.py` | ✅ Exists | Metric time series |
| Insight Discovery | `domain/intelligence/services/insight_discovery_engine.py` | ✅ Exists | Metric data |
| Recommendation Engine | `domain/intelligence/services/recommendation_engine.py` | ✅ Exists | Insight data |
| Opportunity Engine | `domain/intelligence/services/opportunity_engine.py` | ✅ Exists | Revenue/expense data |
| Briefing Engine | `domain/intelligence/services/briefing_engine.py` | ✅ Exists | All KPIs + alerts |
| Narrative Engine | `domain/intelligence/services/narrative_engine.py` | ✅ Exists | Financial data |
| Root Cause Engine | `domain/intelligence/services/root_cause_engine.py` | ✅ Exists | Anomaly data |
| Scoring Engine | `domain/intelligence/services/scoring.py` | ✅ Exists | Multi-factor scoring |

### 7.2 AI Connectivity to Frontend

| Frontend Component | Backend AI Endpoint | Connected? |
|-------------------|-------------------|------------|
| `ask-ai-button.tsx` | `/api/v2/ai/ask` | ✅ Yes |
| `ai-cfo-chat.tsx` | `/api/v2/ai-cfo/questions` | ✅ Yes |
| Copilot page | `/api/v2/copilot/query` | ✅ Yes |
| Executive briefings | `/api/v2/executive/briefing` | ✅ Yes |
| Intelligence feed | `/api/v2/intelligence/feed` | ✅ Yes |
| Anomaly center | `/api/v2/intelligence/anomalies` | ✅ Yes |
| Recommendation center | `/api/v2/intelligence/recommendations` | ✅ Yes |
| **Revenue page AI** | None | ❌ NO AI on revenue page |
| **Dashboard AI** | `/api/v1/insights/narrative` | ⚠️ V1 only; generic text |
| **Department AI** | None | ❌ NO AI on department data |
| **Forecasting AI** | `/api/v2/forecasting/models` | ⚠️ Model mgmt only; no AI explain |

---

## SECTION 8 — WHAT EXISTS vs WHAT IS DEAD

### 8.1 PRODUCTION GRADE ✅

- Intelligence page + components (anomaly, opportunity, recommendation, briefing)
- Decisions workflow (full CRUD + status machine)
- Auth system (V1 — login/register/JWT)
- Semantic layer (dimensions, SCD2, hierarchies)
- Metric Studio (full lifecycle)
- BFL (formula language — parse/validate/SQL)
- Governance (certifications, approvals, versions)
- Collaboration (comments, threads, assignments)
- Strategic planning (Monte Carlo, What-If, driver trees)
- Learning engine (accuracy tracking, patterns)
- Backend infrastructure (PostgreSQL, Redis, Temporal, pgvector)

### 8.2 PARTIALLY WIRED ⚠️

- Dashboard page (KPIs load but charts are placeholders)
- Executive Center (KPI grid loads; briefings empty because no data seeded)
- AI CFO (UI exists; LLM returns generic responses without real financial context)
- Forecasting page (model list loads; no visualization)
- Exports (job creation works; actual file generation not end-to-end tested)
- Revenue page (API calls work; chart components are placeholder divs)
- Workspace (loads; briefings empty)
- Settings (UI renders; no save API)

### 8.3 FAKE / PLACEHOLDER ❌

- Revenue chart — "Connect ECharts to visualize data" placeholder text
- Revenue trends tab — "Time series visualization with forecasts" placeholder
- Revenue insights — **HARDCODED STRINGS**: "Revenue has increased by 8.3%", "Medicaid volume has increased by 5.2%"
- Knowledge graph — SVG renders empty
- Analytics query page — No query builder UI built

### 8.4 DEAD / DISCONNECTED ❌

- `/forecasts` route — orphaned, duplicate, not in navigation
- `/auth` route — duplicate of login, not in navigation  
- `lib/hooks/` directory — completely empty
- `components/dashboard/` — completely empty
- `duckdb/` directory — completely empty
- `BI/` directory — contains only a sub-nested copy of the same project (possible git artifact)

### 8.5 DUPLICATED

| Duplication | Instances | Problem |
|------------|-----------|---------|
| Revenue model | `models/models.py:Revenue` + `persistence/models.py:RevenueTransactionModel` | Two different schemas for same entity |
| KPI model | `models/models.py:KPI` + `persistence/models.py:KPIDefinitionModel` | Completely different column sets |
| Forecast model | `models/models.py:Forecast` + `persistence/models.py:ForecastModelModel` | V1 forecasts vs V2 ML forecast models |
| Scenarios | V1 scenarios + V2 strategic scenarios | Different data structures |
| Auth | V1 auth endpoint + no V2 equivalent | V2 relies on V1 auth |
| Alert | V1 alerts + V2 intelligence anomalies | Semantic overlap |
| API client | `api` (v1) + `v2` (v2 axios) in same file | Two axios instances with separate configs |

---

## SECTION 9 — CONNECTIVITY MATRIX

Every component must prove data lineage. Red = broken chain.

```
REVENUE PAGE
  ├── KPI Summary → /api/v1/kpis/revenue → services/kpi/engine.py → revenues table ✅
  ├── Department breakdown → /api/v1/kpis/revenue/by-department → revenues table ✅
  ├── Payer breakdown → /api/v1/kpis/revenue/by-payer → revenues table ✅
  ├── Revenue chart → ❌ NO CHART COMPONENT — placeholder div
  ├── Revenue trends → ❌ NO CHART COMPONENT — placeholder div
  └── Revenue insights → ❌ HARDCODED STRINGS — not from any API

DASHBOARD PAGE
  ├── KPIs → /api/v1/kpis/executive-summary → revenues/expenses/claims tables ✅
  ├── AI Narrative → /api/v1/insights/narrative → computed text ✅
  ├── Anomaly alerts → /api/v1/insights/comprehensive → computed anomalies ✅
  ├── Trends → /api/v1/insights/trends → computed trends ✅
  ├── Opportunities → /api/v1/insights/opportunities → computed opportunities ✅
  └── Charts → ❌ NONE

EXECUTIVE CENTER
  ├── KPIs → /api/v2/executive/kpis → executive_center.py → KPIDefinitionModel ✅
  ├── Alerts → /api/v2/executive/alerts → IntelligenceAnomalyModel ✅
  ├── Decisions → /api/v2/executive/decisions → DecisionModel ✅
  ├── Summary → /api/v2/executive/summary → Computed ✅
  ├── Revenue Forecast → /api/v2/executive/forecasts/revenue → ForecastRunModel ✅
  └── AI Briefing → /api/v2/executive/briefing → LLM ⚠️ (no real financial data injected)

INTELLIGENCE PAGE
  ├── Feed → /api/v2/intelligence/feed → IntelligenceInsightModel ✅
  ├── Anomalies → /api/v2/intelligence/anomalies → IntelligenceAnomalyModel ✅
  ├── Opportunities → /api/v2/intelligence/opportunities → IntelligenceOpportunityModel ✅
  ├── Recommendations → /api/v2/intelligence/recommendations → IntelligenceRecommendationModel ✅
  ├── Briefings → /api/v2/intelligence/briefings → IntelligenceBriefingModel ✅
  └── Graph → /api/v2/intelligence/graph/nodes → IntelligenceGraphNodeModel ✅

FORECASTING PAGE
  ├── Model list → /api/v2/forecasting/models → ForecastModelModel ✅
  ├── Train model → /api/v2/forecasting/models/{id}/train → ForecastModelModel ✅
  ├── Generate forecast → /api/v2/forecasting/models/{id}/forecast → ForecastRunModel ✅
  └── Forecast chart → ❌ NO CHART COMPONENT
```

---

## SECTION 10 — THE UNIFIED INTELLIGENCE FABRIC — CURRENT STATE

**Status: ❌ DOES NOT EXIST**

What should exist vs what does:

| UIF Component | Required | Current State |
|--------------|---------|---------------|
| KPI Registry | Single source of all KPI definitions | Exists in `domain/services/metric_registry.py` — but NOT consumed by pages |
| Metric Registry | Versioned metric definitions | Exists in `domain/services/metric_registry.py` |
| Dimension Registry | All filterable dimensions | Defined in analytics endpoint — not centralized |
| Entity Registry | Revenue, Expense, Patient, Claim, Payer | Split across two model files |
| Time Registry | Period types, fiscal calendar | Defined in domain entities only |
| Department Registry | All departments with hierarchy | No registry — direct DB query |
| Executive Registry | Hospital score, EBITDA, KPI targets | No registry — ad-hoc |
| UnifiedDataFabric | Single data access layer | ❌ MISSING — pages query independently |

---

## SECTION 11 — WHAT WAVE-2 MUST DELIVER

Based on this audit, WAVE-2 must:

1. **Create Unified Intelligence Fabric (UIF)** — All pages consume data through one fabric
2. **Build Missing Charts** — Revenue, Dashboard, Forecasting all need ECharts integration
3. **Fix Revenue Page** — Remove hardcoded strings; wire real AI insights
4. **Build Missing Pages** — Departments, Patients, Claims, Cash Flow, Occupancy, Expenses
5. **Eliminate V1/V2 Split** — Migrate remaining V1 frontend calls to V2
6. **Unify Domain Models** — Eliminate `models/models.py`; V2 persistence models are authoritative
7. **Add Global State Layer** — Implement React Query or Zustand for shared state
8. **Seed Real Data** — Without seeded data, executive briefings and AI insights are empty
9. **Fix Knowledge Graph** — Wire D3/force graph renderer
10. **Complete Excel Export** — Ensure openpyxl generates real KPI packs

---

*Audit by: Antigravity AI Architectural Audit System*  
*Classification: CONFIDENTIAL — Internal Technical Document*
