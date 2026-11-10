import { useId } from 'react'

/**
 * A labelled form control with optional hint and error text.
 *
 *   <FormField label="Email" type="email" value={email} onChange={...} error={errors.email} />
 *   <FormField label="Program" as="select" ...><option>...</option></FormField>
 *   <FormField label="Description" as="textarea" ... />
 *
 * `action` is an optional button shown inside the input on the right
 * (used by PasswordField for the show/hide password toggle).
 */
export default function FormField({
  label,
  as = 'input',
  error,
  hint,
  optional = false,
  className = '',
  action,
  children,
  ...controlProps
}) {
  const id = useId()
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined
  const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined

  const sharedProps = {
    id,
    'aria-invalid': error ? 'true' : undefined,
    'aria-describedby': describedBy,
    ...controlProps,
  }

  let control
  if (as === 'select') {
    control = (
      <select className="select" {...sharedProps}>
        {children}
      </select>
    )
  } else if (as === 'textarea') {
    control = <textarea className="textarea" {...sharedProps} />
  } else {
    control = <input className="input" {...sharedProps} />
  }

  return (
    <div className={`field ${className}`}>
      <label className="field-label" htmlFor={id}>
        {label} {optional && <span className="optional">(optional)</span>}
      </label>
      {action ? (
        <div className="input-with-action">
          {control}
          {action}
        </div>
      ) : (
        control
      )}
      {hint && (
        <span className="field-hint" id={hintId}>
          {hint}
        </span>
      )}
      {error && (
        <span className="field-error" id={errorId}>
          {error}
        </span>
      )}
    </div>
  )
}
