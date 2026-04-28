import type { Component, JSX } from 'solid-js'
import styles from './styles.module.css'

type ButtonProps = {
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'small' | 'medium' | 'large'
  disabled?: boolean
  onClick?: () => void
  class?: string
  type?: 'button' | 'submit' | 'reset'
  children: JSX.Element
}

/**
 * Foundational Button primitive.
 *
 * - Do not destructure props — access as props.foo to preserve reactivity.
 * - Use variant and size to compose CSS Module classes.
 * - Pass isBusy / isProcessing from the caller as `disabled`.
 * - Default type to "button" to avoid accidental form submissions.
 */
export const Button: Component<ButtonProps> = (props) => {
  return (
    <button
      class={`${styles.button} ${styles[props.variant ?? 'primary']} ${styles[props.size ?? 'medium']} ${props.class ?? ''}`}
      type={props.type ?? 'button'}
      disabled={props.disabled}
      onClick={props.onClick}
    >
      {props.children}
    </button>
  )
}
