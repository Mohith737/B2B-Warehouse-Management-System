// client/src/design-system/ui/organisms/POLineEditor.tsx
import {
  ActionableNotification,
  Button,
  DataTable,
  NumberInput,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react'

import { EmptyState, LoadingSkeleton } from '../atoms'
import { FormFieldError } from '../molecules'

type POLine = {
  productId: string
  productName: string
  quantity: number
  unitPrice: number
}

type ProductOption = {
  id: string
  name: string
}

type POLineEditorProps = {
  lines: POLine[]
  products: ProductOption[]
  onAddLine: (productId: string) => void
  onRemoveLine: (productId: string) => void
  onUpdateQuantity: (productId: string, quantity: number) => void
  onUpdateUnitPrice: (productId: string, unitPrice: number) => void
  state: 'loading' | 'empty' | 'error' | 'success'
  errorMessage?: string
  onRetry?: () => void
}

const headers = [
  { key: 'product', header: 'Product' },
  { key: 'quantity', header: 'Quantity' },
  { key: 'unitPrice', header: 'Unit Price' },
  { key: 'lineTotal', header: 'Line Total' },
  { key: 'actions', header: 'Actions' },
]

export function POLineEditor({
  lines,
  products,
  onAddLine,
  onRemoveLine,
  onUpdateQuantity,
  onUpdateUnitPrice,
  state,
  errorMessage,
  onRetry,
}: POLineEditorProps): JSX.Element {
  if (state === 'loading') {
    return <LoadingSkeleton lines={4} state="loading" />
  }

  if (state === 'error') {
    return (
      <ActionableNotification
        actionButtonLabel="Retry"
        hideCloseButton
        kind="error"
        onActionButtonClick={() => onRetry?.()}
        subtitle={errorMessage ?? 'Unable to load line editor.'}
        title="Line editor unavailable"
      />
    )
  }

  if (state === 'empty') {
    return (
      <EmptyState
        description="Add at least one PO line to continue."
        state="empty"
        title="No lines"
      />
    )
  }

  const rows = lines.map((line) => ({
    id: line.productId,
    product: line.productName,
    quantity: line.quantity,
    unitPrice: line.unitPrice,
    lineTotal: (line.quantity * line.unitPrice).toFixed(2),
    actions: line.productId,
  }))

  return (
    <>
      <Button
        kind="tertiary"
        onClick={() => {
          const nextProduct = products.find(
            (product) => !lines.some((line) => line.productId === product.id),
          )
          if (nextProduct) {
            onAddLine(nextProduct.id)
          }
        }}
      >
        Add Line
      </Button>
      <DataTable headers={headers} rows={rows}>
        {({ rows: dataRows, headers: dataHeaders, getHeaderProps, getTableProps }) => (
          <TableContainer title="PO Lines">
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
                    {row.cells.map((cell) => {
                      if (cell.info.header === 'quantity') {
                        return (
                          <TableCell key={cell.id}>
                            <NumberInput
                              hideSteppers
                              id={`qty-${row.id}`}
                              label="Quantity"
                              max={99999}
                              min={1}
                              onChange={(_, { value }) =>
                                onUpdateQuantity(row.id, Number(value))
                              }
                              value={Number(cell.value)}
                            />
                          </TableCell>
                        )
                      }

                      if (cell.info.header === 'unitPrice') {
                        return (
                          <TableCell key={cell.id}>
                            <NumberInput
                              hideSteppers
                              id={`price-${row.id}`}
                              label="Unit Price"
                              max={999999}
                              min={0.01}
                              onChange={(_, { value }) =>
                                onUpdateUnitPrice(row.id, Number(value))
                              }
                              step={0.01}
                              value={Number(cell.value)}
                            />
                          </TableCell>
                        )
                      }

                      if (cell.info.header === 'actions') {
                        return (
                          <TableCell key={cell.id}>
                            <Button kind="ghost" onClick={() => onRemoveLine(row.id)}>
                              Remove
                            </Button>
                          </TableCell>
                        )
                      }

                      return <TableCell key={cell.id}>{cell.value}</TableCell>
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DataTable>
      <FormFieldError
        message={
          lines.some((line) => line.quantity <= 0 || line.unitPrice <= 0)
            ? 'Quantity and unit price must be greater than zero.'
            : undefined
        }
      />
    </>
  )
}
