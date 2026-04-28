import type { Component, JSX } from 'solid-js'
import { Show, createUniqueId, splitProps } from 'solid-js'
import styles from './styles.module.css'

type InputOptions = {
  name: string
  label?: string
  class?: string
  formGroupClass?: string
  errorMessage?: string | null
}

type InputProps = JSX.InputHTMLAttributes<HTMLInputElement> & InputOptions

/**
 * Foundational Input primitive.
 *
 * - Do not destructure props — access as props.foo to preserve reactivity.
 * - Uses createUniqueId() from solid-js for SSR-safe stable IDs per instance.
 * - Renders a real <label> tied to the input with `for`.
 * - Sets aria-invalid and aria-describedby when errorMessage is present.
 * - Renders the error with role="alert" so screen readers announce it.
 * - Uses splitProps to separate custom props from native HTML attributes
 *   before spreading, so custom props are never forwarded to the DOM element.
 */
export const Input: Component<InputProps> = (rawProps) => {
  const [local, inputProps] = splitProps(rawProps, [
    'label',
    'class',
    'formGroupClass',
    'errorMessage',
  ])
  // createUniqueId is SSR-safe and generates a stable ID per component instance
  const inputId = rawProps.id ?? createUniqueId()
  const errorId = `${inputId}-error`

  return (
    <div class={`${styles.formGroup} ${local.formGroupClass ?? ''}`}>
      <Show when={local.label}>
        <label for={inputId} class={styles.label}>
          {local.label}
        </label>
      </Show>

      <div class={styles.inputWrapper}>
        <input
          {...inputProps}
          id={inputId}
          class={`${styles.input} ${local.class ?? ''} ${local.errorMessage ? styles.inputError : ''}`}
          aria-invalid={local.errorMessage ? 'true' : undefined}
          aria-describedby={local.errorMessage ? errorId : undefined}
        />
      </div>

      <Show when={local.errorMessage}>
        <span id={errorId} role="alert" class={styles.error}>
          {local.errorMessage}
        </span>
      </Show>
    </div>
  )
}
