// client/src/design-system/ui/organisms/GRNSummaryPanel.tsx
import { ActionableNotification, Button, InlineNotification, Tile } from '@carbon/react'

import { EmptyState, LoadingSkeleton } from '../atoms'

type GRNSummaryPanelProps = {
  totalLines: number
  fullyReceivedLines: number
  pendingLines: number
  backorderLines: number
  state: 'loading' | 'empty' | 'error' | 'success'
  errorMessage?: string
  receiveFailureSummary?: string | null
  completeErrorMessage?: string | null
  onRetry?: () => void
  onComplete?: () => void
  onRetryComplete?: () => void
  onDismissReceiveFailures?: () => void
}

export function GRNSummaryPanel({
  totalLines,
  fullyReceivedLines,
  pendingLines,
  backorderLines,
  state,
  errorMessage,
  receiveFailureSummary,
  completeErrorMessage,
  onRetry,
  onComplete,
  onRetryComplete,
  onDismissReceiveFailures,
}: GRNSummaryPanelProps): JSX.Element {
  if (state === 'loading') {
    return <LoadingSkeleton lines={4} state="loading" />
  }

  if (state === 'error') {
    return (
      <ActionableNotification
        actionButtonLabel="Retry"
        hideCloseButton
        kind="error"
        onActionButtonClick={() => onRetry?.()}
        subtitle={errorMessage ?? 'Unable to load GRN summary.'}
        title="Summary unavailable"
      />
    )
  }

  if (state === 'empty') {
    return (
      <EmptyState
        description="Start scanning lines to build the GRN summary."
        state="empty"
        title="No summary yet"
      />
    )
  }

  return (
    <>
      <Tile>
        {`Total lines: ${totalLines}`}
        <br />
        {`Fully received: ${fullyReceivedLines}`}
        <br />
        {`Pending: ${pendingLines}`}
        <br />
        {`Backorders: ${backorderLines}`}
      </Tile>
      {receiveFailureSummary ? (
        <>
          <InlineNotification
            kind="error"
            subtitle={receiveFailureSummary}
            title="Some line receives failed"
          />
          <Button kind="ghost" onClick={() => onDismissReceiveFailures?.()}>
            Dismiss
          </Button>
        </>
      ) : null}
      {completeErrorMessage ? (
        <>
          <InlineNotification
            kind="error"
            subtitle={completeErrorMessage}
            title="Unable to complete GRN"
          />
          <Button kind="secondary" onClick={() => onRetryComplete?.()}>
            Retry complete
          </Button>
        </>
      ) : null}
      <InlineNotification
        hideCloseButton
        kind={backorderLines > 0 ? 'warning' : 'success'}
        subtitle={
          backorderLines > 0
            ? 'Completing GRN will create backorder records for pending quantities.'
            : 'All lines are fully receivable.'
        }
        title="Completion impact"
      />
      <Button
        disabled={pendingLines > 0 && !onComplete}
        kind="primary"
        onClick={() => onComplete?.()}
      >
        Complete GRN
      </Button>
    </>
  )
}
