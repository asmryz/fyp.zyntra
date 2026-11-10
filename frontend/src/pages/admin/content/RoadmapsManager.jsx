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
import { formatDate } from '../../../utils/format'
import { roadmapToBody, useProgramChoices } from './roadmapHelpers'

const EMPTY_ROADMAP = { title: '', category: '', summary: '', description: '', program_id: '', status: 'draft' }

export function RoadmapFields({ form, setForm, programs }) {
  const set = (field) => (event) => setForm({ ...form, [field]: event.target.value })
  return (
    <div className="form-grid">
      <FormField
        label="Program heading (roadmap title)"
        value={form.title}
        onChange={set('title')}
        className="span-2"
        placeholder="e.g. Computer Science"
        hint="Shown at the top of the roadmap, with the branches below it."
      />
      <FormField
        label="Category"
        optional
        value={form.category}
        onChange={set('category')}
        placeholder="e.g. Program roadmap, Career roadmap"
      />
      <FormField label="Linked program" optional as="select" value={form.program_id} onChange={set('program_id')}>
        <option value="">Not linked to a program</option>
        {programs.map((program) => (
          <option key={program.id} value={program.id}>
            {program.name}
          </option>
        ))}
      </FormField>
      <FormField label="Short summary" optional className="span-2" maxLength={300} value={form.summary} onChange={set('summary')} />
      <FormField label="Description" optional as="textarea" className="span-2" value={form.description} onChange={set('description')} />
      <StatusField value={form.status} onChange={(status) => setForm({ ...form, status })} />
    </div>
  )
}

export default function RoadmapsManager() {
  usePageTitle('Roadmap management')
  return (
    <ModuleGuard module="roadmaps">
      <RoadmapsManagerContent />
    </ModuleGuard>
  )
}

function RoadmapsManagerContent() {
  const access = useModuleAccess('roadmaps')
  const base = useConsoleBase()
  const toast = useToast()
  const [confirm, confirmDialog] = useConfirm()
  const roadmaps = useApi('/api/admin/roadmaps')
  const programs = useProgramChoices()
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  async function create() {
    setSaving(true)
    setError(null)
    try {
      await api.post('/api/admin/roadmaps', roadmapToBody(form))
      toast.success('Roadmap created. Open it to add branches and steps.')
      setForm(null)
      roadmaps.reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function remove(roadmap) {
    const ok = await confirm({
      title: 'Delete roadmap?',
      message: `"${roadmap.title}" with its ${roadmap.branch_count} branches and ${roadmap.node_count} steps will be permanently deleted.`,
    })
    if (!ok) return
    try {
      await api.delete(`/api/admin/roadmaps/${roadmap.id}`)
      toast.success('Roadmap deleted.')
      roadmaps.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  return (
    <>
      <PageHeader
        title="Roadmaps"
        description="Program roadmaps: a central heading with any number of coloured branches, each with its own steps and step details."
        actions={
          access.canWrite && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                setError(null)
                setForm({ ...EMPTY_ROADMAP })
              }}
            >
              <Icon name="plus" size={18} /> Add roadmap
            </button>
          )
        }
      />
      <AccessNote module="roadmaps" />

      <div style={{ marginTop: 16 }}>
        {roadmaps.loading && <SkeletonList />}
        {roadmaps.error && <Alert type="error">{roadmaps.error.message}</Alert>}
        {roadmaps.data?.length === 0 && (
          <EmptyState title="No roadmaps yet">
            {access.canWrite ? 'Create a roadmap, then add its branches and steps.' : 'No roadmaps are available to you.'}
          </EmptyState>
        )}
        {roadmaps.data?.length > 0 && (
          <ul className="record-list">
            {roadmaps.data.map((roadmap) => (
              <li key={roadmap.id} className="record-row">
                <div className="record-main">
                  <Link to={`${base}/roadmaps/${roadmap.id}`} className="record-title">
                    {roadmap.title}
                  </Link>
                  <div className="record-meta">
                    <StatusBadge status={roadmap.status} />
                    {roadmap.category && <span>{roadmap.category}</span>}
                    {roadmap.program_name && <span>{roadmap.program_name}</span>}
                    <span>{roadmap.branch_count} branches</span>
                    <span>{roadmap.node_count} steps</span>
                    <span>Updated {formatDate(roadmap.updated_at)}</span>
                  </div>
                </div>
                <div className="record-actions">
                  <Link to={`${base}/roadmaps/${roadmap.id}`} className="btn btn-secondary btn-sm">
                    <Icon name={roadmap.can_edit ? 'edit' : 'file'} size={16} /> {roadmap.can_edit ? 'Open editor' : 'View'}
                  </Link>
                  {roadmap.can_edit && (
                    <button type="button" className="btn btn-danger btn-sm" onClick={() => remove(roadmap)}>
                      <Icon name="trash" size={16} /> Delete
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <EditorDialog open={Boolean(form)} title="Add roadmap" onClose={() => setForm(null)} onSubmit={create} saving={saving} error={error}>
        {form && <RoadmapFields form={form} setForm={setForm} programs={programs} />}
      </EditorDialog>
      {confirmDialog}
    </>
  )
}
