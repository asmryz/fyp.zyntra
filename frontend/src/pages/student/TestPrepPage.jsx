import { Link } from 'react-router-dom'
import { PageHeader } from '../../components/layout/DashboardLayout'
import { Alert, EmptyState, SkeletonList } from '../../components/ui/Feedback'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'

export default function TestPrepPage() {
  usePageTitle('Test preparation')
  const subjects = useApi('/api/content/test-prep/subjects')

  return (
    <>
      <PageHeader
        title="Admission test preparation"
        description="Choose a subject to study its topics, explanations, learning resources and past papers."
      />

      {subjects.loading && <SkeletonList rows={3} height={80} />}
      {subjects.error && <Alert type="error">{subjects.error.message}</Alert>}
      {subjects.data?.length === 0 && (
        <EmptyState title="No subjects published yet">
          Test preparation material will appear here once the ZYNTRA team publishes it.
        </EmptyState>
      )}
      {subjects.data?.length > 0 && (
        <ul className="record-list">
          {subjects.data.map((subject) => (
            <li key={subject.id} className="record-row">
              <div className="record-main">
                <Link to={`/student/test-prep/subjects/${subject.id}`} className="record-title">
                  {subject.name}
                </Link>
                {subject.description && <p style={{ marginTop: 4, fontSize: '0.92rem' }}>{subject.description}</p>}
                <div className="record-meta">
                  <span>{subject.topic_count} topics</span>
                </div>
              </div>
              <div className="record-actions">
                <Link to={`/student/test-prep/subjects/${subject.id}`} className="btn btn-secondary btn-sm">
                  Study
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
