# ERP-1 — PLATFORM FORENSICS, TRUTH DISCOVERY & DEFECT REGISTRY

**BuildIT Healthcare Financial Intelligence Platform**

**Authoritative Emergency Recovery Phase Specification**

---

## MISSION

Stop all feature development.
Stop all enhancements.
Stop all optimization.
Stop all AI improvements.
Stop all UI redesign.

ERP-1 exists for one purpose:

**Discover the actual state of the platform.**

Not the intended state.
Not the documented state.
Not the architectural state.

The actual state.

---

## HARD RULES

During ERP-1:

```
NO CODE FIXES
NO REFACTORING
NO NEW FEATURES
NO UI REDESIGN
NO DATABASE CHANGES
NO MIGRATIONS
NO PACKAGE INSTALLS
```

The system may only:

```
READ
ANALYZE
TRACE
VERIFY
DOCUMENT
```

Nothing else.

---

## PRIMARY OBJECTIVE

Produce a complete **platform truth map**.

Answer:

| Question | Purpose |
|----------|---------|
| What works? | Verified, tested, real |
| What partially works? | Works sometimes, or under certain conditions |
| What is fake? | Returns hardcoded/mock data pretending to be real |
| What is disconnected? | Frontend calls something that doesn't exist |
| What is broken? | Errors, crashes, wrong results |
| What crashes? | Runtime exceptions, unhandled errors |
| What never executes? | Dead code paths, unreachable routes |
| What nobody uses? | Components or pages with no users |
| What survives restart? | Actually persisted to database |
| What loses data? | In-memory only, disappears on restart |

---

## PHASE 1 — COMPLETE SOURCE CODE INVENTORY

Scan entire repository.

Generate: **SYSTEM_INVENTORY.md**

### Backend Inventory

Catalog:

- All endpoint files
- All routers
- All services
- All repositories
- All domain modules
- All migrations
- All ORM models
- All background jobs
- All Celery tasks
- All Temporal workflows
- All caches
- All middleware

For each:

| Field | Description |
|-------|-------------|
| Name | Identifier |
| Path | File location |
| Purpose | What it does |
| Dependencies | What it imports |
| Lines of code | LOC count |
| Last modification | Git timestamp |

### Frontend Inventory

Catalog:

- All pages
- All layouts
- All components
- All hooks
- All contexts
- All API clients
- All utility modules

For each:

| Field | Description |
|-------|-------------|
| Path | File location |
| Purpose | What it renders |
| Dependencies | What it imports |
| Imports | External packages |
| Lines of code | LOC count |

### Database Inventory

Inspect:

- PostgreSQL
- Redis
- DuckDB
- Vector Store (pgvector)

Generate:

- Table list (name, schema, row count estimate)
- Index list (name, type, columns)
- Constraint list (type, columns)
- Foreign keys (source → target)
- Materialized views (if any)
- Table sizes

---

## PHASE 2 — PAGE-BY-PAGE FUNCTIONAL AUDIT

Audit **every page**. All 36+ pages.

For each page:

| Field | Description |
|-------|-------------|
| Route | URL path |
| Purpose | What user sees |
| Components rendered | React component tree |
| APIs called | Backend endpoints hit |
| Data dependencies | What must exist for page to work |

### Status Assignment

| Status | Meaning |
|--------|---------|
| WORKING | Fully operational end-to-end |
| PARTIAL | Mostly works, some gaps |
| BROKEN | Errors occur during normal use |
| CRITICAL | Page unusable, cannot render or crashes |
| FAKE | Shows data but not real (hardcoded/mock) |
| DISCONNECTED | No backend connection, frontend-only shell |

### Test Battery Per Page

**Load Test** — Can page load?

| Result | Meaning |
|--------|---------|
| PASS | Page loads without error |
| FAIL | Page fails to load |

**Render Test** — Can page render?

| Result | Meaning |
|--------|---------|
| PASS | Page renders correctly |
| FAIL | Blank page, error boundary, or crash |

**Data Test** — Real data?

| Result | Meaning |
|--------|---------|
| REAL | Data comes from database via API |
| MOCK | Data is hardcoded or generated client-side |
| EMPTY | API returns empty/no data |

**Interaction Test** — Interactive elements work?

Test:

- Buttons → do they trigger actions?
- Dialogs → do they open/close?
- Forms → do they submit?
- Filters → do they filter?
- Search → does search return results?
- Pagination → does paging work?
- Sorting → does sort order change?
- Tabs → do tabs switch content?

**API Test** — Backend connectivity?

| Step | Verification |
|------|-------------|
| Request sent | Network tab shows outbound call |
| Response received | 2xx or error code returned |
| Data rendered | Response data appears in UI |

---

## PHASE 3 — COMPONENT FORENSICS

Audit every reusable component.

Examples:

- Dashboard cards
- Charts
- Metric widgets
- Decision Center
- Outcome Center
- Knowledge Graph
- Sidebar
- Dialogs
- Forms
- Tables
- Loading skeletons
- Error boundaries
- Empty states

Determine:

| Status | Meaning |
|--------|---------|
| USED | Actively imported by pages |
| UNUSED | Defined but never imported |
| BROKEN | Imported but throws errors |
| DUPLICATED | Same component in multiple files |

Generate: **COMPONENT_HEALTH_REPORT.md**

---

## PHASE 4 — API FORENSICS

Audit **all 413 routes**. Not sample routes. All routes.

For each endpoint:

| Field | Description |
|-------|-------------|
| Method | GET/POST/PUT/DELETE |
| Path | /api/v2/... |
| File | Source file location |
| Handler | Function name |
| Dependencies | Services/repos injected |

### Verification Checklist

**Registration** — Is route mounted on FastAPI router?

| Result | Meaning |
|--------|---------|
| YES | Route is in router.include_router() |
| NO | Route defined but never registered |

**Runtime** — What does endpoint actually return?

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request |
| 401 | Unauthorized |
| 404 | Not found |
| 422 | Validation error |
| 500 | Server error |

**Database** — Does endpoint hit DB?

| Result | Meaning |
|--------|---------|
| YES | Executes SQL queries |
| NO | Returns static/hardcoded data |

**Real Data** — What does endpoint return?

| Result | Meaning |
|--------|---------|
| REAL | Data from database |
| MOCK | Hardcoded or generated data |
| STATIC | Fixed response, never changes |

**Frontend Usage** — Which pages call this endpoint?

List page names and component names that import/use this endpoint.

**Dead Routes** — Identify endpoints that are:

- Never called by any frontend code
- Never referenced in any component
- Defined but unused

Generate: **API_FORENSICS_REPORT.md**

---

## PHASE 5 — DATA FLOW TRACE

Trace every major feature. Not page — **feature**.

For each feature, trace the complete path:

```
UI Component
    ↓
API Client call
    ↓
Backend Endpoint
    ↓
Service Layer
    ↓
Repository/Domain
    ↓
Database Query
    ↓
Return Path
    ↓
UI Render
```

### Features to Trace

| Feature | Scope |
|---------|-------|
| Dashboard | KPI cards, charts, alerts, time range |
| Metrics | CRUD, computation, quality scoring |
| Forecasts | Create, compute, view, compare |
| Scenarios | Build, compare, Monte Carlo |
| Decisions | Create, track, outcome, review |
| Learning | Outcomes, feature store, model registry |
| Knowledge Graph | Nodes, edges, paths, exploration |
| AI CFO | Briefings, questions, recommendations |
| Copilot | NL query, reasoning chain, suggestions |
| Collaboration | Comments, threads, assignments |
| Exports | Generate, download, schedule |
| Currency | Rates, conversion, consolidation |
| Governance | Rules, certification, audit |
| Analytics | Semantic queries, insights, anomalies |

### Classification

| Status | Meaning |
|--------|---------|
| COMPLETE | Full round-trip, real data, working |
| PARTIAL | Some steps work, gaps exist |
| BROKEN | Chain interrupted at some point |
| FAKE | Returns mock/hardcoded data somewhere in chain |

Generate: **DATA_FLOW_REPORT.md**

---

## PHASE 6 — DATABASE REALITY CHECK

Audit actual persistence.

### Persistence Test Per Domain

For every domain that claims to store data:

```
1. Create record via API
2. Restart backend (kill + start)
3. Read record via API
4. Compare: does it survive?
```

### Classification

| Status | Meaning |
|--------|---------|
| Persistent | Survives restart, stored in PostgreSQL |
| Transient | In-memory only, lost on restart |
| Broken | Should persist but doesn't |

### Special Attention Domains

These are high-risk because they involve complex data:

- AI CFO (briefings, alerts, recommendations)
- Copilot (conversations, context)
- Forecasts (forecast values, model state)
- Memory (executive behavior, preferences)
- Knowledge Graph (nodes, edges, paths)
- Scenarios (scenario configs, results)
- Executive Briefings (generated content, delivery state)

Generate: **PERSISTENCE_REPORT.md**

---

## PHASE 7 — UI/UX FORENSICS

Audit every visible page.

### Layout Audit

| Check | Description |
|-------|-------------|
| Overflow | Content overflows container |
| Alignment | Elements misaligned |
| Spacing | Inconsistent padding/margins |
| Responsive | Breaks on different screen sizes |

### CSS Audit

| Check | Description |
|-------|-------------|
| Broken classes | Tailwind classes that don't resolve |
| Missing styles | Intended styles not applied |
| Wrong colors | Colors don't match design system |
| Tailwind issues | Invalid or deprecated classes |

### Navigation Audit

| Check | Description |
|-------|-------------|
| Dead links | Sidebar links to nonexistent pages |
| Duplicate links | Same destination in multiple places |
| Confusing structure | Illogical grouping or ordering |

### Visual Quality Score

Score each page 1-10 for:

| Dimension | Description |
|-----------|-------------|
| Executive appearance | Looks like enterprise software |
| Professional appearance | Polished, not prototype |
| Consistency | Same patterns across all pages |

Generate: **UI_FORENSICS_REPORT.md**

---

## PHASE 8 — EXECUTIVE WALKTHROUGH

Pretend user is **Dr. Darshan Shukla**.

Not developer.
Not engineer.

Hospital executive.

### Walkthrough Scope

Walk through as executive, not developer:

| Page | Executive Question |
|------|--------------------|
| Dashboard | "Can I see hospital performance at a glance?" |
| Executive Center | "Can I make strategic decisions from this?" |
| AI CFO | "Can I ask a financial question and get a real answer?" |
| Forecasting | "Can I see where revenue is heading?" |
| Decisions | "Can I track if our decisions are working?" |
| Knowledge Graph | "Can I understand how everything connects?" |
| Strategic Planning | "Can I plan scenarios for next year?" |

### Evaluation Questions

| Question | What It Tests |
|----------|---------------|
| Can he understand it? | Clarity, labels, language |
| Can he use it? | Intuitive, no training needed |
| Can he trust it? | Data feels real, not mock |
| Can he make a decision from it? | Actionable insights, not just charts |

Generate: **EXECUTIVE_READINESS_REPORT.md**

---

## PHASE 9 — DEFECT REGISTRY

This is ERP-1's most important output.

Create: **MASTER_DEFECT_REGISTRY.md**

### Defect Entry Format

```
DEFECT-{NNN}

Title:        [Short description]
Severity:     [P0/P1/P2/P3]
Category:     [Backend/Frontend/Database/API/UX/Integration]
File:         [Exact file path]
Page:         [Page route or N/A]
Component:    [Component name or N/A]
Root Cause:   [Why it happens]
Reproduction: [Step-by-step to trigger]
Impact:       [What user experiences]
Fix Effort:   [S/M/L/XL]
Dependencies: [Other defects that must be fixed first]
```

### Severity Levels

**P0 — Platform Unusable**

| Example | Impact |
|---------|--------|
| Page crash (white screen) | User cannot access feature |
| 500 errors on core flows | Feature completely broken |
| Data corruption | Trust destroyed |

**P1 — Major Functionality Broken**

| Example | Impact |
|---------|--------|
| Cannot save forecast | Core feature unusable |
| Cannot create decision | Workflow blocked |
| API returns wrong data | Silent failure, wrong results |

**P2 — Works Incorrectly**

| Example | Impact |
|---------|--------|
| Wrong chart type | Misleading visualization |
| Bad filtering | Cannot find data |
| Slow response | Poor experience |

**P3 — UX Issues**

| Example | Impact |
|---------|--------|
| Sidebar spacing | Cosmetic |
| Color inconsistency | Minor polish |
| Missing tooltip | Guidance gap |

### Dependencies

Some defects cannot be fixed until others are:

```
DEFECT-001 (P0) ← blocks DEFECT-015 (P1)
DEFECT-002 (P0) ← blocks DEFECT-016 (P1)
DEFECT-003 (P1) ← blocks DEFECT-020 (P2)
```

ERP-2 must respect this dependency graph.

---

## PHASE 10 — PLATFORM READINESS SCORE

Score each area 0-100.

| Area | Score |
|------|-------|
| Frontend | |
| Backend | |
| Database | |
| APIs | |
| Dashboards | |
| Analytics | |
| Intelligence | |
| AI CFO | |
| Forecasting | |
| Knowledge Graph | |
| Collaboration | |
| Governance | |
| Performance | |
| UX | |

### Scoring Rubric

| Score | Meaning |
|-------|---------|
| 0-20 | Non-functional or fake |
| 21-40 | Severely broken, major gaps |
| 41-60 | Partially working, significant issues |
| 61-80 | Mostly working, minor issues |
| 81-100 | Production-ready |

### Overall Readiness

```
Overall Readiness % = Sum of area scores / (14 areas × 100) × 100
```

Generate: **PLATFORM_READINESS_SCORECARD.md**

---

## FINAL DELIVERABLES

ERP-1 must produce:

| # | Document | Content |
|---|----------|---------|
| 1 | `SYSTEM_INVENTORY.md` | Complete file/function catalog |
| 2 | `PAGE_AUDIT_REPORT.md` | Every page tested and classified |
| 3 | `COMPONENT_HEALTH_REPORT.md` | Every component audited |
| 4 | `API_FORENSICS_REPORT.md` | All 413 routes verified |
| 5 | `DATA_FLOW_REPORT.md` | 14 feature chains traced |
| 6 | `PERSISTENCE_REPORT.md` | Database reality verified |
| 7 | `UI_FORENSICS_REPORT.md` | Visual quality assessed |
| 8 | `EXECUTIVE_READINESS_REPORT.md` | Executive perspective |
| 9 | `MASTER_DEFECT_REGISTRY.md` | Every defect cataloged |
| 10 | `PLATFORM_READINESS_SCORECARD.md` | Scores and verdict |

---

## SUCCESS CRITERIA

ERP-1 is complete **only when**:

- [ ] 100% of pages audited
- [ ] 100% of endpoints audited
- [ ] 100% of components audited
- [ ] 100% of workflows traced
- [ ] 100% of persistence verified
- [ ] 100% of defects cataloged

And the team can answer, **with evidence**:

| Question | Answer Source |
|----------|---------------|
| What exactly is broken? | MASTER_DEFECT_REGISTRY.md |
| Why is it broken? | Root Cause field in each defect |
| How severe is it? | P0/P1/P2/P3 classification |
| What must be fixed first? | Dependency graph in registry |
| How many total defects remain? | Count in scorecard |

---

## TRANSITION TO ERP-2

Only after ERP-1 is complete should ERP-2 begin.

ERP-2 must be driven **entirely** by the P0 and P1 defects discovered in ERP-1.

Not by assumptions.
Not by preferences.
Not by "it would be nice."

By evidence.

This prevents months of random patching and gives a prioritized recovery path toward a genuinely operational platform.

---

## EXECUTION ORDER

ERP-1 phases must execute in order:

```
Phase 1: Source Code Inventory
    ↓
Phase 2: Page-by-Page Functional Audit
    ↓
Phase 3: Component Forensics
    ↓
Phase 4: API Forensics
    ↓
Phase 5: Data Flow Trace
    ↓
Phase 6: Database Reality Check
    ↓
Phase 7: UI/UX Forensics
    ↓
Phase 8: Executive Walkthrough
    ↓
Phase 9: Defect Registry
    ↓
Phase 10: Platform Readiness Score
```

**Rationale:** Each phase feeds the next. You cannot score readiness (Phase 10) without first tracing data flows (Phase 5). You cannot trace data flows without first auditing APIs (Phase 4). You cannot audit APIs without first knowing what exists (Phase 1).

---

## VIOLATIONS

If at any point during ERP-1 the AI:

- Modifies a source file
- Installs a package
- Creates a migration
- Refactors a function
- "Fixes" something it found

**The entire ERP-1 run is invalidated.**

The contamination cannot be undone. The audit must restart.

**ERP-1 is a read-only operation on the codebase.**
