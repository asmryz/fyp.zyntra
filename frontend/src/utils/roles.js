/** Where each role lands after logging in. */
export function homePathForRole(role) {
  if (role === 'root_admin') return '/root'
  if (role === 'staff') return '/staff'
  return '/student'
}

export const ROLE_LABELS = {
  root_admin: 'Root Admin',
  staff: 'Staff',
  student: 'Student',
}

/**
 * Only allow redirects to paths inside this site (prevents "open redirect"
 * links such as /login?next=https://evil.example).
 */
export function safeNextPath(value) {
  if (typeof value !== 'string') return null
  if (!value.startsWith('/') || value.startsWith('//')) return null
  return value
}
