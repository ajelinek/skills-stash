/**
 * House-style foundational Input example.
 *
 * Place in: components/foundation/Input/index.tsx
 * Pair with styles.module.css in the same folder.
 */

import {
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type ReactNode,
} from 'react'
import s from './styles.module.css'

export type BaseComponentProps = {
  className?: string
  children?: ReactNode
}

export type InputType = 'text' | 'email' | 'password' | 'tel' | 'number' | 'url' | 'search'

export type InputProps = BaseComponentProps &
  InputHTMLAttributes<HTMLInputElement> & {
    type?: InputType
    label?: string
    errorMessage?: string
  }

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, errorMessage, id, label, type = 'text', ...props }, ref) => {
    const generatedId = useId()
    const inputId = id ?? `input-${generatedId}`
    const errorId = errorMessage ? `${inputId}-error` : undefined
    const describedBy = [props['aria-describedby'], errorId].filter(Boolean).join(' ') || undefined
    const classes = [s.input, errorMessage && s.error, className].filter(Boolean).join(' ')

    return (
      <div className={s.wrapper}>
        {label ? (
          <label className={s.label} htmlFor={inputId}>
            {label}
          </label>
        ) : null}

        <input
          {...props}
          ref={ref}
          id={inputId}
          type={type}
          aria-invalid={errorMessage ? true : undefined}
          aria-describedby={describedBy}
          className={classes}
        />

        {errorMessage ? (
          <span id={errorId} className={s.errorText} role="alert">
            {errorMessage}
          </span>
        ) : null}
      </div>
    )
  },
)

Input.displayName = 'Input'
