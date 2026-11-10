import { Link } from 'react-router-dom'
import { usePageTitle } from '../../hooks/usePageTitle'

export default function NotFoundPage() {
  usePageTitle('Page not found')
  return (
    <section className="container page-body page-enter" style={{ textAlign: 'center', minHeight: '50vh' }}>
      <p className="eyebrow">Error 404</p>
      <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.2rem)', margin: '12px 0' }}>This page does not exist.</h1>
      <p>The link may be broken or the page may have been removed.</p>
      <Link to="/" className="btn btn-primary" style={{ marginTop: 24 }}>
        Go to the home page
      </Link>
    </section>
  )
}
