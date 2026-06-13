import { useQuery } from '@tanstack/react-query';
import { kpiAPI } from '@/lib/api/client';

export interface KPIMetric {
  name: string;
  value: number;
  target?: number;
  previous_value?: number;
  change_percent?: number;
  trend: 'up' | 'down' | 'stable';
  category: string;
  unit?: string;
}

export interface ExecutiveSummary {
  kpis: Record<string, KPIMetric>;
}

export function useExecutiveSummary(params?: {
  branch_id?: number;
  department_id?: number;
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ['kpis', 'executive-summary', params],
    queryFn: async () => {
      const response = await kpiAPI.getExecutiveSummary(params);
      return response.data as ExecutiveSummary;
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useRevenueKPIs(params?: {
  branch_id?: number;
  department_id?: number;
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ['kpis', 'revenue', params],
    queryFn: async () => {
      const response = await kpiAPI.getRevenueKPIs(params);
      return response.data as Record<string, KPIMetric>;
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useRevenueByDepartment(params?: {
  branch_id?: number;
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ['kpis', 'revenue-by-department', params],
    queryFn: async () => {
      const response = await kpiAPI.getRevenueByDepartment(params);
      return response.data.departments as Array<{
        name: string;
        revenue: number;
        transaction_count: number;
      }>;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useRevenueByPayer(params?: {
  branch_id?: number;
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ['kpis', 'revenue-by-payer', params],
    queryFn: async () => {
      const response = await kpiAPI.getRevenueByPayer(params);
      return response.data.payers as Array<{
        name: string;
        payer_type: string;
        revenue: number;
        percentage: number;
        transaction_count: number;
      }>;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useKPITrend(kpiCode: string, params?: { branch_id?: number; periods?: number }) {
  return useQuery({
    queryKey: ['kpis', 'trend', kpiCode, params],
    queryFn: async () => {
      const response = await kpiAPI.getKPITrend(kpiCode, params);
      return response.data.trend as Array<{
        period_id: number;
        value: number;
        target_value?: number;
        created_at: string;
      }>;
    },
    enabled: !!kpiCode,
    staleTime: 5 * 60 * 1000,
  });
}

export function useOccupancyKPIs(params?: { branch_id?: number; department_id?: number }) {
  return useQuery({
    queryKey: ['kpis', 'occupancy', params],
    queryFn: async () => {
      const response = await kpiAPI.getOccupancyKPIs(params);
      return response.data as Record<string, KPIMetric>;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useClaimKPIs(params?: {
  branch_id?: number;
  department_id?: number;
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ['kpis', 'claims', params],
    queryFn: async () => {
      const response = await kpiAPI.getClaimKPIs(params);
      return response.data as Record<string, KPIMetric>;
    },
    staleTime: 5 * 60 * 1000,
  });
}
