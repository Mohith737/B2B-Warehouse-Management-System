// client/src/pages/NotFoundPage.tsx
import { ActionableNotification } from '@carbon/react'
import { useNavigate } from 'react-router-dom'

export default function NotFoundPage(): JSX.Element {
  const navigate = useNavigate()

  return (
    <ActionableNotification
      actionButtonLabel="Go Home"
      hideCloseButton
      kind="warning"
      onActionButtonClick={() => navigate('/')}
      subtitle="The page you requested does not exist."
      title="Page Not Found"
    />
  )
}
