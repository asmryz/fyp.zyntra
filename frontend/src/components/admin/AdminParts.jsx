/** Small building blocks shared by the admin and staff content pages. */
import { useId } from 'react'
import { useModuleAccess } from '../../hooks/useModuleAccess'
import Dialog from '../ui/Dialog'
import { Alert } from '../ui/Feedback'
import FormField from '../ui/FormField'
import Icon from '../ui/Icon'

/** Shows the page only if the user has access to the module. */
export function ModuleGuard({ module, children }) {
  const { canView } = useModuleAccess(module)
  if (!canView) {
    return (
      <Alert type="error">
        You do not have access to this module. Ask the root administrator if you need it.
      </Alert>
    )
  }
  return children
}

/** Explains what the current permission level allows. */
export function AccessNote({ module }) {
  const { level } = useModuleAccess(module)
  if (level === 'read') {
    return (
      <p className="read-only-note">
        <Icon name="shield" size={16} /> Read-only access: you can view content but not change it.
      </p>
    )
  }
  if (level === 'write') {
    return (
      <p className="read-only-note">
        <Icon name="shield" size={16} /> Write access: you can create content and edit the records you created.
      </p>
    )
  }
  return null
}

/**
 * Dialog that wraps a create/edit form. In read-only mode every input is
 * disabled (via <fieldset disabled>) and the Save button is hidden.
 */
export function EditorDialog({ open, title, onClose, onSubmit, saving, error, readOnly = false, children }) {
  const formId = useId()
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={title}
      wide
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            {readOnly ? 'Close' : 'Cancel'}
          </button>
          {!readOnly && (
            <button type="submit" form={formId} className="btn btn-primary" disabled={saving}>
              {saving && <span className="spinner" aria-hidden="true" />}
              {saving ? 'Saving...' : 'Save'}
            </button>
          )}
        </>
      }
    >
      <form
        id={formId}
        onSubmit={(event) => {
          event.preventDefault()
          onSubmit()
        }}
        noValidate
      >
        {error && (
          <div style={{ marginBottom: 16 }}>
            <Alert type="error">{error}</Alert>
          </div>
        )}
        <fieldset disabled={readOnly} className="form-stack" style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>
          {children}
        </fieldset>
      </form>
    </Dialog>
  )
}

export function StatusField({ value, onChange }) {
  return (
    <FormField
      label="Publication status"
      as="select"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      hint="Students only see published content."
    >
      <option value="draft">Draft (hidden from students)</option>
      <option value="published">Published</option>
    </FormField>
  )
}

/** Edit the ordered application steps of a scholarship: [{ title, description }]. */
export function StepsEditor({ value, onChange }) {
  const steps = value || []
  const update = (index, field, text) =>
    onChange(steps.map((step, i) => (i === index ? { ...step, [field]: text } : step)))
  const remove = (index) => onChange(steps.filter((_, i) => i !== index))
  const move = (index, direction) => {
    const target = index + direction
    if (target < 0 || target >= steps.length) return
    const copy = [...steps]
    ;[copy[index], copy[target]] = [copy[target], copy[index]]
    onChange(copy)
  }

  return (
    <fieldset className="list-editor">
      <legend className="field-label">Application procedure (steps)</legend>
      {steps.length === 0 && <p className="list-editor-empty">No steps yet.</p>}
      {steps.map((step, index) => (
        <div key={index} className="panel" style={{ padding: 14, background: 'var(--input-bg)' }}>
          <div className="panel-head" style={{ marginBottom: 10 }}>
            <strong>Step {index + 1}</strong>
            <div className="list-editor-actions">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => move(index, -1)} disabled={index === 0}>
                <Icon name="chevron-up" size={16} label={`Move step ${index + 1} up`} />
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => move(index, 1)}
                disabled={index === steps.length - 1}
              >
                <Icon name="chevron-down" size={16} label={`Move step ${index + 1} down`} />
              </button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => remove(index)}>
                <Icon name="trash" size={16} label={`Remove step ${index + 1}`} />
              </button>
            </div>
          </div>
          <div className="form-stack" style={{ gap: 10 }}>
            <FormField label="Step title" value={step.title} onChange={(event) => update(index, 'title', event.target.value)} />
            <FormField
              label="Description"
              as="textarea"
              rows={2}
              value={step.description}
              onChange={(event) => update(index, 'description', event.target.value)}
            />
          </div>
        </div>
      ))}
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        onClick={() => onChange([...steps, { title: '', description: '' }])}
      >
        <Icon name="plus" size={16} /> Add step
      </button>
    </fieldset>
  )
}

/** Edit a list of external links: [{ label, url }]. */
export function LinksEditor({ value, onChange, label = 'Links (optional)' }) {
  const links = value || []
  const update = (index, field, text) =>
    onChange(links.map((link, i) => (i === index ? { ...link, [field]: text } : link)))

  return (
    <fieldset className="list-editor">
      <legend className="field-label">{label}</legend>
      {links.map((link, index) => (
        <div key={index} className="list-editor-row" style={{ gridTemplateColumns: '1fr 1.4fr auto' }}>
          <input
            className="input"
            placeholder="Label"
            aria-label={`Link ${index + 1} label`}
            value={link.label}
            onChange={(event) => update(index, 'label', event.target.value)}
          />
          <input
            className="input"
            placeholder="https://..."
            aria-label={`Link ${index + 1} address`}
            value={link.url}
            onChange={(event) => update(index, 'url', event.target.value)}
          />
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onChange(links.filter((_, i) => i !== index))}>
            <Icon name="trash" size={16} label={`Remove link ${index + 1}`} />
          </button>
        </div>
      ))}
      <button type="button" className="btn btn-secondary btn-sm" onClick={() => onChange([...links, { label: '', url: '' }])}>
        <Icon name="plus" size={16} /> Add link
      </button>
    </fieldset>
  )
}

/**
 * Choose an access level per module.
 * value: { module: 'read' | 'write' | 'read_write' | null }
 */
export function PermissionMatrix({ modules, levels, value, onChange, idPrefix = 'perm' }) {
  const columns = [[null, 'No access'], ...Object.entries(levels)]
  return (
    <div className="table-wrap" style={{ border: 'none' }}>
      <table className="permission-matrix">
        <thead>
          <tr>
            <th scope="col">Module</th>
            {columns.map(([, label]) => (
              <th key={label} scope="col">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(modules).map(([module, moduleLabel]) => (
            <tr key={module}>
              <th scope="row" style={{ fontWeight: 600 }}>
                {moduleLabel}
              </th>
              {columns.map(([level, label]) => (
                <td key={label}>
                  <input
                    type="radio"
                    name={`${idPrefix}-${module}`}
                    aria-label={`${moduleLabel}: ${label}`}
                    checked={(value[module] || null) === level}
                    onChange={() => onChange({ ...value, [module]: level })}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function PermissionTags({ permissions, modules, levels }) {
  const entries = Object.entries(permissions || {})
  if (entries.length === 0) return <span className="field-hint">No module access</span>
  return (
    <div className="permission-tags">
      {entries.map(([module, level]) => (
        <span key={module} className={`badge ${level === 'read' ? '' : 'badge-blue'}`}>
          {modules?.[module] || module}: {levels?.[level] || level}
        </span>
      ))}
    </div>
  )
}
