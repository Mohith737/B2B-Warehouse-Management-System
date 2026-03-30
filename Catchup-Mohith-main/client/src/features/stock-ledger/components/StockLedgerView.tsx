// client/src/features/stock-ledger/components/StockLedgerView.tsx
import { Stack, Tile } from '@carbon/react'

import { CursorLoadMore } from '../../../design-system/ui/molecules'
import { StockLedgerTable } from '../../../design-system/ui/organisms'
import type { StockLedgerPageResponse } from '../types'
import styles from './StockLedgerView.module.scss'

type StockLedgerViewProps = {
  pages: StockLedgerPageResponse[]
  isLoading: boolean
  isFetchingNextPage: boolean
  error: string | null
  onRetry: () => void
  onLoadMore: () => void
}

export function StockLedgerView({
  pages,
  isLoading,
  isFetchingNextPage,
  error,
  onRetry,
  onLoadMore,
}: StockLedgerViewProps): JSX.Element {
  const toNumber = (value: unknown): number => {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : 0
  }

  const formatQuantity = (value: number): string =>
    new Intl.NumberFormat(undefined, {
      maximumFractionDigits: 2,
      minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
    }).format(value)

  const entries = pages.flatMap((page) =>
    page.data.map((entry) => ({
      ...entry,
      quantity_change: toNumber(entry.quantity_change),
      balance_after: toNumber(entry.balance_after),
      product_name: entry.product_name ?? 'Unknown Product',
      product_sku: entry.product_sku ?? 'N/A',
      reference_type: entry.reference_type ?? null,
    })),
  )
  const hasNextCursor =
    (pages.length > 0 ? pages[pages.length - 1]?.meta.next_cursor : null) !== null
  const netChange = entries.reduce((sum, entry) => sum + entry.quantity_change, 0)
  const positiveChanges = entries.filter((entry) => entry.quantity_change > 0).length
  const negativeChanges = entries.filter((entry) => entry.quantity_change < 0).length

  return (
    <Stack className={styles.page} gap={6}>
      <Tile className={styles.summaryTile}>
        <div className={styles.summaryGrid}>
          <div>
            <p className={styles.summaryLabel}>Net Movement</p>
            <p
              className={
                netChange >= 0
                  ? styles.summaryValuePositive
                  : styles.summaryValueNegative
              }
            >
              {netChange > 0
                ? `+${formatQuantity(netChange)}`
                : formatQuantity(netChange)}
            </p>
          </div>
          <div>
            <p className={styles.summaryLabel}>Increases</p>
            <p className={styles.summaryValue}>{positiveChanges}</p>
          </div>
          <div>
            <p className={styles.summaryLabel}>Decreases</p>
            <p className={styles.summaryValue}>{negativeChanges}</p>
          </div>
        </div>
      </Tile>

      <StockLedgerTable
        entries={entries}
        error={error}
        isEmpty={!isLoading && !error && entries.length === 0}
        isLoading={isLoading}
        onRetry={onRetry}
      />

      <CursorLoadMore
        hasNextCursor={Boolean(hasNextCursor)}
        isLoading={isFetchingNextPage}
        onLoadMore={onLoadMore}
      />
    </Stack>
  )
}
