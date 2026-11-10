import { Link } from 'react-router-dom'
import { PageHeader } from '../../components/layout/DashboardLayout'
import { Alert, Skeleton } from '../../components/ui/Feedback'
// Icon and QUICK_LINKS are used by the 'Explore ZYNTRA' block, which is commented out below
// eslint-disable-next-line no-unused-vars
import Icon from '../../components/ui/Icon'
import { useAuth } from '../../context/AuthContext'
import { useApi } from '../../hooks/useApi'
import { usePageTitle } from '../../hooks/usePageTitle'

// eslint-disable-next-line no-unused-vars
const QUICK_LINKS = [
  { to: '/student/test-prep', icon: 'clipboard', title: 'Test Preparation', text: 'Topics, explanations, videos and past papers.' },
  { to: '/student/roadmaps', icon: 'route', title: 'Program & Career Roadmaps', text: 'Career paths with the skills and tools for each step.' },
  { to: '/student/scholarships', icon: 'award', title: 'Scholarships', text: 'Eligibility, benefits and how to apply.' },
  { to: '/student/whatsapp', icon: 'chat', title: 'WhatsApp Assistance', text: 'Ask admission questions on WhatsApp.' },
]

export default function StudentHome() {
  usePageTitle('Student dashboard')
  const { user } = useAuth()
  const profile = useApi('/api/student/profile')
  const firstName = user?.full_name?.split(' ')[0]

  return (
    <>
      <PageHeader
        className="page-header-hero"
        title={`Welcome, ${firstName}`}
        description="Everything you need to understand SZABIST admission requirements and prepare with confidence."
      />

      <section className="panel" aria-labelledby="profile-progress" style={{ marginBottom: 24 }}>
        <div className="panel-head">
          <h2 id="profile-progress" className="panel-title">
            Your academic profile
          </h2>
          <Link to="/student/profile" className="btn btn-secondary btn-sm">
            Edit profile
          </Link>
        </div>
        {profile.loading && <Skeleton height={60} />}
        {profile.error && <Alert type="error">{profile.error.message}</Alert>}
        {profile.data && (
          <>
            <p style={{ marginBottom: 10 }}>
              <strong style={{ color: 'var(--text)', fontSize: '1.6rem' }}>{profile.data.completeness_percent}%</strong>{' '}
              complete
            </p>
            <div
              className="meter"
              role="progressbar"
              aria-valuenow={profile.data.completeness_percent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Profile completeness"
            >
              <div className="meter-fill" style={{ width: `${profile.data.completeness_percent}%` }} />
            </div>
            {profile.data.missing_fields.length > 0 ? (
              <p className="field-hint" style={{ marginTop: 12 }}>
                Still missing: {profile.data.missing_fields.join(', ')}. A complete profile helps ZYNTRA give
                you more relevant guidance.
              </p>
            ) : (
              <p className="field-hint" style={{ marginTop: 12 }}>
                Your profile is complete.
              </p>
            )}
          </>
        )}
      </section>

      {/* <h2 className="panel-title">Explore ZYNTRA</h2>
      <div className="quick-links">
        {QUICK_LINKS.map((link) => (
          <Link key={link.to} to={link.to} className="quick-link">
            <span className="quick-link-icon">
              <Icon name={link.icon} size={22} />
            </span>
            <span>
              <h3>{link.title}</h3>
              <p>{link.text}</p>
            </span>
            <Icon name="chevron-right" size={18} />
          </Link>
        ))}
      </div> */}

      <p className="field-hint" style={{ marginTop: 24 }}>
        ZYNTRA provides guidance only. Admission decisions are made by SZABIST through its official admission process.
      </p>
    </>
  )
}
