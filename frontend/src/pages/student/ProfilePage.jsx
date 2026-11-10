import { useState } from 'react'
import { PageHeader } from '../../components/layout/DashboardLayout'
import { Alert, PageLoader } from '../../components/ui/Feedback'
import FormField from '../../components/ui/FormField'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import { useApi } from '../../hooks/useApi'
import { useFormOptions } from '../../hooks/useFormOptions'
import { usePageTitle } from '../../hooks/usePageTitle'
import { api } from '../../services/api'

const TEXT_FIELDS = [
  'full_name', 'contact_number', 'previous_qualification', 'academic_background', 'board_or_university',
  'additional_details',
]
const NUMBER_FIELDS = ['passing_year', 'obtained_marks', 'total_marks', 'percentage', 'preferred_program_id']

/** Convert the profile from the API into form values (all strings). */
function toFormValues(profile) {
  const values = {}
  for (const field of [...TEXT_FIELDS, ...NUMBER_FIELDS]) {
    values[field] = profile[field] === null || profile[field] === undefined ? '' : String(profile[field])
  }
  return values
}

/** Convert form values back into the JSON the API expects (empty -> null). */
function toRequestBody(values) {
  const body = {}
  for (const field of TEXT_FIELDS) body[field] = values[field].trim() || null
  for (const field of NUMBER_FIELDS) body[field] = values[field] === '' ? null : Number(values[field])
  body.full_name = values.full_name.trim()
  return body
}

function ProfileForm({ profile, programs, qualifications }) {
  const { refreshUser } = useAuth()
  const toast = useToast()
  const [values, setValues] = useState(() => {
    const initial = toFormValues(profile)
    // A preferred program that is no longer published cannot be selected again
    if (!programs.some((program) => String(program.id) === initial.preferred_program_id)) {
      initial.preferred_program_id = ''
    }
    return initial
  })
  const [saved, setSaved] = useState(profile)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const update = (field) => (event) => setValues({ ...values, [field]: event.target.value })
  const marksGiven = values.obtained_marks !== '' && values.total_marks !== ''

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const updated = await api.put('/api/student/profile', toRequestBody(values))
      setSaved(updated)
      setValues(toFormValues(updated))
      await refreshUser()
      toast.success('Your profile has been saved.')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="panel">
        <h2 className="panel-title">Personal details</h2>
        <div className="form-grid">
          <FormField label="Full name" value={values.full_name} onChange={update('full_name')} autoComplete="name" />
          <FormField
            label="Email address"
            value={saved.email}
            readOnly
            disabled
            hint="Verified. Your email address cannot be changed here."
          />
          <FormField
            label="Contact number"
            optional
            type="tel"
            autoComplete="tel"
            value={values.contact_number}
            onChange={update('contact_number')}
            placeholder="+92 300 1234567"
          />
        </div>
      </div>

      <div className="panel">
        <h2 className="panel-title">Academic background</h2>
        <div className="form-grid">
          <FormField
            label="Previous qualification"
            as="select"
            value={values.previous_qualification}
            onChange={update('previous_qualification')}
          >
            <option value="">Select a qualification</option>
            {qualifications.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </FormField>
          <FormField
            label="Academic background / group"
            value={values.academic_background}
            onChange={update('academic_background')}
            placeholder="e.g. Pre-Engineering, ICS, Commerce"
          />
          <FormField
            label="Board or university"
            value={values.board_or_university}
            onChange={update('board_or_university')}
          />
          <FormField
            label="Passing year"
            type="number"
            inputMode="numeric"
            value={values.passing_year}
            onChange={update('passing_year')}
          />
          <FormField
            label="Obtained marks"
            optional
            type="number"
            min="0"
            value={values.obtained_marks}
            onChange={update('obtained_marks')}
          />
          <FormField
            label="Total marks"
            optional
            type="number"
            min="1"
            value={values.total_marks}
            onChange={update('total_marks')}
          />
          <FormField
            label="Percentage"
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={values.percentage}
            onChange={update('percentage')}
            disabled={marksGiven}
            hint={marksGiven ? 'Calculated automatically from your marks when you save.' : 'Enter this if marks do not apply.'}
          />
          <FormField
            label="Preferred program"
            as="select"
            value={values.preferred_program_id}
            onChange={update('preferred_program_id')}
          >
            <option value="">No preference yet</option>
            {programs.map((program) => (
              <option key={program.id} value={program.id}>
                {program.name}
              </option>
            ))}
          </FormField>
          <FormField
            label="Other relevant details"
            optional
            as="textarea"
            className="span-2"
            value={values.additional_details}
            onChange={update('additional_details')}
            placeholder="Anything else that helps describe your academic background."
          />
        </div>
      </div>

      <div className="panel">
        <Alert type="error">{error}</Alert>
        <div className="form-actions" style={{ marginTop: error ? 14 : 0 }}>
          <span className="field-hint" style={{ marginRight: 'auto', alignSelf: 'center' }}>
            Profile {saved.completeness_percent}% complete
          </span>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving && <span className="spinner" aria-hidden="true" />}
            {saving ? 'Saving...' : 'Save profile'}
          </button>
        </div>
      </div>
    </form>
  )
}

export default function ProfilePage() {
  usePageTitle('My profile')
  const profile = useApi('/api/student/profile')
  const programs = useApi('/api/public/programs')
  const options = useFormOptions()

  return (
    <>
      <PageHeader
        title="Academic profile"
        description="Only you and the ZYNTRA administrator can see this information. It is used to personalise the guidance ZYNTRA gives you."
      />
      {profile.error && <Alert type="error">{profile.error.message}</Alert>}
      {profile.loading || programs.loading || !options ? (
        <PageLoader />
      ) : (
        profile.data && (
          <ProfileForm profile={profile.data} programs={programs.data || []} qualifications={options.qualifications} />
        )
      )}
    </>
  )
}
