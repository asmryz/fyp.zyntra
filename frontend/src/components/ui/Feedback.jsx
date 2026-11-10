/** Small presentational components for loading, empty and message states. */
import { toParagraphs } from '../../utils/format'
import Icon from './Icon'

const ALERT_ICONS = { error: 'alert', success: 'check-circle', info: 'info', warning: 'alert' }

export function Alert({ type = 'info', children }) {
  if (!children) return null
  return (
    <div className={`alert alert-${type}`} role={type === 'error' ? 'alert' : 'status'}>
      <Icon name={ALERT_ICONS[type]} size={18} />
      <div>{children}</div>
    </div>
  )
}

export function Spinner({ label = 'Loading' }) {
  return <span className="spinner" role="status" aria-label={label} />
}

export function PageLoader({ label = 'Loading...' }) {
  return (
    <div className="page-loader">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <span className="spinner" aria-hidden="true" />
        <span>{label}</span>
      </div>
    </div>
  )
}

export function Skeleton({ height = 16, width = '100%', style }) {
  return <span className="skeleton" aria-hidden="true" style={{ height, width, ...style }} />
}

export function SkeletonList({ rows = 4, height = 56 }) {
  return (
    <div style={{ display: 'grid', gap: 10 }} aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton key={index} height={height} />
      ))}
    </div>
  )
}

export function EmptyState({ title, children, action }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  )
}

export function StatusBadge({ status }) {
  const published = status === 'published'
  return <span className={`badge ${published ? 'badge-published' : 'badge-draft'}`}>{published ? 'Published' : 'Draft'}</span>
}

/** Plain text from the database shown as paragraphs (never as raw HTML). */
export function RichText({ text, className = '' }) {
  if (!text) return null
  return (
    <div className={`rich-text ${className}`}>
      {toParagraphs(text).map((paragraph, index) => (
        <p key={index}>{paragraph}</p>
      ))}
    </div>
  )
}
