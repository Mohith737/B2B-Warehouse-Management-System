// client/src/features/dashboard/hooks/useDashboardQuery.ts
import { useQuery } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import { DASHBOARD_QUERY_CONFIG } from '../constants/dashboardConfig'
import type { DashboardRead } from '../types'

async function fetchDashboard(): Promise<DashboardRead> {
  const response = await apiClient.get<ApiResponse<DashboardRead>>('/dashboard')
  return response.data.data
}

export function useDashboardQuery() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    staleTime: DASHBOARD_QUERY_CONFIG.staleTimeMs,
    refetchInterval: DASHBOARD_QUERY_CONFIG.refetchIntervalMs,
    refetchIntervalInBackground: false,
    retry: 1,
  })
}
