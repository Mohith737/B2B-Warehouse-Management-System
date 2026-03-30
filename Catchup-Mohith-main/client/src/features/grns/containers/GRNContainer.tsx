// client/src/features/grns/containers/GRNContainer.tsx
import { useEffect, useMemo, useState } from 'react'
import { useShallow } from 'zustand/react/shallow'

import { apiClient } from '../../../api/client'
import type { ApiResponse } from '../../../api/types'
import { useGRNSessionStore } from '../../../stores/grnSessionStore'
import { useUIStore } from '../../../stores/uiStore'
import type { ProductRead } from '../../products/types'
import { GRN_CONFIG } from '../constants/grnConfig'
import { GRNView } from '../components/GRNView'
import { useCompleteGRNMutation } from '../hooks/useCompleteGRNMutation'
import { useCreateGRNMutation } from '../hooks/useCreateGRNMutation'
import { useOpenPOsQuery } from '../hooks/useOpenPOsQuery'
import { useReceiveLineMutation } from '../hooks/useReceiveLineMutation'
import type { GRNScanRow, PurchaseOrderDetailRead } from '../types'

async function lookupProductByBarcode(
  barcode: string,
): Promise<{ id: string; name: string }> {
  const response = await apiClient.get<ApiResponse<ProductRead>>(
    '/products/barcode-lookup',
    {
      params: { barcode },
    },
  )
  return {
    id: response.data.data.id,
    name: response.data.data.name,
  }
}

async function receiveLineForCompletion(
  grnId: string,
  lineId: string,
  quantityReceived: number,
): Promise<void> {
  await apiClient.post(`/grns/${grnId}/lines/${lineId}/receive`, {
    quantity_received: quantityReceived,
    unit_cost: 1,
  })
}

async function fetchPurchaseOrderDetails(
  poId: string,
): Promise<PurchaseOrderDetailRead> {
  const response = await apiClient.get<ApiResponse<PurchaseOrderDetailRead>>(
    `/purchase-orders/${poId}`,
  )
  return response.data.data
}

export function GRNContainer(): JSX.Element {
  const openPOsQuery = useOpenPOsQuery()
  const createGRNMutation = useCreateGRNMutation()
  const receiveLineMutation = useReceiveLineMutation()
  const completeGRNMutation = useCompleteGRNMutation()
  const addToast = useUIStore((state) => state.addToast)

  const {
    selectedPOId,
    scannedLines,
    sessionStarted,
    currentGRNId,
    setSelectedPO,
    setCurrentGRNId,
    addScannedLine,
    updateScannedLineQty,
    resetSession,
  } = useGRNSessionStore(
    useShallow((state) => ({
      selectedPOId: state.selectedPOId,
      scannedLines: state.scannedLines,
      sessionStarted: state.sessionStarted,
      currentGRNId: state.currentGRNId,
      setSelectedPO: state.setSelectedPO,
      setCurrentGRNId: state.setCurrentGRNId,
      addScannedLine: state.addScannedLine,
      updateScannedLineQty: state.updateScannedLineQty,
      resetSession: state.resetSession,
    })),
  )

  const [showResumeBanner, setShowResumeBanner] = useState(false)
  const [scannerError, setScannerError] = useState<string | null>(null)
  const [completeError, setCompleteError] = useState<string | null>(null)
  const [receiveFailureSummary, setReceiveFailureSummary] = useState<string | null>(
    null,
  )
  const [completedLineIds, setCompletedLineIds] = useState<Set<string>>(new Set())
  const [poLineExpectedQtyByProductId, setPoLineExpectedQtyByProductId] = useState<
    Record<string, number>
  >({})
  const [isCompletingWithReceives, setIsCompletingWithReceives] = useState(false)

  useEffect(() => {
    if (sessionStarted) {
      setShowResumeBanner(true)
    }
  }, [sessionStarted])

  useEffect(() => {
    if (!selectedPOId) {
      setPoLineExpectedQtyByProductId({})
      return
    }

    void (async () => {
      try {
        const po = await fetchPurchaseOrderDetails(selectedPOId)
        const expectedQtyMap = po.lines.reduce<Record<string, number>>(
          (accumulator, line) => ({
            ...accumulator,
            [line.product_id]: Number(line.quantity_ordered),
          }),
          {},
        )
        setPoLineExpectedQtyByProductId(expectedQtyMap)
      } catch {
        setPoLineExpectedQtyByProductId({})
      }
    })()
  }, [selectedPOId])

  const lines: GRNScanRow[] = useMemo(
    () =>
      scannedLines.map((line) => ({
        id: line.poLineId,
        barcode: line.barcodeScanned ?? '',
        productName: line.productName,
        expectedQty: line.quantityExpected,
        receivedQty: line.quantityReceived,
      })),
    [scannedLines],
  )

  const parseErrorMessage = (error: unknown, fallback: string): string =>
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof error.message === 'string'
      ? error.message
      : fallback

  const handleComplete = async () => {
    if (!currentGRNId) {
      return
    }

    setCompleteError(null)
    setIsCompletingWithReceives(true)

    const pendingLines = scannedLines.filter(
      (line) => !completedLineIds.has(line.poLineId),
    )
    const failures: string[] = []

    for (const line of pendingLines) {
      const remainingQty = Math.max(line.quantityExpected - line.quantityReceived, 0)
      if (remainingQty === 0) {
        setCompletedLineIds((previous) => new Set(previous).add(line.poLineId))
        continue
      }

      try {
        await receiveLineForCompletion(currentGRNId, line.poLineId, remainingQty)
        updateScannedLineQty(line.poLineId, line.quantityExpected)
        setCompletedLineIds((previous) => new Set(previous).add(line.poLineId))
      } catch {
        failures.push(line.productName)
      }
    }

    if (failures.length > 0) {
      setReceiveFailureSummary(
        `${failures.length} line(s) failed: ${failures.join(', ')}`,
      )
      setCompleteError(
        `Failed to receive: ${failures.join(', ')}. Retry to attempt again.`,
      )
      setIsCompletingWithReceives(false)
      return
    }
    setReceiveFailureSummary(null)

    try {
      await completeGRNMutation.mutateAsync(currentGRNId)
      resetSession()
      setShowResumeBanner(false)
      setCompletedLineIds(new Set())
    } catch {
      const message =
        'GRN completion failed. Your line receives were saved. Retry to complete.'
      setCompleteError(message)
      addToast({
        kind: 'error',
        message,
      })
    } finally {
      setIsCompletingWithReceives(false)
    }
  }

  return (
    <GRNView
      completeError={completeError}
      currentGRNId={currentGRNId}
      isCreatingGRN={createGRNMutation.isPending}
      isLoadingPOs={openPOsQuery.isLoading}
      isReceiving={
        receiveLineMutation.isPending ||
        completeGRNMutation.isPending ||
        isCompletingWithReceives
      }
      lines={lines}
      onComplete={() => {
        void handleComplete()
      }}
      onContinueSession={() => {
        setShowResumeBanner(false)
      }}
      onDismissReceiveFailures={() => {
        setReceiveFailureSummary(null)
      }}
      onRetry={() => {
        void openPOsQuery.refetch()
      }}
      onRetryComplete={() => {
        void handleComplete()
      }}
      onScan={(barcode, lineId) => {
        if (!currentGRNId) {
          return
        }

        void (async () => {
          try {
            setScannerError(null)

            if (
              import.meta.env.DEV &&
              lineId &&
              barcode.startsWith('MOCK-')
            ) {
              const scannedLine = scannedLines.find((line) => line.poLineId === lineId)
              if (!scannedLine) {
                setScannerError('Unable to simulate scan for unknown line.')
                return
              }

              const remainingQty = Math.max(
                scannedLine.quantityExpected - scannedLine.quantityReceived,
                0,
              )
              if (remainingQty === 0) {
                return
              }

              const quantityToReceive = Math.min(
                GRN_CONFIG.defaultLineReceiveQty,
                remainingQty,
              )
              await receiveLineForCompletion(
                currentGRNId,
                lineId,
                quantityToReceive,
              )
              updateScannedLineQty(
                lineId,
                scannedLine.quantityReceived + quantityToReceive,
              )
              return
            }

            const scannedProduct = await lookupProductByBarcode(barcode)

            receiveLineMutation.mutate(
              {
                grnId: currentGRNId,
                product_id: scannedProduct.id,
                barcode,
                quantity_received: GRN_CONFIG.defaultLineReceiveQty,
                unit_cost: 1,
              },
              {
                onSuccess: (response) => {
                  const matchingLines = response.lines.filter(
                    (line) => line.product_id === scannedProduct.id,
                  )
                  const latestLine = matchingLines[matchingLines.length - 1]
                  if (!latestLine) {
                    return
                  }

                  addScannedLine({
                    poLineId: latestLine.id,
                    productId: latestLine.product_id,
                    productName: scannedProduct.name,
                    quantityReceived: latestLine.quantity_received,
                    quantityExpected:
                      poLineExpectedQtyByProductId[latestLine.product_id] ??
                      latestLine.quantity_received,
                    barcodeScanned: barcode,
                  })
                },
                onError: (error) => {
                  const message = parseErrorMessage(
                    error,
                    'Failed to receive GRN line.',
                  )
                  setScannerError(message)

                  addToast({
                    kind: 'error',
                    message,
                  })
                },
              },
            )
          } catch (error) {
            const message = parseErrorMessage(error, 'Failed to scan barcode.')
            setScannerError(message)

            addToast({
              kind: 'error',
              message,
            })
          }
        })()
      }}
      onSelectPO={(poId) => {
        const selectedPO = openPOsQuery.data?.find((po) => po.id === poId)
        setSelectedPO(poId || null, selectedPO?.po_number ?? null)
      }}
      onStartFresh={() => {
        resetSession()
        setShowResumeBanner(false)
        setScannerError(null)
        setCompleteError(null)
        setReceiveFailureSummary(null)
        setCompletedLineIds(new Set())
        setPoLineExpectedQtyByProductId({})
      }}
      onStartGRN={() => {
        if (!selectedPOId) {
          return
        }

        createGRNMutation.mutate(
          { po_id: selectedPOId },
          {
            onSuccess: (response) => {
              setCurrentGRNId(response.id)
              setShowResumeBanner(false)
              setCompleteError(null)
              setReceiveFailureSummary(null)
              setCompletedLineIds(new Set())
              setScannerError(null)
            },
            onError: (error) => {
              const message = parseErrorMessage(error, 'Failed to start GRN.')
              setScannerError(message)

              addToast({
                kind: 'error',
                message,
              })
            },
          },
        )
      }}
      openPOs={openPOsQuery.data ?? []}
      receiveFailureSummary={receiveFailureSummary}
      scannerError={scannerError}
      selectedPOId={selectedPOId}
      sessionStarted={showResumeBanner}
      title={GRN_CONFIG.pageTitle}
    />
  )
}
