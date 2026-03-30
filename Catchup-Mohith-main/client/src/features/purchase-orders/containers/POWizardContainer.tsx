// client/src/features/purchase-orders/containers/POWizardContainer.tsx
import { useEffect, useMemo, useState } from 'react'
import { useBlocker, useNavigate } from 'react-router-dom'
import { useShallow } from 'zustand/react/shallow'
import { Button, ButtonSet, ComposedModal, ModalBody, ModalHeader } from '@carbon/react'

import { useAuthStore } from '../../../stores/authStore'
import { useUIStore } from '../../../stores/uiStore'
import { useWizardStore } from '../../../stores/wizardStore'
import { useProductsQuery } from '../../products/hooks/useProductsQuery'
import { useSuppliersQuery } from '../../suppliers/hooks/useSuppliersQuery'
import { PO_CONFIG } from '../constants/poConfig'
import { useCreatePOMutation } from '../hooks/useCreatePOMutation'
import { POWizardView } from '../components/POWizardView'
import type {
  WizardProductOption,
  WizardSnapshot,
  WizardSupplierOption,
} from '../types'

export function POWizardContainer(): JSX.Element {
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role)
  const addToast = useUIStore((state) => state.addToast)

  useEffect(() => {
    if (role === 'warehouse_staff') {
      navigate('/unauthorized')
    }
  }, [navigate, role])

  const {
    currentStep,
    supplierId,
    supplierName,
    lines,
    notes,
    setStep,
    updateSupplier,
    addLine,
    removeLine,
    updateLine,
    setNotes,
    resetWizard,
  } = useWizardStore(
    useShallow((state) => ({
      currentStep: state.currentStep,
      supplierId: state.supplierId,
      supplierName: state.supplierName,
      lines: state.lines,
      notes: state.notes,
      setStep: state.setStep,
      updateSupplier: state.updateSupplier,
      addLine: state.addLine,
      removeLine: state.removeLine,
      updateLine: state.updateLine,
      setNotes: state.setNotes,
      resetWizard: state.resetWizard,
    })),
  )

  const createPOMutation = useCreatePOMutation()
  const suppliersQuery = useSuppliersQuery({
    page: 1,
    pageSize: 50,
    search: '',
    tier: 'all',
  })
  const productsQuery = useProductsQuery({
    page: 1,
    pageSize: 50,
    search: '',
  })
  const [createdPONumber, setCreatedPONumber] = useState<string | null>(null)
  const [showSavedStateBanner, setShowSavedStateBanner] = useState(false)
  const [submissionError, setSubmissionError] = useState<string | null>(null)

  const supplierOptions: WizardSupplierOption[] = useMemo(
    () =>
      (suppliersQuery.data?.data ?? []).map((supplier) => ({
        id: supplier.id,
        name: supplier.name,
        creditLimit: supplier.credit_limit,
      })),
    [suppliersQuery.data],
  )

  const productOptions: WizardProductOption[] = useMemo(
    () =>
      (productsQuery.data?.data ?? []).map((product) => ({
        id: product.id,
        name: product.name,
      })),
    [productsQuery.data],
  )

  const estimatedTotal = useMemo(
    () => lines.reduce((total, line) => total + line.quantity * line.unitPrice, 0),
    [lines],
  )

  const selectedSupplierCreditLimit = useMemo(() => {
    const selectedSupplier = supplierOptions.find(
      (supplier) => supplier.id === supplierId,
    )
    return selectedSupplier?.creditLimit ?? null
  }, [supplierId, supplierOptions])

  useEffect(() => {
    if (supplierId !== null || lines.length > 0) {
      setShowSavedStateBanner(true)
    }
  }, [supplierId, lines.length])

  useEffect(() => {
    return () => {
      if (useWizardStore.getState().currentStep === 4) {
        useWizardStore.getState().resetWizard()
      }
    }
  }, [])

  const wizard: WizardSnapshot = useMemo(
    () => ({
      currentStep,
      supplierId,
      supplierName,
      lines,
      notes,
    }),
    [currentStep, supplierId, supplierName, lines, notes],
  )

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      currentStep > 1 &&
      currentStep < 4 &&
      currentLocation.pathname !== nextLocation.pathname,
  )

  return (
    <>
      <POWizardView
        createdPONumber={createdPONumber}
        errorMessage={
          createPOMutation.isError
            ? (createPOMutation.error as Error).message
            : undefined
        }
        hasSavedState={showSavedStateBanner}
        submissionError={submissionError}
        onAddLine={(productId) => {
          const product = productOptions.find((item) => item.id === productId)
          if (!product) {
            return
          }

          addLine({
            productId,
            productName: product.name,
            quantity: 1,
            unitPrice: 1,
          })
          setSubmissionError(null)
        }}
        onContinueSaved={() => {
          setShowSavedStateBanner(false)
        }}
        onNext={() => {
          if (currentStep < 4) {
            setStep((currentStep + 1) as 1 | 2 | 3 | 4)
          }
        }}
        onPrevious={() => {
          if (currentStep > 1) {
            setStep((currentStep - 1) as 1 | 2 | 3 | 4)
            setSubmissionError(null)
          }
        }}
        onRemoveLine={(productId) => {
          removeLine(productId)
          setSubmissionError(null)
        }}
        onSelectSupplier={(nextSupplierId) => {
          const supplier = supplierOptions.find((item) => item.id === nextSupplierId)
          if (!supplier) {
            return
          }
          updateSupplier(supplier.id, supplier.name)
        }}
        onStartFresh={() => {
          resetWizard()
          setShowSavedStateBanner(false)
          setSubmissionError(null)
        }}
        onSubmit={() => {
          if (!supplierId || lines.length === 0) {
            return
          }
          setSubmissionError(null)

          createPOMutation.mutate(
            {
              supplier_id: supplierId,
              notes,
              lines: lines.map((line) => ({
                product_id: line.productId,
                quantity_ordered: line.quantity,
                unit_price: line.unitPrice,
              })),
            },
            {
              onSuccess: (data) => {
                setCreatedPONumber(data.po_number)
                setSubmissionError(null)
                setStep(4)
              },
              onError: (error) => {
                const message =
                  typeof error === 'object' &&
                  error !== null &&
                  'message' in error &&
                  typeof error.message === 'string'
                    ? error.message
                    : 'Failed to create purchase order.'

                addToast({
                  kind: 'error',
                  message,
                })
                setSubmissionError(message)
              },
            },
          )
        }}
        onUpdateNotes={(value) => {
          setNotes(value)
          setSubmissionError(null)
        }}
        onUpdateQuantity={(productId, quantity) => {
          updateLine(productId, { quantity })
          setSubmissionError(null)
        }}
        onUpdateUnitPrice={(productId, unitPrice) => {
          updateLine(productId, { unitPrice })
          setSubmissionError(null)
        }}
        estimatedTotal={estimatedTotal}
        productOptions={productOptions}
        selectedSupplierCreditLimit={selectedSupplierCreditLimit}
        state={
          createPOMutation.isPending ||
          suppliersQuery.isLoading ||
          productsQuery.isLoading
            ? 'loading'
            : 'success'
        }
        steps={[...PO_CONFIG.wizardSteps]}
        supplierOptions={supplierOptions}
        title={PO_CONFIG.wizardTitle}
        wizard={wizard}
      />
      <ComposedModal
        open={blocker.state === 'blocked'}
        onClose={() => {
          blocker.reset?.()
        }}
      >
        <ModalHeader title="Leave wizard?" />
        <ModalBody>
          <p>Your progress will be lost. Are you sure you want to leave?</p>
          <ButtonSet>
            <Button
              kind="primary"
              onClick={() => {
                blocker.reset?.()
              }}
            >
              Stay
            </Button>
            <Button
              kind="danger"
              onClick={() => {
                resetWizard()
                blocker.proceed?.()
              }}
            >
              Leave
            </Button>
          </ButtonSet>
        </ModalBody>
      </ComposedModal>
    </>
  )
}
