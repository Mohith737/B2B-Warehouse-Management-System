// client/src/design-system/ui/atoms/EmptyState.tsx
import { Button, Heading, InlineNotification, Tile } from '@carbon/react'

import { LoadingSkeleton } from './LoadingSkeleton'

type ViewState = 'loading' | 'empty' | 'error' | 'success'

type EmptyStateProps = {
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  state?: ViewState
}

export function EmptyState({
  title,
  description,
  action,
  state = 'empty',
}: EmptyStateProps): JSX.Element {
  if (state === 'loading') {
    return <LoadingSkeleton />
  }

  if (state === 'error') {
    return (
      <InlineNotification
        hideCloseButton
        kind="error"
        subtitle={description}
        title={title}
      />
    )
  }

  if (state === 'success') {
    return (
      <InlineNotification
        hideCloseButton
        kind="success"
        subtitle={description}
        title={title}
      />
    )
  }

  return (
    <Tile className="sb-empty-state">
      <Heading>{title}</Heading>
      <p>{description}</p>
      {action ? <Button onClick={action.onClick}>{action.label}</Button> : null}
    </Tile>
  )
}
