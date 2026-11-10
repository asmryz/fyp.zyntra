/**
 * Branching roadmap (layout inspired by roadmap.sh): the program heading at
 * the top, curved lines to one column per branch, and the branch's steps as
 * circles going down. Everything comes from the database, so any number of
 * branches and steps is supported; wide roadmaps scroll sideways.
 *
 * Selecting a step opens a floating detail card next to it (a bottom sheet
 * on small screens). Used by the student roadmap page and the admin preview.
 */
import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import '../../styles/roadmap.css'
import { useMediaQuery } from '../../hooks/useMediaQuery'
import Icon from '../ui/Icon'
import NodeDetail from './NodeDetail'
import { branchStyle } from './roadmapColors'

const WIDE = { column: 216, gap: 28, curve: 84, minWidth: 360 }
const COMPACT = { column: 168, gap: 16, curve: 60, minWidth: 260 }
const CARD_GAP = 14 // space between a step and its card
const EDGE = 16 // minimum space between the card and the window edge
const TOP_SAFE = 80 // keeps the card below the sticky dashboard top bar

function findDefault(branches) {
  for (const branch of branches) {
    const node = branch.nodes.find((item) => item.is_default)
    if (node) return node.id
  }
  return null
}

/** Floating card placed beside the selected step, or a bottom sheet when `sheet` is true. */
function DetailCard({ nodeId, sheet, cardRef, titleId, style, onClose, children }) {
  const [position, setPosition] = useState(null)

  useLayoutEffect(() => {
    if (sheet) return undefined
    let frame = 0
    const place = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        const card = cardRef.current
        const anchor = document.querySelector(`[data-node-id="${nodeId}"]`)
        if (!card || !anchor) return
        const rect = anchor.getBoundingClientRect()
        const viewportWidth = document.documentElement.clientWidth
        const viewportHeight = window.innerHeight
        const { offsetWidth: width, offsetHeight: height } = card
        // Prefer the right of the step, then the left, then centred above it
        let left = rect.right + CARD_GAP
        if (left + width > viewportWidth - EDGE) left = rect.left - CARD_GAP - width
        if (left < EDGE) left = Math.min(Math.max(EDGE, rect.left + rect.width / 2 - width / 2), viewportWidth - width - EDGE)
        const top = Math.max(TOP_SAFE, Math.min(rect.top - 24, viewportHeight - height - EDGE))
        // Hide the card while its step is scrolled out of view
        const hidden = rect.bottom < 0 || rect.top > viewportHeight
        setPosition({ left, top, hidden })
      })
    }
    place()
    window.addEventListener('resize', place)
    window.addEventListener('scroll', place, true) // also catches the roadmap's own horizontal scroll
    const observer = new ResizeObserver(place)
    observer.observe(cardRef.current)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', place, true)
      observer.disconnect()
    }
  }, [nodeId, sheet, cardRef])

  const placement = sheet
    ? {}
    : { left: position?.left ?? 0, top: position?.top ?? 0, visibility: !position || position.hidden ? 'hidden' : 'visible' }

  return (
    <section
      ref={cardRef}
      id="rm-detail"
      className={`rm-detail ${sheet ? 'is-sheet' : 'is-floating'}`}
      role="dialog"
      aria-modal="false"
      aria-labelledby={titleId}
      tabIndex={-1}
      style={{ ...style, ...placement }}
    >
      <button type="button" className="rm-detail-close" onClick={onClose}>
        <Icon name="close" size={18} label="Close details" />
      </button>
      {children}
    </section>
  )
}

export default function RoadmapCanvas({ heading, branches, useDefaultStep = true }) {
  const compact = useMediaQuery('(max-width: 640px)')
  const sheet = useMediaQuery('(max-width: 899px)')
  const size = compact ? COMPACT : WIDE
  const titleId = useId()

  // The default step opens automatically on larger screens only, so a bottom
  // sheet never covers the roadmap as soon as the page loads on a phone.
  const [selectedId, setSelectedId] = useState(() =>
    useDefaultStep && !window.matchMedia('(max-width: 899px)').matches ? findDefault(branches) : null,
  )
  const [overflowing, setOverflowing] = useState(false)
  const scrollRef = useRef(null)
  const cardRef = useRef(null)
  const nodeRefs = useRef({})
  const focusCardNext = useRef(false)

  const selectedBranch = branches.find((branch) => branch.nodes.some((node) => node.id === selectedId))
  const selectedNode = selectedBranch?.nodes.find((node) => node.id === selectedId)

  // Geometry: every column has the same width, so the curve end points can be calculated
  const count = branches.length
  const columnsWidth = count * size.column + Math.max(count - 1, 0) * size.gap
  const width = Math.max(columnsWidth, size.minWidth)
  const offset = (width - columnsWidth) / 2
  const centre = width / 2
  const columnCentre = (index) => offset + index * (size.column + size.gap) + size.column / 2

  // Start with the heading in view when the roadmap is wider than the screen
  useLayoutEffect(() => {
    const element = scrollRef.current
    if (!element) return undefined
    element.scrollLeft = (element.scrollWidth - element.clientWidth) / 2
    // The observer also runs once right away, which sets the first value
    const observer = new ResizeObserver(() => setOverflowing(element.scrollWidth > element.clientWidth + 1))
    observer.observe(element)
    return () => observer.disconnect()
  }, [count, compact])

  const close = useCallback(
    (returnFocus) => {
      if (returnFocus && selectedId) nodeRefs.current[selectedId]?.focus()
      setSelectedId(null)
    },
    [selectedId],
  )

  // Escape closes the card; clicking outside it (but not on another step) closes it too
  useEffect(() => {
    if (!selectedId) return undefined
    const onKey = (event) => event.key === 'Escape' && close(true)
    const onPointer = (event) => {
      if (cardRef.current?.contains(event.target) || event.target.closest?.('.rm-node')) return
      close(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('pointerdown', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('pointerdown', onPointer)
    }
  }, [selectedId, close])

  // Move focus into the card after the student opens a step (not for the default step)
  useEffect(() => {
    if (focusCardNext.current && selectedId) cardRef.current?.focus({ preventScroll: true })
    focusCardNext.current = false
  }, [selectedId])

  function select(nodeId) {
    if (nodeId === selectedId) {
      close(false)
      return
    }
    focusCardNext.current = true
    setSelectedId(nodeId)
  }

  if (count === 0) {
    return (
      <div className="rm-empty">
        <h3>No branches yet</h3>
        <p>The career paths for this roadmap will appear here once they are published.</p>
      </div>
    )
  }

  return (
    <div className="rm">
      {overflowing && (
        <p className="rm-hint">
          <Icon name="arrow-left" size={14} />
          Scroll sideways to see all {count} branches
          <Icon name="arrow-right" size={14} />
        </p>
      )}
      <div className="rm-scroll" ref={scrollRef} role="region" aria-label={`${heading} roadmap`} tabIndex={0}>
        <div className="rm-board" style={{ width }}>
          <div className="rm-root">
            <h2 className="rm-root-title">{heading}</h2>
          </div>

          <svg className="rm-curves" width={width} height={size.curve} viewBox={`0 0 ${width} ${size.curve}`} aria-hidden="true">
            {branches.map((branch, index) => {
              const x = columnCentre(index)
              const h = size.curve
              return (
                <path
                  key={branch.id}
                  d={`M ${centre} 0 C ${centre} ${h * 0.62}, ${x} ${h * 0.38}, ${x} ${h}`}
                  stroke={branchStyle(branch.color)['--branch']}
                />
              )
            })}
            <circle cx={centre} cy={3} r={4.5} />
          </svg>

          <ol className="rm-columns" style={{ gap: size.gap, paddingInline: offset }}>
            {branches.map((branch) => (
              <li key={branch.id} className="rm-column" style={{ width: size.column, ...branchStyle(branch.color) }}>
                <h3 className="rm-branch">{branch.name}</h3>
                {branch.nodes.length === 0 ? (
                  <p className="rm-branch-empty">Steps will be added soon.</p>
                ) : (
                  <ol className="rm-steps">
                    {branch.nodes.map((node, index) => {
                      const active = node.id === selectedId
                      return (
                        <li key={node.id} className="rm-step">
                          <span className="rm-line" aria-hidden="true" />
                          <button
                            type="button"
                            ref={(element) => {
                              nodeRefs.current[node.id] = element
                            }}
                            data-node-id={node.id}
                            className={`rm-node ${active ? 'is-active' : ''}`}
                            aria-expanded={active}
                            aria-controls={active ? 'rm-detail' : undefined}
                            onClick={() => select(node.id)}
                          >
                            <span className="rm-dot" aria-hidden="true" />
                            <span className="rm-label">
                              <span className="sr-only">
                                {branch.name}, step {index + 1} of {branch.nodes.length}:{' '}
                              </span>
                              {node.title}
                            </span>
                          </button>
                        </li>
                      )
                    })}
                  </ol>
                )}
              </li>
            ))}
          </ol>
        </div>
      </div>

      {selectedNode && (
        <DetailCard
          nodeId={selectedNode.id}
          sheet={sheet}
          cardRef={cardRef}
          titleId={titleId}
          style={branchStyle(selectedBranch.color)}
          onClose={() => close(true)}
        >
          <NodeDetail branch={selectedBranch} node={selectedNode} titleId={titleId} />
        </DetailCard>
      )}
    </div>
  )
}
