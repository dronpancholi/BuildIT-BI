# COMPONENT HEALTH REPORT

**ERP-1 Phase 3 — Component Forensics**
**Date:** 2026-06-12

---

## Summary

| Status | Count |
|--------|-------|
| USED | 15 |
| UNUSED (dead) | 3 |
| BROKEN | 0 |

---

## Used Components (15)

| # | Component | File | LOC | Pages | Mock Data | Issues |
|---|-----------|------|-----|-------|-----------|--------|
| 1 | DashboardLayout | layout/dashboard-layout.tsx | 283 | 33 pages | None | Hardcoded `localhost:8000` |
| 2 | KPICard | kpi/kpi-card.tsx | 65 | dashboard, revenue | None | Clean |
| 3 | AICFOChat | ai/ai-cfo-chat.tsx | 218 | insights | **YES** — fake AI responses, random confidence | No real API call |
| 4 | IntelligenceFeed | intelligence/intelligence-feed.tsx | 633 | intelligence | Fallback sparkline | Good error handling |
| 5 | AnomalyCenter | intelligence/anomaly-center.tsx | 475 | intelligence | Fallback sparkline | Good error handling |
| 6 | OpportunityCenter | intelligence/opportunity-center.tsx | 513 | intelligence | None | Clean |
| 7 | RecommendationCenter | intelligence/recommendation-center.tsx | 576 | intelligence | None | Approve/reject uses GET not PUT |
| 8 | BriefingLibrary | intelligence/briefing-library.tsx | 489 | intelligence | None | Dead dialog code |
| 9 | IntelligenceGraphExplorer | intelligence/graph-explorer.tsx | 229 | intelligence, knowledge-graph | None | Raw HTML select, basic SVG |
| 10 | DecisionCenter | decision/decision-center.tsx | 359 | decisions | **YES** — hardcoded UUIDs | Console-only errors |
| 11 | OutcomeCenter | outcome/outcome-center.tsx | 240 | decisions | None | Unused state variable |
| 12 | FeatureCatalog | outcome/feature-catalog.tsx | 226 | decisions | None | Console-only errors |
| 13 | ModelRegistry | outcome/model-registry.tsx | 214 | decisions | None | Console-only errors |
| 14 | KnowledgeGraphExplorer | knowledge-graph/knowledge-graph-explorer.tsx | 362 | knowledge-graph | None | Basic SVG graph |
| 15 | LearningDashboard | learning/learning-dashboard.tsx | 281 | learning | None | Raw JSON.stringify output |

---

## Unused Components (3) — DEAD CODE

| # | Component | File | LOC | Issue |
|---|-----------|------|-----|-------|
| 1 | QualityDashboard | quality/quality-dashboard.tsx | 478 | Never imported by any page. Uses `api.get()` directly. |
| 2 | MetricExplorer | metrics/metric-explorer.tsx | 435 | Never imported by any page. Division by zero risk. |
| 3 | LineageGraph | lineage/lineage-graph.tsx | 368 | Never imported by any page. Raw HTML table. |

---

## Critical Component Issues

1. **AICFOChat is completely fake** — `generateAIResponse()` returns hardcoded strings, confidence is `0.85 + Math.random() * 0.15`
2. **DecisionCenter uses hardcoded UUIDs** — `owner_id` and `created_by` set to `"00000000-0000-0000-0000-000000000000"`
3. **RecommendationCenter wrong HTTP method** — approve/reject calls GET instead of PUT/PATCH
4. **DashboardLayout hardcoded URL** — `http://localhost:8000` on line 149
5. **3 dead components** — 1,281 lines of unused code
6. **Console-only error handling** — Most components catch errors but only `console.error()` them
