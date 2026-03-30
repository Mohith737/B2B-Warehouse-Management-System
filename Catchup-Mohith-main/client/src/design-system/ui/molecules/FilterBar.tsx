// client/src/design-system/ui/molecules/FilterBar.tsx
import { ContentSwitcher, Switch } from '@carbon/react'

export type FilterOption = {
  value: string
  label: string
}

type FilterBarProps = {
  filters: FilterOption[]
  activeFilter: string
  onFilterChange: (value: string) => void
}

export function FilterBar({
  filters,
  activeFilter,
  onFilterChange,
}: FilterBarProps): JSX.Element {
  const selectedIndex = Math.max(
    filters.findIndex((filter) => filter.value === activeFilter),
    0,
  )

  return (
    <ContentSwitcher
      onChange={(event) => {
        if (typeof event.index !== 'number') {
          return
        }
        const selectedFilter = filters[event.index]
        if (selectedFilter !== undefined) {
          onFilterChange(selectedFilter.value)
        }
      }}
      selectedIndex={selectedIndex}
    >
      {filters.map((filter) => (
        <Switch key={filter.value} name={filter.value} text={filter.label} />
      ))}
    </ContentSwitcher>
  )
}
