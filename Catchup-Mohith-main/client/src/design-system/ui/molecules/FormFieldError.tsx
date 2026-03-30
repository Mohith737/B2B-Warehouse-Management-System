// client/src/design-system/ui/molecules/FormFieldError.tsx
import { InlineNotification } from '@carbon/react'

type FormFieldErrorProps = {
  message?: string
}

export function FormFieldError({ message }: FormFieldErrorProps): JSX.Element | null {
  if (!message) {
    return null
  }

  return (
    <InlineNotification
      hideCloseButton
      kind="error"
      subtitle={message}
      title="Field validation error"
    />
  )
}
