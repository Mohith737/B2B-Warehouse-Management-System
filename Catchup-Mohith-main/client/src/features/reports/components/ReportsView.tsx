// client/src/features/reports/components/ReportsView.tsx
import {
  Button,
  NumberInput,
  Select,
  SelectItem,
  Tag,
  TextInput,
  Tile,
} from '@carbon/react'
import { Download } from '@carbon/icons-react'

import type { SupplierRead } from '../../suppliers/types'
import styles from './ReportsView.module.scss'

type ReportsViewProps = {
  suppliers: SupplierRead[]
  supplierId: string
  months: number
  month: string
  isLoadingSuppliers: boolean
  isDownloading: boolean
  onSupplierIdChange: (supplierId: string) => void
  onMonthsChange: (months: number) => void
  onMonthChange: (month: string) => void
  onDownloadSupplierReport: () => void
  onDownloadMonthlyTierSummary: () => void
}

export function ReportsView({
  suppliers,
  supplierId,
  months,
  month,
  isLoadingSuppliers,
  isDownloading,
  onSupplierIdChange,
  onMonthsChange,
  onMonthChange,
  onDownloadSupplierReport,
  onDownloadMonthlyTierSummary,
}: ReportsViewProps): JSX.Element {
  return (
    <div className={styles.page}>
      <Tile className={styles.sectionTile}>
        <div className={styles.sectionHeader}>
          <h4 className={styles.sectionTitle}>Supplier Performance</h4>
          <Tag type="blue">CSV</Tag>
        </div>
        <div className={styles.supplierRow}>
          <Select
            id="reports-supplier"
            labelText="Supplier"
            onChange={(event) => onSupplierIdChange(event.target.value)}
            value={supplierId}
          >
            <SelectItem
              text={isLoadingSuppliers ? 'Loading suppliers...' : 'Choose a supplier'}
              value=""
            />
            {suppliers.map((supplier) => (
              <SelectItem key={supplier.id} text={supplier.name} value={supplier.id} />
            ))}
          </Select>
          <NumberInput
            id="reports-months"
            label="Months"
            max={36}
            min={1}
            onChange={(_, state) => onMonthsChange(Number(state.value) || 1)}
            value={months}
          />
          <Button
            className={styles.downloadButton}
            disabled={!supplierId || isDownloading}
            kind="primary"
            onClick={onDownloadSupplierReport}
          >
            <Download size={16} />
            Download CSV
          </Button>
        </div>
      </Tile>

      <Tile className={styles.sectionTile}>
        <div className={styles.sectionHeader}>
          <h4 className={styles.sectionTitle}>Monthly Tier Summary</h4>
          <Tag type="teal">Monthly</Tag>
        </div>
        <div className={styles.tierRow}>
          <TextInput
            id="reports-month"
            labelText="Month (YYYY-MM)"
            onChange={(event) => onMonthChange(event.target.value)}
            value={month}
          />
          <Button
            className={styles.downloadButton}
            disabled={isDownloading}
            kind="primary"
            onClick={onDownloadMonthlyTierSummary}
          >
            <Download size={16} />
            Download CSV
          </Button>
        </div>
      </Tile>
    </div>
  )
}
