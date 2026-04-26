type LoadState<T> =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'loaded'; value: T }
  | { kind: 'failed'; message: string }

export function renderLoadState(state: LoadState<string>) {
  switch (state.kind) {
    case 'idle':
      return 'Nothing started yet.'
    case 'loading':
      return 'Loading...'
    case 'loaded':
      return state.value
    case 'failed':
      return state.message
    default: {
      const exhaustiveCheck: never = state
      return exhaustiveCheck
    }
  }
}
