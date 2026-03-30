// client/src/features/grns/components/GRNView.tsx
import { Button, Select, SelectItem, Stack, Tile } from '@carbon/react'

import { ConfirmationBanner, PageTitle } from '../../../design-system/ui/atoms'
import { GRNLineScanner, GRNSummaryPanel } from '../../../design-system/ui/organisms'
import type { GRNScanRow, OpenPORead } from '../types'
import styles from './GRNView.module.scss'

type GRNViewProps = {
  title: string
  openPOs: OpenPORead[]
  selectedPOId: string | null
  lines: GRNScanRow[]
  sessionStarted: boolean
  currentGRNId: string | null
  isLoadingPOs: boolean
  isCreatingGRN: boolean
  isReceiving: boolean
  scannerError: string | null
  receiveFailureSummary: string | null
  completeError: string | null
  onSelectPO: (poId: string) => void
  onStartGRN: () => void
  onRetry: () => void
  onScan: (barcode: string, lineId: string | null) => void
  onComplete: () => void
  onRetryComplete: () => void
  onDismissReceiveFailures: () => void
  onContinueSession: () => void
  onStartFresh: () => void
}

export function GRNView({
  title,
  openPOs,
  selectedPOId,
  lines,
  sessionStarted,
  currentGRNId,
  isLoadingPOs,
  isCreatingGRN,
  isReceiving,
  scannerError,
  receiveFailureSummary,
  completeError,
  onSelectPO,
  onStartGRN,
  onRetry,
  onScan,
  onComplete,
  onRetryComplete,
  onDismissReceiveFailures,
  onContinueSession,
  onStartFresh,
}: GRNViewProps): JSX.Element {
  const grnState = isLoadingPOs || isCreatingGRN || isReceiving ? 'loading' : 'success'

  return (
    <Stack className={styles.page} gap={6}>
      <PageTitle title={title} />

      {sessionStarted ? (
        <ConfirmationBanner
          message="An existing GRN session is available."
          onContinue={onContinueSession}
          onStartFresh={onStartFresh}
        />
      ) : null}

      {!currentGRNId ? (
        <Tile className={styles.startCard}>
          <div className={styles.startHeader}>
            <p className={styles.hintText}>
              Select an open purchase order to initialize goods receipt processing.
            </p>
          </div>
          <div className={styles.startControls}>
            <Select
              id="grn-open-po"
              labelText="Open purchase orders"
              onChange={(event) => onSelectPO(event.target.value)}
              value={selectedPOId ?? ''}
            >
              <SelectItem text="Choose a PO" value="" />
              {openPOs.map((po) => (
                <SelectItem
                  key={po.id}
                  text={`${po.po_number} - ${po.supplier_id}`}
                  value={po.id}
                />
              ))}
            </Select>
            <Button
              className={styles.startButton}
              disabled={!selectedPOId || isCreatingGRN}
              onClick={onStartGRN}
            >
              Start GRN
            </Button>
          </div>
        </Tile>
      ) : null}

      {currentGRNId ? (
        <div className={styles.activeGrid}>
          <GRNLineScanner
            errorMessage={scannerError ?? undefined}
            lines={lines}
            onRetry={onRetry}
            onScan={onScan}
            state={scannerError ? 'error' : lines.length === 0 ? 'empty' : grnState}
          />

          <GRNSummaryPanel
            backorderLines={
              lines.filter((line) => line.receivedQty < line.expectedQty).length
            }
            fullyReceivedLines={
              lines.filter((line) => line.receivedQty >= line.expectedQty).length
            }
            onComplete={onComplete}
            onDismissReceiveFailures={onDismissReceiveFailures}
            onRetry={onRetry}
            onRetryComplete={onRetryComplete}
            pendingLines={
              lines.filter((line) => line.receivedQty < line.expectedQty).length
            }
            receiveFailureSummary={receiveFailureSummary}
            completeErrorMessage={completeError}
            state={lines.length === 0 ? 'empty' : grnState}
            totalLines={lines.length}
          />
        </div>
      ) : null}
    </Stack>
  )
}
