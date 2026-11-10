import { Link } from 'react-router-dom'

/** The ZYNTRA text wordmark used in navigation bars and sidebars. */
export default function Logo({ to = '/', subtitle }) {
  return (
    <Link to={to} className="logo" aria-label="ZYNTRA home">
      <span className="logo-mark" aria-hidden="true">
        Z
      </span>
      <span className="logo-text">
        <span className="logo-word">ZYNTRA</span>
        {subtitle && <span className="logo-subtitle">{subtitle}</span>}
      </span>
    </Link>
  )
}
