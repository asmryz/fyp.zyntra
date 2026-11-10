import { useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import AuthLayout, { AuthSubmit } from '../../components/layout/AuthLayout'
import { Alert } from '../../components/ui/Feedback'
import FormField from '../../components/ui/FormField'
import PasswordField from '../../components/ui/PasswordField'
import { useAuth } from '../../context/AuthContext'
import { usePageTitle } from '../../hooks/usePageTitle'
import { homePathForRole, safeNextPath } from '../../utils/roles'
import { validateEmail } from '../../utils/validation'

export default function LoginPage() {
  usePageTitle('Login')
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const nextPath = safeNextPath(searchParams.get('next'))

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState(null)
  const [needsVerification, setNeedsVerification] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to={nextPath || homePathForRole(user.role)} replace />

  async function handleSubmit(event) {
    event.preventDefault()
    const newErrors = {}
    const emailError = validateEmail(email)
    if (emailError) newErrors.email = emailError
    if (!password) newErrors.password = 'Please enter your password.'
    setErrors(newErrors)
    if (Object.keys(newErrors).length) return

    setSubmitting(true)
    setServerError(null)
    setNeedsVerification(false)
    try {
      const loggedInUser = await login(email, password)
      navigate(nextPath || homePathForRole(loggedInUser.role), { replace: true })
    } catch (error) {
      if (error.data?.detail?.code === 'email_not_verified') setNeedsVerification(true)
      setServerError(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      eyebrow="Welcome back"
      title="Sign in to ZYNTRA"
      subtitle="Continue exploring your academic journey with ZYNTRA."
      footer={
        <p>
          New to ZYNTRA?{' '}
          <Link to="/register" className="text-link">
            Create a student account
          </Link>
        </p>
      }
    >
      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        {serverError && (
          <Alert type="error">
            <p>{serverError}</p>
            {needsVerification && (
              <p style={{ marginTop: 8 }}>
                <Link to={`/verify-email?email=${encodeURIComponent(email)}`} className="text-link">
                  Enter your verification code
                </Link>
              </p>
            )}
          </Alert>
        )}
        <FormField
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={errors.email}
          required
        />
        <PasswordField
          label="Password"
          autoComplete="current-password"
          placeholder="Enter your password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={errors.password}
          required
        />
        <div className="auth-row">
          <Link to="/forgot-password" className="text-link">
            Forgot password?
          </Link>
        </div>
        <AuthSubmit busy={submitting} busyLabel="Signing in...">
          Sign in
        </AuthSubmit>
      </form>
    </AuthLayout>
  )
}
