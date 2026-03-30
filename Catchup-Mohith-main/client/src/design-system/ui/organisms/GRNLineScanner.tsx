// client/src/design-system/ui/organisms/GRNLineScanner.tsx
import {
  ActionableNotification,
  Button,
  DataTable,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
  TextInput,
} from '@carbon/react'
import type { KeyboardEvent } from 'react'
import { useState } from 'react'

import { EmptyState, LoadingSkeleton, StatusBadge } from '../atoms'
import { FormFieldError } from '../molecules'

type GRNScanLine = {
  id: string
  barcode: string
  productName: string
  expectedQty: number
  receivedQty: number
}

type GRNLineScannerProps = {
  lines: GRNScanLine[]
  state: 'loading' | 'empty' | 'error' | 'success'
  errorMessage?: string
  onRetry?: () => void
  onScan: (barcode: string, lineId: string | null) => void
}

const headers = [
  { key: 'barcode', header: 'Barcode' },
  { key: 'productName', header: 'Product' },
  { key: 'expectedQty', header: 'Ordered Qty' },
  { key: 'receivedQty', header: 'Received Qty' },
  { key: 'status', header: 'Status' },
]

export function GRNLineScanner({
  lines,
  state,
  errorMessage,
  onRetry,
  onScan,
}: GRNLineScannerProps): JSX.Element {
  const [barcode, setBarcode] = useState('')
  const [simulatorValue, setSimulatorValue] = useState('')
  const firstLineId = lines[0]?.id ?? null
  const isDevMode = import.meta.env.DEV

  const submitScan = () => {
    const nextBarcode = barcode.trim()
    if (nextBarcode.length === 0) {
      return
    }
    onScan(nextBarcode, firstLineId)
    setBarcode('')
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== 'Enter') {
      return
    }
    event.preventDefault()
    submitScan()
  }

  if (state === 'loading') {
    return <LoadingSkeleton lines={5} state="loading" />
  }

  if (state === 'error') {
    return (
      <ActionableNotification
        actionButtonLabel="Retry"
        hideCloseButton
        kind="error"
        onActionButtonClick={() => onRetry?.()}
        subtitle={errorMessage ?? 'Unable to load GRN scanner state.'}
        title="Scanner unavailable"
      />
    )
  }

  if (state === 'empty') {
    return (
      <EmptyState
        description="No receivable lines are available for this GRN session."
        state="empty"
        title="No GRN lines"
      />
    )
  }

  const rows = lines.map((line) => ({
    id: line.id,
    barcode: line.barcode,
    productName: line.productName,
    expectedQty: String(line.expectedQty),
    receivedQty: String(line.receivedQty),
    status: line.receivedQty >= line.expectedQty ? 'completed' : 'open',
  }))

  return (
    <>
      {isDevMode ? (
        <div className="sb-barcode-simulator">
          <p style={{ color: 'var(--cds-text-secondary)' }}>
            🔧 Dev: Barcode Simulator (keyboard simulation)
          </p>
          <TextInput
            id="barcode-simulator-input"
            labelText="Simulate scanner — type barcode + Enter"
            placeholder="e.g. SKU-001-BATCH-42"
            value={simulatorValue}
            onChange={(event) => setSimulatorValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && simulatorValue.trim()) {
                const unscanned = lines.find(
                  (line) => line.receivedQty < line.expectedQty,
                )
                if (unscanned) {
                  onScan(simulatorValue.trim(), unscanned.id)
                  setSimulatorValue('')
                }
              }
            }}
          />
          <p style={{ fontSize: '12px', color: 'var(--cds-text-helper)' }}>
            Press Enter to simulate scanner input on next unscanned line
          </p>
        </div>
      ) : null}
      <TextInput
        id="grn-barcode-input"
        onKeyDown={handleKeyDown}
        labelText="Scan barcode"
        onChange={(event) => setBarcode(event.target.value)}
        placeholder="Scan or type barcode"
        value={barcode}
      />
      <Button kind="primary" onClick={submitScan}>
        Receive Line
      </Button>
      <DataTable headers={headers} rows={rows}>
        {({ rows: dataRows, headers: dataHeaders, getHeaderProps, getTableProps }) => (
          <TableContainer title="GRN Line Scanner">
            <Table {...getTableProps()}>
              <TableHead>
                <TableRow>
                  {dataHeaders.map((header) => {
                    const { key, ...headerProps } = getHeaderProps({ header })
                    return (
                      <TableHeader key={key} {...headerProps}>
                        {header.header}
                      </TableHeader>
                    )
                  })}
                </TableRow>
              </TableHead>
              <TableBody>
                {dataRows.map((row) => (
                  <TableRow key={row.id}>
                    {row.cells.map((cell) => (
                      <TableCell key={cell.id}>
                        {cell.info.header === 'status' ? (
                          <StatusBadge domain="grn" status={String(cell.value)} />
                        ) : (
                          cell.value
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DataTable>
      <FormFieldError
        message={
          barcode.length > 0 && barcode.length < 3
            ? 'Barcode appears too short.'
            : undefined
        }
      />
    </>
  )
}
