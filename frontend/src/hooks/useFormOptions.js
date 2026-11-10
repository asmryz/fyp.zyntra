import { useEffect, useState } from 'react'
import { api } from '../services/api'

// The lists (qualifications, modules, node types...) are defined once in the
// backend (app/constants.py). They are loaded once and shared by every form.
let cachedOptions = null
let loadingPromise = null

export function useFormOptions() {
  const [options, setOptions] = useState(cachedOptions)

  useEffect(() => {
    if (cachedOptions) return
    if (!loadingPromise) {
      loadingPromise = api.get('/api/public/form-options').then((data) => {
        cachedOptions = data
        return data
      })
    }
    loadingPromise.then(setOptions).catch(() => {
      loadingPromise = null
    })
  }, [])

  return options
}
