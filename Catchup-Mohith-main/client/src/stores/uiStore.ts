// client/src/stores/uiStore.ts
import { create } from 'zustand'

export type ToastKind = 'success' | 'error' | 'info' | 'warning'

export type Toast = {
  id: string
  kind: ToastKind
  message: string
}

type UIState = {
  sidebarOpen: boolean
  toasts: Toast[]
  setSidebarOpen: (open: boolean) => void
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

const MAX_TOASTS = 3

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  toasts: [],
  setSidebarOpen: (open) =>
    set({
      sidebarOpen: open,
    }),
  addToast: (toast) =>
    set((state) => {
      const duplicate = state.toasts.some(
        (existingToast) => existingToast.message === toast.message,
      )
      if (duplicate) {
        return state
      }

      const newToast: Toast = {
        ...toast,
        id: crypto.randomUUID(),
      }
      const nextToasts = [newToast, ...state.toasts].slice(0, MAX_TOASTS)

      return {
        toasts: nextToasts,
      }
    }),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id),
    })),
}))
