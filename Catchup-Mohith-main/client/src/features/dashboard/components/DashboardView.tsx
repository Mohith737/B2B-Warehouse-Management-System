// client/src/features/dashboard/components/DashboardView.tsx
import { Button, Column, Grid, InlineNotification } from '@carbon/react'
import type { UseQueryResult } from '@tanstack/react-query'
import { useMemo } from 'react'

import {
  DashboardMetricCard,
  EmptyState,
  LoadingSkeleton,
} from '../../../design-system/ui/atoms'
import { StockMovementChart } from '../../../design-system/ui/molecules'
import type { UserRole } from '../../../stores/authStore'
import { METRIC_DEFINITIONS } from '../constants/dashboardConfig'
import styles from '../dashboard.module.scss'
import { LowStockTable } from './LowStockTable'
import { RecentGRNsTable } from './RecentGRNsTable'
import { TopSuppliersList } from './TopSuppliersList'
import type {
  DashboardLowStockProduct,
  DashboardMetricData,
  DashboardRecentGRN,
  DashboardTopSupplier,
} from '../types'

type DashboardViewProps = {
  role: UserRole
  metricsQuery: UseQueryResult<DashboardMetricData>
  lowStockQuery: UseQueryResult<DashboardLowStockProduct[]>
  recentGRNsQuery: UseQueryResult<DashboardRecentGRN[]>
  topSuppliersQuery: UseQueryResult<DashboardTopSupplier[]>
}

function roleLabel(role: UserRole): string {
  return role
    .split('_')
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(' ')
}

type ErrorCardProps = {
  title: string
  message: string
  onRetry: () => void
}

function ErrorCard({ title, message, onRetry }: ErrorCardProps): JSX.Element {
  return (
    <>
      <InlineNotification
        hideCloseButton
        kind="error"
        subtitle={message}
        title={title}
      />
      <Button kind="ghost" onClick={onRetry} size="sm">
        Retry
      </Button>
    </>
  )
}

export function DashboardView({
  role,
  metricsQuery,
  lowStockQuery,
  recentGRNsQuery,
  topSuppliersQuery,
}: DashboardViewProps): JSX.Element {
  const formattedDate = useMemo(
    () =>
      new Intl.DateTimeFormat('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      }).format(new Date()),
    [],
  )

  const metricsData = metricsQuery.data
  const chartData = metricsData?.stockMovement7Days ?? []
  const lowStockData = lowStockQuery.data
  const recentGRNsData = recentGRNsQuery.data
  const topSuppliersData = topSuppliersQuery.data

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Dashboard</h1>
        <p className={styles.pageSubtitle}>
          {formattedDate} · {roleLabel(role)} view
        </p>
      </div>

      <Grid fullWidth>
        <Column lg={16} md={8} sm={4}>
          <div className={styles.metricsGrid}>
            {metricsQuery.isLoading && !metricsData
              ? Array.from({ length: 6 }).map((_, index) => (
                  <LoadingSkeleton
                    key={`metric-skeleton-${index}`}
                    lines={2}
                    state="loading"
                  />
                ))
              : METRIC_DEFINITIONS.map((definition) => {
                  const value = metricsData?.[definition.key] ?? 0
                  const variant =
                    (definition.key === 'outOfStockItems' ||
                      definition.key === 'lowStockItems') &&
                    Number(value) > 0
                      ? definition.key === 'outOfStockItems'
                        ? 'danger'
                        : 'warning'
                      : definition.key === 'openBackorders' && Number(value) > 0
                        ? 'warning'
                        : 'default'

                  return (
                    <DashboardMetricCard
                      key={definition.key}
                      title={definition.title}
                      trend={definition.trend}
                      trendLabel={
                        definition.trend === 'down' ? 'Needs attention' : 'Stable'
                      }
                      unit={definition.unit}
                      value={value}
                      variant={variant}
                    />
                  )
                })}
          </div>
          {metricsQuery.isError ? (
            <ErrorCard
              message={
                (metricsQuery.error as Error)?.message ??
                'Unable to load dashboard metrics.'
              }
              onRetry={() => {
                void metricsQuery.refetch()
              }}
              title="Failed to load metrics"
            />
          ) : null}
        </Column>

        <Column lg={16} md={8} sm={4}>
          <div className={styles.chartsRow}>
            <div className={styles.sectionCard}>
              <p className={styles.sectionTitle}>Stock In vs Stock Out — Last 7 Days</p>
              {metricsQuery.isLoading && !metricsData ? (
                <LoadingSkeleton lines={6} state="loading" />
              ) : metricsQuery.isError ? (
                <ErrorCard
                  message={
                    (metricsQuery.error as Error)?.message ??
                    'Unable to load movement chart.'
                  }
                  onRetry={() => {
                    void metricsQuery.refetch()
                  }}
                  title="Failed to load chart"
                />
              ) : chartData.length > 0 ? (
                <StockMovementChart data={chartData} />
              ) : (
                <EmptyState
                  description="Stock movements will appear here"
                  title="No movement data"
                />
              )}
            </div>

            <div className={styles.sectionCard}>
              <p className={styles.sectionTitle}>Low Stock Products</p>
              {lowStockQuery.isLoading && !lowStockData ? (
                <LoadingSkeleton lines={5} state="loading" />
              ) : lowStockQuery.isError ? (
                <ErrorCard
                  message={
                    (lowStockQuery.error as Error)?.message ??
                    'Unable to load low stock products.'
                  }
                  onRetry={() => {
                    void lowStockQuery.refetch()
                  }}
                  title="Failed to load low stock"
                />
              ) : lowStockData && lowStockData.length > 0 ? (
                <LowStockTable data={lowStockData} />
              ) : (
                <EmptyState
                  description="No products below reorder point"
                  title="All stocked up"
                />
              )}
            </div>
          </div>
        </Column>

        <Column lg={16} md={8} sm={4}>
          <div className={styles.tablesRow}>
            <div className={styles.sectionCard}>
              <p className={styles.sectionTitle}>Recent Goods Receipts</p>
              {recentGRNsQuery.isLoading && !recentGRNsData ? (
                <LoadingSkeleton lines={5} state="loading" />
              ) : recentGRNsQuery.isError ? (
                <ErrorCard
                  message={
                    (recentGRNsQuery.error as Error)?.message ??
                    'Unable to load recent GRNs.'
                  }
                  onRetry={() => {
                    void recentGRNsQuery.refetch()
                  }}
                  title="Failed to load recent GRNs"
                />
              ) : recentGRNsData && recentGRNsData.length > 0 ? (
                <RecentGRNsTable data={recentGRNsData} />
              ) : (
                <EmptyState
                  description="Completed GRNs will appear here"
                  title="No recent receipts"
                />
              )}
            </div>

            <div className={styles.sectionCard}>
              <p className={styles.sectionTitle}>Top Suppliers by Deliveries</p>
              {topSuppliersQuery.isLoading && !topSuppliersData ? (
                <LoadingSkeleton lines={5} state="loading" />
              ) : topSuppliersQuery.isError ? (
                <ErrorCard
                  message={
                    (topSuppliersQuery.error as Error)?.message ??
                    'Unable to load top suppliers.'
                  }
                  onRetry={() => {
                    void topSuppliersQuery.refetch()
                  }}
                  title="Failed to load top suppliers"
                />
              ) : topSuppliersData && topSuppliersData.length > 0 ? (
                <TopSuppliersList data={topSuppliersData} />
              ) : (
                <EmptyState
                  description="Supplier rankings will appear here"
                  title="No supplier data"
                />
              )}
            </div>
          </div>
        </Column>
      </Grid>
    </div>
  )
}
