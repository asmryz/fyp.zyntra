import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import AuthLayout, { AuthSubmit } from '../../components/layout/AuthLayout'
import { Alert, PageLoader } from '../../components/ui/Feedback'
import PasswordField from '../../components/ui/PasswordField'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import { useApi } from '../../hooks/useApi'
import { useFormOptions } from '../../hooks/useFormOptions'
import { usePageTitle } from '../../hooks/usePageTitle'
import { api } from '../../services/api'
import { formatDateTime } from '../../utils/format'
import { validatePasswordPair } from '../../utils/validation'

/** Staff members finish their registration here from the emailed invitation link. */
export default function AcceptInvitePage() {
  usePageTitle('Accept invitation')
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''
  const navigate = useNavigate()
  const { user, startSession } = useAuth()
  const toast = useToast()
  const options = useFormOptions()
  const preview = useApi(token ? `/api/invitations/preview?token=${encodeURIComponent(token)}` : null)

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const newErrors = validatePasswordPair(password, confirmPassword)
    setErrors(newErrors)
    if (Object.keys(newErrors).length) return

    setSubmitting(true)
    setServerError(null)
    try {
      const data = await api.post('/api/invitations/accept', { token, password, confirm_password: confirmPassword })
      startSession(data)
      toast.success('Your staff account is active.')
      navigate('/staff', { replace: true })
    } catch (error) {
      setServerError(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  let content
  if (!token) {
    content = <Alert type="error">This invitation link is incomplete. Please open the full link from your email.</Alert>
  } else if (preview.loading) {
    content = <PageLoader label="Checking your invitation..." />
  } else if (preview.error) {
    content = (
      <>
        <Alert type="error">{preview.error.message}</Alert>
        <Link to="/login" className="btn btn-secondary btn-block auth-secondary" style={{ marginTop: 18 }}>
          Go to sign in
        </Link>
      </>
    )
  } else if (preview.data) {
    const invite = preview.data
    content = (
      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        {user && (
          <Alert type="warning">
            You are currently logged in as {user.email}. Accepting this invitation will switch to the new staff account.
          </Alert>
        )}
        <div className="auth-invitee">
          <p>
            <strong>{invite.full_name}</strong>
            <br />
            {invite.email}
          </p>
          <p className="field-hint" style={{ marginTop: 6 }}>
            This invitation expires on {formatDateTime(invite.expires_at)}.
          </p>
        </div>
        <div>
          <p className="field-label" style={{ marginBottom: 8 }}>
            Your access
          </p>
          <ul className="permission-list">
            {Object.entries(invite.permissions).map(([module, level]) => (
              <li key={module}>
                <span>{options?.content_modules?.[module] || module}</span>
                <strong>{options?.access_levels?.[level] || level}</strong>
              </li>
            ))}
          </ul>
        </div>
        <Alert type="error">{serverError}</Alert>
        <PasswordField
          label="Create a password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={errors.password}
          hint="At least 8 characters, including a letter and a number."
        />
        <PasswordField
          label="Confirm password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          error={errors.confirmPassword}
        />
        <AuthSubmit busy={submitting} busyLabel="Activating...">
          Activate staff account
        </AuthSubmit>
      </form>
    )
  }

  return (
    <AuthLayout
      eyebrow="Staff invitation"
      title="Join the ZYNTRA staff team"
      subtitle="Set your password to activate your staff account."
    >
      {content}
    </AuthLayout>
  )
}
