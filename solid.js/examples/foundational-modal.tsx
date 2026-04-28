import type { Component, JSX } from 'solid-js'
import { Show, createEffect, onCleanup } from 'solid-js'
import { Portal } from 'solid-js/web'
import styles from './styles.module.css'

type ModalProps = {
  isOpen: boolean
  onClose: () => void
  title: string
  children: JSX.Element
  class?: string
}

/**
 * Foundational Modal primitive.
 *
 * - Do not destructure props — access as props.foo to preserve reactivity.
 * - Uses Portal from solid-js/web to render outside the component tree.
 *   This avoids CSS stacking context issues.
 * - Uses Show to conditionally render — the modal is fully unmounted when closed.
 * - Locks body scroll via createEffect + onCleanup.
 * - Handles Escape key and backdrop click to close.
 * - role="dialog", aria-modal, and aria-labelledby for full ARIA compliance.
 */
export const Modal: Component<ModalProps> = (props) => {
  createEffect(() => {
    if (props.isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    onCleanup(() => {
      document.body.style.overflow = ''
    })
  })

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      props.onClose()
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      props.onClose()
    }
  }

  return (
    <Show when={props.isOpen}>
      <Portal>
        <div
          class={styles.backdrop}
          onClick={handleBackdropClick}
          onKeyDown={handleKeyDown}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div class={`${styles.modal} ${props.class ?? ''}`}>
            <div class={styles.header}>
              <h2 id="modal-title" class={styles.title}>
                {props.title}
              </h2>
              <button
                type="button"
                class={styles.closeButton}
                onClick={props.onClose}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>
            <div class={styles.content}>{props.children}</div>
          </div>
        </div>
      </Portal>
    </Show>
  )
}
