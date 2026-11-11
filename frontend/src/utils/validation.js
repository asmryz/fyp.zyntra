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

// Letters from any language (with accents), spaces, full stops, apostrophes and hyphens
const NAME_PATTERN = /^[\p{L}\p{M} .'-]+$/u

export function validateFullName(name) {
  const value = (name || '').trim().replace(/\s+/g, ' ')
  if (value.length < 2) return 'Please enter your full name.'
  if (value.length > 120) return 'Name must be at most 120 characters long.'
  if (!NAME_PATTERN.test(value) || !/\p{L}/u.test(value)) {
    return 'Name can only contain letters, spaces, full stops, apostrophes and hyphens.'
  }
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

// Every "Display order" field (programs, scholarships, test subjects, topics, resources)
export const DISPLAY_ORDER_MIN = 1
export const DISPLAY_ORDER_MAX = 100

/** Returns an error message, or null when the display order is a whole number from 1 to 100. */
export function displayOrderError(value) {
  const text = String(value ?? '').trim()
  if (text === '') return `Enter a display order from ${DISPLAY_ORDER_MIN} to ${DISPLAY_ORDER_MAX}.`
  const number = Number(text)
  if (!/^\d+$/.test(text) || number < DISPLAY_ORDER_MIN || number > DISPLAY_ORDER_MAX) {
    return `Display order must be a whole number from ${DISPLAY_ORDER_MIN} to ${DISPLAY_ORDER_MAX}.`
  }
  return null
}

// Website contact phone: digits only, optionally starting with + for the country code
export const PHONE_PATTERN = /^\+?[0-9]{7,15}$/

export function phoneError(value) {
  const text = String(value ?? '').trim()
  if (text === '') return 'Enter the phone number.'
  if (!PHONE_PATTERN.test(text)) {
    return 'Enter digits only (7 to 15), optionally starting with + for the country code. No spaces, dashes or text.'
  }
  return null
}
