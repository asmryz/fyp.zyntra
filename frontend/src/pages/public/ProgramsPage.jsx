
import { Link } from 'react-router-dom'
import { Alert, EmptyState, SkeletonList } from '../../components/ui/Feedback'
import Icon from '../../components/ui/Icon'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'

export default function ProgramsPage() {
  usePageTitle('Programs')
  const { data: programs, error, loading } = useApi('/api/public/programs')

  return (
    <div className="page-enter">
      <section className="page-hero">
        <div className="container">
          <p className="eyebrow">Programs</p>
          <h1>SZABIST programs</h1>
          <p>
            Browse the programs currently published in ZYNTRA. 
          </p>
        </div>
      </section>

      <section className="page-body">
        <div className="container">
          {loading && <SkeletonList rows={3} height={84} />}
          {error && <Alert type="error">{error.message}</Alert>}
          {programs?.length === 0 && (
            <EmptyState title="No programs published yet">
              Program information will appear here once it has been published by the ZYNTRA team.
            </EmptyState>
          )}
          {programs?.length > 0 && (
            <ul className="program-rows">
              {programs.map((program) => (
                <li key={program.id}>
                  <Link to={`/programs/${program.slug}`} className="program-row">
                    <span className="program-row-name">{program.name}</span>
                    <span className="program-row-meta">
                      {[program.department, program.degree_level, program.duration].filter(Boolean).join(' · ') ||
                        program.summary}
                    </span>
                    <Icon name="arrow-right" size={22} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  )
}
