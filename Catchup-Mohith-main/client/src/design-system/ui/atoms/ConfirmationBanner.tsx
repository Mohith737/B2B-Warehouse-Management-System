// client/src/design-system/ui/atoms/ConfirmationBanner.tsx
import { Button, ButtonSet, InlineNotification, Tile } from '@carbon/react'

import { EmptyState } from './EmptyState'
import { LoadingSkeleton } from './LoadingSkeleton'

type ViewState = 'loading' | 'empty' | 'error' | 'success'

type ConfirmationBannerProps = {
  message: string
  onContinue: () => void
  onStartFresh: () => void
  state?: ViewState
}

export function ConfirmationBanner({
  message,
  onContinue,
  onStartFresh,
  state = 'success',
}: ConfirmationBannerProps): JSX.Element {
  if (state === 'loading') {
    return <LoadingSkeleton lines={2} />
  }

  if (state === 'empty') {
    return (
      <EmptyState
        description="There is no saved session to continue."
        title="No saved session"
      />
    )
  }

  if (state === 'error') {
    return (
      <InlineNotification
        hideCloseButton
        kind="error"
        subtitle="Unable to load saved session state."
        title="Session unavailable"
      />
    )
  }

  return (
    <Tile className="sb-confirmation-banner">
      <InlineNotification
        hideCloseButton
        kind="info"
        subtitle={message}
        title="Saved progress found"
      />
      <ButtonSet>
        <Button kind="primary" onClick={onContinue}>
          Continue
        </Button>
        <Button kind="secondary" onClick={onStartFresh}>
          Start Fresh
        </Button>
      </ButtonSet>
    </Tile>
  )
}
