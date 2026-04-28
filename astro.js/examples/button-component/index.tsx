// Button/index.tsx — SolidJS foundational button
//
// Foundational components are SolidJS (or React) components, never .astro files.
// They handle onClick, manage disabled state, and expose typed callbacks.
//
// CSS Modules rule: import styles from './styles.module.css'
// SolidJS uses `class`, not `className`.
//
// For a React project: swap `class` → `className` and follow the `react` skill.

import type { JSX, ParentComponent } from 'solid-js'
import { splitProps } from 'solid-js'
import styles from './styles.module.css'

type ButtonVariant = 'primary' | 'secondary' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  onClick?: JSX.EventHandlerUnion<HTMLButtonElement, MouseEvent>
  class?: string
  'aria-label'?: string
}

const Button: ParentComponent<ButtonProps> = (props) => {
  const [local, rest] = splitProps(props, [
    'variant',
    'size',
    'type',
    'disabled',
    'loading',
    'class',
    'children',
  ])

  const variant = () => local.variant ?? 'primary'
  const size = () => local.size ?? 'md'
  const isDisabled = () => local.disabled || local.loading

  return (
    <button
      {...rest}
      type={local.type ?? 'button'}
      disabled={isDisabled()}
      aria-disabled={isDisabled()}
      aria-busy={local.loading}
      class={`${styles.button} ${styles[variant()]} ${styles[size()]} ${local.class ?? ''}`}
    >
      {local.children}
    </button>
  )
}

export default Button
