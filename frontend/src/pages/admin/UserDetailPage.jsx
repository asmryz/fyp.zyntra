import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { EditorDialog, PermissionTags } from '../../components/admin/AdminParts'
import { PageHeader } from '../../components/layout/DashboardLayout'
import { Alert, PageLoader } from '../../components/ui/Feedback'
import FormField from '../../components/ui/FormField'
import Icon from '../../components/ui/Icon'
import { useToast } from '../../context/ToastContext'
import { useApi } from '../../hooks/useApi'
import { useConfirm } from '../../hooks/useConfirm'
import { useFormOptions } from '../../hooks/useFormOptions'
import { usePageTitle } from '../../hooks/usePageTitle'
import { api } from '../../services/api'
import { formatDate, formatDateTime } from '../../utils/format'
import { ROLE_LABELS } from '../../utils/roles'
import { AccountStatus } from './UsersPage'

const PROFILE_ROWS = [
  ['Contact number', 'contact_number'],
  ['Previous qualification', 'previous_qualification'],
  ['Academic background', 'academic_background'],
  ['Board or university', 'board_or_university'],
  ['Passing year', 'passing_year'],
  ['Marks', null],
  ['Percentage', 'percentage'],
  ['Preferred program', 'preferred_program_name'],
  ['Other details', 'additional_details'],
]

export default function UserDetailPage() {
  const { userId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const options = useFormOptions()
  const [confirm, confirmDialog] = useConfirm()
  const { data: user, error, loading, reload } = useApi(`/api/admin/users/${userId}`)
  usePageTitle(user?.full_name || 'User')
  const [nameForm, setNameForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState(null)

  if (loading && !user) return <PageLoader />
  if (error) return <Alert type="error">{error.message}</Alert>

  const manageable = user.role !== 'root_admin'

  async function setActive(isActive) {
    const ok = await confirm({
      title: isActive ? 'Activate account?' : 'Deactivate account?',
      message: isActive
        ? `${user.full_name} will be able to log in again.`
        : `${user.full_name} will be signed out immediately and will not be able to log in.`,
      confirmLabel: isActive ? 'Activate' : 'Deactivate',
    })
    if (!ok) return
    try {
      await api.patch(`/api/admin/users/${user.id}`, { is_active: isActive })
      toast.success(isActive ? 'Account activated.' : 'Account deactivated.')
      reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function deleteAccount() {
    const ok = await confirm({
      title: 'Delete account permanently?',
      message: `${user.full_name}'s account${user.role === 'student' ? ' and profile' : ''} will be permanently deleted. Content they created is kept. This cannot be undone.`,
    })
    if (!ok) return
    try {
      await api.delete(`/api/admin/users/${user.id}`)
      toast.success('Account deleted.')
      navigate('/root/users', { replace: true })
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function saveName() {
    setSaving(true)
    setFormError(null)
    try {
      await api.patch(`/api/admin/users/${user.id}`, { full_name: nameForm })
      toast.success('Name updated.')
      setNameForm(null)
      reload()
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const profile = user.profile

  return (
    <>
      <Link to="/root/users" className="back-link" style={{ marginBottom: 12 }}>
        <Icon name="arrow-left" size={16} /> All users
      </Link>
      <PageHeader
        title={user.full_name}
        description={user.email}
        actions={
          manageable && (
            <>
              <button type="button" className="btn btn-secondary" onClick={() => setNameForm(user.full_name)}>
                <Icon name="edit" size={18} /> Edit name
              </button>
              {user.is_active ? (
                <button type="button" className="btn btn-secondary" onClick={() => setActive(false)}>
                  Deactivate
                </button>
              ) : (
                <button type="button" className="btn btn-primary" onClick={() => setActive(true)}>
                  Activate
                </button>
              )}
              <button type="button" className="btn btn-danger" onClick={deleteAccount}>
                <Icon name="trash" size={18} /> Delete
              </button>
            </>
          )
        }
      />
      {!manageable && (
        <div style={{ marginBottom: 20 }}>
          <Alert type="info">Root admin accounts are managed from the command line, not from the dashboard.</Alert>
        </div>
      )}

      <div className="two-column">
        <section className="panel" aria-labelledby="account-details">
          <h2 id="account-details" className="panel-title">
            Account
          </h2>
          <dl className="detail-list">
            <div>
              <dt>Status</dt>
              <dd>
                <AccountStatus user={user} />
              </dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{ROLE_LABELS[user.role]}</dd>
            </div>
            <div>
              <dt>Account created</dt>
              <dd>{formatDateTime(user.created_at)}</dd>
            </div>
            <div>
              <dt>Last login</dt>
              <dd>{formatDateTime(user.last_login_at)}</dd>
            </div>
          </dl>
        </section>

        {user.role === 'student' && profile && (
          <section className="panel" aria-labelledby="profile-details">
            <h2 id="profile-details" className="panel-title">
              Academic profile ({profile.completeness_percent}% complete)
            </h2>
            <dl className="detail-list">
              {PROFILE_ROWS.map(([label, field]) => {
                const value =
                  field === null
                    ? profile.obtained_marks !== null && profile.total_marks !== null
                      ? `${profile.obtained_marks} / ${profile.total_marks}`
                      : null
                    : profile[field]
                return (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value === null || value === '' ? '-' : field === 'percentage' ? `${value}%` : value}</dd>
                  </div>
                )
              })}
            </dl>
          </section>
        )}

        {user.role === 'staff' && (
          <section className="panel" aria-labelledby="staff-permissions">
            <div className="panel-head">
              <h2 id="staff-permissions" className="panel-title">
                Module permissions
              </h2>
              <Link to="/root/staff" className="btn btn-ghost btn-sm">
                Manage permissions
              </Link>
            </div>
            <PermissionTags permissions={user.permissions} modules={options?.content_modules} levels={options?.access_levels} />
          </section>
        )}
      </div>

      <section className="panel" style={{ marginTop: 20 }} aria-labelledby="user-activity">
        <h2 id="user-activity" className="panel-title">
          Recent activity
        </h2>
        {user.recent_activity.length === 0 ? (
          <p className="field-hint">No recorded activity.</p>
        ) : (
          <ul className="activity-list">
            {user.recent_activity.map((log) => (
              <li key={log.id}>
                <span>{log.summary}</span>
                <span className="activity-meta">
                  {log.actor_name || 'System'} · {formatDate(log.created_at)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <EditorDialog
        open={nameForm !== null}
        title="Edit name"
        onClose={() => setNameForm(null)}
        onSubmit={saveName}
        saving={saving}
        error={formError}
      >
        <FormField label="Full name" value={nameForm || ''} onChange={(event) => setNameForm(event.target.value)} />
      </EditorDialog>
      {confirmDialog}
    </>
  )
}
