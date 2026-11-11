/** Where each role lands after logging in. */
export function homePathForRole(role) {
  if (role === 'root_admin') return '/root'
  if (role === 'staff') return '/staff'
  return '/student'
}

/**
 * Where a roadmap opens in each role's dashboard: students see it on their
 * roadmap page; staff and the root admin open it in their console (which still
 * checks their Roadmaps module permission).
 */
export function roadmapPathForRole(role, roadmapId) {
  if (role === 'root_admin' || role === 'staff') return `${homePathForRole(role)}/roadmaps/${roadmapId}`
  return `/student/roadmaps/${roadmapId}`
}

/**
 * A student roadmap link (e.g. from a program page, or kept as ?next= through
 * login) opened by staff or the root admin goes to the same roadmap in their
 * own console. Returns null for any other path.
 */
export function roadmapPathFromStudentPath(pathname, role) {
  const match = /^\/student\/roadmaps\/(\d+)\/?$/.exec(pathname)
  return match ? roadmapPathForRole(role, match[1]) : null
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
  if (typeof value !== 'string' || value.length > 500) return null
  // One leading slash only; browsers treat a backslash like a slash ("/\\evil.com" = "//evil.com"),
  // and control characters or spaces can be used to disguise a path
  if (!value.startsWith('/') || value.startsWith('//') || /[\\\s]/.test(value)) return null
  if ([...value].some((ch) => ch.charCodeAt(0) < 32)) return null
  return value
}
