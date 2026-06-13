# API Failure Registry — ERP-4 Operational Resurrection Audit

**Generated:** 2026-06-13
**Scope:** All 31 frontend page files + 12 sub-component files
**API Client:** `frontend/src/lib/api/client.ts` (v1 + v2 axios instances)

---

## CRITICAL Failures

### 1. `/settings` — Zero API Integration
- **File:** `frontend/src/app/settings/page.tsx`
- **Impact:** Settings page is completely non-functional
- **Details:** Pure static UI with no API calls. Save button does nothing. No data persistence whatsoever.
- **Fix Required:** Wire up `authAPI.updateMe()` or create settings API endpoints

---

## HIGH — Error Handling Deficiencies

### 2. Multiple Pages Use `console.error` in Catch Blocks
- **Affected Pages:**
  - `/alerts` (line ~56) — `catch { setError("Failed to fetch alerts"); }`
  - `/insights` (line ~38) — `catch (e) { console.error("Error fetching insights:", e); }`
  - `/forecasts` (line ~31) — `catch (e) { console.error(e); }`
  - `/revenue` (line ~58) — `catch (e) { console.error(e); }`
  - `/scenarios` — catch blocks use `Alert` but no user-facing retry
- **Impact:** Errors are silently logged; users see broken UI with no recovery path
- **Fix Required:** Add `setError()` state and render `<Alert>` components

### 3. `/alerts` — Promise.all Fail-Fast Pattern
- **File:** `frontend/src/app/alerts/page.tsx`
- **Issue:** Uses `Promise.all([alertsAPI.listAlerts(), alertsAPI.getStats()])` 
- **Impact:** If either API fails, both calls fail. Stats AND alerts both disappear.
- **Fix Required:** Switch to `Promise.allSettled()` for graceful degradation

### 4. `/alerts` — No User-Facing Error UI
- **File:** `frontend/src/app/alerts/page.tsx`
- **Issue:** `catch` block sets error string but no error UI renders
- **Impact:** User sees empty table with no explanation
- **Fix Required:** Add error state rendering

---

## MEDIUM — Inconsistent Patterns

### 5. `/insights` — No Error State Rendering
- **File:** `frontend/src/app/insights/page.tsx`
- **Issue:** `error` state is set but never rendered in JSX
- **Impact:** API failures result in empty content with no error feedback

### 6. `/revenue` — Sub-section Error Swallowing
- **File:** `frontend/src/app/revenue/page.tsx`
- **Issue:** Revenue KPIs render but department/payer data silently falls back to empty arrays
- **Impact:** Partial data load without user notification

### 7. `/dashboard` vs Other Pages — Inconsistent Resilience
- **File:** `frontend/src/app/dashboard/page.tsx`
- **Good:** Uses `Promise.allSettled()` — partial data still shows
- **Bad:** Most other pages use `Promise.all()` — any single failure kills the entire view
- **Fix Required:** Standardize on `Promise.allSettled()` across all multi-fetch pages

---

## MEDIUM — Silent Failures

### 8. `recommendation-center.tsx` — Approve/Reject Silently Swallows Errors
- **File:** `frontend/src/components/intelligence/recommendation-center.tsx`
- **Issue:** `handleApprove()` and `handleReject()` catch blocks are empty (`catch {}`)
- **Impact:** User clicks approve, UI updates optimistically, but if API fails user never knows
- **Fix Required:** Revert optimistic update on failure; show toast/alert

### 9. `knowledge-graph-explorer.tsx` — Promise.allSettled but Console.error Only
- **File:** `frontend/src/components/knowledge-graph/knowledge-graph-explorer.tsx`
- **Issue:** Uses `Promise.allSettled()` (good) but catch block only does `console.error()`
- **Impact:** Partial graph loads but user doesn't know which parts failed
- **Fix Required:** Add per-section error indicators

---

## LOW — Missing Features

### 10. `/forecasts` — No Loading State
- **File:** `frontend/src/app/forecasts/page.tsx`
- **Issue:** No loading spinner during forecast generation
- **Impact:** User doesn't know if request is processing

### 11. `/scenarios` — No Loading State
- **File:** `frontend/src/app/scenarios/page.tsx`
- **Issue:** No loading indicator during scenario simulation
- **Impact:** User doesn't know if simulation is running

### 12. `/settings` — Save Button No-Op
- **File:** `frontend/src/app/settings/page.tsx`
- **Issue:** Save button onClick handler is empty
- **Impact:** Users think settings are saved but nothing persists

---

## API Client Issues

### 13. No Global Error Interceptor for Non-401 Errors
- **File:** `frontend/src/lib/api/client.ts`
- **Issue:** Only intercepts 401 errors. 403, 429, 500 errors are not handled globally.
- **Impact:** Each page must implement its own error handling for common failure modes
- **Recommendation:** Add global handlers for 403 (forbidden), 429 (rate limit), 500 (server error)

### 14. No Request Retry Logic
- **File:** `frontend/src/lib/api/client.ts`
- **Issue:** No exponential backoff or retry on network failures
- **Impact:** Transient network issues cause immediate failures
- **Recommendation:** Add axios-retry or similar middleware

### 15. No Request Cancellation
- **File:** `frontend/src/lib/api/client.ts`
- **Issue:** No AbortController or request cancellation on component unmount
- **Impact:** Race conditions when navigating quickly between pages; potential memory leaks
- **Recommendation:** Use AbortController in fetch functions

---

## Sub-Component API Coverage (Delegation Pages)

### `/decisions` (4 sub-components)
| Component | API Client | Operations | Error Handling | Loading State |
|-----------|-----------|------------|----------------|---------------|
| DecisionCenter | decisionsAPI | list, propose, submit, approve, start, complete, timeline, value | `catch { setDecisions([]) }` | Text-based loading |
| OutcomeCenter | outcomesAPI | list, define, measurements, trajectory | `catch { setDefinitions([]) }` | Text-based loading |
| FeatureCatalog | featuresAPI | list, register, search, validate | `catch { setFeatures([]) }` | Text-based loading |
| ModelRegistry | modelsAPI | list, register, approve, retire | `catch { setModels([]) }` | Text-based loading |

### `/intelligence` (6 sub-components)
| Component | API Client | Operations | Error Handling | Loading State |
|-----------|-----------|------------|----------------|---------------|
| IntelligenceFeed | intelligenceAPI.getFeed | list | Full error classification (network/auth/downstream/unknown) | Skeleton components |
| AnomalyCenter | intelligenceAPI.listAnomalies | list | Full error classification | Skeleton components |
| OpportunityCenter | intelligenceAPI.listOpportunities | list | Full error classification | Skeleton components |
| RecommendationCenter | intelligenceAPI.listRecommendations | list, approve | Full error classification | Skeleton components |
| BriefingLibrary | intelligenceAPI.listBriefings | list | Full error classification | Skeleton components |
| IntelligenceGraphExplorer | intelligenceAPI + graphAPI | nodes, relationships, neighbors | Silent failure | Text-based loading |

### `/knowledge-graph` (1 sub-component)
| Component | API Client | Operations | Error Handling | Loading State |
|-----------|-----------|------------|----------------|---------------|
| KnowledgeGraphExplorer | graphAPI + intelligenceAPI | stats, contradictions, nodes, relationships, pathway, impact, validation | Promise.allSettled + console.error | Spinner + text |

### `/learning` (1 sub-component)
| Component | API Client | Operations | Error Handling | Loading State |
|-----------|-----------|------------|----------------|---------------|
| LearningDashboard | learningAPI | metrics, accuracy, adoption, patterns, adjustments, dashboard | Promise.allSettled + console.error | Boolean loading flag |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Pages Audited | 31 |
| Total Sub-Components Audited | 12 |
| CRITICAL Failures | 1 |
| HIGH Issues | 2 |
| MEDIUM Issues | 4 |
| LOW Issues | 3 |
| API Client Issues | 3 |
| **Total Issues Found** | **13** |

| Status | Pages |
|--------|-------|
| WORKING | 30 |
| BROKEN | 1 (`/settings`) |

---

## Recommendations

1. **Immediate (P0):** Fix `/settings` page — add API integration
2. **High (P1):** Add error UI to all pages using `console.error` in catch blocks
3. **High (P1):** Standardize on `Promise.allSettled()` for all multi-fetch pages
4. **Medium (P2):** Add global error interceptor for 403/429/500 in API client
5. **Medium (P2):** Add request retry logic with exponential backoff
6. **Medium (P2):** Add AbortController for request cancellation
7. **Low (P3):** Add loading states to `/forecasts` and `/scenarios`
8. **Low (P3):** Add optimistic update rollback in recommendation approve/reject
