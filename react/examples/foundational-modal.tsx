/**
 * House-style foundational modal example.
 *
 * Place in: components/foundation/Modal/index.tsx
 * Pair with styles.module.css in the same folder.
 */

import {
  forwardRef,
  useEffect,
  useId,
  useImperativeHandle,
  useRef,
  type ReactNode,
} from 'react'
import s from './styles.module.css'

export type ModalProps = {
  className?: string
  children?: ReactNode
  isOpen: boolean
  title: string
  onClose: () => void
}

export const Modal = forwardRef<HTMLDialogElement, ModalProps>(
  ({ children, className, isOpen, onClose, title }, ref) => {
    const dialogRef = useRef<HTMLDialogElement>(null)
    const titleId = useId()
    const classes = [s.dialog, className].filter(Boolean).join(' ')

    useImperativeHandle(ref, () => dialogRef.current as HTMLDialogElement, [])

    useEffect(() => {
      if (!dialogRef.current) {
        return
      }

      if (isOpen && !dialogRef.current.open) {
        dialogRef.current.showModal()
      }

      if (!isOpen && dialogRef.current.open) {
        dialogRef.current.close()
      }
    }, [isOpen])

    return (
      <dialog
        ref={dialogRef}
        className={classes}
        aria-labelledby={titleId}
        onClose={onClose}
      >
        <div className={s.content}>
          <div className={s.header}>
            <h2 id={titleId} className={s.title}>
              {title}
            </h2>
            <button type="button" className={s.closeButton} onClick={onClose}>
              Close
            </button>
          </div>
          <div className={s.body}>{children}</div>
        </div>
      </dialog>
    )
  },
)

Modal.displayName = 'Modal'
