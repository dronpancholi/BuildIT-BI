# PlatformReadinessMatrix — BuildIT Healthcare Financial Intelligence Platform
# Generated: Phase 5.5 Step 1 Audit

## Backend Endpoint Audit

```
Module                    | Backend Status     | Frontend Status    | DB Persistence | Workflows Supported          | Priority Fix
--------------------------|--------------------|--------------------|----------------|------------------------------|-------------
v1/alerts.py              | FULLY_WORKING      | PARTIALLY_WORKING  | ✅ Real DB     | Alert CRUD                   | -
v1/auth.py                | FULLY_WORKING      | FULLY_WORKING      | ✅ Real DB     | Auth flow                    | -
v1/forecasts.py           | FULLY_WORKING      | PARTIALLY_WORKING  | ✅ Real DB     | Forecast create/read         | -
v1/insights.py            | FULLY_WORKING      | PARTIALLY_WORKING  | ✅ Real DB     | Insight generation           | -
v1/kpi.py                 | FULLY_WORKING      | PARTIALLY_WORKING  | ✅ Real DB     | KPI computation              | -
v1/scenarios.py           | FULLY_WORKING      | PARTIALLY_WORKING  | ✅ Real DB     | Scenario save/read           | -
v2/ai_cfo.py              | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Profile, Q&A, Briefing       | HIGH — needs migration 006
v2/analytics.py           | MOCK_DATA          | FULLY_WORKING      | ❌ No DB       | Metrics CRUD, Query exec     | HIGH — replace mocks
v2/api.py                 | MOCK_DATA          | (master stubs)     | ❌ No DB       | API health                   | MEDIUM — stubs only
v2/advanced_currency.py   | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | FX rates, conversion         | HIGH — needs migration 006
v2/bfl.py                 | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Formula parse/validate/SQL   | HIGH — needs migration 006
v2/causal_inference.py    | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Causal analysis              | MEDIUM — stateless compute
v2/collaboration.py       | MOCK_DATA          | FULLY_WORKING      | ❌ No DB       | Comments, threads            | HIGH — replace mocks
v2/copilot.py             | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | NL copilot                   | HIGH — needs migration 006
v2/dashboards.py          | MOCK_DATA          | FULLY_WORKING      | ❌ No DB       | Dashboard CRUD               | HIGH — replace mocks
v2/decisions.py           | FULLY_WORKING      | PARTIALLY_WORKING  | ✅ Real DB     | Decision lifecycle           | LOW — already works
v2/deployment.py          | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Env/promotion                | HIGH — needs migration 006
v2/embedded.py            | MOCK_DATA          | FULLY_WORKING      | ❌ No DB       | Embedded analytics           | HIGH — replace mocks
v2/enterprise_governance.py| IN_MEMORY_ONLY    | FULLY_WORKING      | ❌ No DB       | Governance lifecycle         | HIGH — needs migration 006
v2/executive_center.py    | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Executive briefing           | HIGH — needs migration 006
v2/exports.py             | MOCK_DATA          | FULLY_WORKING      | ❌ No DB       | Export jobs                  | HIGH — replace mocks
v2/financial.py           | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Currency/FX                  | HIGH — needs migration 006
v2/forecasting.py         | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Forecast model/train/predict | HIGH — needs migration 006
v2/governance.py          | MOCK_DATA          | FULLY_WORKING      | ❌ No DB       | Dashboard versioning         | HIGH — replace mocks
v2/institutional_knowledge.py| IN_MEMORY_ONLY | FULLY_WORKING      | ❌ No DB       | Knowledge graph              | HIGH — needs migration 006
v2/intelligence.py        | PARTIALLY_WORKING  | FULLY_WORKING      | ⚠️ Partial     | Intelligence analysis        | HIGH — wire to DB tables
v2/learning.py            | PARTIALLY_WORKING  | PARTIALLY_WORKING  | ⚠️ Partial     | Learning metrics             | HIGH — wire to DB tables
v2/metric_studio.py       | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Metric lifecycle             | HIGH — needs migration 006
v2/multi_currency.py      | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Multi-currency consolidation | HIGH — needs migration 006
v2/nl_analytics.py        | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | NL query processing          | HIGH — needs migration 006
v2/outcomes.py            | FULLY_WORKING      | PARTIALLY_WORKING  | ✅ Real DB     | Outcome/feature/model        | LOW — already works
v2/performance.py         | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Cache, tasks, MVs            | HIGH — needs migration 006
v2/query_engine.py        | MOCK_DATA          | (no frontend)      | ❌ No DB       | Semantic → SQL               | HIGH — replace mocks
v2/semantic_layer.py      | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Semantic dimensions          | HIGH — needs migration 006
v2/strategic_planning.py  | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Scenarios, Monte Carlo       | HIGH — needs migration 006
v2/vector_memory.py       | IN_MEMORY_ONLY     | FULLY_WORKING      | ❌ No DB       | Vector memory, clustering    | HIGH — needs migration 006
v2/visualization.py       | MOCK_DATA          | FULLY_WORKING      | ❌ No DB       | Chart types, rendering       | HIGH — replace mocks
v2/workspace.py           | MOCK_DATA          | FULLY_WORKING      | ❌ No DB       | Workspace, briefings         | HIGH — replace mocks
```

## Summary Statistics

| Status | Count | Endpoints |
|--------|-------|-----------|
| FULLY_WORKING | 8 | v1/* (6), v2/decisions, v2/outcomes |
| PARTIALLY_WORKING | 2 | v2/intelligence, v2/learning |
| MOCK_DATA | 11 | v2/analytics, v2/api, v2/collaboration, v2/dashboards, v2/embedded, v2/exports, v2/governance, v2/query_engine, v2/visualization, v2/workspace |
| IN_MEMORY_ONLY | 19 | v2/ai_cfo, v2/advanced_currency, v2/bfl, v2/causal_inference, v2/copilot, v2/deployment, v2/enterprise_governance, v2/executive_center, v2/financial, v2/forecasting, v2/institutional_knowledge, v2/metric_studio, v2/multi_currency, v2/nl_analytics, v2/performance, v2/semantic_layer, v2/strategic_planning, v2/vector_memory |

## Frontend Page Audit

| Status | Count | Pages |
|--------|-------|-------|
| FULLY_WORKING | 27 | dashboard, intelligence, analytics, dashboards, nl-query, exports, collaboration, workspace, governance, embedded, visualization, alerts, formulas, metric-studio, semantic, deployments, currency, ai-cfo, causal, strategic, forecasting, memory, knowledge-system, multi-currency, performance, executive-center, copilot |
| PARTIALLY_WORKING | 7 | revenue, insights, forecasts, scenarios, decisions, learning, knowledge-graph |
| FRONTEND_DISCONNECTED | 2 | settings, auth |

## Domain Module Audit

| Module | @dataclass | ORM Models | Repository | Alembic | Persistence |
|--------|:----------:|:----------:|:----------:|:-------:|:-----------:|
| advanced_currency | Yes | No | No | No | IN_MEMORY |
| ai_cfo | Yes | No | No | No | IN_MEMORY |
| analytics | Yes | No | No | No | IN_MEMORY |
| bfl | Yes | No | No | No | IN_MEMORY |
| causal_inference | Yes | No | No | No | IN_MEMORY (stateless) |
| collaboration | Yes | No | No | No | IN_MEMORY |
| copilot | Yes | No | No | No | IN_MEMORY |
| dashboard | Yes | No | No | No | IN_MEMORY |
| decision | Yes | No | No | No | IN_MEMORY (v2 has real DB repos) |
| deployment | Yes | No | No | No | IN_MEMORY |
| embedded | Yes | No | No | No | IN_MEMORY |
| enterprise_governance | Yes | No | No | No | IN_MEMORY |
| executive | Yes | No | No | No | IN_MEMORY |
| executive_center | Yes | No | No | No | IN_MEMORY |
| export | Yes | No | No | No | IN_MEMORY |
| financial | Yes | No | No | No | IN_MEMORY |
| forecasting | Yes | No | No | No | IN_MEMORY |
| governance | Yes | No | No | No | IN_MEMORY |
| institutional_knowledge | Yes | No | No | No | IN_MEMORY |
| intelligence | Yes | No | Abstract | No | IN_MEMORY (DB tables exist from 002) |
| knowledge_graph | Yes | No | No | No | IN_MEMORY |
| learning | Yes | No | No | No | IN_MEMORY |
| memory | Yes | No | No | No | IN_MEMORY |
| metric_studio | Yes | No | No | No | IN_MEMORY |
| multi_currency | Yes | No | No | No | IN_MEMORY |
| nl_analytics | Yes | No | No | No | IN_MEMORY |
| outcome | Yes | No | Abstract | No | IN_MEMORY (DB tables exist from 004) |
| performance | Yes | No | No | No | IN_MEMORY |
| query_engine | Yes | No | No | No | IN_MEMORY |
| repositories | Yes | No | **Interfaces** | No | ABSTRACT |
| semantic_layer | Yes | No | No | No | IN_MEMORY |
| services | Yes | No | No | No | IN_MEMORY |
| strategic_planning | Yes | No | No | No | IN_MEMORY |
| vector_memory | Yes | No | No | No | IN_MEMORY |
| visualization | Yes | No | No | No | IN_MEMORY |
| workflows | No | No | No | No | IN_MEMORY |
| workspace | Yes | No | No | No | IN_MEMORY |

## Alembic Migrations

| Migration | Tables Created |
|-----------|----------------|
| 001_initial_schema | tenants, users, hospitals, branches, departments, payers, doctors, metric_definitions, metric_computed_values, data_sources, quality_rules, quality_issues, data_quality_scores, lineage_*, domain_events, outbox_events, import_*, workflow_executions, audit_logs, notifications, system_config (~26 tables) |
| 002_intelligence_engine | intelligence_insights, intelligence_root_causes, intelligence_anomalies, intelligence_opportunities, intelligence_recommendations, intelligence_briefings, intelligence_graph_nodes, intelligence_relationships (8 tables) |
| 003_decision_intelligence | decisions, decision_evidence, decision_outcomes, decision_reviews, decision_timeline (5 tables) |
| 004_outcome_feature_model | outcome_definitions, outcome_measurements, causal_impact_analyses, feature_definitions, model_artifacts (5 tables) |
| 005_financial_architecture | currencies, exchange_rates, tenant_currency_config, monetary_amounts (4 tables) |

**Total existing tables: ~48. No tables for any Phase 5 domain.**

## Critical Gaps

1. **19 IN_MEMORY_ONLY domains** need DB persistence (migration 006)
2. **11 MOCK_DATA endpoints** need real DB queries
3. **2 PARTIALLY_WORKING endpoints** (intelligence, learning) need DB wiring
4. **Zero ORM models** in domain layer — all @dataclass only
5. **Zero repository implementations** — only abstract interfaces
6. **No LLM integration** — copilot/AI CFO return templated responses
7. **No seed data** — no hospital simulation data exists
8. **No Redis caching** on any endpoint
9. **No pgvector** extension — memory semantic search uses in-memory FAISS
10. **4 frontend pages use raw fetch** instead of API client
