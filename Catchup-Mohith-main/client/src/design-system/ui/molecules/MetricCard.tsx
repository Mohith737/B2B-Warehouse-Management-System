// client/src/design-system/ui/molecules/MetricCard.tsx
import { Button, Tile } from '@carbon/react'
import { useNavigate } from 'react-router-dom'

import { LoadingSkeleton } from '../atoms'

type MetricCardProps = {
  label: string
  value: string | number
  trend?: string
  linkTo?: string
  isLoading?: boolean
}

export function MetricCard({
  label,
  value,
  trend,
  linkTo,
  isLoading = false,
}: MetricCardProps): JSX.Element {
  const navigate = useNavigate()

  if (isLoading) {
    return <LoadingSkeleton lines={2} state="loading" />
  }

  return (
    <Tile>
      <h4>{label}</h4>
      <h2>{String(value)}</h2>
      {trend ? <p>{trend}</p> : null}
      {linkTo ? (
        <Button kind="ghost" onClick={() => navigate(linkTo)} size="sm">
          View
        </Button>
      ) : null}
    </Tile>
  )
}
