import { lazy, Suspense, useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import PublicLayout from './components/layout/PublicLayout'
import { PageLoader } from './components/ui/Feedback'
import LandingPage from './pages/public/LandingPage'

// Pages are loaded on demand so the landing page downloads less JavaScript
const lazyNamed = (loader, name) => lazy(() => loader().then((module) => ({ default: module[name] })))

const ProgramsPage = lazy(() => import('./pages/public/ProgramsPage'))
const ProgramDetailPage = lazy(() => import('./pages/public/ProgramDetailPage'))
const TermsPage = lazyNamed(() => import('./pages/public/LegalPages'), 'TermsPage')
const PrivacyPage = lazyNamed(() => import('./pages/public/LegalPages'), 'PrivacyPage')
const NotFoundPage = lazy(() => import('./pages/public/NotFoundPage'))

const LoginPage = lazy(() => import('./pages/auth/LoginPage'))
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'))
const VerifyEmailPage = lazy(() => import('./pages/auth/VerifyEmailPage'))
const ForgotPasswordPage = lazy(() => import('./pages/auth/ForgotPasswordPage'))
const AcceptInvitePage = lazy(() => import('./pages/auth/AcceptInvitePage'))

const StudentConsole = lazyNamed(() => import('./components/layout/Consoles'), 'StudentConsole')
const RootConsole = lazyNamed(() => import('./components/layout/Consoles'), 'RootConsole')
const StaffConsole = lazyNamed(() => import('./components/layout/Consoles'), 'StaffConsole')

const StudentHome = lazy(() => import('./pages/student/StudentHome'))
const ProfilePage = lazy(() => import('./pages/student/ProfilePage'))
const TestPrepPage = lazy(() => import('./pages/student/TestPrepPage'))
const SubjectPage = lazy(() => import('./pages/student/SubjectPage'))
const TopicPage = lazy(() => import('./pages/student/TopicPage'))
const RoadmapsPage = lazyNamed(() => import('./pages/student/RoadmapsPage'), 'RoadmapsPage')
const RoadmapDetailPage = lazyNamed(() => import('./pages/student/RoadmapsPage'), 'RoadmapDetailPage')
const ScholarshipsPage = lazy(() => import('./pages/student/ScholarshipsPage'))
const WhatsAppPage = lazy(() => import('./pages/student/WhatsAppPage'))

const RootOverviewPage = lazyNamed(() => import('./pages/admin/OverviewPages'), 'RootOverviewPage')
const StaffOverviewPage = lazyNamed(() => import('./pages/admin/OverviewPages'), 'StaffOverviewPage')
const UsersPage = lazy(() => import('./pages/admin/UsersPage'))
const UserDetailPage = lazy(() => import('./pages/admin/UserDetailPage'))
const StaffPage = lazy(() => import('./pages/admin/StaffPage'))
const ActivityPage = lazy(() => import('./pages/admin/ActivityPage'))
const ProgramsManager = lazy(() => import('./pages/admin/content/ProgramsManager'))
const ScholarshipsManager = lazy(() => import('./pages/admin/content/ScholarshipsManager'))
const RoadmapsManager = lazy(() => import('./pages/admin/content/RoadmapsManager'))
const RoadmapEditor = lazy(() => import('./pages/admin/content/RoadmapEditor'))
const TestPrepManager = lazy(() => import('./pages/admin/content/TestPrepManager'))
const SubjectEditor = lazy(() => import('./pages/admin/content/SubjectEditor'))
const SiteContentManager = lazy(() => import('./pages/admin/content/SiteContentManager'))

/** Content management routes, shared by the root admin and staff consoles. */
function contentRoutes() {
  return (
    <>
      <Route path="programs" element={<ProgramsManager />} />
      <Route path="scholarships" element={<ScholarshipsManager />} />
      <Route path="roadmaps" element={<RoadmapsManager />} />
      <Route path="roadmaps/:roadmapId" element={<RoadmapEditor />} />
      <Route path="test-prep" element={<TestPrepManager />} />
      <Route path="test-prep/subjects/:subjectId" element={<SubjectEditor />} />
      <Route path="site-content" element={<SiteContentManager />} />
    </>
  )
}

/** Scroll to the top when moving to a new page (unless a #section is targeted). */
function ScrollToTop() {
  const { pathname, hash } = useLocation()
  useEffect(() => {
    if (!hash) window.scrollTo(0, 0)
  }, [pathname, hash])
  return null
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route index element={<LandingPage />} />
            <Route path="programs" element={<ProgramsPage />} />
            <Route path="programs/:slug" element={<ProgramDetailPage />} />
            <Route path="terms" element={<TermsPage />} />
            <Route path="privacy" element={<PrivacyPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>

          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          <Route path="verify-email" element={<VerifyEmailPage />} />
          <Route path="forgot-password" element={<ForgotPasswordPage />} />
          <Route path="invite/accept" element={<AcceptInvitePage />} />

          <Route element={<ProtectedRoute roles={['student']} />}>
            <Route path="student" element={<StudentConsole />}>
              <Route index element={<StudentHome />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="test-prep" element={<TestPrepPage />} />
              <Route path="test-prep/subjects/:subjectId" element={<SubjectPage />} />
              <Route path="test-prep/topics/:topicId" element={<TopicPage />} />
              <Route path="roadmaps" element={<RoadmapsPage />} />
              <Route path="roadmaps/:roadmapId" element={<RoadmapDetailPage />} />
              <Route path="scholarships" element={<ScholarshipsPage />} />
              <Route path="whatsapp" element={<WhatsAppPage />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={['root_admin']} />}>
            <Route path="root" element={<RootConsole />}>
              <Route index element={<RootOverviewPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="users/:userId" element={<UserDetailPage />} />
              <Route path="staff" element={<StaffPage />} />
              <Route path="activity" element={<ActivityPage />} />
              {contentRoutes()}
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={['staff']} />}>
            <Route path="staff" element={<StaffConsole />}>
              <Route index element={<StaffOverviewPage />} />
              {contentRoutes()}
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </>
  )
}
