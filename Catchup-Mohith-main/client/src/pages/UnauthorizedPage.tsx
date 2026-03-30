// client/src/pages/UnauthorizedPage.tsx
import { ActionableNotification } from '@carbon/react'
import { useNavigate } from 'react-router-dom'

export default function UnauthorizedPage(): JSX.Element {
  const navigate = useNavigate()

  return (
    <ActionableNotification
      actionButtonLabel="Go Home"
      hideCloseButton
      kind="error"
      onActionButtonClick={() => navigate('/')}
      subtitle="You do not have permission to access this page."
      title="Unauthorized"
    />
  )
}
