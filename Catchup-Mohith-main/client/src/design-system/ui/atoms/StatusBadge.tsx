// client/src/design-system/ui/atoms/StatusBadge.tsx
import { Tag, TagSkeleton } from '@carbon/react'

type TagType =
  | 'red'
  | 'magenta'
  | 'purple'
  | 'blue'
  | 'cyan'
  | 'teal'
  | 'green'
  | 'gray'
  | 'cool-gray'
  | 'warm-gray'
  | 'high-contrast'
  | 'outline'

type ViewState = 'loading' | 'empty' | 'error' | 'success'

interface StatusBadgeProps {
  status: string
  domain?: 'po' | 'grn' | 'stock' | 'tier' | 'user' | 'backorder'
  state?: ViewState
}

const STATUS_TYPE: Record<string, TagType> = {
  draft: 'gray',
  submitted: 'blue',
  acknowledged: 'teal',
  shipped: 'purple',
  received: 'green',
  closed: 'cool-gray',
  cancelled: 'red',
  open: 'blue',
  completed: 'green',
  pending: 'warm-gray',
  fulfilled: 'green',
  critical: 'red',
  warning: 'magenta',
  normal: 'green',
  low_stock: 'magenta',
  out_of_stock: 'red',
  in_stock: 'green',
  silver: 'gray',
  gold: 'warm-gray',
  diamond: 'blue',
  active: 'green',
  inactive: 'gray',
  approved: 'green',
  rejected: 'red',
}

const STATUS_LABEL: Record<string, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  acknowledged: 'Acknowledged',
  shipped: 'Shipped',
  received: 'Received',
  closed: 'Closed',
  cancelled: 'Cancelled',
  open: 'Open',
  completed: 'Completed',
  pending: 'Pending',
  fulfilled: 'Fulfilled',
  critical: 'Critical',
  warning: 'Warning',
  normal: 'Normal',
  low_stock: 'Low Stock',
  out_of_stock: 'Out of Stock',
  in_stock: 'In Stock',
  silver: 'Silver',
  gold: 'Gold',
  diamond: 'Diamond',
  active: 'Active',
  inactive: 'Inactive',
  approved: 'Approved',
  rejected: 'Rejected',
}

function toTitleCaseLabel(value: string): string {
  return value
    .replace(/_/g, ' ')
    .trim()
    .split(/\s+/)
    .map((segment) => {
      if (segment.length === 0) {
        return segment
      }
      return `${segment.charAt(0).toUpperCase()}${segment.slice(1).toLowerCase()}`
    })
    .join(' ')
}

export function StatusBadge({
  status,
  domain,
  state = 'success',
}: StatusBadgeProps): JSX.Element {
  void domain

  if (state === 'loading') {
    return <TagSkeleton />
  }

  if (state === 'error') {
    return <Tag type="red">Unavailable</Tag>
  }

  if (state === 'empty') {
    return <Tag type="gray">Not Set</Tag>
  }

  const normalizedStatus = status.trim().toLowerCase()
  const type = STATUS_TYPE[normalizedStatus] ?? 'gray'
  const label = STATUS_LABEL[normalizedStatus] ?? toTitleCaseLabel(status)

  return <Tag type={type}>{label}</Tag>
}
