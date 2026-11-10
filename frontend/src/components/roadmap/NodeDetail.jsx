import { RichText } from '../ui/Feedback'
import Icon from '../ui/Icon'

/** One block of a step's details. The section types come from the backend (ROADMAP_SECTION_TYPES). */
function DetailSection({ section, headingId }) {
  const { section_title: title, section_type: type, content } = section
  const items = (content.items || []).filter(Boolean)
  const links = content.links || []

  if (['skills', 'tools', 'list'].includes(type) && items.length === 0) return null
  if (type === 'text' && !content.text) return null
  if (type === 'links' && links.length === 0) return null

  return (
    <section className={`rm-detail-section rm-section-${type}`} aria-labelledby={headingId}>
      <h4 className="rm-detail-heading" id={headingId}>
        {type === 'tools' && <Icon name="wrench" size={15} />}
        {title}
      </h4>
      {(type === 'skills' || type === 'tools') && (
        <ul className={`rm-tags rm-tags-${type}`}>
          {items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      )}
      {type === 'list' && (
        <ul className="rm-detail-list">
          {items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      )}
      {type === 'text' && <RichText text={content.text} className="rm-detail-text" />}
      {type === 'links' && (
        <ul className="rm-detail-links">
          {links.map((link, index) => (
            <li key={index}>
              <a href={link.url} target="_blank" rel="noopener noreferrer">
                <Icon name="external" size={15} />
                {link.label}
                <span className="sr-only"> (opens in a new tab)</span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

/** The content of the floating detail card for one roadmap step. */
export default function NodeDetail({ branch, node, titleId }) {
  const sections = node.sections || []
  return (
    <>
      <p className="rm-detail-branch">{branch.name}</p>
      <h3 className="rm-detail-title" id={titleId}>
        {node.title}
      </h3>
      {node.description && <RichText text={node.description} className="rm-detail-description" />}
      {sections.map((section, index) => (
        <DetailSection key={section.id ?? index} section={section} headingId={`${titleId}-s${index}`} />
      ))}
      {!node.description && sections.length === 0 && (
        <p className="rm-detail-description">Details for this step will be added soon.</p>
      )}
    </>
  )
}
