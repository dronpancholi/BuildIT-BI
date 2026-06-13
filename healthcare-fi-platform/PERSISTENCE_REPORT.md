# PERSISTENCE REPORT

**ERP-1 Phase 6 — Database Reality Check**
**Date:** 2026-06-12

---

## Domain Persistence Classification

| # | Domain | Classification | Evidence |
|---|--------|---------------|----------|
| 1 | AI CFO | **PERSISTENT** | CFOProfileRepository + CFOBriefingRepository + get_db() auto-commit |
| 2 | Copilot | **PERSISTENT** | CopilotConversationRepository → CopilotConversationModel |
| 3 | Forecasts | **PERSISTENT** | ForecastModelRepository → ForecastModelModel + seed script |
| 4 | Memory | **PERSISTENT** | MemoryRecordRepository → MemoryRecordModel + seed script |
| 5 | Knowledge Graph | **PERSISTENT** | KnowledgeNodeRepository + KnowledgeEdgeRepository + seed script |
| 6 | Scenarios | **PERSISTENT** | ScenarioSimulator → db.add() + flush() → Scenario table |
| 7 | Executive Briefings | **TRANSIENT** | Generated on-the-fly, NOT persisted via CFOBriefingRepository |
| 8 | Decisions | **PERSISTENT** | DecisionRepository + 4 related repos → 5 tables |
| 9 | Intelligence | **TRANSIENT** | Computed on-the-fly from Revenue/Expense, never stored |
| 10 | Collaboration | **PERSISTENT** | CollaborationCommentRepository → CollaborationCommentModel |
| 11 | Exports | **PERSISTENT** | ExportJobRepository → ExportJobModel |
| 12 | Metrics | **TRANSIENT** | MetricStudioService uses in-memory dicts, no SQL persistence |
| 13 | Quality | **BROKEN** | No ORM models, no repositories, all endpoints return hardcoded [] |
| 14 | Financial | **PERSISTENT** | Revenue/Expense/Claim tables + FXRateSnapshotRepository |

---

## Critical Persistence Gaps

### Quality Domain — No Persistence Whatsoever
- No ORM models for QualityRule, QualityIssue, DataQualityScore
- No repositories for quality entities
- All quality endpoints return hardcoded `data=[]`
- Domain entities exist (`domain/entities/quality.py`) but are not backed by any storage

### Intelligence Domain — Computed, Never Stored
- Intelligence services compute insights/anomalies/recommendations on every request
- No ORM models to store computed intelligence
- Results are ephemeral — next request recomputes everything
- The `intelligence_insights` table exists in migration 002 but is never written to by endpoints

### Metric Studio — In-Memory Only
- `MetricStudioService` stores metrics in `self.metrics: dict[UUID, Metric] = {}`
- Module-level singleton `_service = MetricStudioService()` — data lost on restart
- Persistence repos exist (`SemanticMetricRepository`) but are NOT used by Metric Studio

### Executive Briefings — Generated, Not Saved
- `ExecutiveCenterService.generate_briefing()` creates `ExecutiveBriefing` dataclass in-memory
- Does NOT call `CFOBriefingRepository.create()` to persist
- Briefing content lost after response is sent
