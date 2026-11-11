import { useState } from 'react'
import { AccessNote, DisplayOrderField, EditorDialog, ModuleGuard, StatusField } from '../../../components/admin/AdminParts'
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
import { DISPLAY_ORDER_MAX, displayOrderError } from '../../../utils/validation'

const EMPTY_PROGRAM = {
  name: '', department: '', degree_level: '', duration: '', summary: '', description: '', admission_requirements: '',
  min_percentage: '', accepted_qualifications: [], eligibility_notes: '', status: 'draft', sort_order: 1,
}

// Optional text fields: an empty input is saved as "no value" (null), not as an empty string
const OPTIONAL_TEXT = ['department', 'degree_level', 'duration', 'summary', 'description', 'admission_requirements', 'eligibility_notes']

function toForm(program) {
  const form = { ...EMPTY_PROGRAM }
  for (const key of Object.keys(EMPTY_PROGRAM)) {
    if (program[key] !== null && program[key] !== undefined) form[key] = program[key]
  }
  form.min_percentage = program.min_percentage ?? ''
  form.accepted_qualifications = Array.isArray(program.accepted_qualifications) ? [...program.accepted_qualifications] : []
  form.sort_order = program.sort_order === null || program.sort_order === undefined ? '' : String(program.sort_order)
  return form
}

function toBody(form) {
  const body = {
    ...form,
    min_percentage: form.min_percentage === '' ? null : Number(form.min_percentage),
    sort_order: Number(form.sort_order),
  }
  for (const key of OPTIONAL_TEXT) {
    if (typeof body[key] === 'string' && body[key].trim() === '') body[key] = null
  }
  return body
}

function ProgramFields({ form, setForm, qualifications, savedQualifications }) {
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
        <FormField label="Program name" maxLength={150} value={form.name} onChange={set('name')} className="span-2" />
        <FormField label="Department" optional maxLength={120} value={form.department} onChange={set('department')} />
        <FormField
          label="Degree level"
          optional
          maxLength={40}
          value={form.degree_level}
          onChange={set('degree_level')}
          placeholder="e.g. Undergraduate"
        />
        <FormField label="Duration" optional maxLength={60} value={form.duration} onChange={set('duration')} />
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
        {/* Top-aligned so the display order hint and error do not stretch the input beside it */}
        <div className="form-grid" style={{ alignItems: 'start' }}>
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
          <DisplayOrderField value={form.sort_order} onChange={set('sort_order')} />
        </div>
        <fieldset className="list-editor" style={{ marginTop: 16 }}>
          <legend className="field-label">Accepted qualifications</legend>
          {/* The standard list, plus any other values this program already stores */}
          {[...qualifications, ...savedQualifications.filter((item) => !qualifications.includes(item))].map((item) => (
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
    // New programs go to the end of the list by default
    const last = Math.max(0, ...(programs.data || []).map((program) => program.sort_order || 0))
    const form = record ? toForm(record) : { ...EMPTY_PROGRAM, sort_order: String(Math.min(DISPLAY_ORDER_MAX, last + 1)) }
    setEditor({ record, form, readOnly: record ? !record.can_edit : false })
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
            savedQualifications={editor.record?.accepted_qualifications || []}
          />
        )}
      </EditorDialog>
      {confirmDialog}
    </>
  )
}
