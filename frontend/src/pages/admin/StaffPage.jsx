import { useState } from 'react'
import { Link } from 'react-router-dom'
import { EditorDialog, PermissionMatrix, PermissionTags } from '../../components/admin/AdminParts'
import { PageHeader } from '../../components/layout/DashboardLayout'
import { Alert, EmptyState, PageLoader, SkeletonList } from '../../components/ui/Feedback'
import FormField from '../../components/ui/FormField'
import Icon from '../../components/ui/Icon'
import { useToast } from '../../context/ToastContext'
import { useApi } from '../../hooks/useApi'
import { useConfirm } from '../../hooks/useConfirm'
import { useFormOptions } from '../../hooks/useFormOptions'
import { usePageTitle } from '../../hooks/usePageTitle'
import { api } from '../../services/api'
import { formatDate, formatDateTime } from '../../utils/format'
import { validateEmail, validateFullName } from '../../utils/validation'

const INVITATION_BADGES = {
  pending: 'badge-blue',
  accepted: 'badge-published',
  expired: 'badge-draft',
  revoked: 'badge-error',
}

/** Remove "no access" entries so only granted modules are sent to the API. */
function grantedOnly(permissions) {
  return Object.fromEntries(Object.entries(permissions).filter(([, level]) => level))
}

function InviteForm({ options, onInvited }) {
  const toast = useToast()
  const [form, setForm] = useState({ fullName: '', email: '', permissions: {} })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState(null)
  const [sending, setSending] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const newErrors = {}
    const nameError = validateFullName(form.fullName)
    const emailError = validateEmail(form.email)
    if (nameError) newErrors.fullName = nameError
    if (emailError) newErrors.email = emailError
    if (Object.keys(grantedOnly(form.permissions)).length === 0) newErrors.permissions = 'Give access to at least one module.'
    setErrors(newErrors)
    if (Object.keys(newErrors).length) return

    setSending(true)
    setServerError(null)
    try {
      await api.post('/api/admin/invitations', {
        full_name: form.fullName,
        email: form.email,
        permissions: grantedOnly(form.permissions),
      })
      toast.success(`Invitation sent to ${form.email}.`)
      setForm({ fullName: '', email: '', permissions: {} })
      onInvited()
    } catch (err) {
      setServerError(err.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <form className="panel form-stack" onSubmit={handleSubmit} noValidate aria-labelledby="invite-title">
      <div>
        <h2 id="invite-title" className="panel-title" style={{ marginBottom: 4 }}>
          Invite a staff member
        </h2>
        <p className="field-hint">
          They receive an email with a single-use link that expires in 72 hours. The account becomes active when they set
          a password.
        </p>
      </div>
      <Alert type="error">{serverError}</Alert>
      <div className="form-grid">
        <FormField label="Full name" value={form.fullName} onChange={(event) => setForm({ ...form, fullName: event.target.value })} error={errors.fullName} />
        <FormField
          label="Email address"
          type="email"
          value={form.email}
          onChange={(event) => setForm({ ...form, email: event.target.value })}
          error={errors.email}
        />
      </div>
      <div>
        <p className="field-label" style={{ marginBottom: 6 }}>
          Permissions
        </p>
        <p className="field-hint" style={{ marginBottom: 8 }}>
          Read: view content. Write: create content and edit their own records. Read + Write: view and edit all content.
        </p>
        <PermissionMatrix
          idPrefix="invite"
          modules={options.content_modules}
          levels={options.access_levels}
          value={form.permissions}
          onChange={(permissions) => setForm({ ...form, permissions })}
        />
        {errors.permissions && <p className="field-error">{errors.permissions}</p>}
      </div>
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={sending}>
          {sending && <span className="spinner" aria-hidden="true" />}
          {sending ? 'Sending invitation...' : 'Send invitation'}
        </button>
      </div>
    </form>
  )
}

export default function StaffPage() {
  usePageTitle('Staff management')
  const options = useFormOptions()
  const toast = useToast()
  const [confirm, confirmDialog] = useConfirm()
  const staff = useApi('/api/admin/staff')
  const invitations = useApi('/api/admin/invitations')
  const [editing, setEditing] = useState(null) // { member, permissions }
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  if (!options) return <PageLoader />

  async function savePermissions() {
    setSaving(true)
    setError(null)
    try {
      await api.put(`/api/admin/staff/${editing.member.id}/permissions`, { permissions: grantedOnly(editing.permissions) })
      toast.success(`Permissions updated for ${editing.member.full_name}.`)
      setEditing(null)
      staff.reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function setActive(member, isActive) {
    const ok = await confirm({
      title: isActive ? 'Activate staff account?' : 'Deactivate staff account?',
      message: isActive
        ? `${member.full_name} will be able to log in again.`
        : `${member.full_name} will be signed out immediately and lose access until reactivated.`,
      confirmLabel: isActive ? 'Activate' : 'Deactivate',
    })
    if (!ok) return
    try {
      await api.patch(`/api/admin/users/${member.id}`, { is_active: isActive })
      toast.success(isActive ? 'Staff account activated.' : 'Staff account deactivated.')
      staff.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function resend(invitation) {
    try {
      await api.post(`/api/admin/invitations/${invitation.id}/resend`)
      toast.success(`A new invitation link was sent to ${invitation.email}.`)
      invitations.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function revoke(invitation) {
    const ok = await confirm({
      title: 'Revoke invitation?',
      message: `The invitation link sent to ${invitation.email} will stop working.`,
      confirmLabel: 'Revoke',
    })
    if (!ok) return
    try {
      await api.delete(`/api/admin/invitations/${invitation.id}`)
      toast.success('Invitation revoked.')
      invitations.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  return (
    <>
      <PageHeader
        title="Staff and permissions"
        description="Invite staff members, choose which content modules they can read or edit, and manage their access."
      />

      <InviteForm options={options} onInvited={invitations.reload} />

      <section className="panel" aria-labelledby="staff-title">
        <h2 id="staff-title" className="panel-title">
          Staff members
        </h2>
        {staff.loading && !staff.data && <SkeletonList rows={2} />}
        {staff.error && <Alert type="error">{staff.error.message}</Alert>}
        {staff.data?.length === 0 && <EmptyState title="No staff members yet">Staff appear here after accepting their invitation.</EmptyState>}
        {staff.data?.length > 0 && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Staff member</th>
                  <th scope="col">Permissions</th>
                  <th scope="col">Status</th>
                  <th scope="col">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {staff.data.map((member) => (
                  <tr key={member.id}>
                    <td>
                      <Link to={`/root/users/${member.id}`} className="cell-primary">
                        {member.full_name}
                      </Link>
                      <span className="cell-secondary">{member.email}</span>
                    </td>
                    <td>
                      <PermissionTags permissions={member.permissions} modules={options.content_modules} levels={options.access_levels} />
                    </td>
                    <td>
                      <span className={`badge ${member.is_active ? 'badge-published' : 'badge-error'}`}>
                        {member.is_active ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td className="cell-actions">
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          setError(null)
                          setEditing({ member, permissions: { ...member.permissions } })
                        }}
                      >
                        Edit permissions
                      </button>{' '}
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setActive(member, !member.is_active)}>
                        {member.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel" aria-labelledby="invitations-title">
        <h2 id="invitations-title" className="panel-title">
          Invitations
        </h2>
        {invitations.loading && !invitations.data && <SkeletonList rows={2} />}
        {invitations.error && <Alert type="error">{invitations.error.message}</Alert>}
        {invitations.data?.length === 0 && <p className="field-hint">No invitations have been sent yet.</p>}
        {invitations.data?.length > 0 && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Invitee</th>
                  <th scope="col">Status</th>
                  <th scope="col">Sent</th>
                  <th scope="col">Expires</th>
                  <th scope="col">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {invitations.data.map((invitation) => (
                  <tr key={invitation.id}>
                    <td>
                      <span className="cell-primary">{invitation.full_name}</span>
                      <span className="cell-secondary">{invitation.email}</span>
                    </td>
                    <td>
                      <span className={`badge ${INVITATION_BADGES[invitation.status]}`}>{invitation.status}</span>
                    </td>
                    <td>
                      {formatDate(invitation.created_at)}
                      {invitation.invited_by_name && <span className="cell-secondary">by {invitation.invited_by_name}</span>}
                    </td>
                    <td>{invitation.status === 'accepted' ? `Accepted ${formatDate(invitation.accepted_at)}` : formatDateTime(invitation.expires_at)}</td>
                    <td className="cell-actions">
                      {invitation.status !== 'accepted' && (
                        <button type="button" className="btn btn-secondary btn-sm" onClick={() => resend(invitation)}>
                          <Icon name="refresh" size={16} /> Resend
                        </button>
                      )}{' '}
                      {invitation.status === 'pending' && (
                        <button type="button" className="btn btn-danger btn-sm" onClick={() => revoke(invitation)}>
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <EditorDialog
        open={Boolean(editing)}
        title={`Permissions: ${editing?.member.full_name || ''}`}
        onClose={() => setEditing(null)}
        onSubmit={savePermissions}
        saving={saving}
        error={error}
      >
        {editing && (
          <>
            <p className="field-hint">Changes take effect on the staff member’s next request.</p>
            <PermissionMatrix
              idPrefix="edit"
              modules={options.content_modules}
              levels={options.access_levels}
              value={editing.permissions}
              onChange={(permissions) => setEditing({ ...editing, permissions })}
            />
          </>
        )}
      </EditorDialog>
      {confirmDialog}
    </>
  )
}
