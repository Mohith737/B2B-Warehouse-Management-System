// client/src/design-system/ui/atoms/LoadingSkeleton.tsx
import { InlineNotification, SkeletonText } from '@carbon/react'

type ViewState = 'loading' | 'empty' | 'error' | 'success'

type LoadingSkeletonProps = {
  lines?: number
  width?: string
  state?: ViewState
}

export function LoadingSkeleton({
  lines = 3,
  width = '100%',
  state = 'loading',
}: LoadingSkeletonProps): JSX.Element {
  if (state === 'error') {
    return (
      <InlineNotification
        hideCloseButton
        kind="error"
        subtitle="Failed to load placeholder content."
        title="Loading failed"
      />
    )
  }

  if (state === 'empty') {
    return (
      <InlineNotification
        hideCloseButton
        kind="info"
        subtitle="No placeholder lines to show."
        title="Nothing to display"
      />
    )
  }

  if (state === 'success') {
    return (
      <InlineNotification
        hideCloseButton
        kind="success"
        subtitle="Content loaded successfully."
        title="Loaded"
      />
    )
  }

  return (
    <>
      {Array.from({ length: lines }).map((_, index) => (
        <SkeletonText key={`skeleton-line-${index}`} width={width} />
      ))}
    </>
  )
}
