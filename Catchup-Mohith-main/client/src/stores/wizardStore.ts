// client/src/stores/wizardStore.ts
import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export type WizardStep = 1 | 2 | 3 | 4

export type WizardLine = {
  productId: string
  productName: string
  quantity: number
  unitPrice: number
}

type WizardState = {
  currentStep: WizardStep
  supplierId: string | null
  supplierName: string | null
  lines: WizardLine[]
  notes: string
  resetWizard: () => void
  setStep: (step: WizardStep) => void
  updateSupplier: (id: string, name: string) => void
  addLine: (line: WizardLine) => void
  removeLine: (productId: string) => void
  updateLine: (productId: string, updates: Partial<WizardLine>) => void
  setNotes: (notes: string) => void
}

const initialState = {
  currentStep: 1 as WizardStep,
  supplierId: null,
  supplierName: null,
  lines: [],
  notes: '',
}

export const useWizardStore = create<WizardState>()(
  persist(
    (set) => ({
      ...initialState,
      resetWizard: () =>
        set({
          ...initialState,
        }),
      setStep: (step) =>
        set({
          currentStep: step,
        }),
      updateSupplier: (id, name) =>
        set({
          supplierId: id,
          supplierName: name,
        }),
      addLine: (line) =>
        set((state) => ({
          lines: [...state.lines, line],
        })),
      removeLine: (productId) =>
        set((state) => ({
          lines: state.lines.filter((line) => line.productId !== productId),
        })),
      updateLine: (productId, updates) =>
        set((state) => ({
          lines: state.lines.map((line) =>
            line.productId === productId ? { ...line, ...updates } : line,
          ),
        })),
      setNotes: (notes) =>
        set({
          notes,
        }),
    }),
    {
      name: 'wizard-store',
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
)
