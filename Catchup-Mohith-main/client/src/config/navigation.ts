// client/src/config/navigation.ts
import type { UserRole } from '../stores/authStore'

export type NavItem = {
  id: string
  label: string
  path: string
}

export const NAV_CONFIG: Record<UserRole, NavItem[]> = {
  warehouse_staff: [
    { id: 'grns', label: 'Receive Goods', path: '/grns' },
    { id: 'stock', label: 'Stock Ledger', path: '/stock-ledger' },
    { id: 'backorders', label: 'Backorders', path: '/backorders' },
  ],
  procurement_manager: [
    { id: 'dashboard', label: 'Dashboard', path: '/dashboard' },
    { id: 'pos', label: 'Purchase Orders', path: '/purchase-orders' },
    { id: 'suppliers', label: 'Suppliers', path: '/suppliers' },
    { id: 'products', label: 'Products', path: '/products' },
    { id: 'grns', label: 'Receive Goods', path: '/grns' },
    { id: 'backorders', label: 'Backorders', path: '/backorders' },
    { id: 'stock', label: 'Stock Ledger', path: '/stock-ledger' },
  ],
  admin: [
    { id: 'dashboard', label: 'Dashboard', path: '/dashboard' },
    { id: 'pos', label: 'Purchase Orders', path: '/purchase-orders' },
    { id: 'suppliers', label: 'Suppliers', path: '/suppliers' },
    { id: 'products', label: 'Products', path: '/products' },
    { id: 'grns', label: 'Receive Goods', path: '/grns' },
    { id: 'backorders', label: 'Backorders', path: '/backorders' },
    { id: 'stock', label: 'Stock Ledger', path: '/stock-ledger' },
    { id: 'users', label: 'Users', path: '/admin/users' },
    { id: 'reports', label: 'Reports', path: '/reports' },
  ],
}

export const ROLE_HOME: Record<UserRole, string> = {
  warehouse_staff: '/grns',
  procurement_manager: '/purchase-orders',
  admin: '/dashboard',
}
