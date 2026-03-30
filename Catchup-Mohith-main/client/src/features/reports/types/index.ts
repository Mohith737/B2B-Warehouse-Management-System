// client/src/features/reports/types/index.ts
export type SupplierReportRequest = {
  supplierId: string
  months: number
}

export type MonthlyTierSummaryRequest = {
  month: string
}

export type DownloadReportRequest =
  | { type: 'supplier'; payload: SupplierReportRequest }
  | { type: 'monthly-tier-summary'; payload: MonthlyTierSummaryRequest }
