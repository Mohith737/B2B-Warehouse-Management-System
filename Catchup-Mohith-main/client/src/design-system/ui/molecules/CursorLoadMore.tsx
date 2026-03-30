// client/src/design-system/ui/molecules/CursorLoadMore.tsx
import { Button, InlineLoading } from '@carbon/react'

type CursorLoadMoreProps = {
  hasNextCursor: boolean
  isLoading: boolean
  onLoadMore: () => void
}

export function CursorLoadMore({
  hasNextCursor,
  isLoading,
  onLoadMore,
}: CursorLoadMoreProps): JSX.Element | null {
  if (!hasNextCursor) {
    return null
  }

  return (
    <>
      {isLoading ? <InlineLoading description="Loading more rows" /> : null}
      <Button disabled={isLoading} kind="secondary" onClick={onLoadMore}>
        Load More
      </Button>
    </>
  )
}
