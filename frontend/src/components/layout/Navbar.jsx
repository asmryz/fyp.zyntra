import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { homePathForRole } from '../../utils/roles'
import Icon from '../ui/Icon'
import Logo from '../ui/Logo'

const NAV_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/#about', label: 'About SZABIST' },
  { to: '/programs', label: 'Programs' },
  { to: '/#admission-guidance', label: 'Admission Guidance' },
]

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const { user } = useAuth()
  const location = useLocation()

  // Close the mobile menu after navigating or when Escape is pressed
  const [lastPath, setLastPath] = useState(location.pathname + location.hash)
  const currentPath = location.pathname + location.hash
  if (currentPath !== lastPath) {
    setLastPath(currentPath)
    setMenuOpen(false)
  }

  useEffect(() => {
    if (!menuOpen) return undefined
    const onKey = (event) => event.key === 'Escape' && setMenuOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [menuOpen])

  const accountActions = user ? (
    <Link to={homePathForRole(user.role)} className="btn btn-primary btn-sm">
      Go to dashboard
    </Link>
  ) : (
    <>
      <Link to="/login" className="btn btn-ghost btn-sm">
        Login
      </Link>
      <Link to="/register" className="btn btn-primary btn-sm">
        Get Started
      </Link>
    </>
  )

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <Logo />

        <nav className="navbar-links" aria-label="Main">
          {NAV_LINKS.map((link) =>
            link.to.includes('#') ? (
              <Link key={link.to} to={link.to} className="navbar-link">
                {link.label}
              </Link>
            ) : (
              <NavLink key={link.to} to={link.to} end={link.end} className="navbar-link">
                {link.label}
              </NavLink>
            ),
          )}
        </nav>

        <div className="navbar-actions">{accountActions}</div>

        <button
          type="button"
          className="btn btn-ghost navbar-toggle"
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <Icon name={menuOpen ? 'close' : 'menu'} size={24} label={menuOpen ? 'Close menu' : 'Open menu'} />
        </button>
      </div>

      {menuOpen && (
        <nav id="mobile-menu" className="mobile-menu" aria-label="Main">
          <div className="container">
            {NAV_LINKS.map((link) => (
              <Link key={link.to} to={link.to} className="mobile-menu-link">
                {link.label}
              </Link>
            ))}
            <div className="mobile-menu-actions">{accountActions}</div>
          </div>
        </nav>
      )}
    </header>
  )
}
