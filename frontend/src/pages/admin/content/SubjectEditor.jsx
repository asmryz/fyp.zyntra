import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { DisplayOrderField, EditorDialog, ModuleGuard, StatusField } from '../../../components/admin/AdminParts'
import { PageHeader } from '../../../components/layout/DashboardLayout'
import ResourceList from '../../../components/ResourceList'
import { safeExternalUrl } from '../../../utils/limits'
import { Alert, EmptyState, PageLoader, StatusBadge } from '../../../components/ui/Feedback'
import FormField from '../../../components/ui/FormField'
import Icon from '../../../components/ui/Icon'
import { useToast } from '../../../context/ToastContext'
import { useApi } from '../../../hooks/useApi'
import { useConfirm } from '../../../hooks/useConfirm'
import { useFormOptions } from '../../../hooks/useFormOptions'
import { useConsoleBase } from '../../../hooks/useModuleAccess'
import { usePageTitle } from '../../../hooks/usePageTitle'
import { api } from '../../../services/api'
import { SubjectFields } from './TestPrepManager'
import { displayOrderError } from '../../../utils/validation'

const EMPTY_TOPIC = { title: '', explanation: '', status: 'draft', sort_order: 1 }
const EMPTY_RESOURCE = { title: '', url: '', resource_type: 'video', description: '', topic_id: '', sort_order: 1 }

export default function SubjectEditor() {
  return (
    <ModuleGuard module="test_prep">
      <SubjectEditorContent />
    </ModuleGuard>
  )
}

function SubjectEditorContent() {
  const { subjectId } = useParams()
  const base = useConsoleBase()
  const toast = useToast()
  const options = useFormOptions()
  const [confirm, confirmDialog] = useConfirm()
  const subject = useApi(`/api/admin/test-prep/subjects/${subjectId}`)
  usePageTitle(subject.data?.name || 'Subject')

  // editor = { kind: 'subject' | 'topic' | 'resource', id, form }
  const [editor, setEditor] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  if (subject.loading && !subject.data) return <PageLoader />
  if (subject.error) return <Alert type="error">{subject.error.message}</Alert>

  const data = subject.data
  const canEdit = data.can_edit
  const topicTitle = (topicId) => data.topics.find((topic) => topic.id === topicId)?.title

  const open = (kind, record) => {
    setError(null)
    let form
    if (kind === 'subject') form = { name: data.name, description: data.description || '', status: data.status, sort_order: data.sort_order }
    if (kind === 'topic') form = record ? { title: record.title, explanation: record.explanation || '', status: record.status, sort_order: record.sort_order } : { ...EMPTY_TOPIC }
    if (kind === 'resource')
      form = record
        ? { ...record, description: record.description || '', topic_id: record.topic_id ? String(record.topic_id) : '' }
        : { ...EMPTY_RESOURCE }
    setEditor({ kind, id: record?.id || null, form })
  }

  async function save() {
    setSaving(true)
    setError(null)
    const { kind, id, form } = editor
    if (displayOrderError(form.sort_order)) {
      setError('Please correct the highlighted field.')
      setSaving(false)
      return
    }
    const sortOrder = Number(form.sort_order)
    try {
      if (kind === 'subject') {
        await api.put(`/api/admin/test-prep/subjects/${data.id}`, { ...form, sort_order: sortOrder })
      } else if (kind === 'topic') {
        const body = { ...form, sort_order: sortOrder }
        if (id) await api.put(`/api/admin/test-prep/topics/${id}`, body)
        else await api.post(`/api/admin/test-prep/subjects/${data.id}/topics`, body)
      } else {
        const body = {
          title: form.title,
          url: form.url,
          resource_type: form.resource_type,
          description: form.description || null,
          topic_id: form.topic_id ? Number(form.topic_id) : null,
          sort_order: sortOrder,
        }
        if (id) await api.put(`/api/admin/test-prep/resources/${id}`, body)
        else await api.post(`/api/admin/test-prep/subjects/${data.id}/resources`, body)
      }
      toast.success('Saved.')
      setEditor(null)
      subject.reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function remove(kind, record) {
    const message =
      kind === 'topic'
        ? `"${record.title}" will be deleted. Its resources stay with the subject.`
        : `"${record.title}" will be deleted.`
    if (!(await confirm({ title: `Delete ${kind}?`, message }))) return
    try {
      await api.delete(kind === 'topic' ? `/api/admin/test-prep/topics/${record.id}` : `/api/admin/test-prep/resources/${record.id}`)
      toast.success('Deleted.')
      subject.reload()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const setForm = (form) => setEditor({ ...editor, form })
  const set = (field) => (event) => setForm({ ...editor.form, [field]: event.target.value })

  return (
    <>
      <Link to={`${base}/test-prep`} className="back-link" style={{ marginBottom: 12 }}>
        <Icon name="arrow-left" size={16} /> All subjects
      </Link>
      <PageHeader
        title={data.name}
        description={data.description}
        actions={
          canEdit && (
            <button type="button" className="btn btn-secondary" onClick={() => open('subject')}>
              <Icon name="edit" size={18} /> Edit subject
            </button>
          )
        }
      />
      <div className="record-meta" style={{ marginBottom: 20 }}>
        <StatusBadge status={data.status} />
        <span>{data.topic_count} topics</span>
        {!canEdit && <span>Read-only</span>}
      </div>

      <section className="panel">
        <div className="panel-head">
          <h2 className="panel-title">Topics</h2>
          {canEdit && (
            <button type="button" className="btn btn-primary btn-sm" onClick={() => open('topic')}>
              <Icon name="plus" size={16} /> Add topic
            </button>
          )}
        </div>
        {data.topics.length === 0 ? (
          <EmptyState title="No topics yet">Topics hold explanations and their own learning resources.</EmptyState>
        ) : (
          <ul className="record-list">
            {data.topics.map((topic) => (
              <li key={topic.id} className="record-row">
                <div className="record-main">
                  <span className="record-title">{topic.title}</span>
                  <div className="record-meta">
                    <StatusBadge status={topic.status} />
                    <span>Order {topic.sort_order}</span>
                  </div>
                </div>
                <div className="record-actions">
                  {!canEdit && (
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => open('topic', topic)}>
                      View
                    </button>
                  )}
                  {canEdit && (
                    <>
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => open('topic', topic)}>
                        <Icon name="edit" size={16} label={`Edit ${topic.title}`} />
                      </button>
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => remove('topic', topic)}>
                        <Icon name="trash" size={16} label={`Delete ${topic.title}`} />
                      </button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2 className="panel-title">Learning resources and past papers</h2>
          {canEdit && (
            <button type="button" className="btn btn-primary btn-sm" onClick={() => open('resource')}>
              <Icon name="plus" size={16} /> Add resource
            </button>
          )}
        </div>
        {data.resources.length === 0 ? (
          <EmptyState title="No resources yet">Add educational videos, learning-platform links, notes or past papers.</EmptyState>
        ) : canEdit ? (
          <ul className="record-list">
            {data.resources.map((resource) => (
              <li key={resource.id} className="record-row">
                <div className="record-main">
                  <a href={safeExternalUrl(resource.url) || undefined} target="_blank" rel="noopener noreferrer" className="record-title">
                    {resource.title}
                  </a>
                  <div className="record-meta">
                    <span>{options?.resource_types?.[resource.resource_type] || resource.resource_type}</span>
                    <span>{resource.topic_id ? `Topic: ${topicTitle(resource.topic_id)}` : 'Whole subject'}</span>
                  </div>
                </div>
                <div className="record-actions">
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => open('resource', resource)}>
                    <Icon name="edit" size={16} label={`Edit ${resource.title}`} />
                  </button>
                  <button type="button" className="btn btn-danger btn-sm" onClick={() => remove('resource', resource)}>
                    <Icon name="trash" size={16} label={`Delete ${resource.title}`} />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <ResourceList resources={data.resources} />
        )}
      </section>

      <EditorDialog
        open={Boolean(editor)}
        title={
          editor?.kind === 'subject'
            ? 'Edit subject'
            : `${!canEdit ? 'View' : editor?.id ? 'Edit' : 'Add'} ${editor?.kind === 'topic' ? 'topic' : 'resource'}`
        }
        onClose={() => setEditor(null)}
        onSubmit={save}
        saving={saving}
        error={error}
        readOnly={!canEdit}
      >
        {editor?.kind === 'subject' && <SubjectFields form={editor.form} setForm={setForm} />}
        {editor?.kind === 'topic' && (
          <div className="form-grid">
            <FormField label="Topic title" value={editor.form.title} onChange={set('title')} className="span-2" />
            <FormField
              label="Topic explanation"
              optional
              as="textarea"
              rows={8}
              className="span-2"
              value={editor.form.explanation}
              onChange={set('explanation')}
              hint="Leave a blank line between paragraphs."
            />
            <StatusField value={editor.form.status} onChange={(status) => setForm({ ...editor.form, status })} />
            <DisplayOrderField value={editor.form.sort_order} onChange={set('sort_order')} />
          </div>
        )}
        {editor?.kind === 'resource' && (
          <div className="form-grid">
            <FormField label="Title" value={editor.form.title} onChange={set('title')} className="span-2" />
            <FormField
              label="Link (URL)"
              type="url"
              value={editor.form.url}
              onChange={set('url')}
              className="span-2"
              placeholder="https://"
            />
            <FormField label="Resource type" as="select" value={editor.form.resource_type} onChange={set('resource_type')}>
              {Object.entries(options?.resource_types || {}).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </FormField>
            <FormField label="Topic" as="select" value={editor.form.topic_id} onChange={set('topic_id')}>
              <option value="">Whole subject</option>
              {data.topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.title}
                </option>
              ))}
            </FormField>
            <FormField label="Short description" optional maxLength={300} value={editor.form.description} onChange={set('description')} className="span-2" />
            <DisplayOrderField value={editor.form.sort_order} onChange={set('sort_order')} />
          </div>
        )}
      </EditorDialog>
      {confirmDialog}
    </>
  )
}
