import { Link, useParams } from 'react-router-dom'
import { Alert, PageLoader, RichText } from '../../components/ui/Feedback'
import Icon from '../../components/ui/Icon'
import { useAuth } from '../../context/AuthContext'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'
import { roadmapPathForRole } from '../../utils/roles'

export default function ProgramDetailPage() {
  const { slug } = useParams()
  const { user } = useAuth()
  const { data: program, error, loading } = useApi(`/api/public/programs/${slug}`)
  usePageTitle(program?.name || 'Program')

  if (loading) return <PageLoader />

  if (error) {
    return (
      <div className="container page-body">
        <Alert type="error">{error.message}</Alert>
        <p style={{ marginTop: 16 }}>
          <Link to="/programs" className="text-link">
            Back to all programs
          </Link>
        </p>
      </div>
    )
  }

  const facts = [
    ['Department', program.department],
    ['Degree level', program.degree_level],
    ['Duration', program.duration],
  ].filter(([, value]) => value)

  const hasCriteria = program.min_percentage !== null || program.accepted_qualifications.length > 0

  return (
    <div className="page-enter">
      <section className="page-hero">
        <div className="container">
          <Link to="/programs" className="back-link">
            <Icon name="arrow-left" size={16} /> All programs
          </Link>
          <h1>{program.name}</h1>
          {program.summary && <p>{program.summary}</p>}
        </div>
      </section>

      <section className="page-body">
        <div className="container program-detail">
          <div>
            {facts.length > 0 && (
              <dl className="program-facts" style={{ marginBottom: 36 }}>
                {facts.map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            )}
            {program.description && (
              <div className="content-section">
                <h2>About this program</h2>
                <RichText text={program.description} />
              </div>
            )}
            {program.admission_requirements && (
              <div className="content-section">
                <h2>Admission requirements</h2>
                <RichText text={program.admission_requirements} />
              </div>
            )}
            {/* Every program ends with its own roadmap link (logged-out visitors are sent to login first) */}
            <div className="content-section">
              <h2>Roadmap for this program</h2>
              {program.roadmaps.length > 0 ? (
                <ul className="footer-links">
                  {program.roadmaps.map((roadmap) => (
                    <li key={roadmap.id}>
                      <span>{roadmap.title}</span>{' '}
                      <Link to={roadmapPathForRole(user?.role, roadmap.id)} className="text-link">
                        Open in your dashboard <Icon name="arrow-right" size={16} />
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="field-hint">A roadmap for this program is not available yet.</p>
              )}
            </div>
          </div>

          <aside className="side-panel" aria-labelledby="criteria-title">
            <h2 id="criteria-title">Published eligibility criteria</h2>
            {hasCriteria ? (
              <dl className="program-facts">
                {program.min_percentage !== null && (
                  <div>
                    <dt>Minimum marks</dt>
                    <dd>{program.min_percentage}%</dd>
                  </div>
                )}
                {program.accepted_qualifications.length > 0 && (
                  <div>
                    <dt>Accepted qualifications</dt>
                    <dd>{program.accepted_qualifications.join(', ')}</dd>
                  </div>
                )}
              </dl>
            ) : (
              <p>Eligibility criteria for this program have not been published yet.</p>
            )}
            {program.eligibility_notes && <RichText text={program.eligibility_notes} className="field-hint" />}
            <p className="field-hint" style={{ marginTop: 14 }}>
              ZYNTRA provides preliminary guidance only. SZABIST makes all official admission decisions.
            </p>
            {!user && (
              <Link to="/register" className="btn btn-primary btn-block" style={{ marginTop: 18 }}>
                Create Student Account
              </Link>
            )}
          </aside>
        </div>
      </section>
    </div>
  )
}
