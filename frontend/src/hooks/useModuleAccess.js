import { useAuth } from '../context/AuthContext'

/**
 * The current user's access to one content module, used to show or hide
 * editing controls. The backend enforces the same rules on every request.
 */
export function useModuleAccess(module) {
  const { user } = useAuth()
  const level = user?.permissions?.[module] || null
  return {
    level,
    canView: Boolean(level),
    canWrite: level === 'write' || level === 'read_write',
    // 'write' staff only see and edit the records they created
    ownRecordsOnly: level === 'write',
  }
}

/** '/root' for the root admin console, '/staff' for the staff console. */
export function useConsoleBase() {
  const { user } = useAuth()
  return user?.role === 'root_admin' ? '/root' : '/staff'
}
