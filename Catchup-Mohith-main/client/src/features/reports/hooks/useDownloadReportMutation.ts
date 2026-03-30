// client/src/features/reports/hooks/useDownloadReportMutation.ts
import { useMutation } from '@tanstack/react-query'

import { apiClient } from '../../../api/client'
import type { DownloadReportRequest } from '../types'

function extractFilename(
  contentDisposition: string | undefined,
  fallback: string,
): string {
  const match = contentDisposition?.match(/filename="(.+)"/)
  return match?.[1] ?? fallback
}

async function downloadCSV(url: string, defaultFilename: string): Promise<void> {
  const response = await apiClient.get<Blob>(url, { responseType: 'blob' })
  const disposition = response.headers['content-disposition'] as string | undefined
  const filename = extractFilename(disposition, defaultFilename)

  const blob = new Blob([response.data], { type: 'text/csv' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

async function runDownload(request: DownloadReportRequest): Promise<void> {
  if (request.type === 'supplier') {
    const { supplierId, months } = request.payload
    await downloadCSV(
      `/reports/suppliers/${supplierId}?months=${months}`,
      `supplier-report-${supplierId}.csv`,
    )
    return
  }

  const { month } = request.payload
  await downloadCSV(
    `/reports/monthly-tier-summary?month=${month}`,
    `monthly-tier-summary-${month}.csv`,
  )
}

export function useDownloadReportMutation() {
  return useMutation({
    mutationFn: runDownload,
    retry: 0,
  })
}
