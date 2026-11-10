import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { useReducedMotion } from '../../hooks/useReducedMotion'
import ErrorBoundary from '../ErrorBoundary'

const Hero3D = lazy(() => import('./Hero3D'))

function supportsWebGL() {
  try {
    const canvas = document.createElement('canvas')
    return Boolean(window.WebGLRenderingContext && (canvas.getContext('webgl2') || canvas.getContext('webgl')))
  } catch {
    return false
  }
}

/**
 * CSS version of the heading: shown while three.js loads, when WebGL is
 * unavailable, and for users who prefer reduced motion.
 */
function HeroWordFallback() {
  return (
    <div className="hero-word-fallback" aria-hidden="true">
      ZYNTRA
    </div>
  )
}

export default function HeroLogo() {
  const reducedMotion = useReducedMotion()
  const [hasWebGL] = useState(supportsWebGL)
  const [onScreen, setOnScreen] = useState(true)
  const wrapperRef = useRef(null)

  // Pause the animation while the hero is scrolled out of view
  useEffect(() => {
    const element = wrapperRef.current
    if (!element || !('IntersectionObserver' in window)) return undefined
    const observer = new IntersectionObserver(([entry]) => setOnScreen(entry.isIntersecting))
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  const fallback = <HeroWordFallback />
  const use3D = hasWebGL && !reducedMotion

  return (
    <div ref={wrapperRef} className="hero-logo" role="img" aria-label="ZYNTRA">
      {use3D ? (
        <ErrorBoundary fallback={fallback}>
          <Suspense fallback={fallback}>
            <Hero3D animate={onScreen} />
          </Suspense>
        </ErrorBoundary>
      ) : (
        fallback
      )}
    </div>
  )
}
