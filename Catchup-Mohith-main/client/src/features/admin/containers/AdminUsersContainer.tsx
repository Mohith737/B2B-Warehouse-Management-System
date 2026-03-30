// client/src/features/admin/containers/AdminUsersContainer.tsx
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuthStore } from '../../../stores/authStore'
import { useUIStore } from '../../../stores/uiStore'
import { AdminUsersView } from '../components/AdminUsersView'
import { useCreateUserMutation } from '../hooks/useCreateUserMutation'
import { useUsersQuery } from '../hooks/useUsersQuery'
import type { AdminUserRead } from '../types'

export function AdminUsersContainer(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role)
  const addToast = useUIStore((state) => state.addToast)

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formState, setFormState] = useState({
    username: '',
    email: '',
    password: '',
    role: 'warehouse_staff' as 'warehouse_staff' | 'procurement_manager' | 'admin',
    is_active: true,
  })

  useEffect(() => {
    if (role !== 'admin') {
      navigate('/unauthorized')
    }
  }, [navigate, role])

  const usersQuery = useUsersQuery({ page: 1, pageSize: 20 })
  const createUserMutation = useCreateUserMutation()

  const users = useMemo<AdminUserRead[]>(
    () => usersQuery.data?.data ?? [],
    [usersQuery.data],
  )

  useEffect(() => {
    if (usersQuery.isError) {
      const message =
        typeof usersQuery.error === 'object' &&
        usersQuery.error !== null &&
        'message' in usersQuery.error &&
        typeof usersQuery.error.message === 'string'
          ? usersQuery.error.message
          : 'Failed to load users.'
      setError(message)
    } else {
      setError(null)
    }
  }, [usersQuery.error, usersQuery.isError])

  return (
    <AdminUsersView
      error={error}
      formState={formState}
      isCreateOpen={isCreateOpen}
      isLoading={usersQuery.isLoading}
      onCloseCreate={() => {
        setIsCreateOpen(false)
      }}
      onFormChange={(patch) => {
        setFormState((previous) => ({ ...previous, ...patch }))
      }}
      onOpenCreate={() => {
        setIsCreateOpen(true)
      }}
      onRetry={() => {
        void usersQuery.refetch()
      }}
      onSubmitCreate={() => {
        createUserMutation.mutate(
          {
            full_name: formState.username,
            email: formState.email,
            password: formState.password,
            role: formState.role,
            is_active: formState.is_active,
          },
          {
            onSuccess: () => {
              setIsCreateOpen(false)
              setFormState({
                username: '',
                email: '',
                password: '',
                role: 'warehouse_staff',
                is_active: true,
              })
            },
            onError: (mutationError) => {
              const message =
                typeof mutationError === 'object' &&
                mutationError !== null &&
                'message' in mutationError &&
                typeof mutationError.message === 'string'
                  ? mutationError.message
                  : 'Failed to create user.'

              addToast({
                kind: 'error',
                message,
              })
            },
          },
        )
      }}
      users={users}
    />
  )
}
