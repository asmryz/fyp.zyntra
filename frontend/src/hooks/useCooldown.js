import { useCallback, useEffect, useState } from 'react'

/**
 * Countdown used for "Resend code" buttons. The backend enforces the real
 * limit; this only shows the user how long to wait.
 */
export function useCooldown(initialSeconds = 0) {
  const [remaining, setRemaining] = useState(initialSeconds)

  useEffect(() => {
    if (remaining <= 0) return undefined
    const timer = setTimeout(() => setRemaining((value) => value - 1), 1000)
    return () => clearTimeout(timer)
  }, [remaining])

  const start = useCallback((seconds) => setRemaining(seconds), [])
  return [remaining, start]
}
