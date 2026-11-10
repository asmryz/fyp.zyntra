import { Link, useParams } from 'react-router-dom'
import { PageHeader } from '../../components/layout/DashboardLayout'
import ResourceList from '../../components/ResourceList'
import { Alert, PageLoader, RichText } from '../../components/ui/Feedback'
import Icon from '../../components/ui/Icon'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'

export default function TopicPage() {
  const { topicId } = useParams()
  const { data: topic, error, loading } = useApi(`/api/content/test-prep/topics/${topicId}`)
  usePageTitle(topic?.title || 'Topic')

  if (loading) return <PageLoader />
  if (error) return <Alert type="error">{error.message}</Alert>

  return (
    <>
      <Link to={`/student/test-prep/subjects/${topic.subject_id}`} className="back-link" style={{ marginBottom: 12 }}>
        <Icon name="arrow-left" size={16} /> {topic.subject_name}
      </Link>
      <PageHeader title={topic.title} />

      <div className="two-column two-column-wide">
        <section className="panel" aria-labelledby="explanation-title">
          <h2 id="explanation-title" className="panel-title">
            Topic explanation
          </h2>
          {topic.explanation ? <RichText text={topic.explanation} /> : <p>An explanation for this topic will be added soon.</p>}
        </section>
        <section className="panel" aria-labelledby="topic-resources">
          <h2 id="topic-resources" className="panel-title">
            Videos and resources
          </h2>
          <ResourceList resources={topic.resources} />
        </section>
      </div>
    </>
  )
}
