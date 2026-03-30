// client/src/design-system/ui/atoms/PageTitle.tsx
import { Heading, InlineNotification, Tile } from '@carbon/react'

import { EmptyState } from './EmptyState'
import { LoadingSkeleton } from './LoadingSkeleton'

type ViewState = 'loading' | 'empty' | 'error' | 'success'

type PageTitleProps = {
  title: string
  subtitle?: string
  state?: ViewState
}

export function PageTitle({
  title,
  subtitle,
  state = 'success',
}: PageTitleProps): JSX.Element {
  if (state === 'loading') {
    return <LoadingSkeleton lines={2} />
  }

  if (state === 'empty') {
    return <EmptyState description="No page title available." title="No title" />
  }

  if (state === 'error') {
    return (
      <InlineNotification
        hideCloseButton
        kind="error"
        subtitle="Could not render the page title."
        title="Title unavailable"
      />
    )
  }

  return (
    <Tile className="sb-page-title">
      <Heading>{title}</Heading>
      {subtitle ? <p>{subtitle}</p> : null}
    </Tile>
  )
}
