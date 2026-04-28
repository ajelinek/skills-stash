# Context And State Sharing

Use SolidJS `createContext` and `useContext` when reactive state needs to be
shared across a component subtree without prop drilling. Prefer context over
global module-level signals when the state is scoped to a provider boundary.

---

## When To Use Context

- Multiple components in a subtree need the same reactive state.
- Prop drilling is becoming deep (more than two levels).
- The shared state has a natural provider boundary (e.g., auth, theme, cart).

When the state is truly global and singleton, a module-level signal or store
is simpler. Use context when scoping and testability matter.

---

## Pattern: Typed Context With A Safe Accessor

Always wrap `useContext` in a custom function that throws a helpful error when
the provider is missing. This also narrows the TypeScript type so consumers
never see `undefined`.

```ts
// context/counter.ts
import { createContext, useContext } from 'solid-js'
import { createStore } from 'solid-js/store'

type CounterState = {
  count: number
  increment: () => void
  decrement: () => void
}

const CounterContext = createContext<CounterState>()

export function CounterProvider(props: { children: JSX.Element }) {
  const [state, setState] = createStore({ count: 0 })
  const counter: CounterState = {
    get count() { return state.count },
    increment: () => setState('count', (c) => c + 1),
    decrement: () => setState('count', (c) => c - 1),
  }
  return (
    <CounterContext.Provider value={counter}>
      {props.children}
    </CounterContext.Provider>
  )
}

export function useCounter(): CounterState {
  const ctx = useContext(CounterContext)
  if (!ctx) throw new Error('useCounter must be used inside <CounterProvider>')
  return ctx
}
```

---

## Consuming Context

```tsx
import { useCounter } from '@/context/counter'

export const CountDisplay: Component = () => {
  const counter = useCounter()
  return (
    <div>
      <p>{counter.count}</p>
      <button type="button" onClick={counter.increment}>+</button>
      <button type="button" onClick={counter.decrement}>−</button>
    </div>
  )
}
```

---

## Multiple Providers

Wrap providers at the closest common ancestor. Nest them in the app root when
the context is app-wide.

```tsx
// App root
<AuthProvider>
  <ThemeProvider>
    <Router>
      <Routes />
    </Router>
  </ThemeProvider>
</AuthProvider>
```

Use `solid-primitives`' `<MultiProvider>` for more concise nesting when you
have many providers.

---

## Passing Signals Into Context

You can pass a signal tuple through context when consumers need to both read
and update the value:

```ts
type ThemeContextValue = [
  Accessor<'light' | 'dark'>,
  Setter<'light' | 'dark'>,
]

const ThemeContext = createContext<ThemeContextValue>()

export function ThemeProvider(props: { children: JSX.Element }) {
  const [theme, setTheme] = createSignal<'light' | 'dark'>('light')
  return (
    <ThemeContext.Provider value={[theme, setTheme]}>
      {props.children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used inside <ThemeProvider>')
  return ctx
}
```

---

## Testing Components With Context

Use the `wrapper` option in `@solidjs/testing-library` to inject the provider:

```tsx
import { render } from '@solidjs/testing-library'
import { CounterProvider } from '@/context/counter'
import { CountDisplay } from './CountDisplay'

const wrapper = (props: { children: JSX.Element }) => (
  <CounterProvider>{props.children}</CounterProvider>
)

it('shows initial count', () => {
  const { getByText } = render(() => <CountDisplay />, { wrapper })
  expect(getByText('0')).toBeInTheDocument()
})
```

---

## Anti-Patterns

- Using context for state that only one component needs — use local signals.
- Forgetting the safe accessor wrapper — raw `useContext` returns `undefined`
  when the provider is missing, which produces confusing runtime errors.
- Passing derived values instead of reactive sources into context — the consumer
  loses fine-grained reactivity; pass signals or store references instead.
- Updating context state directly inside a `createEffect` without tracking the
  source — creates circular reactive dependencies.

## See Also

- `./state-and-data.md`
- `./component-structure.md`
