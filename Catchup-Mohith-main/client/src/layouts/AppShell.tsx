// client/src/layouts/AppShell.tsx
import {
  Header,
  HeaderGlobalAction,
  HeaderGlobalBar,
  HeaderName,
  Theme,
} from '@carbon/react'
import { Logout } from '@carbon/icons-react'
import type { ReactNode } from 'react'
import { useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { NAV_CONFIG } from '../config/navigation'
import { useAuthStore, type UserRole } from '../stores/authStore'
import styles from './AppShell.module.scss'

type AppShellProps = {
  children: ReactNode
  pageTitle?: string
  activeView?: string
  onLogout?: () => void
  role?: UserRole
}

function toRoleKey(role: UserRole | null | undefined): UserRole {
  if (
    role === 'admin' ||
    role === 'procurement_manager' ||
    role === 'warehouse_staff'
  ) {
    return role
  }
  return 'warehouse_staff'
}

export function AppShell({
  children,
  pageTitle,
  activeView,
  onLogout,
  role,
}: AppShellProps): JSX.Element {
  const navigate = useNavigate()
  const location = useLocation()
  const storeRole = useAuthStore((state) => state.role)
  const username = useAuthStore((state) => state.username)
  const resolvedRole = toRoleKey(role ?? storeRole)
  const navItems = NAV_CONFIG[resolvedRole] ?? []

  const formattedDate = useMemo(
    () =>
      new Intl.DateTimeFormat('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      }).format(new Date()),
    [],
  )

  const initials = (username ?? 'U').charAt(0).toUpperCase()
  void pageTitle
  void activeView

  return (
    <Theme theme="white">
      <Header aria-label="StockBridge">
        <HeaderName
          href="/"
          onClick={(event) => {
            event.preventDefault()
          }}
          prefix=""
        >
          StockBridge
        </HeaderName>
        <HeaderGlobalBar>
          <span className={styles.headerDate}>{formattedDate}</span>
          <span className={styles.headerUser}>{username ?? 'User'}</span>
          <HeaderGlobalAction aria-label="Profile">
            <div className={styles.avatar}>{initials}</div>
          </HeaderGlobalAction>
          <HeaderGlobalAction aria-label="Logout" onClick={onLogout}>
            <Logout size={20} />
          </HeaderGlobalAction>
        </HeaderGlobalBar>
      </Header>

      <div className={styles.bodyWrapper}>
        <nav className={styles.sidebar}>
          <ul className={styles.navList}>
            {navItems.map((item) => (
              <li key={item.id}>
                <a
                  className={[
                    styles.navLink,
                    location.pathname === item.path ||
                    location.pathname.startsWith(`${item.path}/`)
                      ? styles.navLinkActive
                      : '',
                  ].join(' ')}
                  href={item.path}
                  onClick={(event) => {
                    event.preventDefault()
                    navigate(item.path)
                  }}
                >
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <main className={styles.content}>{children}</main>
      </div>
    </Theme>
  )
}
