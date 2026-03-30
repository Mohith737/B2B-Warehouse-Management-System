// client/src/features/auth/components/LoginForm.tsx
// client/src/features/auth/components/LoginForm.tsx
import {
  Button,
  Form,
  InlineLoading,
  InlineNotification,
  PasswordInput,
  TextInput,
} from '@carbon/react'

import styles from '../../../pages/LoginPage.module.scss'
import type { LoginRequest } from '../types'

type LoginFormProps = {
  onSubmit: (payload: LoginRequest) => void
  isLoading: boolean
  error: string | null
}

export function LoginForm({ onSubmit, isLoading, error }: LoginFormProps): JSX.Element {
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const email = String(formData.get('email') ?? '').trim()
    const password = String(formData.get('password') ?? '')
    onSubmit({ email, password })
  }

  return (
    <Form aria-label="login form" className={styles.loginForm} onSubmit={handleSubmit}>
      <TextInput
        id="login-email"
        labelText="Email address"
        name="email"
        size="lg"
        type="email"
      />
      <PasswordInput
        id="login-password"
        labelText="Password"
        name="password"
        size="lg"
      />
      {error ? (
        <InlineNotification
          hideCloseButton
          kind="error"
          subtitle={error}
          title="Login failed"
        />
      ) : null}
      <Button
        className={styles.submitButton}
        disabled={isLoading}
        kind="primary"
        size="lg"
        type="submit"
      >
        {isLoading ? <InlineLoading description="Signing In" /> : 'Sign In'}
      </Button>
    </Form>
  )
}
