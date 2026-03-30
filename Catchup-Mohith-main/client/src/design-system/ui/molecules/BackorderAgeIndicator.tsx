// client/src/design-system/ui/molecules/BackorderAgeIndicator.tsx
import { Tag } from '@carbon/react'

type BackorderAgeIndicatorProps = {
  createdAt: string
  overdueThresholdDays?: number
}

export function BackorderAgeIndicator({
  createdAt,
  overdueThresholdDays = 7,
}: BackorderAgeIndicatorProps): JSX.Element {
  const ageMs = Date.now() - new Date(createdAt).getTime()
  const ageDays = Math.max(0, Math.floor(ageMs / (1000 * 60 * 60 * 24)))

  if (ageDays > overdueThresholdDays) {
    return <Tag type="red">Overdue</Tag>
  }

  return <Tag type="blue">{`${ageDays} days`}</Tag>
}
