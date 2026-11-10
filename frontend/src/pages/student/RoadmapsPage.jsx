import { Link, useParams } from 'react-router-dom'
import { PageHeader } from '../../components/layout/DashboardLayout'
import RoadmapCanvas from '../../components/roadmap/RoadmapCanvas'
import { Alert, EmptyState, PageLoader, RichText, SkeletonList } from '../../components/ui/Feedback'
import Icon from '../../components/ui/Icon'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'

export function RoadmapsPage() {
  usePageTitle('Roadmaps')
  const { data: roadmaps, error, loading } = useApi('/api/content/roadmaps')

  return (
    <>
      <PageHeader
        title="Roadmaps"
        description="Explore the career paths each program can lead to, and the skills and tools for every step."
      />
      {loading && <SkeletonList rows={3} height={84} />}
      {error && <Alert type="error">{error.message}</Alert>}
      {roadmaps?.length === 0 && (
        <EmptyState title="No roadmaps published yet">Roadmaps will appear here once the ZYNTRA team publishes them.</EmptyState>
      )}
      {roadmaps?.length > 0 && (
        // One card per published roadmap, headed by its program; the whole card opens the roadmap
        <ul className="program-cards">
          {roadmaps.map((roadmap) => (
            <li key={roadmap.id}>
              <Link to={`/student/roadmaps/${roadmap.id}`} className="program-card">
                <span className="program-card-top">
                  <span className="program-card-icon" aria-hidden="true">
                    <Icon name="route" size={24} />
                  </span>
                  {roadmap.category && <span className="program-card-category">{roadmap.category}</span>}
                </span>
                <span className="program-card-body">
                  <span className="program-card-title">{roadmap.program_name || roadmap.title}</span>
                  {roadmap.program_name && <span className="program-card-subtitle">{roadmap.title}</span>}
                  {roadmap.summary && <span className="program-card-summary">{roadmap.summary}</span>}
                </span>
                <span className="program-card-meta">
                  <span>
                    {roadmap.branch_count} {roadmap.branch_count === 1 ? 'branch' : 'branches'}
                  </span>
                  <span>{roadmap.node_count} steps</span>
                </span>
                <span className="program-card-action">
                  Open roadmap <Icon name="arrow-right" size={18} />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}

export function RoadmapDetailPage() {
  const { roadmapId } = useParams()
  const { data: roadmap, error, loading } = useApi(`/api/content/roadmaps/${roadmapId}`)
  usePageTitle(roadmap?.title || 'Roadmap')

  if (loading) return <PageLoader />
  if (error) return <Alert type="error">{error.message}</Alert>

  return (
    <>
      <Link to="/student/roadmaps" className="back-link" style={{ marginBottom: 12 }}>
        <Icon name="arrow-left" size={16} /> All roadmaps
      </Link>
      <PageHeader
        title={roadmap.title}
        description={roadmap.summary}
      />
      {roadmap.description && (
        <div style={{ marginBottom: 24, maxWidth: '70ch' }}>
          <RichText text={roadmap.description} />
        </div>
      )}
      <RoadmapCanvas heading={roadmap.title} branches={roadmap.branches} />
      <p className="field-hint" style={{ marginTop: 14 }}>
        Select any step to see its details. Roadmaps are guidance for planning and may change as programs are updated.
      </p>
    </>
  )
}
