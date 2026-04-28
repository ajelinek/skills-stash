/**
 * House-style foundational toggle example.
 *
 * Place in: components/foundation/ToggleSlider/index.tsx
 * Pair with styles.module.css in the same folder.
 */

import { forwardRef, useId, type InputHTMLAttributes } from 'react'
import s from './styles.module.css'

export type ToggleSliderProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  'type'
> & {
  className?: string
  label: string
}

export const ToggleSlider = forwardRef<HTMLInputElement, ToggleSliderProps>(
  ({ checked, className, id, label, ...props }, ref) => {
    const generatedId = useId()
    const inputId = id ?? `toggle-${generatedId}`
    const classes = [s.wrapper, className].filter(Boolean).join(' ')

    return (
      <label className={classes} htmlFor={inputId}>
        <input
          {...props}
          ref={ref}
          id={inputId}
          type="checkbox"
          checked={checked}
          className={s.input}
        />
        <span className={s.slider} aria-hidden="true" />
        <span className={s.label}>{label}</span>
      </label>
    )
  },
)

ToggleSlider.displayName = 'ToggleSlider'
