import { Link, useParams } from 'react-router-dom'
import { PageHeader } from '../../components/layout/DashboardLayout'
import ResourceList from '../../components/ResourceList'
import { Alert, EmptyState, PageLoader } from '../../components/ui/Feedback'
import Icon from '../../components/ui/Icon'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'

export default function SubjectPage() {
  const { subjectId } = useParams()
  const { data: subject, error, loading } = useApi(`/api/content/test-prep/subjects/${subjectId}`)
  usePageTitle(subject?.name || 'Subject')

  if (loading) return <PageLoader />
  if (error) return <Alert type="error">{error.message}</Alert>

  return (
    <>
      <Link to="/student/test-prep" className="back-link" style={{ marginBottom: 12 }}>
        <Icon name="arrow-left" size={16} /> All subjects
      </Link>
      <PageHeader
        title={subject.name}
        description={subject.description}
      />

      <div className="two-column two-column-wide">
        <section className="panel" aria-labelledby="topics-title">
          <h2 id="topics-title" className="panel-title">
            Topics
          </h2>
          {subject.topics.length === 0 ? (
            <EmptyState title="No topics yet">Topics for this subject will be added soon.</EmptyState>
          ) : (
            <ul className="topic-list">
              {subject.topics.map((topic) => (
                <li key={topic.id}>
                  <Link to={`/student/test-prep/topics/${topic.id}`} className="topic-link">
                    <span className="topic-title">{topic.title}</span>
                    <Icon name="chevron-right" size={18} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel" aria-labelledby="resources-title">
          <h2 id="resources-title" className="panel-title">
            Learning resources and past papers
          </h2>
          <ResourceList resources={subject.resources} />
        </section>
      </div>
    </>
  )
}
