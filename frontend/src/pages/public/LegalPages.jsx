import { Alert } from '../../components/ui/Feedback'
import { usePageTitle } from '../../hooks/usePageTitle'

function DraftNotice() {
  return (
    <Alert type="warning">
      <p>
        <strong>Draft for review.</strong> This page describes how ZYNTRA currently works. It has not been reviewed
        by SZABIST or a legal adviser. Items marked “to be confirmed” must be completed before public launch.
      </p>
    </Alert>
  )
}

function LegalLayout({ title, intro, children }) {
  return (
    <div className="page-enter">
      <section className="page-hero">
        <div className="container">
          <p className="eyebrow">Legal</p>
          <h1>{title}</h1>
          <p>{intro}</p>
        </div>
      </section>
      <section className="page-body">
        <div className="container legal">
          <DraftNotice />
          {children}
        </div>
      </section>
    </div>
  )
}

export function TermsPage() {
  usePageTitle('Terms of Service')
  return (
    <LegalLayout title="Terms of Service" intro="The rules for using the ZYNTRA admission assistance platform.">
      <h2>1. What ZYNTRA is</h2>
      <p>
        ZYNTRA is a Final Year Project that provides admission guidance, preliminary eligibility information, admission
        test preparation, program and career roadmaps and scholarship information for prospective SZABIST students.
      </p>
      <p>
        ZYNTRA is not an official SZABIST system. It does not make admission decisions, accept or submit applications,
        process enrollment or collect payments.
      </p>

      <h2>2. Accounts</h2>
      <ul>
        <li>Anyone can create a student account. You must verify your email address with a one-time code before using it.</li>
        <li>Staff accounts are created only through an invitation from the ZYNTRA root administrator.</li>
        <li>You are responsible for keeping your password private and for the information you add to your profile.</li>
        <li>Never share verification or password reset codes with anyone.</li>
      </ul>

      <h2>3. Guidance only</h2>
      <p>
        Eligibility results compare your profile with the criteria published in ZYNTRA. They are preliminary guidance,
        not an official decision. Always confirm requirements, deadlines, fees and scholarship terms with official SZABIST
        sources.
      </p>

      <h2>4. Content</h2>
      <p>
        Program, scholarship, roadmap and test-preparation content is entered by ZYNTRA administrators and authorised
        staff. During development some pages show clearly labelled placeholder content. Practice questions are for
        preparation and are not official examination material.
      </p>

      <h2>5. Acceptable use</h2>
      <ul>
        <li>Do not try to access accounts, data or administrative areas you are not authorised to use.</li>
        <li>Do not interfere with the platform, for example by automated or excessive requests.</li>
        <li>Do not create accounts with email addresses you do not control.</li>
      </ul>
      <p>The administrator may deactivate accounts that break these rules.</p>

      <h2>6. Changes</h2>
      <p>These terms may be updated as the project develops. The date of the latest version will be shown here.</p>

      <h2>7. Contact</h2>
      <p>Contact details: to be confirmed.</p>
    </LegalLayout>
  )
}

export function PrivacyPage() {
  usePageTitle('Privacy Policy')
  return (
    <LegalLayout title="Privacy Policy" intro="What information ZYNTRA stores, why, and who can see it.">
      <h2>1. Information we store</h2>
      <ul>
        <li><strong>Account details:</strong> your name, email address and role. Your password is stored only as a bcrypt hash, never in readable form.</li>
        <li><strong>Profile details you choose to add:</strong> contact number, previous qualification, academic background, board or university, passing year, marks or percentage, preferred program and any additional details.</li>
        <li><strong>Security records:</strong> hashed one-time codes (with expiry time and attempt count), hashed login session tokens and your last login time.</li>
        <li><strong>Activity log:</strong> important account and administrative events, such as registrations, logins, invitations, permission changes and content updates, with the name of the person who performed them.</li>
      </ul>

      <h2>2. How the information is used</h2>
      <ul>
        <li>To create and secure your account and keep you signed in.</li>
        <li>To send emails you need: verification codes, account confirmation, password reset codes, password change notices and staff invitations. ZYNTRA does not send promotional emails.</li>
        <li>To personalise the admission guidance ZYNTRA shows you.</li>
        <li>To let the administrator manage accounts and keep the platform secure.</li>
      </ul>

      <h2>3. Who can see your information</h2>
      <ul>
        <li>You can view and edit your own profile at any time.</li>
        <li>The root administrator can view account and profile details in order to manage accounts.</li>
        <li>Staff members manage content only; they cannot view student accounts or profiles.</li>
      </ul>

      <h2>4. Where the information is kept</h2>
      <p>
        Data is stored in a PostgreSQL database hosted by Neon. Emails are delivered through Google’s Gmail SMTP
        service. The website loads its fonts from Google Fonts, which means Google receives your IP address when the page loads.
      </p>

      <h2>5. Cookies</h2>
      <p>
        ZYNTRA uses one cookie, <code>zyntra_refresh</code>, to keep you signed in for up to 7 days. It is marked
        HttpOnly so page scripts cannot read it. ZYNTRA does not use advertising or analytics cookies.
      </p>

      <h2>6. AI assistant and WhatsApp</h2>
      <p>
        The AI admission assistant and WhatsApp assistance are not connected yet. This policy will be updated to explain
        what information they use before either feature is turned on.
      </p>

      <h2>7. Keeping and deleting information</h2>
      <p>
        Information is kept while your account exists. Deleting an account removes its profile, codes and
        sessions. Self-service account deletion is not available yet; ask the administrator. The retention
        period for inactive accounts is to be confirmed.
      </p>

      <h2>8. Contact</h2>
      <p>Data controller and contact details: to be confirmed.</p>
    </LegalLayout>
  )
}
