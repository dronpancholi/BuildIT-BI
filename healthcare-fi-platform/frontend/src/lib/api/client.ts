import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password })),
  register: (data: { email: string; password: string; full_name: string; role: string }) =>
    api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  updateMe: (data: { full_name?: string; email?: string }) =>
    api.put('/auth/me', data),
};

export const kpiAPI = {
  getExecutiveSummary: (params?: { branch_id?: number; department_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/kpis/executive-summary', { params }),
  getRevenueKPIs: (params?: { branch_id?: number; department_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/kpis/revenue', { params }),
  getProfitabilityKPIs: (params?: { branch_id?: number; department_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/kpis/profitability', { params }),
  getOccupancyKPIs: (params?: { branch_id?: number; department_id?: number }) =>
    api.get('/kpis/occupancy', { params }),
  getClaimKPIs: (params?: { branch_id?: number; department_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/kpis/claims', { params }),
  getKPITrend: (kpiCode: string, params?: { branch_id?: number; department_id?: number; periods?: number }) =>
    api.get(`/kpis/trend/${kpiCode}`, { params }),
  getRevenueByDepartment: (params?: { branch_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/kpis/revenue/by-department', { params }),
  getRevenueByPayer: (params?: { branch_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/kpis/revenue/by-payer', { params }),
};

export const insightsAPI = {
  getComprehensiveInsights: (params?: { branch_id?: number; department_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/insights/comprehensive', { params }),
  getAnomalies: (params?: { branch_id?: number; department_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/insights/anomalies', { params }),
  getTrends: (params?: { branch_id?: number; department_id?: number }) =>
    api.get('/insights/trends', { params }),
  getOpportunities: (params?: { branch_id?: number; department_id?: number }) =>
    api.get('/insights/opportunities', { params }),
  getNarrative: (params?: { branch_id?: number; department_id?: number; start_date?: string; end_date?: string }) =>
    api.get('/insights/narrative', { params }),
};

export const forecastsAPI = {
  createForecast: (data: { metric_type: string; branch_id?: number; department_id?: number; periods_ahead?: number }) =>
    api.post('/forecasts/create', data),
  getHistoricalData: (metricType: string, params?: { branch_id?: number; department_id?: number; periods?: number }) =>
    api.get(`/forecasts/historical/${metricType}`, { params }),
  decomposeForecast: (metricType: string, params?: { branch_id?: number; department_id?: number; periods?: number }) =>
    api.post(`/forecasts/decompose?metric_type=${metricType}`, null, { params }),
  validateForecast: (forecastValue: number, actualValue: number) =>
    api.post(`/forecasts/validate?forecast_value=${forecastValue}&actual_value=${actualValue}`),
};

export const scenariosAPI = {
  runSimulation: (data: { scenario_type: string; parameters: Record<string, any>; periods?: number }) =>
    api.post('/scenarios/simulate', null, { params: data }),
  simulatePricingChange: (params: { current_revenue: number; price_change_percent: number; volume_impact_percent?: number; periods?: number }) =>
    api.post('/scenarios/pricing-change', null, { params }),
  simulateDepartmentExpansion: (params: { current_revenue: number; current_expenses: number; investment: number; monthly_revenue: number; monthly_expenses: number; periods?: number }) =>
    api.post('/scenarios/department-expansion', null, { params }),
  simulateStaffingChange: (params: { current_monthly_salary_cost: number; new_hires: number; average_salary: number; productivity_improvement_percent?: number; periods?: number }) =>
    api.post('/scenarios/staffing-change', null, { params }),
  saveScenario: (data: { name: string; description?: string; parameters: Record<string, any> }) =>
    api.post('/scenarios/save', data),
  listScenarios: () => api.get('/scenarios/list'),
};

export const alertsAPI = {
  listAlerts: (params?: { severity?: string; category?: string; is_read?: boolean; skip?: number; limit?: number }) =>
    api.get('/alerts/list', { params }),
  getAlert: (id: number) => api.get(`/alerts/${id}`),
  markAsRead: (id: number) => api.put(`/alerts/${id}/read`),
  resolveAlert: (id: number) => api.put(`/alerts/${id}/resolve`),
  createAlert: (data: { title: string; message: string; severity: string; category: string; recommendation?: string }) =>
    api.post('/alerts/create', data),
  getStats: () => api.get('/alerts/stats/summary'),
};

const v2 = axios.create({
  baseURL: `${API_BASE_URL}/api/v2`,
  headers: { 'Content-Type': 'application/json' },
});
v2.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const intelligenceAPI = {
  listInsights: (params?: { status?: string; scope_type?: string; limit?: number; offset?: number }) =>
    v2.get('/intelligence/insights', { params }),
  getInsight: (id: string) => v2.get(`/intelligence/insights/${id}`),
  listAnomalies: (params?: { status?: string; severity?: string; limit?: number; offset?: number }) =>
    v2.get('/intelligence/anomalies', { params }),
  getAnomaly: (id: string) => v2.get(`/intelligence/anomalies/${id}`),
  listOpportunities: (params?: { status?: string; limit?: number; offset?: number }) =>
    v2.get('/intelligence/opportunities', { params }),
  getOpportunity: (id: string) => v2.get(`/intelligence/opportunities/${id}`),
  listRecommendations: (params?: { status?: string; limit?: number; offset?: number }) =>
    v2.get('/intelligence/recommendations', { params }),
  getRecommendation: (id: string) => v2.get(`/intelligence/recommendations/${id}`),
  approveRecommendation: (id: string, data?: { reviewed_by?: string; review_notes?: string }) =>
    v2.post(`/intelligence/recommendations/${id}/approve`, data || {}),
  rejectRecommendation: (id: string, data?: { reason?: string }) =>
    v2.post(`/intelligence/recommendations/${id}/reject`, data || {}),
  implementRecommendation: (id: string) =>
    v2.post(`/intelligence/recommendations/${id}/implement`),
  completeRecommendation: (id: string, data?: { actual_vs_expected_impact?: number; implementation_result?: string }) =>
    v2.post(`/intelligence/recommendations/${id}/complete`, data || {}),
  generateRecommendations: (data: { insight_data: Record<string, any>; scope_id?: string }) =>
    v2.post('/intelligence/recommendations/generate', data),
  listBriefings: (params?: { briefing_type?: string; status?: string; limit?: number; offset?: number }) =>
    v2.get('/intelligence/briefings', { params }),
  getBriefing: (id: string) => v2.get(`/intelligence/briefings/${id}`),
  getGraphNodes: (params?: { node_type?: string; limit?: number }) =>
    v2.get('/intelligence/graph/nodes', { params }),
  getGraphNode: (id: string) => v2.get(`/intelligence/graph/nodes/${id}`),
  getGraphNeighbors: (id: string) => v2.get(`/intelligence/graph/nodes/${id}/neighbors`),
  listRelationships: (params?: { relationship_type?: string; limit?: number }) =>
    v2.get('/intelligence/graph/relationships', { params }),
  getFeed: (params?: { limit?: number; offset?: number; type?: string }) =>
    v2.get('/intelligence/feed', { params }),
};

export const decisionsAPI = {
  propose: (data: any) => v2.post('/decisions', data),
  list: (params?: { status?: string; decision_type?: string; category?: string; search?: string; offset?: number; limit?: number }) =>
    v2.get('/decisions', { params }),
  get: (id: string) => v2.get(`/decisions/${id}`),
  submit: (id: string) => v2.post(`/decisions/${id}/submit`),
  approve: (id: string, data?: any) => v2.post(`/decisions/${id}/approve`, data || {}),
  reject: (id: string, data: { reason: string }) => v2.post(`/decisions/${id}/reject`, data),
  startImplementation: (id: string) => v2.post(`/decisions/${id}/start-implementation`),
  complete: (id: string) => v2.post(`/decisions/${id}/complete`),
  attachEvidence: (id: string, data: any) => v2.post(`/decisions/${id}/evidence`, data),
  getTimeline: (id: string) => v2.get(`/decisions/${id}/timeline`),
  getValue: (id: string) => v2.get(`/decisions/${id}/value`),
  getPendingReview: () => v2.get('/decisions/pending-review'),
};

export const outcomesAPI = {
  list: (params?: { offset?: number; limit?: number }) => v2.get('/outcomes/definitions', { params }),
  defineOutcome: (data: any) => v2.post('/outcomes/definitions', data),
  getDefinition: (id: string) => v2.get(`/outcomes/definitions/${id}`),
  recordMeasurement: (data: any) => v2.post('/outcomes/measurements', data),
  getMeasurements: (defId: string) => v2.get(`/outcomes/definitions/${defId}/measurements`),
  getTrajectory: (defId: string) => v2.get(`/outcomes/definitions/${defId}/trajectory`),
};

export const featuresAPI = {
  register: (data: any) => v2.post('/features', data),
  list: (params?: { offset?: number; limit?: number }) => v2.get('/features', { params }),
  get: (id: string) => v2.get(`/features/${id}`),
  search: (q: string) => v2.get('/features/search', { params: { q } }),
  validate: (id: string) => v2.post(`/features/${id}/validate`),
};

export const modelsAPI = {
  register: (data: any) => v2.post('/models', data),
  list: (params?: { offset?: number; limit?: number }) => v2.get('/models', { params }),
  get: (id: string) => v2.get(`/models/${id}`),
  approve: (id: string) => v2.post(`/models/${id}/approve`),
  retire: (id: string) => v2.post(`/models/${id}/retire`),
};

export const learningAPI = {
  getMetrics: () => v2.get('/learning/metrics'),
  getRecommendationAccuracy: (params?: { start_date?: string; end_date?: string }) =>
    v2.get('/learning/recommendation-accuracy', { params }),
  getDecisionAccuracy: () => v2.get('/learning/decision-accuracy'),
  getAdoptionSummary: () => v2.get('/learning/adoption-summary'),
  getPatterns: () => v2.get('/learning/patterns'),
  getScoringAdjustments: () => v2.get('/learning/scoring-adjustments'),
  getDashboard: () => v2.get('/learning/dashboard'),
};

export const graphAPI = {
  getStats: () => v2.get('/graph/stats'),
  findPathway: (fromId: string, toId: string) =>
    v2.get('/graph/pathway', { params: { from_id: fromId, to_id: toId } }),
  getImpactNetwork: (decisionId: string, depth?: number) =>
    v2.get(`/graph/impact-network/${decisionId}`, { params: { depth } }),
  getValidationChain: (decisionId: string) => v2.get(`/graph/validation-chain/${decisionId}`),
  findContradictions: () => v2.get('/graph/contradictions'),
  createEdge: (data: { source_id: string; target_id: string; relationship_type: string }) =>
    v2.post('/graph/edges', data),
};

export const financialAPI = {
  listCurrencies: () => v2.get('/financial/currencies'),
  getCurrency: (code: string) => v2.get(`/financial/currencies/${code}`),
  getFxRate: (params: { from: string; to: string }) => v2.get('/financial/fx-rates', { params }),
  convertMoney: (data: { amount: number; from_currency: string; to_currency: string }) =>
    v2.post('/financial/convert', data),
  convertBatch: (data: { conversions: Array<{ amount: number; from_currency: string; to_currency: string }> }) =>
    v2.post('/financial/convert/batch', data),
  formatMoney: (data: { amount: number; currency: string; locale?: string }) =>
    v2.post('/financial/money/format', data),
};

export const analyticsAPI = {
  listMetrics: (params?: { category?: string; search?: string; limit?: number; offset?: number }) =>
    v2.get('/analytics/metrics', { params }),
  createMetric: (data: any) => v2.post('/analytics/metrics', data),
  getMetric: (id: string) => v2.get(`/analytics/metrics/${id}`),
  listDimensions: (params?: { cardinality?: string; search?: string; limit?: number }) =>
    v2.get('/analytics/dimensions', { params }),
  createDimension: (data: any) => v2.post('/analytics/dimensions', data),
  executeQuery: (data: any) => v2.post('/analytics/query', data),
  listSavedReports: (params?: { limit?: number }) => v2.get('/analytics/reports/saved', { params }),
  saveReport: (data: any) => v2.post('/analytics/reports/saved', data),
  listTemplates: () => v2.get('/analytics/templates'),
};

export const dashboardsAPI = {
  list: (params?: { owner?: string; tags?: string; search?: string }) => v2.get('/dashboards', { params }),
  create: (data: any) => v2.post('/dashboards', data),
  get: (id: string) => v2.get(`/dashboards/${id}`),
  update: (id: string, data: any) => v2.put(`/dashboards/${id}`, data),
  addWidget: (id: string, data: any) => v2.post(`/dashboards/${id}/widgets`, data),
  updateWidget: (dashId: string, widgetId: string, data: any) =>
    v2.put(`/dashboards/${dashId}/widgets/${widgetId}`, data),
  removeWidget: (dashId: string, widgetId: string) =>
    v2.delete(`/dashboards/${dashId}/widgets/${widgetId}`),
  getVersions: (id: string) => v2.get(`/dashboards/${id}/versions`),
  createVersion: (id: string) => v2.post(`/dashboards/${id}/versions`),
  getPrebuiltTemplates: () => v2.get('/dashboards/prebuilt/templates'),
};

export const queryAPI = {
  execute: (data: any) => v2.post('/query/execute', data),
  generateSQL: (data: any) => v2.post('/query/generate-sql', data),
  listSaved: () => v2.get('/query/saved'),
  saveQuery: (data: any) => v2.post('/query/saved', data),
  deleteSaved: (id: string) => v2.delete(`/query/saved/${id}`),
  validate: (data: any) => v2.post('/query/validate', data),
  explain: (data: any) => v2.post('/query/explain', data),
  listTemplates: () => v2.get('/query/templates'),
};

export const exportsAPI = {
  createJob: (data: any) => v2.post('/exports/jobs', data),
  listJobs: (params?: { status?: string }) => v2.get('/exports/jobs', { params }),
  getJob: (id: string) => v2.get(`/exports/jobs/${id}`),
  cancelJob: (id: string) => v2.delete(`/exports/jobs/${id}`),
  getFormats: () => v2.get('/exports/formats'),
  createSchedule: (data: any) => v2.post('/exports/schedule', data),
  listSchedules: () => v2.get('/exports/schedule'),
  cancelSchedule: (id: string) => v2.delete(`/exports/schedule/${id}`),
  subscribe: (data: any) => v2.post('/exports/subscribe', data),
  listSubscriptions: () => v2.get('/exports/subscriptions'),
};

export const collaborationAPI = {
  listComments: (params: { target_type: string; target_id: string }) =>
    v2.get('/collaboration/comments', { params }),
  createComment: (data: { content: string; target_type: string; target_id: string }) =>
    v2.post('/collaboration/comments', null, { params: data }),
  editComment: (id: string, data: { content: string }) =>
    v2.put(`/collaboration/comments/${id}`, null, { params: { content: data.content } }),
  resolveComment: (id: string) =>
    v2.post(`/collaboration/comments/${id}/resolve`, null),
  listThreads: (params: { target_type: string; target_id: string }) =>
    v2.get('/collaboration/threads', { params }),
  createThread: (data: { target_type: string; target_id: string; title: string; initial_message: string }) =>
    v2.post('/collaboration/threads', null, { params: data }),
  closeThread: (id: string) =>
    v2.post(`/collaboration/threads/${id}/close`, null),
  listAssignments: (params?: { status?: string }) =>
    v2.get('/collaboration/assignments', { params }),
  createAssignment: (data: {
    title: string;
    description?: string;
    assigned_to: string;
    priority: string;
    due_date?: string;
    target_type?: string;
    target_id?: string;
  }) =>
    v2.post('/collaboration/assignments', null, {
      params: {
        title: data.title,
        description: data.description || '',
        assignee_id: data.assigned_to,
        priority: data.priority,
        due_date: data.due_date || new Date(Date.now() + 7*24*60*60*1000).toISOString().split('T')[0],
        target_type: data.target_type || 'dashboard',
        target_id: data.target_id || undefined,
      }
    }),
  updateAssignment: (id: string, data: { status: string }) =>
    v2.put(`/collaboration/assignments/${id}`, null, { params: { status: data.status } }),
  completeAssignment: (id: string) =>
    v2.post(`/collaboration/assignments/${id}/complete`, null),
  listWatchlists: () =>
    v2.get('/collaboration/watchlists'),
  createWatchlist: (data: { name: string; description?: string }) =>
    v2.post('/collaboration/watchlists', null, { params: { name: data.name, description: data.description || '' } }),
  updateWatchlist: (id: string, data: { name?: string; description?: string }) =>
    v2.put(`/collaboration/watchlists/${id}`, null, { params: { name: data.name, description: data.description } }),
  removeWatchlistItem: (watchlistId: string, itemId: string) =>
    v2.delete(`/collaboration/watchlists/${watchlistId}/items/${itemId}`),
};

export const workspaceAPI = {
  get: () => v2.get('/workspace'),
  update: (data: any) => v2.put('/workspace', data),
  updateSection: (sectionType: string, data: any) => v2.put(`/workspace/sections/${sectionType}`, data),
  listBriefings: () => v2.get('/workspace/briefings'),
  getBriefing: (id: string) => v2.get(`/workspace/briefings/${id}`),
  generateBriefing: () => v2.post('/workspace/briefings/generate'),
  markBriefingRead: (id: string) => v2.put(`/workspace/briefings/${id}/read`),
  getNotifications: () => v2.get('/workspace/notifications/config'),
  updateNotifications: (data: any) => v2.put('/workspace/notifications/config', data),
};

export const visualizationAPI = {
  getChartTypes: () => v2.get('/visualization/chart-types'),
  createSpec: (data: any) => v2.post('/visualization/specs', data),
  getSpec: (id: string) => v2.get(`/visualization/specs/${id}`),
  updateSpec: (id: string, data: any) => v2.put(`/visualization/specs/${id}`, data),
  renderSpec: (id: string) => v2.post(`/visualization/specs/${id}/render`),
  getColorSchemes: () => v2.get('/visualization/color-schemes'),
  getConfig: () => v2.get('/visualization/config'),
  updateConfig: (data: any) => v2.put('/visualization/config', data),
};

export const governanceAPI = {
  getDashboardVersions: (dashId: string) => v2.get(`/governance/dashboards/${dashId}/versions`),
  createDashboardVersion: (dashId: string, data: any) =>
    v2.post(`/governance/dashboards/${dashId}/versions`, data),
  getReportVersions: (reportId: string) => v2.get(`/governance/reports/${reportId}/versions`),
  createReportVersion: (reportId: string, data: any) =>
    v2.post(`/governance/reports/${reportId}/versions`, data),
  listCertifiedMetrics: () => v2.get('/governance/certifications/metrics'),
  submitMetricForCertification: (data: any) => v2.post('/governance/certifications/metrics', data),
  certifyMetric: (id: string, data?: any) => v2.put(`/governance/certifications/metrics/${id}/certify`, data),
  listCertifiedReports: () => v2.get('/governance/certifications/reports'),
  createApproval: (data: any) => v2.post('/governance/approvals', data),
  approve: (id: string, data?: any) => v2.put(`/governance/approvals/${id}/approve`, data),
  reject: (id: string, data?: any) => v2.put(`/governance/approvals/${id}/reject`, data),
  listUsage: (params?: { stale_only?: boolean }) => v2.get('/governance/usage', { params }),
};

export const bflAPI = {
  parse: (data: { expression: string; dialect?: string }) => v2.post('/bfl/parse', data),
  validate: (data: { expression: string; metrics?: string[]; dimensions?: string[] }) => v2.post('/bfl/validate', data),
  generateSql: (data: { expression: string; dialect?: string }) => v2.post('/bfl/generate-sql', data),
  listFunctions: (params?: { category?: string }) => v2.get('/bfl/functions', { params }),
  publish: (data: any) => v2.post('/bfl/publish', data),
  listPublished: (params?: { category?: string; skip?: number; limit?: number }) => v2.get('/bfl/published', { params }),
  getPublished: (id: string) => v2.get(`/bfl/published/${id}`),
  deletePublished: (id: string) => v2.delete(`/bfl/published/${id}`),
};

export const metricStudioAPI = {
  list: (params?: { category?: string; status?: string; skip?: number; limit?: number }) => v2.get('/metric-studio/', { params }),
  create: (data: any) => v2.post('/metric-studio/', data),
  get: (id: string) => v2.get(`/metric-studio/${id}`),
  update: (id: string, data: any) => v2.put(`/metric-studio/${id}`, data),
  publish: (id: string) => v2.post(`/metric-studio/${id}/publish`),
  certify: (id: string, data?: any) => v2.post(`/metric-studio/${id}/certify`, data),
  deprecate: (id: string) => v2.post(`/metric-studio/${id}/deprecate`),
  getVersions: (id: string) => v2.get(`/metric-studio/${id}/versions`),
  rollback: (id: string, targetVersion: number) => v2.post(`/metric-studio/${id}/rollback`, { target_version: targetVersion }),
  getDependencies: (id: string) => v2.get(`/metric-studio/${id}/dependencies`),
  getImpact: (id: string) => v2.get(`/metric-studio/${id}/impact`),
  delete: (id: string) => v2.delete(`/metric-studio/${id}`),
};

export const semanticLayerAPI = {
  listDimensions: (params?: { cardinality?: string; skip?: number; limit?: number }) => v2.get('/semantic/dimensions', { params }),
  createDimension: (data: any) => v2.post('/semantic/dimensions', data),
  getDimension: (id: string) => v2.get(`/semantic/dimensions/${id}`),
  getDimensionHistory: (id: string) => v2.get(`/semantic/dimensions/${id}/history`),
  addSCD2Record: (data: any) => v2.post('/semantic/dimensions/scd2', data),
  getSCD2Current: (slug: string, key: string) => v2.get(`/semantic/dimensions/scd2/${slug}/${key}`),
  listFactTables: () => v2.get('/semantic/fact-tables'),
  createFactTable: (data: any) => v2.post('/semantic/fact-tables', data),
  listRelationships: (params?: { source?: string; target?: string }) => v2.get('/semantic/relationships', { params }),
  createRelationship: (data: any) => v2.post('/semantic/relationships', data),
  listHierarchies: () => v2.get('/semantic/hierarchies'),
  createHierarchy: (data: any) => v2.post('/semantic/hierarchies', data),
  listAliases: () => v2.get('/semantic/aliases'),
  createAlias: (data: any) => v2.post('/semantic/aliases', data),
  resolveAlias: (name: string) => v2.get(`/semantic/resolve/${name}`),
};

export const aiCfoAPI = {
  listProfiles: () => v2.get('/ai-cfo/profiles'),
  createProfile: (data: any) => v2.post('/ai-cfo/profiles', data),
  getProfile: (id: string) => v2.get(`/ai-cfo/profiles/${id}`),
  updateProfile: (id: string, data: any) => v2.put(`/ai-cfo/profiles/${id}`, data),
  askQuestion: (data: { user_query: string; context?: any }) => v2.post('/ai-cfo/questions', data),
  getQuestion: (id: string) => v2.get(`/ai-cfo/questions/${id}`),
  generateBriefing: (data: { mode: string; period: string; context?: any }) => v2.post('/ai-cfo/briefings', data),
  getBriefing: (id: string) => v2.get(`/ai-cfo/briefings/${id}`),
  createWorkspace: (data: any) => v2.post('/ai-cfo/workspaces', data),
  listWorkspaces: () => v2.get('/ai-cfo/workspaces'),
  addWidget: (id: string, data: any) => v2.put(`/ai-cfo/workspaces/${id}/widgets`, data),
  deleteWorkspace: (id: string) => v2.delete(`/ai-cfo/workspaces/${id}`),
  createAlertConfig: (data: any) => v2.post('/ai-cfo/alerts/configs', data),
  getAlerts: (params?: { unread_only?: boolean }) => v2.get('/ai-cfo/alerts', { params }),
  dismissAlert: (id: string) => v2.put(`/ai-cfo/alerts/${id}/dismiss`),
};

export const strategicAPI = {
  createScenario: (data: any) => v2.post('/strategic/scenarios', data),
  getScenario: (id: string) => v2.get(`/strategic/scenarios/${id}`),
  listScenarios: () => v2.get('/strategic/scenarios'),
  runScenario: (id: string, data: any) => v2.post(`/strategic/scenarios/${id}/run`, data),
  compareScenarios: (data: any) => v2.post('/strategic/scenarios/compare', data),
  buildDriverTree: (data: any) => v2.post('/strategic/driver-trees', data),
  calculateDrivers: (id: string, data: any) => v2.put(`/strategic/driver-trees/${id}/calculate`, data),
  runMonteCarlo: (data: any) => v2.post('/strategic/monte-carlo', data),
  createWhatIf: (data: any) => v2.post('/strategic/what-if', data),
  runWhatIf: (id: string, data: any) => v2.post(`/strategic/what-if/${id}/run`, data),
  sensitivityAnalysis: (data: any) => v2.post('/strategic/sensitivity', data),
  assessRisks: (data: any) => v2.post('/strategic/risks', data),
  deleteScenario: (id: string) => v2.delete(`/strategic/scenarios/${id}`),
};

export const forecastingAPI = {
  createModel: (data: any) => v2.post('/forecasting/models', data),
  getModel: (id: string) => v2.get(`/forecasting/models/${id}`),
  listModels: (params?: { status?: string; metric_id?: string }) => v2.get('/forecasting/models', { params }),
  trainModel: (id: string, data: any) => v2.post(`/forecasting/models/${id}/train`, data),
  generateForecast: (id: string, data: any) => v2.post(`/forecasting/models/${id}/forecast`, data),
  evaluateModel: (id: string, data: any) => v2.post(`/forecasting/models/${id}/evaluate`, data),
  compareModels: (data: any) => v2.post('/forecasting/compare', data),
  createEnsemble: (data: any) => v2.post('/forecasting/ensemble', data),
  detectDrift: (id: string, data: any) => v2.post(`/forecasting/models/${id}/drift`, data),
  promoteModel: (id: string) => v2.put(`/forecasting/models/${id}/promote`),
  demoteModel: (id: string) => v2.put(`/forecasting/models/${id}/demote`),
  listMethods: () => v2.get('/forecasting/methods'),
};

export const executiveAPI = {
  getKPIs: (params?: { time_range?: string }) => v2.get('/executive/kpis', { params }),
  getAlerts: (params?: { severity?: string; limit?: number }) => v2.get('/executive/alerts', { params }),
  markAlertRead: (id: string) => v2.put(`/executive/alerts/${id}/read`),
  dismissAlert: (id: string) => v2.put(`/executive/alerts/${id}/dismiss`),
  getDecisions: (params?: { status?: string }) => v2.get('/executive/decisions', { params }),
  createDecision: (data: any) => v2.post('/executive/decisions', data),
  updateDecisionStatus: (id: string, data: any) => v2.put(`/executive/decisions/${id}/status`, data),
  getSummary: (params?: { time_range?: string }) => v2.get('/executive/summary', { params }),
  getRevenueForecast: (params?: { periods_ahead?: number }) => v2.get('/executive/forecasts/revenue', { params }),
  getCostForecast: (params?: { periods_ahead?: number }) => v2.get('/executive/forecasts/cost', { params }),
  getRisks: () => v2.get('/executive/risks'),
  generateBriefing: (data: any) => v2.post('/executive/briefing', data),
};

export const copilotAPI = {
  processQuery: (data: { user_query: string; context?: any }) => v2.post('/copilot/query', data),
  getReasoning: (data: { query: string; context?: any }) => v2.post('/copilot/reasoning', data),
  getSuggestions: (params?: { limit?: number }) => v2.get('/copilot/suggestions', { params }),
  listConversations: (params?: { limit?: number }) => v2.get('/copilot/conversations', { params }),
  getConversation: (id: string) => v2.get(`/copilot/conversations/${id}`),
  archiveConversation: (id: string) => v2.put(`/copilot/conversations/${id}/archive`),
  explainReasoning: (id: string) => v2.get(`/copilot/actions/${id}/reasoning`),
  getCapabilities: () => v2.get('/copilot/capabilities'),
};

export const aiEverywhereAPI = {
  ask: (data: {
    question: string;
    page_context?: {
      page: string;
      metrics?: string[];
      filters?: Record<string, any>;
      date_range?: string[];
      selected_entity?: Record<string, any>;
    };
  }) => v2.post('/ai/ask', data),
};
