// client/src/features/dashboard/components/TopSuppliersList.tsx
import styles from '../dashboard.module.scss'
import type { DashboardTopSupplier } from '../types'

type TopSuppliersListProps = {
  data: DashboardTopSupplier[]
}

export function TopSuppliersList({ data }: TopSuppliersListProps): JSX.Element {
  return (
    <ol className={styles.suppliersList}>
      {data.map((supplier, index) => (
        <li
          className={styles.suppliersItem}
          key={`${supplier.rank}-${supplier.supplierName}`}
        >
          <span className={styles.rank}>{supplier.rank ?? index + 1}</span>
          <span>{supplier.supplierName}</span>
          <span>{supplier.deliveryCount}</span>
        </li>
      ))}
    </ol>
  )
}
