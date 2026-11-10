import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import AuthLayout, { AuthSubmit, CodeErrorAlert } from '../../components/layout/AuthLayout'
import { Alert } from '../../components/ui/Feedback'
import FormField from '../../components/ui/FormField'
import Icon from '../../components/ui/Icon'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import { useCooldown } from '../../hooks/useCooldown'
import { usePageTitle } from '../../hooks/usePageTitle'
import { api } from '../../services/api'
import { validateEmail } from '../../utils/validation'

const RESEND_SECONDS = 60

export default function VerifyEmailPage() {
  usePageTitle('Verify your email')
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { startSession } = useAuth()
  const toast = useToast()

  const [email, setEmail] = useState(searchParams.get('email') || '')
  // The email arrives from the registration page; it can still be changed here
  const [editingEmail, setEditingEmail] = useState(!searchParams.get('email'))
  const [code, setCode] = useState('')
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState(null)
  const [info, setInfo] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [resending, setResending] = useState(false)
  const [cooldown, startCooldown] = useCooldown(searchParams.get('sent') ? RESEND_SECONDS : 0)

  async function handleSubmit(event) {
    event.preventDefault()
    const newErrors = {}
    const emailError = validateEmail(email)
    if (emailError) {
      newErrors.email = emailError
      setEditingEmail(true)
    }
    if (!/^\d{6}$/.test(code)) newErrors.code = 'Enter the 6-digit code from the email.'
    setErrors(newErrors)
    if (Object.keys(newErrors).length) return

    setSubmitting(true)
    setServerError(null)
    try {
      const data = await api.post('/api/auth/verify-email', { email, code })
      startSession(data)
      toast.success('Your email is verified. Welcome to ZYNTRA!')
      navigate('/student', { replace: true })
    } catch (error) {
      setServerError(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleResend() {
    const emailError = validateEmail(email)
    if (emailError) {
      setErrors({ email: emailError })
      setEditingEmail(true)
      return
    }
    setResending(true)
    setServerError(null)
    try {
      const data = await api.post('/api/auth/resend-verification', { email })
      setInfo(data.message)
      setCode('')
      startCooldown(RESEND_SECONDS)
    } catch (error) {
      setServerError(error.message)
    } finally {
      setResending(false)
    }
  }

  return (
    <AuthLayout
      eyebrow="Verify your email"
      title="Check your inbox"
      subtitle={'Enter the 6‑digit code we emailed you to activate your student account.'}
      footer={
        <p>
          Wrong email?{' '}
          <Link to="/register" className="text-link">
            Register again
          </Link>
        </p>
      }
    >
      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        <Alert type="success">{info}</Alert>
        <CodeErrorAlert message={serverError} />

        {editingEmail ? (
          <FormField
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            error={errors.email}
          />
        ) : (
          <div className="auth-email">
            <Icon name="mail" size={18} />
            <span>
              Code sent to <strong>{email}</strong>
            </span>
            <button type="button" className="link-button" onClick={() => setEditingEmail(true)}>
              Change
            </button>
          </div>
        )}

        <FormField
          label="Verification code"
          className="code-field"
          inputMode="numeric"
          autoComplete="one-time-code"
          placeholder="000000"
          maxLength={6}
          value={code}
          onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
          error={errors.code}
        />
        <p className="auth-note">
          <Icon name="info" size={16} />
          <span>Codes expire 15 minutes after they are sent. Each code allows 5 attempts.</span>
        </p>

        <AuthSubmit busy={submitting} busyLabel="Verifying...">
          Verify email
        </AuthSubmit>

        <p className="auth-resend" aria-live="polite">
          {cooldown > 0 ? (
            <>Didn&apos;t get it? You can request a new code in {cooldown}s.</>
          ) : (
            <>
              Didn&apos;t get it?{' '}
              <button type="button" className="link-button" onClick={handleResend} disabled={resending}>
                {resending ? 'Sending...' : 'Send a new code'}
              </button>
            </>
          )}
        </p>
      </form>
    </AuthLayout>
  )
}
