import { createStore } from 'solid-js/store'
import { createEffect, onCleanup } from 'solid-js'

// ─── Types ────────────────────────────────────────────────────────────────────

export type AsyncStatus = {
  isProcessing: boolean
  isError: boolean
  isDone: boolean
  isReprocessing: boolean
  isInitial: boolean
  isSuccess: boolean
}

export type ApiError = {
  code: string
  message: string
}

export type AsyncStore<T> = {
  status: AsyncStatus
  errors: ApiError[] | null
  data: T | null
}

// ─── createAsyncStore ─────────────────────────────────────────────────────────

/**
 * Creates a reactive SolidJS store in the AsyncStore<T> shape and exposes
 * state-transition helpers. Used internally by useAsyncOperation and
 * useAsyncSubscription.
 */
export function createAsyncStore<T>(initialData: T | null = null) {
  const [state, setState] = createStore<AsyncStore<T>>({
    status: {
      isProcessing: false,
      isError: false,
      isDone: false,
      isReprocessing: false,
      isInitial: true,
      isSuccess: false,
    },
    errors: null,
    data: initialData,
  })

  function setLoading() {
    setState({
      status: {
        isProcessing: true,
        isError: false,
        isDone: false,
        isReprocessing: false,
        isInitial: false,
        isSuccess: false,
      },
    })
  }

  function setSuccess(data: T) {
    setState({
      status: {
        isProcessing: false,
        isError: false,
        isDone: true,
        isReprocessing: false,
        isInitial: false,
        isSuccess: true,
      },
      data,
      errors: null,
    })
  }

  function setErrors(errors: ApiError[]) {
    setState({
      status: {
        isProcessing: false,
        isError: true,
        isDone: true,
        isReprocessing: false,
        isInitial: false,
        isSuccess: false,
      },
      errors,
    })
  }

  function setError(code: string, message: string) {
    setErrors([{ code, message }])
  }

  function addError(code: string, message: string) {
    setState((current) => ({
      status: {
        isProcessing: false,
        isError: true,
        isDone: true,
        isReprocessing: false,
        isInitial: false,
        isSuccess: false,
      },
      errors: [...(current.errors ?? []), { code, message }],
    }))
  }

  return { state, setState, setLoading, setSuccess, setError, setErrors, addError }
}

// ─── useAsyncOperation ────────────────────────────────────────────────────────

/**
 * Wraps a one-time async operation (create, update, delete, send) in a reactive
 * AsyncStore. Returns { execute, status, errors, data }.
 *
 * execute() sets loading, calls the operation, then sets success or error.
 * Structured ApiError[] thrown by the service surface through op.errors.
 * Generic Error instances surface as a single error entry.
 *
 * Usage:
 *   const op = useAsyncOperation(async (args) => await myService(args))
 *   await op.execute(args)
 *   // In JSX: op.status.isProcessing, op.errors, op.data
 */
export function useAsyncOperation<TArgs extends any[], TReturn>(
  operation: (...args: TArgs) => Promise<TReturn>,
) {
  const { state, setLoading, setSuccess, setError, setErrors } = createAsyncStore<TReturn>()

  const execute = async (...args: TArgs): Promise<TReturn> => {
    setLoading()
    try {
      const result = await operation(...args)
      setSuccess(result)
      return result
    } catch (error) {
      if (Array.isArray(error)) {
        setErrors(error as ApiError[])
      } else if (error && typeof error === 'object' && 'code' in error && 'message' in error) {
        setError((error as ApiError).code, (error as ApiError).message)
      } else if (error instanceof Error) {
        setError('operation/failed', error.message)
      } else {
        setError('operation/unknown', 'An unknown error occurred')
      }
      throw error
    }
  }

  return {
    execute,
    get status() { return state.status },
    get errors() { return state.errors },
    get data() { return state.data },
  }
}

// ─── useAsyncSubscription ─────────────────────────────────────────────────────

/**
 * Wraps a real-time subscription in a reactive AsyncStore. Returns
 * { status, errors, data }.
 *
 * The subscription service returns { subscribe, enabled }. When enabled is
 * false, status stays isInitial. When args change, the previous subscription
 * is cleaned up and a new one is established. Cleanup also runs on unmount.
 *
 * Business logic for edge cases (e.g. handling a 'NEW' id) belongs in the
 * service layer, not here.
 *
 * Usage:
 *   const data = useAsyncSubscription<Details | null, [string]>(myService, id)
 *   // In JSX: data.status.isSuccess, data.data, data.errors
 */
export function useAsyncSubscription<T, TArgs extends any[]>(
  subscriptionService: (...args: TArgs) => {
    subscribe: (onData: (data: T) => void, onError: (error: Error) => void) => (() => void) | undefined
    enabled: boolean
  },
  ...args: TArgs
) {
  const { state, setLoading, setSuccess, setError } = createAsyncStore<T>()
  let unsubscribe: (() => void) | undefined

  createEffect(() => {
    if (unsubscribe) {
      unsubscribe()
      unsubscribe = undefined
    }

    const { subscribe, enabled } = subscriptionService(...args)

    if (!enabled) return

    setLoading()

    unsubscribe = subscribe(
      (data) => setSuccess(data),
      (error) => setError('subscription/failed', error.message),
    )

    onCleanup(() => {
      if (unsubscribe) {
        unsubscribe()
        unsubscribe = undefined
      }
    })
  })

  return {
    get status() { return state.status },
    get errors() { return state.errors },
    get data() { return state.data },
  }
}
