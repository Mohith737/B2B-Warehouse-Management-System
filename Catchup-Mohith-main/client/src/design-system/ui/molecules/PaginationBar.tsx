// client/src/design-system/ui/molecules/PaginationBar.tsx
import { Pagination } from '@carbon/react'

type PaginationBarProps = {
  page: number
  pageSize: number
  totalItems: number
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
}

export function PaginationBar({
  page,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
}: PaginationBarProps): JSX.Element {
  return (
    <Pagination
      backwardText="Previous page"
      forwardText="Next page"
      itemRangeText={(min, max, total) => `${min}-${max} of ${total}`}
      onChange={({ page: nextPage, pageSize: nextPageSize }) => {
        if (nextPageSize !== pageSize) {
          onPageSizeChange(nextPageSize)
        }
        if (nextPage !== page) {
          onPageChange(nextPage)
        }
      }}
      page={page}
      pageSize={pageSize}
      pageSizes={[10, 20, 50]}
      totalItems={totalItems}
    />
  )
}
