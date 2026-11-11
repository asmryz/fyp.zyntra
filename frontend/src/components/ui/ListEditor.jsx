import { useId } from 'react'
import Icon from './Icon'
import { LIMITS } from '../../utils/limits'

/**
 * Edit an ordered list of short text items, e.g. eligibility criteria.
 * `value` is an array of strings; `onChange` receives the new array.
 */
export default function ListEditor({ label, value, onChange, placeholder = '', addLabel = 'Add item', hint }) {
  const groupId = useId()
  const items = value || []

  const update = (index, text) => onChange(items.map((item, i) => (i === index ? text : item)))
  const remove = (index) => onChange(items.filter((_, i) => i !== index))
  const move = (index, direction) => {
    const target = index + direction
    if (target < 0 || target >= items.length) return
    const copy = [...items]
    ;[copy[index], copy[target]] = [copy[target], copy[index]]
    onChange(copy)
  }

  return (
    <fieldset className="list-editor" aria-describedby={hint ? `${groupId}-hint` : undefined}>
      <legend className="field-label">{label}</legend>
      {hint && (
        <span className="field-hint" id={`${groupId}-hint`}>
          {hint}
        </span>
      )}
      {items.length === 0 && <p className="list-editor-empty">No items yet.</p>}
      <ol className="list-editor-items">
        {items.map((item, index) => (
          <li key={index} className="list-editor-row">
            <span className="list-editor-number" aria-hidden="true">
              {index + 1}
            </span>
            <input
              className="input"
              value={item}
              maxLength={LIMITS.listItem}
              placeholder={placeholder}
              aria-label={`${label} item ${index + 1}`}
              onChange={(event) => update(index, event.target.value)}
            />
            <div className="list-editor-actions">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => move(index, -1)} disabled={index === 0}>
                <Icon name="chevron-up" size={16} label={`Move item ${index + 1} up`} />
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => move(index, 1)}
                disabled={index === items.length - 1}
              >
                <Icon name="chevron-down" size={16} label={`Move item ${index + 1} down`} />
              </button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => remove(index)}>
                <Icon name="trash" size={16} label={`Remove item ${index + 1}`} />
              </button>
            </div>
          </li>
        ))}
      </ol>
      <button type="button" className="btn btn-secondary btn-sm" onClick={() => onChange([...items, ''])}>
        <Icon name="plus" size={16} /> {addLabel}
      </button>
    </fieldset>
  )
}
