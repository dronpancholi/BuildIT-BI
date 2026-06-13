# ERP-2 — PLATFORM RECOVERY & SYSTEM WIRING

**BuildIT Healthcare Financial Intelligence Platform**

**Authoritative Recovery Specification**

---

## MISSION

ERP-1 proved that BuildIT's primary problem is not missing features.

The primary problem is:

**Features exist.**
**Pages exist.**
**Routes exist.**
**Domains exist.**

But many are disconnected, miswired, stubbed, or using incorrect contracts.

ERP-2 exists to make the platform function.

No new modules.
No new domains.
No new AI features.
No new BI features.
No new dashboards.

Only recovery.
Only wiring.
Only integration.
Only operationalization.

---

## RULE 0

Before writing code, read and verify:

- `MASTER_DEFECT_REGISTRY.md`
- `PAGE_AUDIT_REPORT.md`
- `API_FORENSICS_REPORT.md`
- `DATA_FLOW_REPORT.md`
- `PERSISTENCE_REPORT.md`

Every defect fixed must reference its ERP-1 defect ID.

Nothing may be fixed without tracing to ERP-1.

---

## RECOVERY DOMAIN 1 — PLATFORM BLOCKERS (P0)

These are preventing large portions of the platform from functioning. Must be fixed first.

---

### DEFECT-001

**Intelligence Router Not Mounted**

ERP-1 discovered: `app/api/v2/endpoints/intelligence.py` exists. Routes exist. But router never mounted.

Result: 404 on every intelligence route.

Affected: Intelligence page, AI CFO, Executive Center, Learning, Knowledge Graph, Copilot.

Fix: `app/api/v2/endpoints/__init__.py` — add `include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])`

Verification: `GET /api/v2/intelligence/anomalies` returns 200 OK.

---

### DEFECT-002

**Dashboard Template URL Mismatch**

ERP-1 found: Frontend calls `/dashboards/templates/prebuilt`, backend route is `/dashboards/prebuilt/templates`.

Fix one side only. Do not create aliases.

Verification: New Dashboard → Template Selection → Works.

---

### DEFECT-003

**Missing Auth Header Usage**

ERP-1 found: 8 pages bypass API client with direct `fetch()`. No auth headers.

Fix all pages to use `src/lib/api/client.ts` only.

Affected pages: deployments, semantic, metric-studio, currency, formulas, copilot, nl-query, auth.

Verification: No direct backend URLs remain in any page file.

---

### DEFECT-004

**Hardcoded localhost**

Replace `http://localhost:8000` with environment configuration. Search entire repository. Zero occurrences allowed.

---

## RECOVERY DOMAIN 2 — FRONTEND ↔ BACKEND CONTRACT REPAIR

ERP-1 identified 9 contract mismatches. Fix every mismatch.

---

### Collaboration

Fix body vs query param mismatch, UUID mismatch, assignment schema mismatch.

All collaboration operations must work.

Verification: Create comment, create assignment, create watchlist, resolve comment — all persist.

---

### Metric Studio

ERP-1: Frontend sends `formula`, backend expects `formula_id`.

Repair.

---

### Memory

Repair: search API, create API, history API. Response contracts must match exactly.

---

### Embedded

Repair: token, url, embed_id contract mismatch.

---

### Analytics

Repair: query builder payload must match backend schema.

---

## RECOVERY DOMAIN 3 — PAGE FUNCTIONALITY RESTORATION

ERP-1 classified pages by status.

---

### Working Pages

Do not rewrite. Only regression test.

Pages: Dashboard, AI CFO, Forecasting, Alerts, Insights, Strategic, Executive Center, Workspace.

---

### Partially Working Pages

Restore to full functionality.

Pages: Intelligence, Learning, Knowledge Graph, Analytics, Collaboration, Memory, Visualization, Performance, Multi Currency, Governance.

Each page must:

| Test | Result Required |
|------|----------------|
| Load | No React errors |
| Fetch | 200 response |
| Render | Data visible |
| Create | Records can be created |
| Edit | Records editable |
| Delete | Records removable |
| Refresh | Changes persist |

---

### Broken Pages

Restore completely.

Pages: Embedded, Revenue, Settings, Query Builder.

---

## RECOVERY DOMAIN 4 — INTELLIGENCE SYSTEM RECOVERY

ERP-1 discovered: Router disconnected. Services exist. Data flow broken.

Verify entire pipeline:

```
Metric → Anomaly → Root Cause → Recommendation → Decision
```

Must work end-to-end.

Verification: Create anomaly → must appear in Intelligence, Executive Center, and AI CFO.

---

## RECOVERY DOMAIN 5 — METRIC STUDIO RECOVERY

ERP-1: Uses in-memory dictionaries. Not persistent.

Replace: `dict`, `list`, singleton state with repository.

Verify: Create metric → refresh page → metric still exists.

---

## RECOVERY DOMAIN 6 — QUALITY DOMAIN RECOVERY

ERP-1: No persistence layer.

Build:

- ORM models
- Repository
- CRUD endpoints

Verify: Quality rules survive restart.

---

## RECOVERY DOMAIN 7 — QUERY ENGINE RECOVERY

ERP-1: Query Engine mostly stubbed.

Must connect: Analytics, Metric Studio, Semantic Layer, BFL.

Verification: Query "Revenue by Department, Last 12 Months" → produces real SQL → executes → returns results.

---

## RECOVERY DOMAIN 8 — EMBEDDED ANALYTICS RECOVERY

ERP-1: Stub implementation.

Must support: Create Embed, Generate Token, Load Dashboard, Audit Access. All DB-backed.

---

## RECOVERY DOMAIN 9 — DATA FLOW RECOVERY

Validate all ERP-1 flows.

| Flow | Path | Verification |
|------|------|-------------|
| A | Metric → Dashboard → Widget → Visualization | Works |
| B | Anomaly → Recommendation → Decision | Works |
| C | Decision → Outcome → Learning | Works |
| D | Forecast → Strategic → Executive Center | Works |
| E | Knowledge Graph → Memory → Copilot | Works |

---

## RECOVERY DOMAIN 10 — UI STABILITY

Remove: White screens, empty pages, infinite spinners, full page crashes.

Every page must have:

| State | Requirement |
|-------|-------------|
| Loading | Skeleton |
| Empty | Useful message |
| Error | Retry |
| Success | Real content |

---

## RECOVERY DOMAIN 11 — SYSTEM-WIDE VERIFICATION

Run complete platform certification.

### Pages

All 38 pages. Test: Open, Refresh, Navigate.

### APIs

All routes. Target: 0 500 errors.

### Database

All repositories. All CRUD operations.

### Frontend

0 console errors.

### Build

`npm run build` passes. `pytest` passes.

---

## COMPLETION GATES

ERP-2 is complete only if:

| Gate | Requirement |
|------|-------------|
| Gate 1 | All P0 defects resolved |
| Gate 2 | All P1 defects resolved |
| Gate 3 | All 9 contract mismatches resolved |
| Gate 4 | All 38 pages load |
| Gate 5 | All major workflows execute |
| Gate 6 | No mock routes remain active |
| Gate 7 | Readiness Score 45.7% → 65%+ |

---

## FINAL DELIVERABLE

Generate: `ERP2_RECOVERY_REPORT.md`

Containing:

- Defect-by-defect fixes
- Before vs after
- API verification
- Page verification
- Workflow verification
- Remaining issues
- Updated readiness score

---

## EXECUTION ORDER

ERP-2 phases must execute in order:

```
Domain 1: Platform Blockers (P0)
    ↓
Domain 2: Contract Repair (P1)
    ↓
Domain 3: Page Restoration
    ↓
Domain 4: Intelligence Recovery
    ↓
Domain 5: Metric Studio Recovery
    ↓
Domain 6: Quality Recovery
    ↓
Domain 7: Query Engine Recovery
    ↓
Domain 8: Embedded Recovery
    ↓
Domain 9: Data Flow Recovery
    ↓
Domain 10: UI Stability
    ↓
Domain 11: System-Wide Verification
```

**Rationale:** P0 blockers must be fixed first because they affect multiple downstream features. Contract repair must come before page restoration because pages cannot function with wrong contracts. Intelligence recovery depends on the router being mounted (Domain 1). Quality and Query Engine recovery can proceed independently but require persistence layers that must be verified.

---

## VIOLATIONS

If at any point during ERP-2 the AI:

- Creates a new domain module
- Creates a new feature
- Redesigns a UI
- Adds new dependencies
- Modifies database schema beyond what's needed for persistence

**The ERP-2 run is contaminated.**

ERP-2 is recovery and wiring. Nothing else.

---

## TRANSITION TO ERP-3

Only after ERP-2 is complete should ERP-3 begin.

ERP-3 should focus on:

- Quality-of-life improvements
- Performance optimization
- Advanced analytics
- Executive UX polish

But only after the platform is operational.

A beautiful platform that doesn't work is worthless.
An ugly platform that works is valuable.
