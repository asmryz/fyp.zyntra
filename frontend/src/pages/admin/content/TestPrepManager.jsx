import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AccessNote, EditorDialog, ModuleGuard, StatusField } from '../../../components/admin/AdminParts'
import { PageHeader } from '../../../components/layout/DashboardLayout'
import { Alert, EmptyState, SkeletonList, StatusBadge } from '../../../components/ui/Feedback'
import FormField from '../../../components/ui/FormField'
import Icon from '../../../components/ui/Icon'
import { useToast } from '../../../context/ToastContext'
import { useApi } from '../../../hooks/useApi'
import { useConfirm } from '../../../hooks/useConfirm'
import { useConsoleBase, useModuleAccess } from '../../../hooks/useModuleAccess'
import { usePageTitle } from '../../../hooks/usePageTitle'
import { api } from '../../../services/api'

const EMPTY_SUBJECT = { name: '', description: '', status: 'draft', sort_order: 0 }

export function SubjectFields({ form, setForm }) {
  const set = (field) => (event) => setForm({ ...form, [field]: event.target.value })
  return (
    <div className="form-grid">
      <FormField label="Subject name" value={form.name} onChange={set('name')} className="span-2" placeholder="e.g. Mathematics" />
      <FormField label="Description" optional as="textarea" className="span-2" value={form.description} onChange={set('description')} />
      <StatusField value={form.status} onChange={(status) => setForm({ ...form, status })} />
      <FormField label="Display order" type="number" value={form.sort_order} onChange={set('sort_order')} />
    </div>
  )
}

export default function TestPrepManager() {
  usePageTitle('Test preparation management')
  return (
    <ModuleGuard module="test_prep">
      <TestPrepManagerContent />
    </ModuleGuard>
  )
}

function TestPrepManagerContent() {
  const access = useModuleAccess('test_prep')
  const base = useConsoleBase()
  const toast = useToast()
  const [confirm, confirmDialog] = useConfirm()
  const subjects = useApi('/api/admin/test-prep/subjects')
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  async function create() {
    setSaving(true)
    setError(null)
    try {
      await api.post('/api/admin/test-prep/subjects', { ...form, sort_order: Number(form.sort_order) || 0 })
      toast.success('Subject created. Open it to add topics and resources.')
      setForm(null)
      subjects.reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function remove(subject) {
    const ok = await confirm({
      title: 'Delete subject?',
      message: `"${subject.name}" with its ${subject.topic_count} topics and ${subject.resource_count} resources will be permanently deleted.`,
    })
    if (!ok) return
    try {
      await api.delete(`/api/admin/test-prep/subjects/${subject.id}`)
      toast.success('Subject deleted.')
      subjects.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  return (
    <>
      <PageHeader
        title="Test preparation"
        description="Subjects, topics, explanations, learning resources and past papers."
        actions={
          access.canWrite && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                setError(null)
                setForm({ ...EMPTY_SUBJECT })
              }}
            >
              <Icon name="plus" size={18} /> Add subject
            </button>
          )
        }
      />
      <AccessNote module="test_prep" />

      <div style={{ marginTop: 16 }}>
        {subjects.loading && <SkeletonList />}
        {subjects.error && <Alert type="error">{subjects.error.message}</Alert>}
        {subjects.data?.length === 0 && (
          <EmptyState title="No subjects yet">
            {access.canWrite ? 'Add a subject, then add its topics and resources.' : 'No subjects are available to you.'}
          </EmptyState>
        )}
        {subjects.data?.length > 0 && (
          <ul className="record-list">
            {subjects.data.map((subject) => (
              <li key={subject.id} className="record-row">
                <div className="record-main">
                  <Link to={`${base}/test-prep/subjects/${subject.id}`} className="record-title">
                    {subject.name}
                  </Link>
                  <div className="record-meta">
                    <StatusBadge status={subject.status} />
                    <span>{subject.topic_count} topics</span>
                    <span>{subject.resource_count} resources</span>
                  </div>
                </div>
                <div className="record-actions">
                  <Link to={`${base}/test-prep/subjects/${subject.id}`} className="btn btn-secondary btn-sm">
                    <Icon name={subject.can_edit ? 'edit' : 'file'} size={16} /> {subject.can_edit ? 'Manage' : 'View'}
                  </Link>
                  {subject.can_edit && (
                    <button type="button" className="btn btn-danger btn-sm" onClick={() => remove(subject)}>
                      <Icon name="trash" size={16} /> Delete
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <EditorDialog open={Boolean(form)} title="Add subject" onClose={() => setForm(null)} onSubmit={create} saving={saving} error={error}>
        {form && <SubjectFields form={form} setForm={setForm} />}
      </EditorDialog>
      {confirmDialog}
    </>
  )
}
