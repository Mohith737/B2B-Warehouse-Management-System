// client/src/features/reports/constants/reportsConfig.ts
export const REPORTS_CONFIG = {
  pageTitle: 'Reports',
  defaultMonths: 12,
  minMonths: 1,
  maxMonths: 36,
  defaultMonth: new Date().toISOString().slice(0, 7),
} as const
