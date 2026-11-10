import { Link } from 'react-router-dom'
import { PermissionTags } from '../../components/admin/AdminParts'
import { PageHeader } from '../../components/layout/DashboardLayout'
import { Alert, EmptyState, SkeletonList } from '../../components/ui/Feedback'
import { useAuth } from '../../context/AuthContext'
import { useApi } from '../../hooks/useApi'
import { useFormOptions } from '../../hooks/useFormOptions'
import { usePageTitle } from '../../hooks/usePageTitle'
import { formatDate, formatDateTime } from '../../utils/format'
import { ROLE_LABELS } from '../../utils/roles'

const STAT_LABELS = {
  students: 'Registered students',
  verified_students: 'Verified students',
  staff: 'Staff members',
  administrators: 'Administrators',
  pending_invitations: 'Pending invitations',
  programs: 'Programs',
  published_programs: 'Published programs',
  scholarships: 'Scholarships',
  published_scholarships: 'Published scholarships',
  roadmaps: 'Roadmaps',
  roadmap_nodes: 'Roadmap steps',
  test_subjects: 'Test subjects',
  test_topics: 'Test topics',
  site_content_blocks: 'Website content blocks',
}

const ROOT_STAT_ORDER = [
  'students', 'staff', 'administrators', 'programs', 'published_scholarships', 'roadmap_nodes',
  'verified_students', 'pending_invitations', 'roadmaps', 'test_subjects',
]

function StatGrid({ stats, order }) {
  const keys = (order || Object.keys(stats)).filter((key) => key in stats)
  return (
    <div className="stats">
      {keys.map((key, index) => (
        <div key={key} className={`stat ${index === 0 ? 'stat-accent' : ''}`}>
          <span className="stat-value">{stats[key]}</span>
          <span className="stat-label">{STAT_LABELS[key] || key}</span>
        </div>
      ))}
    </div>
  )
}

function ActivityList({ logs, emptyText }) {
  if (!logs?.length) return <p className="field-hint">{emptyText}</p>
  return (
    <ul className="activity-list">
      {logs.map((log) => (
        <li key={log.id}>
          <span>{log.summary}</span>
          <span className="activity-meta">
            {log.actor_name || 'System'} · {formatDateTime(log.created_at)}
          </span>
        </li>
      ))}
    </ul>
  )
}

export function RootOverviewPage() {
  usePageTitle('Root admin overview')
  const { data, error, loading } = useApi('/api/admin/overview')

  return (
    <>
      <PageHeader
        title="Platform overview"
        description="Live counts from the ZYNTRA database and the latest account and content activity."
      />
      {loading && <SkeletonList rows={2} height={90} />}
      {error && <Alert type="error">{error.message}</Alert>}
      {data && (
        <>
          <StatGrid stats={data.stats} order={ROOT_STAT_ORDER} />
          <div className="two-column">
            <section className="panel" aria-labelledby="recent-accounts">
              <div className="panel-head">
                <h2 id="recent-accounts" className="panel-title">
                  Newest accounts
                </h2>
                <Link to="/root/users" className="btn btn-ghost btn-sm">
                  All users
                </Link>
              </div>
              {data.recent_accounts.length === 0 ? (
                <p className="field-hint">No accounts yet.</p>
              ) : (
                <ul className="activity-list">
                  {data.recent_accounts.map((account) => (
                    <li key={account.id}>
                      <Link to={`/root/users/${account.id}`} className="cell-primary">
                        {account.full_name}
                      </Link>
                      <span className="activity-meta">
                        {ROLE_LABELS[account.role]} · {account.email} · joined {formatDate(account.created_at)}
                        {!account.is_email_verified && ' · unverified'}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section className="panel" aria-labelledby="recent-content">
              <div className="panel-head">
                <h2 id="recent-content" className="panel-title">
                  Recent content updates
                </h2>
                <Link to="/root/activity" className="btn btn-ghost btn-sm">
                  Activity log
                </Link>
              </div>
              <ActivityList logs={data.recent_content} emptyText="No content changes yet." />
            </section>
          </div>
          <section className="panel" style={{ marginTop: 20 }} aria-labelledby="recent-account-activity">
            <h2 id="recent-account-activity" className="panel-title">
              Recent account activity
            </h2>
            <ActivityList logs={data.recent_account_activity} emptyText="No account activity yet." />
          </section>
        </>
      )}
    </>
  )
}

const MODULE_LINKS = {
  programs: '/staff/programs',
  scholarships: '/staff/scholarships',
  roadmaps: '/staff/roadmaps',
  test_prep: '/staff/test-prep',
  site_content: '/staff/site-content',
}

export function StaffOverviewPage() {
  usePageTitle('Staff overview')
  const { user } = useAuth()
  const options = useFormOptions()
  const { data, error, loading } = useApi('/api/admin/overview')

  return (
    <>
      <PageHeader
        title={`Hello, ${user?.full_name?.split(' ')[0]}`}
        description="Manage the ZYNTRA content you have been given access to."
      />
      {loading && <SkeletonList rows={2} height={90} />}
      {error && <Alert type="error">{error.message}</Alert>}
      {data && (
        <>
          {Object.keys(data.stats).length > 0 && <StatGrid stats={data.stats} />}
          <div className="two-column">
            <section className="panel" aria-labelledby="my-access">
              <h2 id="my-access" className="panel-title">
                Your access
              </h2>
              {Object.keys(data.permissions).length === 0 ? (
                <EmptyState title="No modules assigned">Ask the root administrator to give you access to a module.</EmptyState>
              ) : (
                <>
                  <PermissionTags permissions={data.permissions} modules={options?.content_modules} levels={options?.access_levels} />
                  <ul className="activity-list" style={{ marginTop: 12 }}>
                    {Object.keys(data.permissions).map((module) => (
                      <li key={module}>
                        <Link to={MODULE_LINKS[module]} className="cell-primary">
                          Open {options?.content_modules?.[module] || module}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </section>
            <section className="panel" aria-labelledby="my-changes">
              <h2 id="my-changes" className="panel-title">
                Your recent changes
              </h2>
              <ActivityList logs={data.recent_content} emptyText="You have not changed any content yet." />
            </section>
          </div>
        </>
      )}
    </>
  )
}
