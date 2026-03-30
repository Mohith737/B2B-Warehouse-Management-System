// client/src/features/admin/components/AdminUsersView.tsx
import {
  ActionableNotification,
  Button,
  Select,
  SelectItem,
  Stack,
  TextInput,
  Tile,
} from '@carbon/react'

import { AdminUsersTable } from '../../../design-system/ui/organisms'
import type { AdminUserRead } from '../types'
import styles from './AdminUsersView.module.scss'

type AdminUsersViewProps = {
  users: AdminUserRead[]
  isLoading: boolean
  error: string | null
  isCreateOpen: boolean
  formState: {
    username: string
    email: string
    password: string
    role: 'warehouse_staff' | 'procurement_manager' | 'admin'
    is_active: boolean
  }
  onOpenCreate: () => void
  onCloseCreate: () => void
  onFormChange: (patch: Partial<AdminUsersViewProps['formState']>) => void
  onSubmitCreate: () => void
  onRetry: () => void
}

export function AdminUsersView({
  users,
  isLoading,
  error,
  isCreateOpen,
  formState,
  onOpenCreate,
  onCloseCreate,
  onFormChange,
  onSubmitCreate,
  onRetry,
}: AdminUsersViewProps): JSX.Element {
  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <h1 className={styles.pageTitle}>Users</h1>
        <Button kind="primary" onClick={onOpenCreate}>
          Create User
        </Button>
      </div>

      <Tile className={styles.tableCard}>
        <AdminUsersTable
          error={error}
          isEmpty={!isLoading && !error && users.length === 0}
          isLoading={isLoading}
          onRetry={onRetry}
          users={users.map((user) => ({ ...user, username: user.full_name }))}
        />
      </Tile>

      {isCreateOpen ? (
        <div className={styles.formWrap}>
          <Tile className={styles.formCard}>
            <Stack gap={6}>
              <div>
                <h2 className={styles.formTitle}>Create User</h2>
                <p className={styles.formSubtitle}>
                  Add a new team member with an appropriate role.
                </p>
              </div>

              {error ? (
                <ActionableNotification
                  actionButtonLabel="Retry"
                  hideCloseButton
                  inline
                  kind="error"
                  lowContrast
                  onActionButtonClick={onRetry}
                  subtitle={error}
                  title="Failed to load users"
                />
              ) : null}

              <TextInput
                id="admin-create-username"
                labelText="Username"
                onChange={(event) => onFormChange({ username: event.target.value })}
                value={formState.username}
              />
              <TextInput
                id="admin-create-email"
                labelText="Email"
                onChange={(event) => onFormChange({ email: event.target.value })}
                value={formState.email}
              />
              <TextInput
                id="admin-create-password"
                labelText="Password"
                onChange={(event) => onFormChange({ password: event.target.value })}
                type="password"
                value={formState.password}
              />
              <Select
                id="admin-create-role"
                labelText="Role"
                onChange={(event) =>
                  onFormChange({
                    role: event.target.value as
                      | 'warehouse_staff'
                      | 'procurement_manager'
                      | 'admin',
                  })
                }
                value={formState.role}
              >
                <SelectItem text="Warehouse Staff" value="warehouse_staff" />
                <SelectItem text="Procurement Manager" value="procurement_manager" />
                <SelectItem text="Admin" value="admin" />
              </Select>

              <div className={styles.formActions}>
                <Button kind="secondary" onClick={onCloseCreate}>
                  Cancel
                </Button>
                <Button kind="primary" onClick={onSubmitCreate}>
                  Create
                </Button>
              </div>
            </Stack>
          </Tile>
        </div>
      ) : null}
    </div>
  )
}
