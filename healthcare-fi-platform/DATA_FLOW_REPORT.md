# DATA FLOW REPORT

**ERP-1 Phase 5 — Data Flow Trace**
**Date:** 2026-06-12

---

## Feature Classification

| # | Feature | Status | Evidence |
|---|---------|--------|----------|
| 1 | Dashboard KPIs | **COMPLETE** | kpiAPI → v1/kpis → KPIEngine(db) → Revenue/Expense tables |
| 2 | Forecasts | **COMPLETE** | forecastsAPI → v1/forecasts → ForecastingEngine(db) → DB |
| 3 | Scenarios | **COMPLETE** | scenariosAPI → v1/scenarios → ScenarioSimulator(db) → Scenario table |
| 4 | Decision Intelligence | **COMPLETE** | decisionsAPI → v2/decisions → DecisionService + repos → 5 tables |
| 5 | Knowledge Graph | **COMPLETE** | knowledgeAPI → v2/knowledge → InstitutionalKnowledgeService + repos → knowledge_nodes/edges |
| 6 | Learning Engine | **FAKE** | learningAPI → v2/learning → returns empty stubs |
| 7 | Collaboration | **COMPLETE** | collaborationAPI → v2/collaboration → CollaborationCommentRepository → DB |
| 8 | Exports | **COMPLETE** | exportsAPI → v2/exports → ExportJobRepository → DB |
| 9 | NL Query | **PARTIAL** | nlAnalyticsAPI → v2/nl → NLProcessor (in-memory, no persistence) |
| 10 | AI CFO | **COMPLETE** | aiCfoAPI → v2/ai-cfo → CFOCoreService + repos → 5 tables |
| 11 | Copilot | **COMPLETE** | copilotAPI → v2/copilot → AICFOCopilot + repos → DB |
| 12 | Currency | **PARTIAL** | Raw fetch → v2/multi-currency → MultiCurrencyService (in-memory) |
| 13 | Analytics | **COMPLETE** | analyticsAPI → v2/analytics → SemanticMetricRepository → DB |
| 14 | Governance | **COMPLETE** | governanceAPI → v2/governance → DashboardRepository → DB |

---

## Broken Chains

| Feature | Break Point | Impact |
|---------|-------------|--------|
| Learning | Backend returns empty stubs | All learning data is fake |
| NL Query | NLProcessor in-memory, no DB | Conversations lost on restart |
| Currency | In-memory service, direct fetch bypass | Data lost, no auth headers |
