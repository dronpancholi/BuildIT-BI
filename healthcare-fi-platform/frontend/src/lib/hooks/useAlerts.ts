import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertsAPI } from '@/lib/api/client';

export interface Alert {
  id: number;
  title: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  category: string;
  is_read: boolean;
  is_resolved: boolean;
  recommendation?: string;
  created_at: string;
}

export function useAlerts(params?: {
  severity?: string;
  category?: string;
  is_read?: boolean;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['alerts', 'list', params],
    queryFn: async () => {
      const response = await alertsAPI.listAlerts({ ...params, limit: params?.limit || 50 });
      return response.data as Alert[];
    },
    staleTime: 60 * 1000,
    refetchInterval: 5 * 60 * 1000, // Poll every 5 min
  });
}

export function useAlertStats() {
  return useQuery({
    queryKey: ['alerts', 'stats'],
    queryFn: async () => {
      const response = await alertsAPI.getStats();
      return response.data as {
        total: number;
        critical: number;
        warning: number;
        info: number;
        unread: number;
      };
    },
    staleTime: 60 * 1000,
  });
}

export function useMarkAlertRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => alertsAPI.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => alertsAPI.resolveAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}
