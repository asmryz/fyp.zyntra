import { useId, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { EditorDialog, LinksEditor, ModuleGuard } from '../../../components/admin/AdminParts'
import { PageHeader } from '../../../components/layout/DashboardLayout'
import RoadmapCanvas from '../../../components/roadmap/RoadmapCanvas'
import { DEFAULT_BRANCH_COLOR } from '../../../components/roadmap/roadmapColors'
import { Alert, EmptyState, PageLoader, RichText, StatusBadge } from '../../../components/ui/Feedback'
import FormField from '../../../components/ui/FormField'
import Icon from '../../../components/ui/Icon'
import ListEditor from '../../../components/ui/ListEditor'
import { useToast } from '../../../context/ToastContext'
import { useApi } from '../../../hooks/useApi'
import { useConfirm } from '../../../hooks/useConfirm'
import { useFormOptions } from '../../../hooks/useFormOptions'
import { useConsoleBase } from '../../../hooks/useModuleAccess'
import { usePageTitle } from '../../../hooks/usePageTitle'
import { api } from '../../../services/api'
import {
  isHexColor, moveItem, newSection, roadmapToBody, roadmapToForm, SECTION_TITLE_SUGGESTIONS, sectionToBody,
  sectionToForm, useProgramChoices,
} from './roadmapHelpers'
import { RoadmapFields } from './RoadmapsManager'

const ITEM_LABELS = { skills: 'Add skill', tools: 'Add tool or technology', list: 'Add item' }

function BranchFields({ form, setForm, colors }) {
  const set = (field) => (event) => setForm({ ...form, [field]: event.target.value })
  const colorValid = isHexColor(form.color)
  return (
    <div className="form-grid">
      <FormField
        label="Branch name"
        value={form.name}
        onChange={set('name')}
        className="span-2"
        placeholder="e.g. Software Development"
      />
      <FormField label="Description" optional as="textarea" rows={3} className="span-2" value={form.description} onChange={set('description')} />
      <fieldset className="color-field span-2">
        <legend className="field-label">Branch colour</legend>
        <div className="color-choices">
          {colors.map((color) => (
            <button
              key={color}
              type="button"
              className="color-choice"
              style={{ background: color }}
              aria-pressed={form.color.toUpperCase() === color}
              onClick={() => setForm({ ...form, color })}
            >
              <span className="sr-only">Use colour {color}</span>
            </button>
          ))}
          <label className="color-custom">
            <input
              type="color"
              value={colorValid ? form.color : DEFAULT_BRANCH_COLOR}
              onChange={(event) => setForm({ ...form, color: event.target.value.toUpperCase() })}
              aria-label="Pick any colour"
            />
            <span>Custom</span>
          </label>
          <input
            className="input color-hex"
            value={form.color}
            onChange={set('color')}
            maxLength={7}
            aria-label="Colour as hex code"
            aria-invalid={colorValid ? undefined : 'true'}
          />
        </div>
        <span className={colorValid ? 'field-hint' : 'field-error'}>
          {colorValid
            ? 'Used for the branch heading, its line, its steps and the selected step.'
            : 'Enter a colour like #2563EB.'}
        </span>
      </fieldset>
    </div>
  )
}

/** The ordered list of detail sections of one step. */
function SectionsEditor({ sections, onChange, types }) {
  const listId = useId()
  const update = (index, changes) => onChange(sections.map((section, i) => (i === index ? { ...section, ...changes } : section)))

  return (
    <fieldset className="sections-editor">
      <legend className="field-label">Detail sections</legend>
      <span className="field-hint">
        Shown in the step&apos;s detail card in this order. Add skills, tools or any other section such as prerequisites or projects.
      </span>
      <datalist id={listId}>
        {SECTION_TITLE_SUGGESTIONS.map((title) => (
          <option key={title} value={title} />
        ))}
      </datalist>

      {sections.length === 0 && <p className="list-editor-empty">No sections yet.</p>}
      {sections.map((section, index) => (
        <div key={index} className="section-editor">
          <div className="section-editor-head">
            <span className="list-editor-number" aria-hidden="true">
              {index + 1}
            </span>
            <FormField
              label="Section title"
              value={section.section_title}
              onChange={(event) => update(index, { section_title: event.target.value })}
              list={listId}
            />
            <FormField
              label="Type"
              as="select"
              value={section.section_type}
              onChange={(event) => update(index, { section_type: event.target.value })}
            >
              {Object.entries(types).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </FormField>
            <div className="list-editor-actions">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange(moveItem(sections, index, -1))} disabled={index === 0}>
                <Icon name="chevron-up" size={16} label={`Move section ${index + 1} up`} />
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => onChange(moveItem(sections, index, 1))}
                disabled={index === sections.length - 1}
              >
                <Icon name="chevron-down" size={16} label={`Move section ${index + 1} down`} />
              </button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange(sections.filter((_, i) => i !== index))}>
                <Icon name="trash" size={16} label={`Remove section ${index + 1}`} />
              </button>
            </div>
          </div>
          {['skills', 'tools', 'list'].includes(section.section_type) && (
            <ListEditor
              label={`${section.section_title || 'Section'} items`}
              value={section.items}
              onChange={(items) => update(index, { items })}
              addLabel={ITEM_LABELS[section.section_type]}
            />
          )}
          {section.section_type === 'text' && (
            <FormField
              label="Text"
              as="textarea"
              rows={4}
              value={section.text}
              onChange={(event) => update(index, { text: event.target.value })}
              hint="Leave a blank line between paragraphs."
            />
          )}
          {section.section_type === 'links' && (
            <LinksEditor label="Links" value={section.links} onChange={(links) => update(index, { links })} />
          )}
        </div>
      ))}

      <div className="sections-editor-add">
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => onChange([...sections, newSection('skills')])}>
          <Icon name="plus" size={16} /> Skills
        </button>
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => onChange([...sections, newSection('tools')])}>
          <Icon name="plus" size={16} /> Tools &amp; Technologies
        </button>
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => onChange([...sections, newSection('list')])}>
          <Icon name="plus" size={16} /> Other section
        </button>
      </div>
    </fieldset>
  )
}

function StepFields({ form, setForm, types }) {
  const set = (field) => (event) => setForm({ ...form, [field]: event.target.value })
  return (
    <>
      <div className="form-grid">
        <FormField label="Step title" value={form.title} onChange={set('title')} className="span-2" />
        <FormField
          label="Description"
          optional
          as="textarea"
          rows={4}
          className="span-2"
          value={form.description}
          onChange={set('description')}
        />
        <label className="checkbox-row span-2">
          <input type="checkbox" checked={form.is_default} onChange={(event) => setForm({ ...form, is_default: event.target.checked })} />
          Open this step automatically when the roadmap is viewed (only one step per roadmap)
        </label>
      </div>
      <SectionsEditor sections={form.sections} onChange={(sections) => setForm({ ...form, sections })} types={types} />
    </>
  )
}

export default function RoadmapEditor() {
  return (
    <ModuleGuard module="roadmaps">
      <RoadmapEditorContent />
    </ModuleGuard>
  )
}

function RoadmapEditorContent() {
  const { roadmapId } = useParams()
  const base = useConsoleBase()
  const toast = useToast()
  const options = useFormOptions()
  const [confirm, confirmDialog] = useConfirm()
  const roadmap = useApi(`/api/admin/roadmaps/${roadmapId}`)
  const programs = useProgramChoices()
  usePageTitle(roadmap.data?.title || 'Roadmap editor')

  const [view, setView] = useState('manage')
  // editor = { kind: 'details' | 'branch' | 'step', id, branchId, form }
  const [editor, setEditor] = useState(null)
  const [saving, setSaving] = useState(false)
  const [moving, setMoving] = useState(false)
  const [error, setError] = useState(null)

  if (roadmap.loading && !roadmap.data) return <PageLoader />
  if (roadmap.error) return <Alert type="error">{roadmap.error.message}</Alert>

  const data = roadmap.data
  const canEdit = data.can_edit
  const colors = options?.roadmap_branch_colors || [DEFAULT_BRANCH_COLOR]
  const sectionTypes = options?.roadmap_section_types || {}

  const open = (kind, record, branchId) => {
    setError(null)
    if (kind === 'details') setEditor({ kind, form: roadmapToForm(data) })
    if (kind === 'branch') {
      const nextColor = colors[data.branches.length % colors.length]
      setEditor({
        kind,
        id: record?.id,
        form: record
          ? { name: record.name, description: record.description || '', color: record.color }
          : { name: '', description: '', color: nextColor },
      })
    }
    if (kind === 'step') {
      setEditor({
        kind,
        id: record?.id,
        branchId,
        form: record
          ? {
              title: record.title,
              description: record.description || '',
              is_default: record.is_default,
              sections: record.sections.map(sectionToForm),
            }
          : { title: '', description: '', is_default: false, sections: [newSection('skills'), newSection('tools')] },
      })
    }
  }

  async function save() {
    setSaving(true)
    setError(null)
    const { kind, id, branchId, form } = editor
    try {
      if (kind === 'details') {
        await api.put(`/api/admin/roadmaps/${data.id}`, roadmapToBody(form))
      } else if (kind === 'branch') {
        const body = { ...form, description: form.description || null }
        if (id) await api.put(`/api/admin/roadmap-branches/${id}`, body)
        else await api.post(`/api/admin/roadmaps/${data.id}/branches`, body)
      } else {
        const body = {
          title: form.title,
          description: form.description || null,
          is_default: form.is_default,
          sections: form.sections.map(sectionToBody),
        }
        if (id) await api.put(`/api/admin/roadmap-nodes/${id}`, body)
        else await api.post(`/api/admin/roadmap-branches/${branchId}/nodes`, body)
      }
      toast.success('Saved.')
      setEditor(null)
      roadmap.reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function remove(kind, record) {
    const message =
      kind === 'branch'
        ? `"${record.name}" and its ${record.nodes.length} step(s) will be permanently deleted.`
        : `"${record.title}" and its details will be permanently deleted.`
    if (!(await confirm({ title: kind === 'branch' ? 'Delete branch?' : 'Delete step?', message }))) return
    try {
      await api.delete(kind === 'branch' ? `/api/admin/roadmap-branches/${record.id}` : `/api/admin/roadmap-nodes/${record.id}`)
      toast.success('Deleted.')
      roadmap.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function reorder(path, list, index, direction) {
    const ids = moveItem(list, index, direction).map((item) => item.id)
    setMoving(true)
    try {
      await api.put(path, { ids })
      roadmap.reload()
    } catch (err) {
      toast.error(err.message)
    } finally {
      setMoving(false)
    }
  }

  const stepCount = data.branches.reduce((total, branch) => total + branch.nodes.length, 0)
  const dialogTitle = {
    details: 'Edit roadmap details',
    branch: editor?.id ? 'Edit branch' : 'Add branch',
    step: !canEdit ? 'Step details' : editor?.id ? 'Edit step' : 'Add step',
  }[editor?.kind]

  return (
    <>
      <Link to={`${base}/roadmaps`} className="back-link" style={{ marginBottom: 12 }}>
        <Icon name="arrow-left" size={16} /> All roadmaps
      </Link>
      <PageHeader
        title={data.title}
        description={data.summary}
        actions={
          canEdit && (
            <>
              <button type="button" className="btn btn-secondary" onClick={() => open('details')}>
                <Icon name="edit" size={18} /> Edit details
              </button>
              <button type="button" className="btn btn-primary" onClick={() => open('branch')}>
                <Icon name="plus" size={18} /> Add branch
              </button>
            </>
          )
        }
      />
      <div className="record-meta" style={{ marginBottom: 20 }}>
        <StatusBadge status={data.status} />
        {data.category && <span>{data.category}</span>}
        {data.program_name && <span>Program: {data.program_name}</span>}
        <span>{data.branches.length} branches</span>
        <span>{stepCount} steps</span>
        {!canEdit && <span>Read-only</span>}
      </div>

      <div className="toolbar" role="group" aria-label="Editor view">
        <button
          type="button"
          className={`btn btn-sm ${view === 'manage' ? 'btn-light' : 'btn-secondary'}`}
          aria-pressed={view === 'manage'}
          onClick={() => setView('manage')}
        >
          Branches and steps
        </button>
        <button
          type="button"
          className={`btn btn-sm ${view === 'preview' ? 'btn-light' : 'btn-secondary'}`}
          aria-pressed={view === 'preview'}
          onClick={() => setView('preview')}
        >
          Student preview
        </button>
      </div>

      {view === 'preview' && <RoadmapCanvas heading={data.title} branches={data.branches} useDefaultStep={false} />}

      {view === 'manage' &&
        (data.branches.length === 0 ? (
          <EmptyState
            title="This roadmap has no branches yet"
            action={
              canEdit && (
                <button type="button" className="btn btn-primary" onClick={() => open('branch')}>
                  Add the first branch
                </button>
              )
            }
          >
            Each branch is a career path or specialisation shown as its own coloured column, for example Software
            Development or Data Science.
          </EmptyState>
        ) : (
          <ol className="branch-list">
            {data.branches.map((branch, branchIndex) => (
              <li key={branch.id} className="panel branch-card" style={{ borderLeftColor: branch.color }}>
                <div className="panel-head">
                  <div>
                    <h2 className="panel-title branch-card-title">
                      <span className="branch-swatch" style={{ background: branch.color }} aria-hidden="true" />
                      {branch.name}
                    </h2>
                    <div className="record-meta">
                      <span>Branch {branchIndex + 1}</span>
                      <span>{branch.nodes.length} steps</span>
                      <span>{branch.color}</span>
                    </div>
                  </div>
                  {canEdit && (
                    <div className="record-actions">
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        disabled={moving || branchIndex === 0}
                        onClick={() => reorder(`/api/admin/roadmaps/${data.id}/branches/order`, data.branches, branchIndex, -1)}
                      >
                        <Icon name="arrow-left" size={16} label={`Move ${branch.name} left`} />
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        disabled={moving || branchIndex === data.branches.length - 1}
                        onClick={() => reorder(`/api/admin/roadmaps/${data.id}/branches/order`, data.branches, branchIndex, 1)}
                      >
                        <Icon name="arrow-right" size={16} label={`Move ${branch.name} right`} />
                      </button>
                      <button type="button" className="btn btn-secondary btn-sm" onClick={() => open('branch', branch)}>
                        <Icon name="edit" size={16} /> Edit
                      </button>
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => remove('branch', branch)}>
                        <Icon name="trash" size={16} label={`Delete branch ${branch.name}`} />
                      </button>
                    </div>
                  )}
                </div>
                {branch.description && <RichText text={branch.description} className="field-hint" />}

                {branch.nodes.length === 0 ? (
                  <p className="field-hint" style={{ margin: '12px 0' }}>
                    No steps yet.
                  </p>
                ) : (
                  <ol className="record-list" style={{ marginTop: 12 }}>
                    {branch.nodes.map((node, nodeIndex) => (
                      <li key={node.id} className="record-row">
                        <div className="record-main">
                          <span className="record-title">
                            {nodeIndex + 1}. {node.title}
                          </span>
                          <div className="record-meta">
                            {node.is_default && <span className="badge badge-orange">Opens first</span>}
                            <span>
                              {node.sections.length} {node.sections.length === 1 ? 'section' : 'sections'}
                            </span>
                            {node.sections.length > 0 && <span>{node.sections.map((section) => section.section_title).join(', ')}</span>}
                          </div>
                        </div>
                        <div className="record-actions">
                          {canEdit ? (
                            <>
                              <button
                                type="button"
                                className="btn btn-ghost btn-sm"
                                disabled={moving || nodeIndex === 0}
                                onClick={() => reorder(`/api/admin/roadmap-branches/${branch.id}/nodes/order`, branch.nodes, nodeIndex, -1)}
                              >
                                <Icon name="chevron-up" size={16} label={`Move ${node.title} up`} />
                              </button>
                              <button
                                type="button"
                                className="btn btn-ghost btn-sm"
                                disabled={moving || nodeIndex === branch.nodes.length - 1}
                                onClick={() => reorder(`/api/admin/roadmap-branches/${branch.id}/nodes/order`, branch.nodes, nodeIndex, 1)}
                              >
                                <Icon name="chevron-down" size={16} label={`Move ${node.title} down`} />
                              </button>
                              <button type="button" className="btn btn-secondary btn-sm" onClick={() => open('step', node, branch.id)}>
                                <Icon name="edit" size={16} /> Edit
                              </button>
                              <button type="button" className="btn btn-danger btn-sm" onClick={() => remove('step', node)}>
                                <Icon name="trash" size={16} label={`Delete step ${node.title}`} />
                              </button>
                            </>
                          ) : (
                            <button type="button" className="btn btn-secondary btn-sm" onClick={() => open('step', node, branch.id)}>
                              View
                            </button>
                          )}
                        </div>
                      </li>
                    ))}
                  </ol>
                )}
                {canEdit && (
                  <button type="button" className="btn btn-secondary btn-sm" style={{ marginTop: 12 }} onClick={() => open('step', null, branch.id)}>
                    <Icon name="plus" size={16} /> Add step to {branch.name}
                  </button>
                )}
              </li>
            ))}
          </ol>
        ))}

      <EditorDialog
        open={Boolean(editor)}
        title={dialogTitle}
        onClose={() => setEditor(null)}
        onSubmit={save}
        saving={saving}
        error={error}
        readOnly={!canEdit}
      >
        {editor?.kind === 'details' && (
          <RoadmapFields form={editor.form} setForm={(form) => setEditor({ ...editor, form })} programs={programs} />
        )}
        {editor?.kind === 'branch' && (
          <BranchFields form={editor.form} setForm={(form) => setEditor({ ...editor, form })} colors={colors} />
        )}
        {editor?.kind === 'step' && (
          <StepFields form={editor.form} setForm={(form) => setEditor({ ...editor, form })} types={sectionTypes} />
        )}
      </EditorDialog>
      {confirmDialog}
    </>
  )
}
