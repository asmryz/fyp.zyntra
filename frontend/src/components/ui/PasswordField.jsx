import { useState } from 'react'
import FormField from './FormField'
import Icon from './Icon'

/** A password FormField with an eye button that shows or hides the password. */
export default function PasswordField({ label, ...props }) {
  const [visible, setVisible] = useState(false)

  return (
    <FormField
      label={label}
      type={visible ? 'text' : 'password'}
      autoCapitalize="none"
      spellCheck={false}
      {...props}
      action={
        <button
          type="button"
          className="input-action"
          onClick={() => setVisible((value) => !value)}
          aria-pressed={visible}
          aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
        >
          <Icon name={visible ? 'eye-off' : 'eye'} size={20} />
        </button>
      }
    />
  )
}
