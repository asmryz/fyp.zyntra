import { useEffect } from 'react'

export function usePageTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} | ZYNTRA` : 'ZYNTRA | SZABIST Admission Assistance'
  }, [title])
}
