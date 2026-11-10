import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import '../../styles/dashboard.css'
import { ROLE_LABELS } from '../../utils/roles'
import ErrorBoundary from '../ErrorBoundary'
import { Alert } from '../ui/Feedback'
import Icon from '../ui/Icon'
import Logo from '../ui/Logo'

/**
 * Sidebar + top bar layout shared by the student dashboard, the staff
 * console and the root admin console.
 *
 * navGroups: [{ heading?: string, items: [{ to, label, icon, end? }] }]
 * theme: optional extra class, e.g. 'theme-student' for the student palette
 */
export default function DashboardLayout({ consoleName, homePath, navGroups, theme = '' }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [drawerOpen, setDrawerOpen] = useState(false)

  // Close the mobile drawer after navigating
  const [lastPath, setLastPath] = useState(location.pathname)
  if (location.pathname !== lastPath) {
    setLastPath(location.pathname)
    setDrawerOpen(false)
  }

  useEffect(() => {
    if (!drawerOpen) return undefined
    const onKey = (event) => event.key === 'Escape' && setDrawerOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [drawerOpen])

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className={`dash ${theme}`}>
      <a href="#dash-main" className="skip-link">
        Skip to content
      </a>

      <aside className={`dash-sidebar ${drawerOpen ? 'is-open' : ''}`} aria-label={`${consoleName} navigation`}>
        <div className="dash-sidebar-top">
          <Logo to={homePath} subtitle={consoleName} />
          <button type="button" className="btn btn-ghost btn-sm dash-close" onClick={() => setDrawerOpen(false)}>
            <Icon name="close" label="Close navigation" />
          </button>
        </div>

        <nav className="dash-nav">
          {navGroups.map((group, index) => (
            <div key={group.heading || index} className="dash-nav-group">
              {group.heading && <p className="dash-nav-heading">{group.heading}</p>}
              {group.items.map((item) => (
                <NavLink key={item.to} to={item.to} end={item.end} className="dash-nav-link">
                  <Icon name={item.icon} size={18} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <button type="button" className="dash-nav-link dash-logout" onClick={handleLogout}>
          <Icon name="logout" size={18} />
          <span>Logout</span>
        </button>
      </aside>
      {drawerOpen && <div className="dash-backdrop" onClick={() => setDrawerOpen(false)} aria-hidden="true" />}

      <div className="dash-body">
        <header className="dash-topbar">
          <button
            type="button"
            className="btn btn-ghost dash-menu-button"
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen(true)}
          >
            <Icon name="menu" size={22} label="Open navigation" />
          </button>
          <span className="dash-console-name">{consoleName}</span>
          <div className="dash-user">
            <span className="dash-user-name">{user?.full_name}</span>
            <span className={`badge ${user?.role === 'root_admin' ? 'badge-orange' : 'badge-blue'}`}>
              {ROLE_LABELS[user?.role]}
            </span>
          </div>
        </header>

        <main id="dash-main" className="dash-main">
          <ErrorBoundary
            key={location.pathname}
            fallback={<Alert type="error">This page could not be displayed. Please reload and try again.</Alert>}
          >
            <div className="page-enter" key={location.pathname}>
              <Outlet />
            </div>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}

export function PageHeader({ title, description, actions, className = '' }) {
  return (
    <div className={`page-header ${className}`}>
      <div>
        <h1>{title}</h1>
        {description && <p className="page-header-description">{description}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </div>
  )
}
