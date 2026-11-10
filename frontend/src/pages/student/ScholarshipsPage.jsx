import { useSearchParams } from 'react-router-dom'
import { PageHeader } from '../../components/layout/DashboardLayout'
import ScholarshipInfographic from '../../components/scholarship/ScholarshipInfographic'
import { Alert, EmptyState, SkeletonList } from '../../components/ui/Feedback'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'

export default function ScholarshipsPage() {
  usePageTitle('Scholarships')
  const { data: scholarships, error, loading } = useApi('/api/content/scholarships')
  const [searchParams, setSearchParams] = useSearchParams()

  const selectedId = Number(searchParams.get('id'))
  const selected = scholarships?.find((item) => item.id === selectedId) || scholarships?.[0]

  return (
    <>
      <PageHeader
        title="Scholarship information"
        description="Scholarship types, eligibility, benefits, required documents and the application procedure, step by step. Always confirm final details with SZABIST."
      />

      {loading && <SkeletonList rows={3} height={120} />}
      {error && <Alert type="error">{error.message}</Alert>}
      {scholarships?.length === 0 && (
        <EmptyState title="No scholarships published yet">
          Scholarship information will appear here once the ZYNTRA team publishes it.
        </EmptyState>
      )}

      {selected && (
        <div className="sch-layout">
          <ul className="sch-picker" aria-label="Choose a scholarship">
            {scholarships.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className="sch-picker-button"
                  aria-pressed={item.id === selected.id}
                  onClick={() => setSearchParams({ id: item.id })}
                >
                  <span className="sch-picker-title">{item.title}</span>
                  {item.scholarship_type && <span className="sch-picker-type">{item.scholarship_type}</span>}
                </button>
              </li>
            ))}
          </ul>
          <ScholarshipInfographic scholarship={selected} />
        </div>
      )}
    </>
  )
}
