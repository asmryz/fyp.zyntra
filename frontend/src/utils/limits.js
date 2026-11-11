// Input limits. They mirror the backend (app/constants.py and the API schemas),
// which checks every value again; these stop overlong input while typing.
export const LIMITS = {
  fullName: 120,
  email: 254,
  password: 72,
  longText: 10000, // descriptions, explanations, website text
  listItem: 500, // one line of a list (eligibility criteria, benefits, ...)
  shortText: 200, // default for single-line text fields
  url: 500,
  search: 100,
  marksMax: 100000,
}

/**
 * A link that is safe to put in href: only complete http(s) addresses.
 * Anything else (javascript:, data:, relative paths) returns null so the
 * caller can show the text without a link. The backend and a database
 * constraint already enforce this; this guards against unexpected data.
 */
export function safeExternalUrl(value) {
  if (typeof value !== 'string') return null
  try {
    const url = new URL(value.trim())
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null
  } catch {
    return null
  }
}
