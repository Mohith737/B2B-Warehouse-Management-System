// client/src/features/purchase-orders/components/POWizardView.tsx
import {
  Button,
  ButtonSet,
  InlineNotification,
  Select,
  SelectItem,
  Stack,
  TextArea,
  Tile,
} from '@carbon/react'

import {
  ConfirmationBanner,
  FormSection,
  PageTitle,
} from '../../../design-system/ui/atoms'
import { CreditWarning, WizardStepper } from '../../../design-system/ui/molecules'
import { POLineEditor } from '../../../design-system/ui/organisms'
import type {
  WizardProductOption,
  WizardSnapshot,
  WizardSupplierOption,
} from '../types'

type POWizardViewProps = {
  title: string
  steps: string[]
  state: 'loading' | 'empty' | 'error' | 'success'
  errorMessage?: string
  submissionError: string | null
  wizard: WizardSnapshot
  supplierOptions: WizardSupplierOption[]
  productOptions: WizardProductOption[]
  hasSavedState: boolean
  createdPONumber: string | null
  estimatedTotal: number
  selectedSupplierCreditLimit: number | null
  onContinueSaved: () => void
  onStartFresh: () => void
  onSelectSupplier: (supplierId: string) => void
  onUpdateNotes: (notes: string) => void
  onAddLine: (productId: string) => void
  onRemoveLine: (productId: string) => void
  onUpdateQuantity: (productId: string, quantity: number) => void
  onUpdateUnitPrice: (productId: string, unitPrice: number) => void
  onPrevious: () => void
  onNext: () => void
  onSubmit: () => void
}

export function POWizardView({
  title,
  steps,
  state,
  errorMessage,
  submissionError,
  wizard,
  supplierOptions,
  productOptions,
  hasSavedState,
  createdPONumber,
  estimatedTotal,
  selectedSupplierCreditLimit,
  onContinueSaved,
  onStartFresh,
  onSelectSupplier,
  onUpdateNotes,
  onAddLine,
  onRemoveLine,
  onUpdateQuantity,
  onUpdateUnitPrice,
  onPrevious,
  onNext,
  onSubmit,
}: POWizardViewProps): JSX.Element {
  const dismissCreditWarning = () => undefined

  return (
    <Stack gap={6}>
      <PageTitle
        state={state}
        subtitle="Follow all steps to submit a PO."
        title={title}
      />

      {hasSavedState ? (
        <ConfirmationBanner
          message="An unfinished PO wizard session was found."
          onContinue={onContinueSaved}
          onStartFresh={onStartFresh}
        />
      ) : null}

      <WizardStepper currentStep={wizard.currentStep} steps={steps} />

      {wizard.currentStep === 1 ? (
        <FormSection title="Select supplier" state={state}>
          <Select
            id="po-supplier"
            labelText="Supplier"
            onChange={(event) => onSelectSupplier(event.target.value)}
            value={wizard.supplierId ?? ''}
          >
            <SelectItem text="Choose a supplier" value="" />
            {supplierOptions.map((supplier) => (
              <SelectItem key={supplier.id} text={supplier.name} value={supplier.id} />
            ))}
          </Select>
          <TextArea
            id="po-notes"
            labelText="Notes"
            onChange={(event) => onUpdateNotes(event.target.value)}
            value={wizard.notes}
          />
        </FormSection>
      ) : null}

      {wizard.currentStep === 2 ? (
        <POLineEditor
          errorMessage={errorMessage}
          lines={wizard.lines}
          onAddLine={onAddLine}
          onRemoveLine={onRemoveLine}
          onRetry={onNext}
          onUpdateQuantity={onUpdateQuantity}
          onUpdateUnitPrice={onUpdateUnitPrice}
          products={productOptions}
          state={wizard.lines.length === 0 ? 'empty' : state}
        />
      ) : null}

      {wizard.currentStep === 3 ? (
        <>
          <Tile>
            <p>{`Supplier: ${wizard.supplierName ?? 'Not selected'}`}</p>
            <p>{`Lines: ${wizard.lines.length}`}</p>
            <p>{`Estimated Total: ${estimatedTotal.toFixed(2)}`}</p>
            <p>{`Notes: ${wizard.notes || 'None'}`}</p>
          </Tile>
          {submissionError ? (
            <InlineNotification
              kind="error"
              subtitle={submissionError}
              title="Unable to submit purchase order"
            />
          ) : null}
          {selectedSupplierCreditLimit !== null &&
          estimatedTotal > selectedSupplierCreditLimit * 0.9 ? (
            <CreditWarning
              creditLimit={selectedSupplierCreditLimit}
              estimatedTotal={estimatedTotal}
              onCancel={dismissCreditWarning}
              onProceed={dismissCreditWarning}
              open
            />
          ) : null}
        </>
      ) : null}

      {wizard.currentStep === 4 ? (
        <InlineNotification
          hideCloseButton
          kind="success"
          subtitle={
            createdPONumber ? `PO ${createdPONumber} was submitted.` : 'PO submitted.'
          }
          title="Purchase order created"
        />
      ) : null}

      <ButtonSet>
        <Button
          disabled={wizard.currentStep === 1}
          kind="secondary"
          onClick={onPrevious}
        >
          Previous
        </Button>
        {wizard.currentStep < 3 ? (
          <Button
            disabled={wizard.currentStep === 1 && wizard.supplierId === null}
            kind="primary"
            onClick={onNext}
          >
            Next
          </Button>
        ) : null}
        {wizard.currentStep === 3 ? (
          <Button kind="primary" onClick={onSubmit}>
            Submit PO
          </Button>
        ) : null}
      </ButtonSet>
    </Stack>
  )
}
