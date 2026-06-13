# ERP-3: Architecture Simplification — Power BI for Hospitals

## Goal
Remove ~35% of code complexity while preserving 95% of value. 
Target architecture: Next.js + FastAPI + PostgreSQL only.

## Target Architecture
```
BuildIT
├── Next.js Frontend
├── FastAPI Backend  
└── PostgreSQL
```

## Components to REMOVE (with rationale)

### 1. Embedded Analytics ❌
**Rationale**: Only useful for SaaS embedding. Uncle uses BuildIT directly.
**Files to remove**:
- `frontend/src/app/embedded/` (page)
- `backend/app/api/v2/endpoints/embedded.py` (7 routes)
- `backend/app/domain/embedded_analytics/` (entire domain)
- `embeddedAPI` from client.ts

### 2. Deployment Center ❌
**Rationale**: Software vendor feature, not executive analytics.
**Files to remove**:
- `frontend/src/app/deployments/` (page)
- `backend/app/api/v2/endpoints/deployment.py` (7 routes)
- `backend/app/domain/deployment/` (entire domain)
- `deploymentAPI` from client.ts

### 3. Multi-Currency ❌
**Rationale**: Indian hospital group, no FX consolidation needed.
**Files to remove**:
- `frontend/src/app/currency/` (page)
- `frontend/src/app/multi-currency/` (page)
- `backend/app/api/v2/endpoints/advanced_currency.py` (6 routes)
- `backend/app/api/v2/endpoints/multi_currency.py` (10 routes)
- `backend/app/domain/multi_currency/` (entire domain)
- `backend/app/domain/advanced_currency/` (entire domain)
- `advancedCurrencyAPI`, `multiCurrencyAPI` from client.ts

### 4. Vector Memory ❌
**Rationale**: Expensive complexity. AI CFO can query SQL directly.
**Files to remove**:
- `frontend/src/app/memory/` (page)
- `backend/app/api/v2/endpoints/vector_memory.py` (7 routes)
- `backend/app/domain/vector_memory/` (entire domain)
- `pgvector` extension from migration
- `memoryAPI` from client.ts

### 5. Institutional Knowledge System ❌
**Rationale**: Adds maintenance burden, little executive value. Keep graph visualization only.
**Files to remove**:
- `frontend/src/app/knowledge-system/` (page)
- `backend/app/api/v2/endpoints/institutional_knowledge.py` (8 routes)
- `backend/app/domain/institutional_knowledge/` (entire domain)
- `knowledgeAPI` from client.ts

### 6. Infrastructure to Remove

| Component | Reason |
|-----------|--------|
| Redis | Only used for caching; can use in-memory |
| DuckDB | Only used for analytics; PostgreSQL is sufficient |
| Celery | Only used for background tasks; can use sync |
| pgvector | Only used for embeddings; not needed |

## Components to FREEZE (keep code, stop investing)

### 7. Learning Engine 🧊
**Rationale**: Nice research, not needed for executives.
**Action**: Keep files but no new features.

### 8. Advanced Collaboration 🧊
**Rationale**: Execs use WhatsApp/Teams. Keep simple task assignment.
**Action**: Simplify to basic comments only.

### 9. Advanced Governance Workflows 🧊
**Keep**: Metric certification, versioning
**Freeze**: Approval chains, workflow orchestration

## Components to KEEP (Core Power BI)

### Dashboards ✅
- `frontend/src/app/dashboards/`
- `backend/app/api/v2/endpoints/dashboards.py`

### Analytics ✅
- `frontend/src/app/analytics/`
- `backend/app/api/v2/endpoints/analytics.py`

### Semantic Layer ✅
- `frontend/src/app/semantic/`
- `backend/app/api/v2/endpoints/semantic_layer.py`

### BFL (DAX equivalent) ✅
- `frontend/src/app/formulas/`
- `backend/app/api/v2/endpoints/bfl.py`

### Query Engine ✅
- `frontend/src/app/analytics/query/`
- `backend/app/api/v2/endpoints/query_engine.py`

### Metric Studio ✅
- `frontend/src/app/metric-studio/`
- `backend/app/api/v2/endpoints/metric_studio.py`

### Forecasting ✅
- `frontend/src/app/forecasting/`
- `backend/app/api/v2/endpoints/forecasting.py`

### Strategic Planning ✅
- `frontend/src/app/strategic/`
- `backend/app/api/v2/endpoints/strategic_planning.py`

### AI CFO ✅
- `frontend/src/app/ai-cfo/`
- `frontend/src/app/copilot/`
- `backend/app/api/v2/endpoints/ai_cfo.py`
- `backend/app/api/v2/endpoints/copilot.py`

### Intelligence ✅
- `frontend/src/app/insights/`
- `backend/app/api/v2/endpoints/intelligence.py`

### Decisions ✅
- `frontend/src/app/decisions/`
- `backend/app/api/v2/endpoints/decisions.py`

### Executive Center ✅
- `frontend/src/app/executive-center/`
- `backend/app/api/v2/endpoints/executive_center.py`

### Workspace ✅
- `frontend/src/app/workspace/`
- `backend/app/api/v2/endpoints/workspace.py`

### Reports/Exports ✅
- `frontend/src/app/exports/`
- `backend/app/api/v2/endpoints/exports.py`

### Basic Governance ✅
- `frontend/src/app/governance/`
- `backend/app/api/v2/endpoints/governance.py`

## Execution Plan

### Phase 1: Backend Removal (estimated 2 hours)
1. Remove domain modules
2. Remove API endpoints
3. Remove ORM models
4. Remove migrations
5. Remove Docker services
6. Update API router

### Phase 2: Frontend Removal (estimated 1 hour)
1. Remove pages
2. Remove API client methods
3. Update sidebar navigation
4. Remove unused components

### Phase 3: Infrastructure (estimated 1 hour)
1. Remove Redis from docker-compose
2. Remove DuckDB from docker-compose
3. Remove Celery from docker-compose
4. Update backend to remove Redis/DuckDB dependencies

### Phase 4: Verification (estimated 1 hour)
1. Run backend tests
2. Run frontend build
3. Test core workflows
4. Update documentation

## Success Criteria
- [ ] Backend: 0 imports from removed modules
- [ ] Frontend: 0 references to removed components
- [ ] Docker: Only PostgreSQL + backend + frontend running
- [ ] All core features working
- [ ] Codebase reduced by ~35%

## Estimated Timeline: 5 hours total
