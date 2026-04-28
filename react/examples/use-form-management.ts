/**
 * House-style shared form hook example.
 *
 * Use this for controlled forms backed by services or store validation.
 */

import { useCallback, useMemo, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import equal from 'fast-deep-equal'

type FormElement = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement

export type UseFormManagementReturn<TData, TSubmitReturn = void> = {
  state: TData
  isDirty: boolean
  onChange: (e: ChangeEvent<FormElement>) => void
  onSubmit: (e: FormEvent<HTMLFormElement>) => TSubmitReturn
  updateState: (updatedData: Partial<TData>) => TData
  resetFormToInitialState: () => void
  resetFormToNew: (next: TData) => void
}

export function useFormManagement<TData, TSubmitReturn = void>(
  initialState: TData,
  formSubmitCb: (data: TData) => TSubmitReturn,
): UseFormManagementReturn<TData, TSubmitReturn> {
  const initialRef = useRef<TData>(structuredClone(initialState))
  const [state, setState] = useState<TData>(structuredClone(initialState))

  const isDirty = useMemo(() => !equal(state, initialRef.current), [state])

  const onChange = useCallback((e: ChangeEvent<FormElement>) => {
    const { checked, name, type, value } = e.currentTarget as HTMLInputElement
    const paths = name.split('.')
    setState((prev) => setDeep(prev, paths, type === 'checkbox' ? checked : value))
  }, [])

  const onSubmit = useCallback(
    (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      return formSubmitCb(state)
    },
    [state, formSubmitCb],
  )

  const updateState = useCallback(
    (updatedData: Partial<TData>) => {
      const newState = { ...(state as object), ...(updatedData as object) } as TData
      setState(newState)
      return newState
    },
    [state],
  )

  const resetFormToInitialState = useCallback(() => {
    setState(initialRef.current)
  }, [])

  const resetFormToNew = useCallback((next: TData) => {
    initialRef.current = next
    setState(next)
  }, [])

  return {
    state,
    isDirty,
    onChange,
    onSubmit,
    updateState,
    resetFormToInitialState,
    resetFormToNew,
  }
}

function setDeep<T>(object: T, path: string[], value: unknown): T {
  const clone = structuredClone(object) as Record<string, unknown>
  let cursor: Record<string, unknown> = clone

  for (let i = 0; i < path.length - 1; i += 1) {
    const key = path[i]
    cursor[key] = typeof cursor[key] === 'object' && cursor[key] !== null ? cursor[key] : {}
    cursor = cursor[key] as Record<string, unknown>
  }

  cursor[path[path.length - 1]] = value
  return clone as T
}
