/**
 * House-style foundational Button example.
 *
 * Place in: components/foundation/Button/index.tsx
 * Pair with styles.module.css in the same folder.
 */

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import s from './styles.module.css'

export type BaseComponentProps = {
  className?: string
  children?: ReactNode
}

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md' | 'lg'

export type ButtonProps = BaseComponentProps &
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant
    size?: ButtonSize
    isBusy?: boolean
  }

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      children,
      disabled,
      isBusy = false,
      size = 'md',
      type = 'button',
      variant = 'primary',
      ...props
    },
    ref,
  ) => {
    const isDisabled = disabled || isBusy
    const classes = [s.button, s[variant], s[size], className].filter(Boolean).join(' ')

    return (
      <button
        {...props}
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-busy={isBusy || undefined}
        className={classes}
      >
        {isBusy ? <span aria-hidden="true">Loading</span> : null}
        <span>{children}</span>
      </button>
    )
  },
)

Button.displayName = 'Button'
