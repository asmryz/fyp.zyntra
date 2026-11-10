import { Link } from 'react-router-dom'
import Icon from '../ui/Icon'
import Logo from '../ui/Logo'

const CONTACT_ITEMS = [
  { key: 'contact_email', icon: 'mail' },
  { key: 'contact_phone', icon: 'phone' },
]

/** `siteContent` is the {key: {title, body}} object from /api/public/site-content. */
export default function Footer({ siteContent }) {
  const contacts = CONTACT_ITEMS.filter((item) => siteContent?.[item.key]?.body)

  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div className="footer-brand">
          <Logo />
          <p>
            ZYNTRA is an agentic AI-powered admission assistance system that helps prospective students understand
            SZABIST admission requirements, prepare for the admission test and plan their academic path.
          </p>
          <p className="footer-disclaimer">
            ZYNTRA provides guidance only. It is not an official SZABIST admission system and does not make admission
            decisions, accept applications or process payments.
          </p>
        </div>

        <nav aria-label="Explore">
          <h2 className="footer-heading">Explore</h2>
          <ul className="footer-links">
            <li><Link to="/#about">About SZABIST</Link></li>
            <li><Link to="/programs">Programs</Link></li>
            <li><Link to="/#admission-guidance">Admission Guidance</Link></li>
            <li><Link to="/#test-preparation">Test Preparation</Link></li>
            <li><Link to="/#scholarships">Scholarships</Link></li>
            <li><Link to="/#career-roadmaps">Career Roadmaps</Link></li>
          </ul>
        </nav>

        <nav aria-label="Account">
          <h2 className="footer-heading">Account</h2>
          <ul className="footer-links">
            <li><Link to="/login">Login</Link></li>
            <li><Link to="/register">Create student account</Link></li>
            <li><Link to="/forgot-password">Forgot password</Link></li>
          </ul>
        </nav>

        <div>
          <h2 className="footer-heading">Contact</h2>
          {contacts.length === 0 ? (
            <p className="footer-muted">Contact details will be published soon.</p>
          ) : (
            <ul className="footer-contact">
              {contacts.map((item) => (
                <li key={item.key}>
                  <Icon name={item.icon} size={18} />
                  <span>{siteContent[item.key].body}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="container footer-bottom">
        <p>&copy; {new Date().getFullYear()} ZYNTRA. Final Year Project for SZABIST.</p>
        <div className="footer-legal">
          <Link to="/terms">Terms of Service</Link>
          <Link to="/privacy">Privacy Policy</Link>
        </div>
      </div>
    </footer>
  )
}
