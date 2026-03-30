// client/src/design-system/ui/atoms/FormSection.tsx
import { FormGroup, InlineNotification } from '@carbon/react'
import type { ReactNode } from 'react'

import { EmptyState } from './EmptyState'
import { LoadingSkeleton } from './LoadingSkeleton'

type ViewState = 'loading' | 'empty' | 'error' | 'success'

type FormSectionProps = {
  title: string
  children: ReactNode
  state?: ViewState
}

export function FormSection({
  title,
  children,
  state = 'success',
}: FormSectionProps): JSX.Element {
  if (state === 'loading') {
    return <LoadingSkeleton lines={4} />
  }

  if (state === 'empty') {
    return (
      <EmptyState
        description="No form fields are available in this section."
        title={title}
      />
    )
  }

  if (state === 'error') {
    return (
      <InlineNotification
        hideCloseButton
        kind="error"
        subtitle="Unable to render this form section."
        title={title}
      />
    )
  }

  return <FormGroup legendText={title}>{children}</FormGroup>
}
