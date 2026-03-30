// client/src/design-system/ui/molecules/CreditWarning.tsx
import { Modal } from '@carbon/react'

type CreditWarningProps = {
  creditLimit: number
  estimatedTotal: number
  onProceed: () => void
  onCancel: () => void
  open: boolean
}

export function CreditWarning({
  creditLimit,
  estimatedTotal,
  onProceed,
  onCancel,
  open,
}: CreditWarningProps): JSX.Element {
  return (
    <Modal
      danger={estimatedTotal > creditLimit}
      modalHeading="Credit usage warning"
      onRequestClose={onCancel}
      onRequestSubmit={onProceed}
      open={open}
      primaryButtonText="Proceed"
      secondaryButtonText="Cancel"
      size="sm"
    >
      {`Estimated total ${estimatedTotal.toFixed(2)} exceeds 90% of credit limit ${creditLimit.toFixed(2)}.`}
    </Modal>
  )
}
