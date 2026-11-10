// Client-side checks give quick feedback. The backend repeats every check,
// so these rules must match app/schemas/auth.py.

export function validatePassword(password) {
  if (!password || password.length < 8) return 'Password must be at least 8 characters long.'
  if (new TextEncoder().encode(password).length > 72) return 'Password must be at most 72 characters long.'
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) return 'Password must contain at least one letter and one number.'
  return null
}

export function validateEmail(email) {
  if (!email) return 'Please enter your email address.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Please enter a valid email address.'
  return null
}

export function validateFullName(name) {
  if (!name || name.trim().length < 2) return 'Please enter your full name.'
  return null
}

/** Returns an object of errors for a new password + confirmation pair. */
export function validatePasswordPair(password, confirmPassword) {
  const errors = {}
  const passwordError = validatePassword(password)
  if (passwordError) errors.password = passwordError
  if (password !== confirmPassword) errors.confirmPassword = 'Passwords do not match.'
  return errors
}
