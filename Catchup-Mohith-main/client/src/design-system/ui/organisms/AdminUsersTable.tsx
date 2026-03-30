// client/src/design-system/ui/organisms/AdminUsersTable.tsx
import {
  ActionableNotification,
  DataTable,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react'

import { EmptyState, LoadingSkeleton, StatusBadge } from '../atoms'

type AdminUserRow = {
  id: string
  username: string
  email: string
  role: 'warehouse_staff' | 'procurement_manager' | 'admin'
  is_active: boolean
}

type AdminUsersTableProps = {
  users: AdminUserRow[]
  isLoading: boolean
  isEmpty: boolean
  error: string | null
  onRetry: () => void
}

const headers = [
  { key: 'name', header: 'Name' },
  { key: 'email', header: 'Email' },
  { key: 'role', header: 'Role' },
  { key: 'active', header: 'Status' },
]

export function AdminUsersTable({
  users,
  isLoading,
  isEmpty,
  error,
  onRetry,
}: AdminUsersTableProps): JSX.Element {
  if (isLoading) {
    return <LoadingSkeleton lines={6} state="loading" />
  }

  if (error) {
    return (
      <ActionableNotification
        actionButtonLabel="Retry"
        hideCloseButton
        kind="error"
        onActionButtonClick={onRetry}
        subtitle={error}
        title="Failed to load users"
      />
    )
  }

  if (isEmpty) {
    return (
      <EmptyState description="No users were found." state="empty" title="No users" />
    )
  }

  const rows = users.map((user) => ({
    id: user.id,
    name: user.username,
    email: user.email,
    role: user.role,
    active: user.is_active ? 'active' : 'inactive',
  }))

  return (
    <DataTable headers={headers} rows={rows}>
      {({ rows: dataRows, headers: dataHeaders, getHeaderProps, getTableProps }) => (
        <TableContainer title="Users">
          <Table {...getTableProps()}>
            <TableHead>
              <TableRow>
                {dataHeaders.map((header) => {
                  const { key, ...headerProps } = getHeaderProps({ header })
                  return (
                    <TableHeader key={key} {...headerProps}>
                      {header.header}
                    </TableHeader>
                  )
                })}
              </TableRow>
            </TableHead>
            <TableBody>
              {dataRows.map((row) => (
                <TableRow key={row.id}>
                  {row.cells.map((cell) => {
                    if (cell.info.header === 'active') {
                      const isActive =
                        String(cell.value).toLowerCase() === 'active'
                      return (
                        <TableCell key={cell.id}>
                          <StatusBadge
                            domain="backorder"
                            status={isActive ? 'open' : 'cancelled'}
                          />
                        </TableCell>
                      )
                    }

                    return <TableCell key={cell.id}>{cell.value}</TableCell>
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </DataTable>
  )
}
