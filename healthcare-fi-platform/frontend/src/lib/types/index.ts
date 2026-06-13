export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'ceo' | 'cfo' | 'finance_manager' | 'department_head' | 'analyst' | 'viewer';
  is_active: boolean;
  created_at: string;
}

export interface KPIMetric {
  name: string;
  value: number;
  target: number | null;
  previous_value: number | null;
  change_percent: number | null;
  trend: 'up' | 'down' | 'stable';
  category: string;
  unit: string;
}

export interface ExecutiveSummary {
  kpis: {
    [key: string]: KPIMetric;
  };
}

export interface Insight {
  type: string;
  kpi_code?: string;
  kpi_name?: string;
  current_value?: number;
  change_percent?: number;
  trend_direction?: string;
  description: string;
  severity: 'critical' | 'warning' | 'info';
}

export interface Anomaly {
  date: string;
  amount: number;
  expected_amount: number;
  z_score: number;
  anomaly_type: 'spike' | 'drop';
  severity: string;
  description: string;
}

export interface Opportunity {
  type: string;
  current_rate: number;
  target_rate: number;
  potential_improvement: number;
  description: string;
  recommendation: string;
}

export interface ComprehensiveInsights {
  anomalies: Anomaly[];
  trends: Insight[];
  opportunities: Opportunity[];
  narrative: string;
  summary: {
    anomaly_count: number;
    trend_count: number;
    opportunity_count: number;
  };
}

export interface ForecastResult {
  metric_type: string;
  predicted_value: number;
  confidence_lower: number;
  confidence_upper: number;
  confidence_score: number;
  methodology: string;
  historical_data: Array<{ date: string; value: number }>;
}

export interface ScenarioResult {
  simulation_type: string;
  parameters: Record<string, any>;
  results: {
    monthly_simulations: Array<{
      period: number;
      revenue?: number;
      expenses?: number;
      profit?: number;
      cumulative_roi?: number;
      [key: string]: any;
    }>;
    [key: string]: any;
  };
}

export interface Alert {
  id: number;
  title: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  category: string;
  entity_type: string | null;
  entity_id: number | null;
  is_read: boolean;
  is_resolved: boolean;
  recommendation: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertStats {
  total: number;
  unread: number;
  critical: number;
}

export interface Branch {
  id: number;
  name: string;
  code: string;
  address: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  branch_id: number;
  head_id: number | null;
  is_active: boolean;
  created_at: string;
}

export interface Payer {
  id: number;
  name: string;
  code: string;
  payer_type: string;
  is_active: boolean;
  created_at: string;
}

export interface Doctor {
  id: number;
  name: string;
  specialization: string | null;
  department_id: number;
  is_active: boolean;
  created_at: string;
}
