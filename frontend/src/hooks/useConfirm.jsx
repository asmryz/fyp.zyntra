import { useCallback, useState } from 'react'
import Dialog from '../components/ui/Dialog'

/**
 * Ask the user to confirm a destructive action.
 *
 *   const [confirm, confirmDialog] = useConfirm()
 *   if (await confirm({ title: 'Delete?', message: '...' })) { ... }
 *   return <>{...}{confirmDialog}</>
 */
export function useConfirm() {
  const [request, setRequest] = useState(null)

  const confirm = useCallback(
    (options) =>
      new Promise((resolve) => {
        setRequest({ ...options, resolve })
      }),
    [],
  )

  const finish = (answer) => {
    request?.resolve(answer)
    setRequest(null)
  }

  const confirmDialog = (
    <Dialog
      open={Boolean(request)}
      onClose={() => finish(false)}
      title={request?.title || 'Are you sure?'}
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={() => finish(false)}>
            Cancel
          </button>
          <button type="button" className="btn btn-danger" onClick={() => finish(true)}>
            {request?.confirmLabel || 'Delete'}
          </button>
        </>
      }
    >
      <p>{request?.message}</p>
    </Dialog>
  )

  return [confirm, confirmDialog]
}
