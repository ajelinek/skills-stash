/**
 * House-style reusable auth-form shell example.
 *
 * This mirrors the pattern where login, registration, and verification pages
 * reuse the same page structure and foundation primitives.
 */

import type { ChangeEvent, FormEvent, ReactNode } from 'react'
import { Button } from './foundational-button'
import { Input } from './foundational-input'

type AuthFormShellProps = {
  title: string
  description?: string
  submitLabel: string
  errorMessage?: string | null
  isSubmitting?: boolean
  footer?: ReactNode
  children?: ReactNode
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

export function AuthFormShell({
  children,
  description,
  errorMessage,
  footer,
  isSubmitting = false,
  onSubmit,
  submitLabel,
  title,
}: AuthFormShellProps) {
  return (
    <main>
      <section aria-labelledby="auth-form-title">
        <h1 id="auth-form-title">{title}</h1>
        {description ? <p>{description}</p> : null}

        {errorMessage ? <p role="alert">{errorMessage}</p> : null}

        <form onSubmit={onSubmit}>
          {children}
          <Button type="submit" isBusy={isSubmitting}>
            {submitLabel}
          </Button>
        </form>

        {footer ? <div>{footer}</div> : null}
      </section>
    </main>
  )
}

type LoginPageProps = {
  email: string
  errorMessage?: string | null
  isSubmitting?: boolean
  onChange: (event: ChangeEvent<HTMLInputElement>) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

export function LoginPage({
  email,
  errorMessage,
  isSubmitting = false,
  onChange,
  onSubmit,
}: LoginPageProps) {
  return (
    <AuthFormShell
      title="Sign in"
      description="Use your email address to receive a sign-in link."
      submitLabel="Send sign-in link"
      errorMessage={errorMessage}
      isSubmitting={isSubmitting}
      onSubmit={onSubmit}
      footer={<p>Need an account? Register with the same email flow.</p>}
    >
      <Input
        label="Email address"
        name="email"
        type="email"
        value={email}
        onChange={onChange}
      />
    </AuthFormShell>
  )
}
