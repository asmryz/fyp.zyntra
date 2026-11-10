import { useState } from 'react'
import { PageHeader } from '../../components/layout/DashboardLayout'
import { Alert, EmptyState, SkeletonList } from '../../components/ui/Feedback'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'
import { formatDateTime } from '../../utils/format'

export default function ActivityPage() {
  usePageTitle('Activity log')
  const [category, setCategory] = useState('')
  const { data: logs, error, loading } = useApi(`/api/admin/audit-logs?limit=200&category=${category}`)

  return (
    <>
      <PageHeader
        title="Activity log"
        description="Important account and content changes, newest first."
      />
      <div className="toolbar" role="group" aria-label="Filter activity">
        {[
          ['', 'All activity'],
          ['account', 'Accounts'],
          ['content', 'Content'],
        ].map(([value, label]) => (
          <button
            key={label}
            type="button"
            className={`btn btn-sm ${category === value ? 'btn-light' : 'btn-secondary'}`}
            aria-pressed={category === value}
            onClick={() => setCategory(value)}
          >
            {label}
          </button>
        ))}
      </div>

      {loading && !logs && <SkeletonList rows={6} height={44} />}
      {error && <Alert type="error">{error.message}</Alert>}
      {logs?.length === 0 && <EmptyState title="No activity recorded">Actions will appear here as people use ZYNTRA.</EmptyState>}
      {logs?.length > 0 && (
        <div className="table-wrap" aria-busy={loading}>
          <table className="table">
            <thead>
              <tr>
                <th scope="col">When</th>
                <th scope="col">Who</th>
                <th scope="col">What happened</th>
                <th scope="col">Type</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ whiteSpace: 'nowrap' }}>{formatDateTime(log.created_at)}</td>
                  <td>{log.actor_name || 'System'}</td>
                  <td>{log.summary}</td>
                  <td>
                    <span className={`badge ${log.category === 'content' ? 'badge-blue' : ''}`}>{log.category}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
