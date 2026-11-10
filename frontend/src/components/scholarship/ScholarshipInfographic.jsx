import '../../styles/scholarship.css'
import { RichText } from '../ui/Feedback'
import Icon from '../ui/Icon'

function InfoPanel({ number, icon, title, items, emptyText }) {
  return (
    <section className="sch-panel" aria-labelledby={`sch-panel-${number}`}>
      <div className="sch-panel-head">
        <span className="sch-panel-number" aria-hidden="true">
          {String(number).padStart(2, '0')}
        </span>
        <Icon name={icon} size={20} />
        <h3 id={`sch-panel-${number}`}>{title}</h3>
      </div>
      {items.length === 0 ? (
        <p className="field-hint">{emptyText}</p>
      ) : (
        <ul className="sch-list">
          {items.map((item, index) => (
            <li key={index}>
              <Icon name="check" size={16} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

/** Visual, step-by-step presentation of one scholarship. Read-only. */
export default function ScholarshipInfographic({ scholarship }) {
  const steps = scholarship.application_steps || []

  return (
    <article className="sch">
      <header className="sch-header">
        {scholarship.scholarship_type && <span className="badge badge-orange">{scholarship.scholarship_type}</span>}
        <h2 className="sch-title">{scholarship.title}</h2>
        {scholarship.summary && <p className="sch-summary">{scholarship.summary}</p>}
        {scholarship.description && <RichText text={scholarship.description} />}
      </header>

      <section className="sch-process" aria-labelledby="sch-process-title">
        <h3 id="sch-process-title" className="sch-section-title">
          Application procedure
        </h3>
        {steps.length === 0 ? (
          <p className="field-hint">The application procedure has not been published yet.</p>
        ) : (
          <ol className="sch-steps" style={{ '--step-count': steps.length }}>
            {steps.map((step, index) => (
              <li key={index} className={`sch-step ${index % 2 === 0 ? 'is-top' : 'is-bottom'}`}>
                <div className="sch-step-content">
                  <span className="sch-step-label">Step {index + 1}</span>
                  <h4>{step.title}</h4>
                  {step.description && <p>{step.description}</p>}
                </div>
                <span className={`sch-step-marker ${index === steps.length - 1 ? 'is-last' : ''}`} aria-hidden="true">
                  {String(index + 1).padStart(2, '0')}
                </span>
              </li>
            ))}
          </ol>
        )}
      </section>

      <div className="sch-panels">
        <InfoPanel
          number={1}
          icon="check-circle"
          title="Eligibility criteria"
          items={scholarship.eligibility_criteria}
          emptyText="Eligibility criteria have not been published yet."
        />
        <InfoPanel
          number={2}
          icon="award"
          title="Benefits"
          items={scholarship.benefits}
          emptyText="Benefits have not been published yet."
        />
        <InfoPanel
          number={3}
          icon="file"
          title="Required documents"
          items={scholarship.required_documents}
          emptyText="Required documents have not been published yet."
        />
        <InfoPanel
          number={4}
          icon="info"
          title="Important conditions"
          items={scholarship.conditions}
          emptyText="No additional conditions have been published."
        />
      </div>
    </article>
  )
}
