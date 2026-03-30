// client/src/stores/grnSessionStore.ts
import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export type ScannedLine = {
  poLineId: string
  productId: string
  productName: string
  quantityReceived: number
  quantityExpected: number
  barcodeScanned: string | null
}

type GRNSessionState = {
  currentGRNId: string | null
  selectedPOId: string | null
  selectedPONumber: string | null
  scannedLines: ScannedLine[]
  sessionStarted: boolean
  setSelectedPO: (poId: string | null, poNumber: string | null) => void
  setCurrentGRNId: (grnId: string | null) => void
  addScannedLine: (line: ScannedLine) => void
  updateScannedLineQty: (poLineId: string, qty: number) => void
  removeScannedLine: (poLineId: string) => void
  resetSession: () => void
}

const initialState = {
  currentGRNId: null,
  selectedPOId: null,
  selectedPONumber: null,
  scannedLines: [],
  sessionStarted: false,
}

export const useGRNSessionStore = create<GRNSessionState>()(
  persist(
    (set) => ({
      ...initialState,
      setSelectedPO: (poId, poNumber) =>
        set({
          selectedPOId: poId,
          selectedPONumber: poNumber,
        }),
      setCurrentGRNId: (grnId) =>
        set({
          currentGRNId: grnId,
          sessionStarted: Boolean(grnId),
        }),
      addScannedLine: (line) =>
        set((state) => ({
          scannedLines: state.scannedLines.some(
            (existing) => existing.poLineId === line.poLineId,
          )
            ? state.scannedLines.map((existing) =>
                existing.poLineId === line.poLineId ? line : existing,
              )
            : [...state.scannedLines, line],
          sessionStarted: true,
        })),
      updateScannedLineQty: (poLineId, qty) =>
        set((state) => ({
          scannedLines: state.scannedLines.map((line) =>
            line.poLineId === poLineId
              ? {
                  ...line,
                  quantityReceived: qty,
                }
              : line,
          ),
        })),
      removeScannedLine: (poLineId) =>
        set((state) => ({
          scannedLines: state.scannedLines.filter((line) => line.poLineId !== poLineId),
        })),
      resetSession: () =>
        set({
          ...initialState,
        }),
    }),
    {
      name: 'grn-session-store',
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
)
