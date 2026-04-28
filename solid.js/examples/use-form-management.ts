import equal from 'fast-deep-equal'
import { batch, createMemo } from 'solid-js'
import { createStore, unwrap } from 'solid-js/store'

/**
 * Shared form hook for SolidJS.
 *
 * Uses createStore internally so reading form.state.fieldName inside JSX is
 * automatically reactive. Never destructure form.state — access fields as
 * form.state.fieldName to preserve reactivity.
 *
 * onChange reads e.currentTarget.name and path-sets into store state.
 * Supports dot-notation for nested field paths (e.g. "address.city").
 *
 * For fields without a name attribute (rich text, custom selects), use setField.
 *
 * Validation lives in the service layer. The submit callback receives the
 * unwrapped (plain JS) copy of the state and calls the service operation.
 */
export default function useFormManagement<Data>(
  initialState: Data,
  formSubmitCb: (data: Data) => void | Promise<void> = defaultFormSubmit,
) {
  const [store, setStore] = createStore({
    initial: deepCopy(initialState),
    state: deepCopy(initialState),
  } as { initial: Data; state: Data })

  /** True when current state differs from initial state. */
  const isDirty = createMemo(() => !equal(store.state, store.initial))

  /**
   * Path-sets into store state using the input's name attribute.
   * Supports dot-notation: name="address.city" updates store.state.address.city.
   */
  function onChange(e: { currentTarget: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement }) {
    const paths = e.currentTarget.name.split('.')
    const value = e.currentTarget.value
    // @ts-expect-error — SolidJS store path-setting with spread
    setStore('state', ...paths, value)
  }

  /** Prevents default form submission and calls the submit callback. */
  function onSubmit(e: SubmitEvent) {
    e.preventDefault()
    const plain = unwrap(store.state)
    return formSubmitCb(plain)
  }

  /** Merges a partial update into current state. */
  function updateState(updatedData: Partial<Data>) {
    const newState = { ...store.state, ...updatedData }
    setStore('state', deepCopy(newState) as any)
    return newState as Data
  }

  /** Resets current state back to original initial state. */
  function resetFormToInitialState() {
    setStore('state', store.initial as any)
  }

  /**
   * Replaces both initial and current state with a new baseline.
   * Use after a successful save when the saved data becomes the new reference.
   */
  function resetFormToNew(state: Data) {
    const copied = deepCopy(state)
    batch(() => {
      setStore('initial', copied as any)
      setStore('state', copied as any)
    })
  }

  /** Sets a single top-level field by key. */
  function setField<K extends keyof Data>(key: K, value: Data[K]) {
    setStore('state', key as any, value as any)
  }

  return {
    state: store.state,
    isDirty,
    onChange,
    onSubmit,
    updateState,
    resetFormToInitialState,
    resetFormToNew,
    setField,
  }
}

function deepCopy<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function defaultFormSubmit<T>(_data: T): never {
  throw new Error('No formSubmitCb was provided to useFormManagement')
}
