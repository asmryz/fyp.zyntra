import { useState } from 'react'
import { AccessNote, EditorDialog, ModuleGuard, StatusField } from '../../../components/admin/AdminParts'
import { PageHeader } from '../../../components/layout/DashboardLayout'
import { Alert, EmptyState, SkeletonList, StatusBadge } from '../../../components/ui/Feedback'
import FormField from '../../../components/ui/FormField'
import Icon from '../../../components/ui/Icon'
import { useToast } from '../../../context/ToastContext'
import { useApi } from '../../../hooks/useApi'
import { useConfirm } from '../../../hooks/useConfirm'
import { useFormOptions } from '../../../hooks/useFormOptions'
import { useModuleAccess } from '../../../hooks/useModuleAccess'
import { usePageTitle } from '../../../hooks/usePageTitle'
import { api } from '../../../services/api'
import { formatDate } from '../../../utils/format'

const EMPTY_PROGRAM = {
  name: '', department: '', degree_level: '', duration: '', summary: '', description: '', admission_requirements: '',
  min_percentage: '', accepted_qualifications: [], eligibility_notes: '', status: 'draft', sort_order: 0,
}

function toForm(program) {
  const form = { ...EMPTY_PROGRAM }
  for (const key of Object.keys(EMPTY_PROGRAM)) {
    if (program[key] !== null && program[key] !== undefined) form[key] = program[key]
  }
  form.min_percentage = program.min_percentage ?? ''
  return form
}

function toBody(form) {
  return {
    ...form,
    min_percentage: form.min_percentage === '' ? null : Number(form.min_percentage),
    sort_order: Number(form.sort_order) || 0,
  }
}

function ProgramFields({ form, setForm, qualifications }) {
  const set = (field) => (event) => setForm({ ...form, [field]: event.target.value })
  const toggleQualification = (item) => {
    const list = form.accepted_qualifications
    setForm({
      ...form,
      accepted_qualifications: list.includes(item) ? list.filter((value) => value !== item) : [...list, item],
    })
  }

  return (
    <>
      <div className="form-grid">
        <FormField label="Program name" value={form.name} onChange={set('name')} className="span-2" />
        <FormField label="Department" optional value={form.department} onChange={set('department')} />
        <FormField
          label="Degree level"
          optional
          value={form.degree_level}
          onChange={set('degree_level')}
          placeholder="e.g. Undergraduate"
        />
        <FormField label="Duration" optional value={form.duration} onChange={set('duration')} />
        <StatusField value={form.status} onChange={(status) => setForm({ ...form, status })} />
        <FormField
          label="Short summary"
          optional
          className="span-2"
          value={form.summary}
          onChange={set('summary')}
          maxLength={300}
          hint="Shown in program lists (up to 300 characters)."
        />
        <FormField label="Description" optional as="textarea" className="span-2" value={form.description} onChange={set('description')} />
        <FormField
          label="Admission requirements"
          optional
          as="textarea"
          className="span-2"
          value={form.admission_requirements}
          onChange={set('admission_requirements')}
        />
      </div>

      <div className="form-section">
        <h3 className="form-section-title">Preliminary eligibility criteria</h3>
        <p className="field-hint" style={{ marginBottom: 12 }}>
          Used to compare student profiles. Leave empty until the official criteria are confirmed.
        </p>
        <div className="form-grid">
          <FormField
            label="Minimum marks (%)"
            optional
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={form.min_percentage}
            onChange={set('min_percentage')}
          />
          <FormField label="Display order" type="number" value={form.sort_order} onChange={set('sort_order')} />
        </div>
        <fieldset className="list-editor" style={{ marginTop: 16 }}>
          <legend className="field-label">Accepted qualifications</legend>
          {qualifications.map((item) => (
            <label key={item} className="checkbox-row">
              <input
                type="checkbox"
                checked={form.accepted_qualifications.includes(item)}
                onChange={() => toggleQualification(item)}
              />
              {item}
            </label>
          ))}
        </fieldset>
        <FormField
          label="Eligibility notes"
          optional
          as="textarea"
          rows={3}
          value={form.eligibility_notes}
          onChange={set('eligibility_notes')}
          className="form-section"
        />
      </div>
    </>
  )
}

export default function ProgramsManager() {
  usePageTitle('Program management')
  return (
    <ModuleGuard module="programs">
      <ProgramsManagerContent />
    </ModuleGuard>
  )
}

function ProgramsManagerContent() {
  const access = useModuleAccess('programs')
  const options = useFormOptions()
  const toast = useToast()
  const [confirm, confirmDialog] = useConfirm()
  const programs = useApi('/api/admin/programs')
  const [editor, setEditor] = useState(null) // { record, form, readOnly }
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const openEditor = (record) => {
    setError(null)
    setEditor({ record, form: record ? toForm(record) : { ...EMPTY_PROGRAM }, readOnly: record ? !record.can_edit : false })
  }

  async function save() {
    setSaving(true)
    setError(null)
    try {
      const body = toBody(editor.form)
      if (editor.record) await api.put(`/api/admin/programs/${editor.record.id}`, body)
      else await api.post('/api/admin/programs', body)
      toast.success(editor.record ? 'Program updated.' : 'Program created.')
      setEditor(null)
      programs.reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function remove(program) {
    const ok = await confirm({
      title: 'Delete program?',
      message: `"${program.name}" will be removed from the website. Linked roadmaps are kept but unlinked.`,
    })
    if (!ok) return
    try {
      await api.delete(`/api/admin/programs/${program.id}`)
      toast.success('Program deleted.')
      programs.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  return (
    <>
      <PageHeader
        title="Program information"
        description="Programs shown on the public website, their admission requirements and eligibility criteria."
        actions={
          access.canWrite && (
            <button type="button" className="btn btn-primary" onClick={() => openEditor(null)}>
              <Icon name="plus" size={18} /> Add program
            </button>
          )
        }
      />
      <AccessNote module="programs" />

      <div style={{ marginTop: 16 }}>
        {programs.loading && <SkeletonList />}
        {programs.error && <Alert type="error">{programs.error.message}</Alert>}
        {programs.data?.length === 0 && (
          <EmptyState title="No programs yet">
            {access.canWrite ? 'Add the first program to show it on the website.' : 'No programs are available to you.'}
          </EmptyState>
        )}
        {programs.data?.length > 0 && (
          <ul className="record-list">
            {programs.data.map((program) => (
              <li key={program.id} className="record-row">
                <div className="record-main">
                  <span className="record-title">{program.name}</span>
                  <div className="record-meta">
                    <StatusBadge status={program.status} />
                    {program.department && <span>{program.department}</span>}
                    <span>
                      Criteria:{' '}
                      {program.min_percentage !== null || program.accepted_qualifications.length
                        ? 'published'
                        : 'not set'}
                    </span>
                    <span>Updated {formatDate(program.updated_at)}</span>
                  </div>
                </div>
                <div className="record-actions">
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => openEditor(program)}>
                    <Icon name={program.can_edit ? 'edit' : 'file'} size={16} /> {program.can_edit ? 'Edit' : 'View'}
                  </button>
                  {program.can_edit && (
                    <button type="button" className="btn btn-danger btn-sm" onClick={() => remove(program)}>
                      <Icon name="trash" size={16} /> Delete
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <EditorDialog
        open={Boolean(editor)}
        title={editor?.record ? (editor.readOnly ? editor.record.name : 'Edit program') : 'Add program'}
        onClose={() => setEditor(null)}
        onSubmit={save}
        saving={saving}
        error={error}
        readOnly={editor?.readOnly}
      >
        {editor && (
          <ProgramFields
            form={editor.form}
            setForm={(form) => setEditor({ ...editor, form })}
            qualifications={options?.qualifications || []}
          />
        )}
      </EditorDialog>
      {confirmDialog}
    </>
  )
}
