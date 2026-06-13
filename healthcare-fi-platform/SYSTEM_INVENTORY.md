# SYSTEM INVENTORY

**ERP-1 Phase 1 — Complete Source Code Inventory**
**Date:** 2026-06-12
**Status:** READ-ONLY AUDIT

---

## Executive Summary

| Area | Files | Lines of Code |
|------|-------|---------------|
| Backend Endpoints | 38 | 13,428 |
| Backend Domain | 75 | 28,572 |
| Backend Infrastructure | 22 | 8,800 |
| Backend Core | 6 | 292 |
| Backend DB Layer | 3 | 41 |
| Frontend Pages | 38 | ~19,400 |
| Frontend Components | 15+ | ~8,100 |
| Frontend API Client | 1 | 587 |
| **Total** | **~200** | **~79,220** |

---

## Backend Structure

```
backend/
├── app/
│   ├── main.py                    (85 LOC) — FastAPI app, router registration
│   ├── api/
│   │   ├── v1/
│   │   │   ├── api.py             (11 LOC) — V1 router (6 sub-routers)
│   │   │   └── endpoints/
│   │   │       ├── auth.py        (367 LOC) — 4 routes, real DB
│   │   │       ├── kpi.py         (152 LOC) — 6 routes, engine-dependent
│   │   │       ├── forecasts.py   (85 LOC) — 4 routes, engine-dependent
│   │   │       ├── scenarios.py   (169 LOC) — 8 routes, mixed
│   │   │       ├── alerts.py      (150 LOC) — 6 routes, real DB
│   │   │       └── insights.py    (87 LOC) — 5 routes, engine-dependent
│   │   └── v2/
│   │       ├── api.py             (70 LOC) — V2 router (31 sub-routers)
│   │       └── endpoints/
│   │           ├── api.py              (828 LOC) — 38 routes, ALL MOCK
│   │           ├── ai_cfo.py           (403 LOC) — 15 routes, real DB
│   │           ├── analytics.py        (444 LOC) — 15 routes, mixed
│   │           ├── bfl.py              (156 LOC) — BFL formulas
│   │           ├── causal_inference.py (279 LOC) — causal analysis
│   │           ├── collaboration.py    (293 LOC) — 15 routes, mixed
│   │           ├── dashboards.py       (375 LOC) — 11 routes, real DB
│   │           ├── decisions.py        (464 LOC) — decisions
│   │           ├── deployment.py       (265 LOC) — deployment
│   │           ├── embedded.py         (148 LOC) — 7 routes, ALL MOCK
│   │           ├── enterprise_governance.py (339 LOC) — governance
│   │           ├── executive_center.py (404 LOC) — 12 routes, mixed
│   │           ├── exports.py          (345 LOC) — 10 routes, real DB
│   │           ├── financial.py        (247 LOC) — 6 routes, mixed
│   │           ├── forecasting.py      (654 LOC) — 12 routes, real DB
│   │           ├── intelligence.py     (903 LOC) — intelligence
│   │           ├── institutional_knowledge.py (781 LOC) — 12 routes, real DB
│   │           ├── learning.py         (350 LOC) — learning
│   │           ├── metric_studio.py    (247 LOC) — metric studio
│   │           ├── multi_currency.py   (350 LOC) — multi-currency
│   │           ├── nl_analytics.py     (153 LOC) — 7 routes, mixed
│   │           ├── outcomes.py         (308 LOC) — outcomes
│   │           ├── performance.py      (405 LOC) — 13 routes, mixed
│   │           ├── query_engine.py     (262 LOC) — 8 routes, ALL MOCK
│   │           ├── semantic_layer.py   (315 LOC) — semantic layer
│   │           ├── strategic_planning.py (630 LOC) — 13 routes, real DB
│   │           ├── vector_memory.py    (534 LOC) — 10 routes, real DB
│   │           ├── visualization.py    (294 LOC) — 8 routes, mixed
│   │           └── workspace.py        (235 LOC) — 9 routes, mixed
│   ├── domain/                    (42 modules, 28,572 LOC)
│   ├── infrastructure/            (22 files, 8,800 LOC)
│   ├── application/               (3 files, 582 LOC)
│   ├── core/                      (6 files, 292 LOC)
│   └── db/                        (3 files, 41 LOC)
├── alembic/versions/              (6 migrations)
├── scripts/
│   └── seed_hospital_data.py      (291 LOC)
└── tests/                         (1,145 passing)
```

---

## Route Registration Chain

```
main.py
├── api_router (prefix="/api/v1")
│   ├── auth.router        → /api/v1/auth
│   ├── kpi.router         → /api/v1/kpis
│   ├── insights.router    → /api/v1/insights
│   ├── forecasts.router   → /api/v1/forecasts
│   ├── scenarios.router   → /api/v1/scenarios
│   └── alerts.router      → /api/v1/alerts
├── v2_router (prefix="/api/v2")
│   └── 31 sub-routers     → /api/v2/*
├── GET /health
└── GET /health/detailed
```

---

## Backend Endpoint Classification

### REAL DB (all routes hit PostgreSQL)

| File | Routes | LOC |
|------|--------|-----|
| v1/auth.py | 4 | 367 |
| v1/alerts.py | 6 | 150 |
| v2/ai_cfo.py | 15 | 403 |
| v2/dashboards.py | 11 | 375 |
| v2/exports.py | 10 | 345 |
| v2/forecasting.py | 12 | 654 |
| v2/institutional_knowledge.py | 12 | 781 |
| v2/strategic_planning.py | 13 | 630 |
| v2/vector_memory.py | 10 | 534 |
| **Subtotal** | **93** | **4,239** |

### MIXED (some routes real DB, some mock/stub)

| File | Routes | LOC | Notes |
|------|--------|-----|-------|
| v2/analytics.py | 15 | 444 | 10 real, 3 stub, 2 hybrid |
| v2/collaboration.py | 15 | 293 | 7 real, 8 mock |
| v2/executive_center.py | 12 | 404 | 3 real, 9 domain service |
| v2/financial.py | 6 | 247 | 2 static, 2 DB, 2 domain |
| v2/governance.py | 12 | 360 | 4 real, 4 static, 4 echo |
| v2/nl_analytics.py | 7 | 153 | 2 static, 3 domain+DB, 2 pure DB |
| v2/performance.py | 13 | 405 | 3 real DB, 10 in-memory |
| v2/visualization.py | 8 | 294 | 4 real, 3 static, 1 echo |
| v2/workspace.py | 9 | 235 | 7 real, 2 mock |
| v1/kpi.py | 6 | 152 | engine-dependent |
| v1/forecasts.py | 4 | 85 | engine-dependent |
| v1/scenarios.py | 8 | 169 | mixed |
| v1/insights.py | 5 | 87 | engine-dependent |
| **Subtotal** | **120** | **3,328** |

### ALL MOCK (no DB, returns hardcoded data)

| File | Routes | LOC |
|------|--------|-----|
| v2/api.py | 38 | 828 |
| v2/query_engine.py | 8 | 262 |
| v2/embedded.py | 7 | 148 |
| **Subtotal** | **53** | **1,238** |

---

## Backend Domain Inventory (42 modules)

| Module | Lines | Key Classes |
|--------|-------|-------------|
| intelligence/ | 7,513 | IntelligenceArtifact, Insight, RootCause, Anomaly, Opportunity, Recommendation, Briefing, 9 services |
| bfl/ | 1,326 | FormulaLexer, FormulaParser, FormulaSQLGenerator, FunctionRegistry (51 functions) |
| causal_inference/ | 1,391 | CausalAnalysisEngine, 8 causal methods |
| copilot/ | 1,015 | AICFOCopilot, 8-step reasoning chain |
| decision/ | 1,158 | Decision, DecisionEvidence, DecisionOutcome, DecisionReview, DecisionTimeline |
| executive_center/ | 995 | ExecutiveCenterService, KPIs, alerts, decisions, forecasts |
| forecasting/ | 1,064 | ForecastingService, sklearn/statsmodels |
| strategic_planning/ | 803 | StrategicPlanningService, Monte Carlo, what-if |
| institutional_knowledge/ | 647 | InstitutionalKnowledgeService, knowledge graph |
| vector_memory/ | 597 | VectorMemoryStore, cosine similarity |
| financial/ | 671 | ReportingCurrencyEngine, FXService |
| performance/ | 684 | PerformanceService, L1/L2/L3 cache |
| metric_studio/ | 326 | MetricStudioService, approval workflows |
| semantic_layer/ | 262 | SemanticLayerService, Kimball dimensions |
| advanced_currency/ | 206 | AdvancedCurrencyService, consolidation |
| nl_analytics/ | 236 | NLProcessor, 9 intent types |
| deployment/ | 181 | DeploymentService, promotion paths |
| auth/ | 549 | PasswordService, TokenService, RBACService |
| analytics/ | 365 | SemanticMetric, SemanticQuery |
| multi_currency/ | 498 | MultiCurrencyService, intercompany |
| workspace/ | 350 | WorkspaceSection, ExecutiveBriefing |
| dashboard/ | 374 | DashboardWidget, Dashboard |
| governance/ | 279 | ContentCertification, AuditEntry |
| collaboration/ | 245 | Comment, CommentThread, Assignment |
| query_engine/ | 391 | SQLGenerator, QueryExecutor |
| embedded/ | 206 | EmbedToken, EmbeddedDashboard |
| export/ | 236 | ExportJob, ExportFormat |
| visualization/ | 411 | ChartSpec, VisualizationConfig |
| outcome/ | 820 | OutcomeDefinition, FeatureStore, ModelRegistry |
| knowledge_graph/ | 113 | ExtendedNodeType, GraphPath |
| learning/ | 91 | LearningMetric, RecommendationAccuracyTracker |
| memory/ | 82 | MemoryDocument, SemanticSearchService |
| causal/ | 76 | BeforeAfterResult, ITSResult |
| executive/ | 89 | ExecutiveProfile |
| repositories/ | 328 | BaseRepository, 10 interfaces |
| entities/ | 1,567 | TenantAwareEntity, DomainEvent, MetricDefinition, QualityRule |
| services/ | 1,060 | MetricRegistry, DependencyResolver, KPIComputationEngine |
| events/ | 0 | Empty |

---

## Database Inventory

### Alembic Migrations

| Migration | Tables Created | Date |
|-----------|---------------|------|
| 001_initial_schema | 22 | 2026-06-11 |
| 002_intelligence_engine | 8 | 2026-06-11 |
| 003_decision_intelligence | 5 | 2026-06-12 |
| 004_outcome_feature_model | 5 | 2026-06-12 |
| 005_financial_architecture | 4 | 2026-06-12 |
| 006_phase5_domains | 26 + pgvector | 2026-06-12 |
| **Total** | **~70 tables** | |

### ORM Models (53 classes)

**Tenant Hierarchy:** TenantModel, HospitalGroupModel, HospitalModel, BranchModel, DepartmentModel, UserModel, PayerModel, DoctorModel

**Metrics:** MetricDefinitionModel, MetricComputedValueModel

**Quality:** QualityRuleModel, QualityIssueModel, DataQualityScoreModel

**Lineage:** LineageNodeModel, LineageEdgeModel, LineageComputationRecordModel

**Events:** DomainEventModel, OutboxMessageModel, AuditLogModel

**Financial:** FinancialPeriodModel, RevenueModel, ExpenseModel, ClaimModel, OccupancyModel

**Intelligence:** IntelligenceInsightModel, IntelligenceRootCauseModel, IntelligenceAnomalyModel, IntelligenceOpportunityModel, IntelligenceRecommendationModel, IntelligenceBriefingModel, IntelligenceGraphNodeModel, IntelligenceRelationshipModel

**Decision:** DecisionModel, DecisionEvidenceModel, DecisionOutcomeModel, DecisionReviewModel, DecisionTimelineModel

**Outcome:** OutcomeDefinitionModel, OutcomeMeasurementModel, CausalImpactAnalysisModel, FeatureDefinitionModel, ModelArtifactModel

**Phase 5:** CFOProfileModel, CFOQuestionModel, CFOBriefingModel, CFOWorkspaceModel, CFOAlertConfigModel, CFOAlertModel, StrategicScenarioModel, StrategicDriverTreeModel, StrategicWhatIfModel, ForecastModelModel, ForecastResultModel, ForecastMonitoringAlertModel, MemoryRecordModel, KnowledgeNodeModel, KnowledgeEdgeModel, CurrencyEntityConfigModel, FXRateSnapshotModel, ExecutiveDecisionModel, CopilotConversationModel, CausalGraphModel, CausalEstimateModel, NLQueryLogModel, ExportJobModel, CollaborationCommentModel, SavedDashboardModel, VisualizationSpecModel, SemanticMetricV2Model, SemanticDimensionV2Model, MaterializedViewCacheModel

### Repository Classes (28 classes)

CFOProfileRepository, CFOQuestionRepository, CFOBriefingRepository, CFOWorkspaceRepository, CFOAlertRepository, StrategicScenarioRepository, StrategicDriverTreeRepository, StrategicWhatIfRepository, ForecastModelRepository, ForecastResultRepository, ForecastAlertRepository, MemoryRecordRepository, KnowledgeNodeRepository, KnowledgeEdgeRepository, CurrencyEntityConfigRepository, FXRateSnapshotRepository, ExecutiveDecisionRepository, CopilotConversationRepository, CausalGraphRepository, CausalEstimateRepository, NLQueryLogRepository, ExportJobRepository, CollaborationCommentRepository, DashboardRepository, VisualizationSpecRepository, SemanticMetricRepository, SemanticDimensionRepository, MaterializedViewCacheRepository

---

## Frontend Structure

```
frontend/src/
├── app/
│   ├── layout.tsx              (34 LOC) — Root layout
│   ├── page.tsx                (5 LOC) — Redirect → /dashboard
│   ├── dashboard/page.tsx      (279 LOC) — Main dashboard
│   ├── ... (38 pages total)
│   └── settings/page.tsx       (209 LOC) — Settings
├── components/
│   ├── layout/
│   │   └── dashboard-layout.tsx (283 LOC) — Sidebar nav
│   ├── kpi/
│   │   └── kpi-card.tsx        (65 LOC)
│   ├── ai/
│   │   └── ai-cfo-chat.tsx     (218 LOC)
│   ├── intelligence/           (6 components, ~3,215 LOC)
│   ├── decision/               (1 component, 359 LOC)
│   ├── outcome/                (3 components, ~680 LOC)
│   ├── knowledge-graph/        (1 component, 362 LOC)
│   ├── learning/               (1 component, 281 LOC)
│   ├── quality/                (1 component, 478 LOC) — unused
│   ├── metrics/                (1 component, 435 LOC) — unused
│   ├── lineage/                (1 component, 368 LOC) — unused
│   └── ui/                     (11 shadcn components)
└── lib/
    └── api/
        └── client.ts           (587 LOC) — 40+ API namespaces
```

---

## Frontend Page Inventory

| Route | File | LOC | Real API | Error Handling |
|-------|------|-----|----------|----------------|
| `/` | page.tsx | 5 | — | — |
| `/login` | login/page.tsx | 113 | ✅ | ✅ |
| `/register` | register/page.tsx | 246 | ✅ | ✅ |
| `/auth` | auth/page.tsx | 249 | ❌ MOCK | ❌ |
| `/dashboard` | dashboard/page.tsx | 279 | ✅ | ✅ |
| `/revenue` | revenue/page.tsx | 273 | ✅ | ✅ |
| `/insights` | insights/page.tsx | 345 | ✅ | ✅ |
| `/intelligence` | intelligence/page.tsx | 76 | Delegates | ❌ |
| `/forecasts` | forecasts/page.tsx | 287 | ✅ | ✅ |
| `/forecasting` | forecasting/page.tsx | 794 | ✅ | ✅ |
| `/scenarios` | scenarios/page.tsx | 446 | ✅ | ✅ |
| `/strategic` | strategic/page.tsx | 974 | ✅ | ✅ |
| `/alerts` | alerts/page.tsx | 259 | ✅ | ✅ |
| `/decisions` | decisions/page.tsx | 37 | Delegates | ❌ |
| `/analytics` | analytics/page.tsx | 760 | ✅ | ✅ |
| `/analytics/query` | analytics/query/page.tsx | 791 | ✅ | ✅ |
| `/dashboards` | dashboards/page.tsx | 609 | ✅ | ✅ |
| `/exports` | exports/page.tsx | 853 | ✅ | ✅ |
| `/collaboration` | collaboration/page.tsx | 989 | ✅ | ✅ |
| `/performance` | performance/page.tsx | 781 | ✅ | ✅ |
| `/copilot` | copilot/page.tsx | 817 | ✅ | ✅ |
| `/multi-currency` | multi-currency/page.tsx | 738 | ✅ | ✅ |
| `/currency` | currency/page.tsx | 315 | ✅ | ✅ |
| `/formulas` | formulas/page.tsx | 278 | ✅ | ✅ |
| `/executive-center` | executive-center/page.tsx | 957 | ✅ | ✅ |
| `/ai-cfo` | ai-cfo/page.tsx | 684 | ✅ | ✅ |
| `/causal` | causal/page.tsx | 867 | ✅ | ✅ |
| `/nl-query` | nl-query/page.tsx | 268 | ❌ MOCK | ❌ |
| `/embedded` | embedded/page.tsx | 509 | ✅ | ✅ |
| `/memory` | memory/page.tsx | 610 | ✅ | ✅ |
| `/knowledge-system` | knowledge-system/page.tsx | 1164 | ✅ | ✅ |
| `/knowledge-graph` | knowledge-graph/page.tsx | 11 | Delegates | ❌ |
| `/workspace` | workspace/page.tsx | 770 | ✅ | ✅ |
| `/governance` | governance/page.tsx | 623 | ✅ | ✅ |
| `/visualization` | visualization/page.tsx | 514 | ✅ | ✅ |
| `/deployments` | deployments/page.tsx | 383 | ✅ raw fetch | ✅ |
| `/semantic` | semantic/page.tsx | 325 | ✅ raw fetch | ✅ |
| `/metric-studio` | metric-studio/page.tsx | 194 | ✅ raw fetch | ✅ |
| `/settings` | settings/page.tsx | 209 | ❌ none | ❌ |
| `/learning` | learning/page.tsx | 11 | Delegates | ❌ |

---

## Frontend Anomalies Found

1. **3 pages bypass API client:** `deployments`, `semantic`, `metric-studio` use raw `fetch()` instead of `metricStudioAPI`, `deploymentAPI`, `semanticLayerAPI`
2. **3 pages are mock-only:** `auth` (hardcoded roles), `nl-query` (hardcoded queries), `settings` (no API calls)
3. **4 pages are thin wrappers:** `learning`, `knowledge-graph`, `intelligence`, `decisions` — delegate entirely to a single component
4. **3 components unused:** `quality-dashboard.tsx`, `metric-explorer.tsx`, `lineage-graph.tsx` — defined but never imported by any page
5. **No route-level layouts** — only root `layout.tsx`
6. **No contexts or hooks** — all state management local to each page
7. **No route-level error boundaries** — errors propagate to root
