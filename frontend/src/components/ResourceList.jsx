import Icon from './ui/Icon'

// Resource types match backend RESOURCE_TYPES (and the ck_learning_resources_type constraint)
const TYPE_ICONS = { video: 'play', article: 'file', pdf: 'clipboard', link: 'link' }
const TYPE_LABELS = { video: 'Video', article: 'Notes', pdf: 'PDF / past paper', link: 'Learning platform' }

/** Learning resources (videos, links, past papers). External links open in a new tab. */
export default function ResourceList({ resources }) {
  if (!resources?.length) return <p className="field-hint">No learning resources have been added yet.</p>
  return (
    <ul className="resource-list">
      {resources.map((resource) => (
        <li key={resource.id} className="resource-item">
          <Icon name={TYPE_ICONS[resource.resource_type] || 'link'} size={20} />
          <div>
            <a href={resource.url} target="_blank" rel="noopener noreferrer">
              {resource.title}
              <span className="sr-only"> (opens in a new tab)</span>
            </a>
            <span className="cell-secondary">
              {TYPE_LABELS[resource.resource_type] || 'Resource'}
              {resource.description ? ` · ${resource.description}` : ''}
            </span>
          </div>
        </li>
      ))}
    </ul>
  )
}
