import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import AuthLayout, { AuthSubmit } from '../../components/layout/AuthLayout'
import { Alert } from '../../components/ui/Feedback'
import FormField from '../../components/ui/FormField'
import PasswordField from '../../components/ui/PasswordField'
import { useAuth } from '../../context/AuthContext'
import { usePageTitle } from '../../hooks/usePageTitle'
import { api } from '../../services/api'
import { homePathForRole } from '../../utils/roles'
import { validateEmail, validateFullName, validatePasswordPair } from '../../utils/validation'

/** Public registration creates student accounts only. */
export default function RegisterPage() {
  usePageTitle('Create account')
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ fullName: '', email: '', password: '', confirmPassword: '' })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to={homePathForRole(user.role)} replace />

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    const newErrors = validatePasswordPair(form.password, form.confirmPassword)
    const nameError = validateFullName(form.fullName)
    const emailError = validateEmail(form.email)
    if (nameError) newErrors.fullName = nameError
    if (emailError) newErrors.email = emailError
    setErrors(newErrors)
    if (Object.keys(newErrors).length) return

    setSubmitting(true)
    setServerError(null)
    try {
      await api.post('/api/auth/register', {
        full_name: form.fullName,
        email: form.email,
        password: form.password,
        confirm_password: form.confirmPassword,
      })
      navigate(`/verify-email?email=${encodeURIComponent(form.email.trim())}&sent=1`)
    } catch (error) {
      setServerError(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      eyebrow="Student account"
      title="Create your account"
      // ‑ is a non-breaking hyphen so "6-digit" never splits across lines
      subtitle={"Free for prospective CS students. We'll email you a 6‑digit code to verify your address."}
      footer={
        <>
          <p>
            Already have an account?{' '}
            <Link to="/login" className="text-link">
              Sign in
            </Link>
          </p>
          <p className="auth-legal">
            By creating an account you agree to the <Link to="/terms">Terms of Service</Link> and{' '}
            <Link to="/privacy">Privacy Policy</Link>.
          </p>
        </>
      }
    >
      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        <Alert type="error">{serverError}</Alert>
        <FormField
          label="Full name"
          autoComplete="name"
          placeholder="Your full name"
          value={form.fullName}
          onChange={update('fullName')}
          error={errors.fullName}
          required
        />
        <FormField
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={form.email}
          onChange={update('email')}
          error={errors.email}
          required
        />
        <PasswordField
          label="Password"
          autoComplete="new-password"
          placeholder="Create a password"
          value={form.password}
          onChange={update('password')}
          error={errors.password}
          hint="At least 8 characters, including a letter and a number."
          required
        />
        <PasswordField
          label="Confirm password"
          autoComplete="new-password"
          placeholder="Re-enter your password"
          value={form.confirmPassword}
          onChange={update('confirmPassword')}
          error={errors.confirmPassword}
          required
        />
        <AuthSubmit busy={submitting} busyLabel="Creating account...">
          Create account
        </AuthSubmit>
      </form>
    </AuthLayout>
  )
}
