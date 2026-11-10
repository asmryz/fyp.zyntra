import { Outlet } from 'react-router-dom'
import { useApi } from '../../hooks/useApi'
import '../../styles/public.css'
import '../../styles/public-theme.css'
import Footer from './Footer'
import Navbar from './Navbar'

/**
 * Layout for public pages. Website content blocks are loaded once here and
 * shared with the page (via the Outlet context) and the footer.
 */
export default function PublicLayout() {
  const siteContent = useApi('/api/public/site-content')

  return (
    // theme-public scopes the public colour theme (styles/public-theme.css)
    <div className="theme-public">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Navbar />
      <main id="main">
        <Outlet context={{ siteContent }} />
      </main>
      <Footer siteContent={siteContent.data} />
    </div>
  )
}
