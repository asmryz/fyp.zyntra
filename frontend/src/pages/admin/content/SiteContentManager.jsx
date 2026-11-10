import { useState } from 'react'
import { AccessNote, EditorDialog, ModuleGuard, StatusField } from '../../../components/admin/AdminParts'
import { PageHeader } from '../../../components/layout/DashboardLayout'
import { Alert, EmptyState, SkeletonList, StatusBadge } from '../../../components/ui/Feedback'
import FormField from '../../../components/ui/FormField'
import Icon from '../../../components/ui/Icon'
import { useToast } from '../../../context/ToastContext'
import { useApi } from '../../../hooks/useApi'
import { usePageTitle } from '../../../hooks/usePageTitle'
import { api } from '../../../services/api'
import { formatDate } from '../../../utils/format'

/**
 * Website content blocks can only be viewed and edited. Each block belongs to
 * a fixed website section (its key); blocks are not added or deleted here.
 */
export default function SiteContentManager() {
  usePageTitle('Website content')
  return (
    <ModuleGuard module="site_content">
      <SiteContentManagerContent />
    </ModuleGuard>
  )
}

function SiteContentManagerContent() {
  const toast = useToast()
  const blocks = useApi('/api/admin/site-content')
  const [editor, setEditor] = useState(null) // { record, form, readOnly }
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const open = (record) => {
    setError(null)
    setEditor({
      record,
      readOnly: !record.can_edit,
      form: { title: record.title, body: record.body, status: record.status },
    })
  }

  async function save() {
    setSaving(true)
    setError(null)
    try {
      await api.put(`/api/admin/site-content/${editor.record.id}`, editor.form)
      toast.success('Website content saved.')
      setEditor(null)
      blocks.reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const form = editor?.form
  const set = (field) => (event) => setEditor({ ...editor, form: { ...form, [field]: event.target.value } })

  return (
    <>
      <PageHeader
        title="General website content"
        description="Editable text for the landing page, the footer contact details and general admission guidance."
      />
      <AccessNote module="site_content" />

      <div style={{ marginTop: 16 }}>
        {blocks.loading && <SkeletonList />}
        {blocks.error && <Alert type="error">{blocks.error.message}</Alert>}
        {blocks.data?.length === 0 && <EmptyState title="No website content available">There is no website content for you to view.</EmptyState>}
        {blocks.data?.length > 0 && (
          <ul className="record-list">
            {blocks.data.map((block) => (
              <li key={block.id} className="record-row">
                <div className="record-main">
                  <span className="record-title">{block.title}</span>
                  <div className="record-meta">
                    <StatusBadge status={block.status} />
                    <span>{block.used_on || `Custom key: ${block.key}`}</span>
                    <span>Updated {formatDate(block.updated_at)}</span>
                  </div>
                </div>
                <div className="record-actions">
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => open(block)}>
                    <Icon name={block.can_edit ? 'edit' : 'file'} size={16} /> {block.can_edit ? 'Edit' : 'View'}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <EditorDialog
        open={Boolean(editor)}
        title={editor?.readOnly ? editor.record.title : 'Edit content block'}
        onClose={() => setEditor(null)}
        onSubmit={save}
        saving={saving}
        error={error}
        readOnly={editor?.readOnly}
      >
        {form && (
          <>
            {/* The section is fixed, so it is shown as text rather than a control */}
            <div className="field">
              <span className="field-label">Website section</span>
              <p className="site-section-name">{editor.record.used_on || `Custom key: ${editor.record.key}`}</p>
            </div>
            <FormField label="Title" value={form.title} onChange={set('title')} />
            <FormField
              label="Text"
              as="textarea"
              rows={8}
              value={form.body}
              onChange={set('body')}
              hint="Leave a blank line between paragraphs. Do not add unofficial statistics or claims."
            />
            <StatusField value={form.status} onChange={(status) => setEditor({ ...editor, form: { ...form, status } })} />
          </>
        )}
      </EditorDialog>
    </>
  )
}
