import { useEffect, useId, useRef } from 'react'
import Icon from './Icon'

/**
 * Modal dialog built on the native <dialog> element, which handles focus
 * trapping and the Escape key for us.
 */
export default function Dialog({ open, onClose, title, children, footer, wide = false }) {
  const dialogRef = useRef(null)
  const titleId = useId()

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={dialogRef}
      className={`dialog ${wide ? 'dialog-wide' : ''}`}
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
      aria-labelledby={titleId}
    >
      {open && (
        <>
          <div className="dialog-header">
            <h2 id={titleId}>{title}</h2>
            <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
              <Icon name="close" label="Close dialog" />
            </button>
          </div>
          <div className="dialog-body">{children}</div>
          {footer && <div className="dialog-footer">{footer}</div>}
        </>
      )}
    </dialog>
  )
}
