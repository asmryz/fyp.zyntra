import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'

/**
 * Load data from a GET endpoint.
 * Returns { data, error, loading, reload, setData }.
 * Pass null as the path to skip loading.
 *
 * While reloading, the previous data stays visible so the page does not flash.
 */
export function useApi(path) {
  const [reloadCount, setReloadCount] = useState(0)
  const [result, setResult] = useState({ requestKey: null, data: null, error: null })
  const requestKey = path ? `${path}#${reloadCount}` : null

  useEffect(() => {
    if (!path) return undefined
    let cancelled = false
    api
      .get(path)
      .then((data) => {
        if (!cancelled) setResult({ requestKey, data, error: null })
      })
      .catch((error) => {
        if (!cancelled) setResult((previous) => ({ requestKey, data: previous.data, error }))
      })
    return () => {
      cancelled = true
    }
  }, [path, requestKey])

  const reload = useCallback(() => setReloadCount((count) => count + 1), [])

  const setData = useCallback((updater) => {
    setResult((previous) => ({
      ...previous,
      data: typeof updater === 'function' ? updater(previous.data) : updater,
    }))
  }, [])

  const finished = result.requestKey === requestKey
  return {
    data: result.data,
    error: finished ? result.error : null,
    loading: Boolean(path) && !finished,
    reload,
    setData,
  }
}
