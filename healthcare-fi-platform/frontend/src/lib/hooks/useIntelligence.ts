import { useQuery } from '@tanstack/react-query';
import { intelligenceAPI } from '@/lib/api/client';

export function useIntelligenceFeed(params?: { limit?: number; type?: string }) {
  return useQuery({
    queryKey: ['intelligence', 'feed', params],
    queryFn: async () => {
      const response = await intelligenceAPI.getFeed(params);
      return response.data;
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useAnomalies(params?: { status?: string; severity?: string; limit?: number }) {
  return useQuery({
    queryKey: ['intelligence', 'anomalies', params],
    queryFn: async () => {
      const response = await intelligenceAPI.listAnomalies(params);
      return response.data;
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useInsights(params?: { status?: string; limit?: number }) {
  return useQuery({
    queryKey: ['intelligence', 'insights', params],
    queryFn: async () => {
      const response = await intelligenceAPI.listInsights(params);
      return response.data;
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useRecommendations(params?: { status?: string; limit?: number }) {
  return useQuery({
    queryKey: ['intelligence', 'recommendations', params],
    queryFn: async () => {
      const response = await intelligenceAPI.listRecommendations(params);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useOpportunities(params?: { status?: string; limit?: number }) {
  return useQuery({
    queryKey: ['intelligence', 'opportunities', params],
    queryFn: async () => {
      const response = await intelligenceAPI.listOpportunities(params);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}
