// client/src/pages/LoginPage.tsx
// client/src/pages/LoginPage.tsx
import { Tag } from '@carbon/react'

import { LoginContainer } from '../features/auth/containers/LoginContainer'
import logoUrl from '../assets/icons/logo.svg'
import styles from './LoginPage.module.scss'

export default function LoginPage(): JSX.Element {
  return (
    <main className={styles.loginPage}>
      <section className={styles.brandPanel}>
        <div className={styles.brandContent}>
          <img alt="StockBridge" className={styles.logo} src={logoUrl} />
          <h1 className={styles.brandTitle}>StockBridge</h1>
          <p className={styles.brandSubtitle}>Warehouse Management System</p>
        </div>
        <div className={styles.brandPills}>
          <Tag className={styles.brandTag} type="teal">
            Real-time Stock
          </Tag>
          <Tag className={styles.brandTag} type="teal">
            Role-based Access
          </Tag>
          <Tag className={styles.brandTag} type="teal">
            Auto-reorder
          </Tag>
        </div>
      </section>
      <section className={styles.formPanel}>
        <LoginContainer />
      </section>
    </main>
  )
}
