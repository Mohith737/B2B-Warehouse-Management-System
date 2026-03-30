// client/src/design-system/ui/atoms/DashboardMetricCard.tsx
import { Tile } from '@carbon/react'
import { ArrowDown, ArrowUp } from '@carbon/icons-react'

import styles from './DashboardMetricCard.module.scss'

type DashboardMetricCardProps = {
  title: string
  value: string | number
  unit?: string
  trend: 'up' | 'down' | 'neutral'
  trendLabel: string
  variant: 'default' | 'warning' | 'danger'
}

export function DashboardMetricCard({
  title,
  value,
  unit,
  trend,
  trendLabel,
  variant,
}: DashboardMetricCardProps): JSX.Element {
  const variantClass =
    variant === 'warning' ? styles.warning : variant === 'danger' ? styles.danger : ''

  const trendClass =
    trend === 'up'
      ? styles.trendUp
      : trend === 'down'
        ? styles.trendDown
        : styles.trendNeutral

  return (
    <Tile className={`${styles.card} ${variantClass}`}>
      <p className={styles.title}>{title}</p>
      <div className={styles.valueRow}>
        <p className={styles.value}>{value}</p>
        {unit ? <span className={styles.unit}>{unit}</span> : null}
      </div>
      <div className={`${styles.trendRow} ${trendClass}`}>
        {trend === 'up' ? <ArrowUp size={14} /> : null}
        {trend === 'down' ? <ArrowDown size={14} /> : null}
        <span>{trendLabel}</span>
      </div>
    </Tile>
  )
}
