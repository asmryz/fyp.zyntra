import { Link } from 'react-router-dom'
import '../../styles/auth.css'
import { Alert } from '../ui/Feedback'
import Icon from '../ui/Icon'

/**
 * Shared layout for login, registration, email verification, password
 * recovery and staff invitations: a minimal header, a soft branded
 * background and one centred card.
 */
export default function AuthLayout({ eyebrow, title, subtitle, children, footer }) {
  return (
    <div className="auth-shell">
      <div className="auth-backdrop" aria-hidden="true">
        <span className="auth-backdrop-left">ZY</span>
        <span className="auth-backdrop-right">RA</span>
      </div>

      <header className="auth-header">
        <Link to="/" className="auth-brand" aria-label="ZYNTRA home">
          <span className="auth-brand-mark" aria-hidden="true">
            Z
          </span>
          <span className="auth-brand-word">ZYNTRA</span>
        </Link>
        <Link to="/" className="auth-home-link">
          <Icon name="arrow-left" size={18} /> Home
        </Link>
      </header>

      <main className="auth-main" id="main">
        <div className="auth-card page-enter">
          {eyebrow && <p className="auth-eyebrow">{eyebrow}</p>}
          <h1 className="auth-title">{title}</h1>
          {subtitle && <p className="auth-subtitle">{subtitle}</p>}
          {children}
          {footer && <div className="auth-footer">{footer}</div>}
        </div>
      </main>
    </div>
  )
}

/**
 * Error box for verification and reset codes. The backend message is shown
 * as-is; a short heading tells apart a wrong code from one that has expired,
 * was replaced, or is locked after too many attempts.
 */
export function CodeErrorAlert({ message }) {
  if (!message) return null
  let heading = null
  if (/expired|already been used|request a new code/i.test(message)) heading = 'This code can no longer be used'
  else if (/incorrect code|invalid/i.test(message)) heading = 'That code is not correct'
  return (
    <Alert type="error">
      {heading && (
        <p>
          <strong>{heading}</strong>
        </p>
      )}
      <p>{message}</p>
    </Alert>
  )
}

/** Full-width pill button used as the main action on every auth card. */
export function AuthSubmit({ busy, busyLabel, children }) {
  return (
    <button type="submit" className="btn btn-block auth-submit" disabled={busy}>
      {busy && <span className="spinner" aria-hidden="true" />}
      {busy ? busyLabel : children}
      {!busy && <Icon name="arrow-right" size={18} />}
    </button>
  )
}
