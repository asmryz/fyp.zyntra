import { useState } from 'react'
import { AccessNote, DisplayOrderField, EditorDialog, ModuleGuard, StatusField, StepsEditor } from '../../../components/admin/AdminParts'
import { PageHeader } from '../../../components/layout/DashboardLayout'
import ScholarshipInfographic from '../../../components/scholarship/ScholarshipInfographic'
import Dialog from '../../../components/ui/Dialog'
import { Alert, EmptyState, SkeletonList, StatusBadge } from '../../../components/ui/Feedback'
import FormField from '../../../components/ui/FormField'
import Icon from '../../../components/ui/Icon'
import ListEditor from '../../../components/ui/ListEditor'
import { useToast } from '../../../context/ToastContext'
import { useApi } from '../../../hooks/useApi'
import { useConfirm } from '../../../hooks/useConfirm'
import { useModuleAccess } from '../../../hooks/useModuleAccess'
import { usePageTitle } from '../../../hooks/usePageTitle'
import { api } from '../../../services/api'
import { formatDate } from '../../../utils/format'
import { displayOrderError } from '../../../utils/validation'

const EMPTY_SCHOLARSHIP = {
  title: '', scholarship_type: '', summary: '', description: '', eligibility_criteria: [], benefits: [],
  required_documents: [], application_steps: [], conditions: [], status: 'draft', sort_order: 1,
}

function toForm(record) {
  const form = { ...EMPTY_SCHOLARSHIP }
  for (const key of Object.keys(EMPTY_SCHOLARSHIP)) {
    if (record[key] !== null && record[key] !== undefined) form[key] = record[key]
  }
  return form
}

function toBody(form) {
  return {
    ...form,
    sort_order: Number(form.sort_order),
    // Drop empty steps the editor may have left behind
    application_steps: form.application_steps.filter((step) => step.title.trim() || step.description.trim()),
  }
}

function ScholarshipFields({ form, setForm }) {
  const set = (field) => (event) => setForm({ ...form, [field]: event.target.value })
  const setList = (field) => (items) => setForm({ ...form, [field]: items })

  return (
    <>
      <div className="form-grid">
        <FormField label="Scholarship title" value={form.title} onChange={set('title')} className="span-2" />
        <FormField
          label="Scholarship type"
          optional
          maxLength={80}
          value={form.scholarship_type}
          onChange={set('scholarship_type')}
          placeholder="e.g. Merit-based, Need-based"
        />
        <StatusField value={form.status} onChange={(status) => setForm({ ...form, status })} />
        <FormField label="Short summary" optional className="span-2" maxLength={300} value={form.summary} onChange={set('summary')} />
        <FormField label="Description" optional as="textarea" className="span-2" value={form.description} onChange={set('description')} />
        <DisplayOrderField value={form.sort_order} onChange={set('sort_order')} />
      </div>
      <div className="form-section form-stack">
        <ListEditor label="Eligibility criteria" value={form.eligibility_criteria} onChange={setList('eligibility_criteria')} addLabel="Add criterion" />
        <ListEditor label="Benefits" value={form.benefits} onChange={setList('benefits')} addLabel="Add benefit" />
        <ListEditor label="Required documents" value={form.required_documents} onChange={setList('required_documents')} addLabel="Add document" />
        <StepsEditor value={form.application_steps} onChange={setList('application_steps')} />
        <ListEditor label="Important conditions" value={form.conditions} onChange={setList('conditions')} addLabel="Add condition" />
      </div>
    </>
  )
}

export default function ScholarshipsManager() {
  usePageTitle('Scholarship management')
  return (
    <ModuleGuard module="scholarships">
      <ScholarshipsManagerContent />
    </ModuleGuard>
  )
}

function ScholarshipsManagerContent() {
  const access = useModuleAccess('scholarships')
  const toast = useToast()
  const [confirm, confirmDialog] = useConfirm()
  const scholarships = useApi('/api/admin/scholarships')
  const [editor, setEditor] = useState(null)
  const [preview, setPreview] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const openEditor = (record) => {
    setError(null)
    setEditor({ record, form: record ? toForm(record) : { ...EMPTY_SCHOLARSHIP }, readOnly: record ? !record.can_edit : false })
  }

  async function save() {
    if (displayOrderError(editor.form.sort_order)) {
      setError('Please correct the highlighted field.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const body = toBody(editor.form)
      if (editor.record) await api.put(`/api/admin/scholarships/${editor.record.id}`, body)
      else await api.post('/api/admin/scholarships', body)
      toast.success(editor.record ? 'Scholarship updated.' : 'Scholarship created.')
      setEditor(null)
      scholarships.reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function togglePublish(record) {
    try {
      const status = record.status === 'published' ? 'draft' : 'published'
      await api.put(`/api/admin/scholarships/${record.id}`, toBody({ ...toForm(record), status }))
      toast.success(status === 'published' ? 'Scholarship published.' : 'Scholarship moved to draft.')
      scholarships.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function remove(record) {
    const ok = await confirm({ title: 'Delete scholarship?', message: `"${record.title}" will be permanently deleted.` })
    if (!ok) return
    try {
      await api.delete(`/api/admin/scholarships/${record.id}`)
      toast.success('Scholarship deleted.')
      scholarships.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  return (
    <>
      <PageHeader
        title="Scholarships"
        description="Scholarship details shown to students: eligibility, benefits, documents and the application procedure."
        actions={
          access.canWrite && (
            <button type="button" className="btn btn-primary" onClick={() => openEditor(null)}>
              <Icon name="plus" size={18} /> Add scholarship
            </button>
          )
        }
      />
      <AccessNote module="scholarships" />

      <div style={{ marginTop: 16 }}>
        {scholarships.loading && <SkeletonList />}
        {scholarships.error && <Alert type="error">{scholarships.error.message}</Alert>}
        {scholarships.data?.length === 0 && (
          <EmptyState title="No scholarships yet">
            {access.canWrite ? 'Add a scholarship to show it in the student dashboard.' : 'No scholarships are available to you.'}
          </EmptyState>
        )}
        {scholarships.data?.length > 0 && (
          <ul className="record-list">
            {scholarships.data.map((record) => (
              <li key={record.id} className="record-row">
                <div className="record-main">
                  <span className="record-title">{record.title}</span>
                  <div className="record-meta">
                    <StatusBadge status={record.status} />
                    {record.scholarship_type && <span>{record.scholarship_type}</span>}
                    <span>{record.application_steps.length} steps</span>
                    <span>Updated {formatDate(record.updated_at)}</span>
                  </div>
                </div>
                <div className="record-actions">
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => setPreview(record)}>
                    Preview
                  </button>
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => openEditor(record)}>
                    <Icon name={record.can_edit ? 'edit' : 'file'} size={16} /> {record.can_edit ? 'Edit' : 'View'}
                  </button>
                  {record.can_edit && (
                    <>
                      <button type="button" className="btn btn-secondary btn-sm" onClick={() => togglePublish(record)}>
                        {record.status === 'published' ? 'Unpublish' : 'Publish'}
                      </button>
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => remove(record)}>
                        <Icon name="trash" size={16} /> Delete
                      </button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <EditorDialog
        open={Boolean(editor)}
        title={editor?.record ? (editor.readOnly ? editor.record.title : 'Edit scholarship') : 'Add scholarship'}
        onClose={() => setEditor(null)}
        onSubmit={save}
        saving={saving}
        error={error}
        readOnly={editor?.readOnly}
      >
        {editor && <ScholarshipFields form={editor.form} setForm={(form) => setEditor({ ...editor, form })} />}
      </EditorDialog>

      <Dialog open={Boolean(preview)} onClose={() => setPreview(null)} title="Student view preview" wide>
        {preview && <ScholarshipInfographic scholarship={preview} />}
      </Dialog>
      {confirmDialog}
    </>
  )
}
