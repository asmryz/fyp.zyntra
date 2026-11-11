import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageHeader } from '../../components/layout/DashboardLayout'
import { Alert, EmptyState, SkeletonList } from '../../components/ui/Feedback'
import Icon from '../../components/ui/Icon'
import { LIMITS } from '../../utils/limits'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'
import { formatDate } from '../../utils/format'
import { ROLE_LABELS } from '../../utils/roles'

const PAGE_SIZE = 20

export function AccountStatus({ user }) {
  return (
    <span className="permission-tags">
      <span className={`badge ${user.is_active ? 'badge-published' : 'badge-error'}`}>{user.is_active ? 'Active' : 'Deactivated'}</span>
      <span className={`badge ${user.is_email_verified ? 'badge-blue' : 'badge-orange'}`}>
        {user.is_email_verified ? 'Verified' : 'Unverified'}
      </span>
    </span>
  )
}

export default function UsersPage() {
  usePageTitle('Users')
  // Filters live in the URL so the browser back button keeps them
  const [params, setParams] = useSearchParams()
  const search = params.get('search') || ''
  const role = params.get('role') || ''
  const status = params.get('status') || ''
  const page = Number(params.get('page')) || 1
  const [searchText, setSearchText] = useState(search)

  const query = new URLSearchParams({ search, role, status, page, page_size: PAGE_SIZE }).toString()
  const { data, error, loading } = useApi(`/api/admin/users?${query}`)

  const updateFilters = (changes) => {
    const next = { search, role, status, page: 1, ...changes }
    setParams(Object.fromEntries(Object.entries(next).filter(([, value]) => value !== '' && value !== 1)))
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  return (
    <>
      <PageHeader
        title="Users"
        description="All registered accounts. Student accounts are created through public registration; staff accounts only through invitations."
        actions={
          <Link to="/root/staff" className="btn btn-primary">
            <Icon name="plus" size={18} /> Invite staff
          </Link>
        }
      />

      <form
        className="toolbar"
        role="search"
        onSubmit={(event) => {
          event.preventDefault()
          updateFilters({ search: searchText.trim() })
        }}
      >
        <label htmlFor="user-search" className="sr-only">
          Search by name or email
        </label>
        <input
          id="user-search"
          className="input"
          placeholder="Search by name or email"
          maxLength={LIMITS.search}
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
        />
        <label htmlFor="role-filter" className="sr-only">
          Filter by role
        </label>
        <select id="role-filter" className="select" value={role} onChange={(event) => updateFilters({ role: event.target.value })}>
          <option value="">All roles</option>
          <option value="student">Students</option>
          <option value="staff">Staff</option>
          <option value="root_admin">Root admins</option>
        </select>
        <label htmlFor="status-filter" className="sr-only">
          Filter by status
        </label>
        <select
          id="status-filter"
          className="select"
          value={status}
          onChange={(event) => updateFilters({ status: event.target.value })}
        >
          <option value="">All statuses</option>
          <option value="active">Active and verified</option>
          <option value="unverified">Unverified</option>
          <option value="inactive">Deactivated</option>
        </select>
        <button type="submit" className="btn btn-secondary">
          <Icon name="search" size={18} /> Search
        </button>
      </form>

      {loading && !data && <SkeletonList rows={5} height={48} />}
      {error && <Alert type="error">{error.message}</Alert>}
      {data?.items.length === 0 && <EmptyState title="No users found">Try a different search or filter.</EmptyState>}
      {data?.items.length > 0 && (
        <>
          <div className="table-wrap" aria-busy={loading}>
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Role</th>
                  <th scope="col">Status</th>
                  <th scope="col">Joined</th>
                  <th scope="col">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((user) => (
                  <tr key={user.id}>
                    <td>
                      <span className="cell-primary">{user.full_name}</span>
                      <span className="cell-secondary">{user.email}</span>
                    </td>
                    <td>
                      <span className={`badge ${user.role === 'root_admin' ? 'badge-orange' : user.role === 'staff' ? 'badge-blue' : ''}`}>
                        {ROLE_LABELS[user.role]}
                      </span>
                    </td>
                    <td>
                      <AccountStatus user={user} />
                    </td>
                    <td>{formatDate(user.created_at)}</td>
                    <td className="cell-actions">
                      <Link to={`/root/users/${user.id}`} className="btn btn-secondary btn-sm">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span>
              {data.total} user{data.total === 1 ? '' : 's'} · page {page} of {totalPages}
            </span>
            <span style={{ display: 'flex', gap: 8 }}>
              <button type="button" className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => updateFilters({ page: page - 1 })}>
                Previous
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                disabled={page >= totalPages}
                onClick={() => updateFilters({ page: page + 1 })}
              >
                Next
              </button>
            </span>
          </div>
        </>
      )}
    </>
  )
}
