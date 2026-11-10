/**
 * Colour helpers for roadmap branches. Branch colours are stored as #RRGGBB
 * and chosen by admins, so text colours are worked out here to stay readable
 * whatever colour is picked.
 */
export const DEFAULT_BRANCH_COLOR = '#2563EB'

function toChannels(hex) {
  const value = /^#[0-9a-f]{6}$/i.test(hex || '') ? hex : DEFAULT_BRANCH_COLOR
  return [1, 3, 5].map((index) => parseInt(value.slice(index, index + 2), 16))
}

function toHex(channels) {
  return `#${channels.map((channel) => channel.toString(16).padStart(2, '0')).join('')}`.toUpperCase()
}

// Relative luminance and contrast ratio as defined by WCAG 2
function luminance(channels) {
  const [r, g, b] = channels.map((channel) => {
    const c = channel / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contrast(a, b) {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (light + 0.05) / (dark + 0.05)
}

const WHITE = [255, 255, 255]
const INK = [17, 24, 39]

export function withAlpha(hex, alpha) {
  const [r, g, b] = toChannels(hex)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

/** White or dark text, whichever reads better on a background of this colour. */
export function textOnColor(hex) {
  const channels = toChannels(hex)
  return contrast(channels, WHITE) >= contrast(channels, INK) ? '#FFFFFF' : '#111827'
}

/** The colour, darkened if needed so it can be used for text on white (4.5:1). */
export function readableOnWhite(hex) {
  let channels = toChannels(hex)
  for (let step = 0; step < 20 && contrast(channels, WHITE) < 4.5; step += 1) {
    channels = channels.map((channel) => Math.round(channel * 0.88))
  }
  return toHex(channels)
}

/** CSS variables used by roadmap.css for everything drawn in a branch's colour. */
export function branchStyle(hex) {
  return {
    '--branch': toHex(toChannels(hex)),
    '--branch-soft': withAlpha(hex, 0.12),
    '--branch-halo': withAlpha(hex, 0.24),
    '--branch-text': readableOnWhite(hex),
    '--branch-on': textOnColor(hex),
  }
}
