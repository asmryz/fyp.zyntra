import { useApi } from '../../../hooks/useApi'
import { useModuleAccess } from '../../../hooks/useModuleAccess'

export function roadmapToForm(roadmap) {
  return {
    title: roadmap.title,
    description: roadmap.description || '',
    program_id: roadmap.program_id ? String(roadmap.program_id) : '',
    status: roadmap.status,
  }
}

export function roadmapToBody(form) {
  return { ...form, program_id: form.program_id ? Number(form.program_id) : null }
}

/**
 * Programs for the "linked program" dropdown. Staff without full access to
 * the programs module can still link a roadmap to any published program.
 */
export function useProgramChoices() {
  const programsAccess = useModuleAccess('programs')
  const path = programsAccess.canView && !programsAccess.ownRecordsOnly ? '/api/admin/programs' : '/api/public/programs'
  return useApi(path).data || []
}

/** A copy of `list` with the item at `index` moved one place up (-1) or down (+1). */
export function moveItem(list, index, direction) {
  const target = index + direction
  if (target < 0 || target >= list.length) return list
  const copy = [...list]
  ;[copy[index], copy[target]] = [copy[target], copy[index]]
  return copy
}

// Titles offered when adding a custom section; admins can type any title
export const SECTION_TITLE_SUGGESTIONS = [
  'Prerequisites',
  'Learning Resources',
  'Recommended Courses',
  'Projects',
  'Certifications',
  'Career Opportunities',
  'Additional Notes',
]

const DEFAULT_SECTION_TITLES = { skills: 'Skills', tools: 'Tools & Technologies', links: 'Learning Resources' }

/** Editor state for a new section. All content fields are kept so switching type does not lose input. */
export function newSection(type) {
  return { section_title: DEFAULT_SECTION_TITLES[type] || '', section_type: type, items: [], text: '', links: [] }
}

export function sectionToForm(section) {
  return {
    section_title: section.section_title,
    section_type: section.section_type,
    items: section.content.items || [],
    text: section.content.text || '',
    links: section.content.links || [],
  }
}

/** Request body for a section: only the content field that matches its type. */
export function sectionToBody(section) {
  const type = section.section_type
  let content
  if (type === 'text') content = { text: section.text }
  else if (type === 'links') content = { links: section.links.filter((link) => link.label.trim() || link.url.trim()) }
  else content = { items: section.items.filter((item) => item.trim()) }
  return { section_title: section.section_title, section_type: type, content }
}

export function isHexColor(value) {
  return /^#[0-9a-f]{6}$/i.test(value || '')
}
