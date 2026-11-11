import { useState } from 'react'
import { Link } from 'react-router-dom'
import AuthLayout, { AuthSubmit, CodeErrorAlert } from '../../components/layout/AuthLayout'
import { Alert } from '../../components/ui/Feedback'
import FormField from '../../components/ui/FormField'
import Icon from '../../components/ui/Icon'
import PasswordField from '../../components/ui/PasswordField'
import { useCooldown } from '../../hooks/useCooldown'
import { usePageTitle } from '../../hooks/usePageTitle'
import { api } from '../../services/api'
import { validateEmail, validatePasswordPair } from '../../utils/validation'

/**
 * Three steps on one page:
 *   1. enter email  -> backend emails a reset code (same reply whether or not the account exists)
 *   2. enter code   -> backend returns a short-lived reset token
 *   3. new password -> backend changes the password and signs out other sessions
 */
const STEP_TEXT = {
  email: {
    eyebrow: 'Password recovery',
    title: 'Forgot your password?',
    subtitle: "Enter the email address of your account and we'll send you reset instructions.",
  },
  code: {
    eyebrow: 'Password recovery',
    title: 'Check your inbox',
    subtitle: 'Enter the 6-digit reset code from the email to continue.',
  },
  password: {
    eyebrow: 'Reset password',
    title: 'Choose a new password',
    subtitle: 'Your new password replaces the old one and signs you out on other devices.',
  },
  done: {
    eyebrow: 'Reset password',
    title: 'Password updated',
    subtitle: 'You can now sign in with your new password.',
  },
}

export default function ForgotPasswordPage() {
  usePageTitle('Reset password')
  const [step, setStep] = useState('email')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [resetToken, setResetToken] = useState(null)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState(null)
  const [info, setInfo] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [cooldown, startCooldown] = useCooldown(0)

  async function run(action) {
    setSubmitting(true)
    setServerError(null)
    try {
      await action()
    } catch (error) {
      setServerError(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  function requestCode(event) {
    event?.preventDefault()
    const emailError = validateEmail(email)
    setErrors(emailError ? { email: emailError } : {})
    if (emailError) {
      setStep('email')
      return
    }
    run(async () => {
      const data = await api.post('/api/auth/forgot-password', { email })
      setInfo(data.message)
      setCode('')
      startCooldown(60)
      setStep('code')
    })
  }

  function verifyCode(event) {
    event.preventDefault()
    if (!/^\d{6}$/.test(code)) {
      setErrors({ code: 'Enter the 6-digit code from the email.' })
      return
    }
    setErrors({})
    run(async () => {
      const data = await api.post('/api/auth/reset-password/verify-code', { email, code })
      setResetToken(data.reset_token)
      setInfo(null)
      setStep('password')
    })
  }

  function savePassword(event) {
    event.preventDefault()
    const newErrors = validatePasswordPair(password, confirmPassword)
    setErrors(newErrors)
    if (Object.keys(newErrors).length) return
    run(async () => {
      const data = await api.post('/api/auth/reset-password', {
        reset_token: resetToken,
        password,
        confirm_password: confirmPassword,
      })
      setInfo(data.message)
      setStep('done')
    })
  }

  function changeEmail() {
    setStep('email')
    setInfo(null)
    setServerError(null)
    setCode('')
  }

  const text = STEP_TEXT[step]

  return (
    <AuthLayout
      eyebrow={text.eyebrow}
      title={text.title}
      subtitle={text.subtitle}
      footer={
        step !== 'done' && (
          <p>
            Remembered it?{' '}
            <Link to="/login" className="text-link">
              Back to sign in
            </Link>
          </p>
        )
      }
    >
      <div className="form-stack">
        <Alert type="success">{info}</Alert>
        {step === 'code' ? <CodeErrorAlert message={serverError} /> : <Alert type="error">{serverError}</Alert>}

        {step === 'email' && (
          <form className="form-stack" onSubmit={requestCode} noValidate>
            <FormField
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              error={errors.email}
            />
            <AuthSubmit busy={submitting} busyLabel="Sending...">
              Send reset instructions
            </AuthSubmit>
          </form>
        )}

        {step === 'code' && (
          <form className="form-stack" onSubmit={verifyCode} noValidate>
            <div className="auth-email">
              <Icon name="mail" size={18} />
              <strong>{email}</strong>
              <button type="button" className="link-button" onClick={changeEmail}>
                Change
              </button>
            </div>
            <FormField
              label="Reset code"
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
              <span>The code expires 10 minutes after it is sent. Check your spam folder if it has not arrived.</span>
            </p>
            <AuthSubmit busy={submitting} busyLabel="Checking...">
              Continue
            </AuthSubmit>
            <p className="auth-resend" aria-live="polite">
              {cooldown > 0 ? (
                <>You can request a new code in {cooldown}s.</>
              ) : (
                <button type="button" className="link-button" onClick={() => requestCode()}>
                  Send a new code
                </button>
              )}
            </p>
          </form>
        )}

        {step === 'password' && (
          <form className="form-stack" onSubmit={savePassword} noValidate>
            <PasswordField
              label="New password"
              autoComplete="new-password"
              placeholder="Create a new password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              error={errors.password}
              hint="At least 8 characters, including a letter and a number."
            />
            <PasswordField
              label="Confirm new password"
              autoComplete="new-password"
              placeholder="Re-enter the new password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              error={errors.confirmPassword}
            />
            <AuthSubmit busy={submitting} busyLabel="Saving...">
              Reset password
            </AuthSubmit>
          </form>
        )}

        {step === 'done' && (
          <Link to="/login" className="btn btn-block auth-submit">
            Sign in <Icon name="arrow-right" size={18} />
          </Link>
        )}
      </div>
    </AuthLayout>
  )
}
