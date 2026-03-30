// client/src/design-system/ui/molecules/DataTableToolbar.tsx
import {
  Button,
  TableToolbar,
  TableToolbarContent,
  TableToolbarSearch,
} from '@carbon/react'

type DataTableToolbarAction = {
  label: string
  onClick: () => void
  kind?: 'primary' | 'secondary' | 'tertiary'
}

type DataTableToolbarProps = {
  title: string
  totalCount: number
  searchProps: {
    value: string
    onChange: (value: string) => void
    placeholder?: string
  }
  actions?: DataTableToolbarAction[]
}

export function DataTableToolbar({
  title,
  totalCount,
  searchProps,
  actions = [],
}: DataTableToolbarProps): JSX.Element {
  return (
    <TableToolbar aria-label={`${title} toolbar`}>
      <TableToolbarContent>
        <TableToolbarSearch
          expanded
          labelText={`${title} search`}
          onChange={(event) => {
            const value =
              typeof event === 'string' ? event : (event?.target?.value ?? '')
            searchProps.onChange(value)
          }}
          placeholder={searchProps.placeholder ?? `Search ${title.toLowerCase()}`}
          value={searchProps.value}
        />
        {actions.map((action) => (
          <Button
            key={action.label}
            kind={action.kind ?? 'secondary'}
            onClick={action.onClick}
          >
            {action.label}
          </Button>
        ))}
        <Button kind="ghost" size="sm">
          {`Total: ${totalCount}`}
        </Button>
      </TableToolbarContent>
    </TableToolbar>
  )
}
