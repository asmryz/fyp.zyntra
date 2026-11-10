/**
 * The three dashboard experiences. They share DashboardLayout but each has
 * its own navigation. The staff navigation only lists modules the staff
 * member has permission for.
 */
import { useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import '../../styles/student-theme.css'
import DashboardLayout from './DashboardLayout'

const STUDENT_NAV = [
  {
    items: [
      { to: '/student', label: 'Dashboard', icon: 'home', end: true },
      { to: '/student/profile', label: 'My Profile', icon: 'user' },
    ],
  },
  {
    heading: 'Guidance',
    items: [
      { to: '/student/test-prep', label: 'Test Preparation', icon: 'clipboard' },
      { to: '/student/roadmaps', label: 'Program & Career Roadmaps', icon: 'route' },
      { to: '/student/scholarships', label: 'Scholarships', icon: 'award' },
      { to: '/student/whatsapp', label: 'WhatsApp Assistance', icon: 'chat' },
    ],
  },
]

const CONTENT_NAV = [
  { module: 'programs', path: 'programs', label: 'Program Information', icon: 'graduation' },
  { module: 'scholarships', path: 'scholarships', label: 'Scholarships', icon: 'award' },
  { module: 'roadmaps', path: 'roadmaps', label: 'Roadmaps', icon: 'route' },
  { module: 'test_prep', path: 'test-prep', label: 'Test Preparation', icon: 'clipboard' },
  { module: 'site_content', path: 'site-content', label: 'Website Content', icon: 'layers' },
]

const ROOT_NAV = [
  { items: [{ to: '/root', label: 'Overview', icon: 'grid', end: true }] },
  {
    heading: 'People',
    items: [
      { to: '/root/users', label: 'Users', icon: 'users' },
      { to: '/root/staff', label: 'Staff & Permissions', icon: 'shield' },
      { to: '/root/activity', label: 'Activity Log', icon: 'activity' },
    ],
  },
  {
    heading: 'Content',
    items: CONTENT_NAV.map((item) => ({ to: `/root/${item.path}`, label: item.label, icon: item.icon })),
  },
]

export function StudentConsole() {
  return <DashboardLayout consoleName="Student Dashboard" homePath="/student" navGroups={STUDENT_NAV} theme="theme-student" />
}

export function RootConsole() {
  return <DashboardLayout consoleName="Root Admin Console" homePath="/root" navGroups={ROOT_NAV} />
}

export function StaffConsole() {
  const { user, refreshUser } = useAuth()

  // Load the latest permissions in case the root admin changed them
  useEffect(() => {
    refreshUser().catch(() => {})
  }, [refreshUser])

  const permissions = user?.permissions || {}
  const navGroups = [
    { items: [{ to: '/staff', label: 'Overview', icon: 'grid', end: true }] },
    {
      heading: 'Content',
      items: CONTENT_NAV.filter((item) => permissions[item.module]).map((item) => ({
        to: `/staff/${item.path}`,
        label: item.label,
        icon: item.icon,
      })),
    },
  ]

  return <DashboardLayout consoleName="Staff Console" homePath="/staff" navGroups={navGroups} />
}
