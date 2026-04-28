# Testing SolidJS Code

For full testing philosophy, Playwright E2E patterns, TestContext system, and
test data generation, see the `testing` standalone skill.

This reference covers only the SolidJS-specific mechanics for unit-level
component and hook tests.

---

## Preference Order

1. **E2E tests with Playwright** — prefer for user-facing behavior.
2. **Unit tests for stores and hooks** — when behavior is complex enough to
   warrant isolation.
3. **Component tests** — only for reusable foundational primitives. Avoid for
   page or feature components.

---

## Setup

Install dependencies:

```sh
pnpm add -D vitest jsdom @solidjs/testing-library @testing-library/user-event @testing-library/jest-dom
```

In `vitest.config.ts`:

```ts
import solid from 'vite-plugin-solid'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [solid()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
  resolve: {
    conditions: ['development', 'browser'],
  },
})
```

Add `@testing-library/jest-dom` types to `tsconfig.json`:

```json
{
  "compilerOptions": {
    "jsx": "preserve",
    "jsxImportSource": "solid-js",
    "types": ["vite/client", "@testing-library/jest-dom"]
  }
}
```

Note: the official package is `@solidjs/testing-library` (not `@testing-library/solid`).
`vite-plugin-solid` automatically loads `@testing-library/jest-dom` if present.

---

## Component Tests

Use Vitest as the test runner and `@solidjs/testing-library` for rendering.

- Co-locate test files as `ComponentName.test.tsx` alongside the component.
- Use a flat structure — no nested `describe` blocks.
- `render()` requires a function returning JSX: `render(() => <Component />)`.
- Solid Testing Library handles cleanup automatically after each test.
- Query by role, label, or text — not by test IDs.
- Use `userEvent` over `fireEvent` for simulating interactions.

```tsx
import { render, screen } from '@solidjs/testing-library'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'

const user = userEvent.setup()

it('calls onClick when clicked', async () => {
  const handleClick = vi.fn()
  render(() => <Button onClick={handleClick}>Save</Button>)
  await user.click(screen.getByRole('button', { name: /save/i }))
  expect(handleClick).toHaveBeenCalledOnce()
})
```

### Testing Portal content

Components using `<Portal>` break out of the render container. Query them
with `screen` rather than the returned container:

```tsx
import { render, screen } from '@solidjs/testing-library'
import { Modal } from './Modal'

it('renders modal content through Portal', () => {
  render(() => <Modal isOpen title="Confirm"><p>Are you sure?</p></Modal>)
  expect(screen.getByRole('dialog')).toBeInTheDocument()
  expect(screen.getByText('Are you sure?')).toBeInTheDocument()
})
```

### Testing with context

Wrap the component using the `wrapper` option when it depends on a provider:

```tsx
import { render } from '@solidjs/testing-library'
import { MyProvider } from './MyProvider'
import { MyConsumer } from './MyConsumer'

const wrapper = (props: { children: JSX.Element }) => (
  <MyProvider value="test-value">{props.children}</MyProvider>
)

it('reads value from context', () => {
  const { getByText } = render(() => <MyConsumer />, { wrapper })
  expect(getByText('test-value')).toBeInTheDocument()
})
```

---

## Hook / Primitive Tests

Use `renderHook` from `@solidjs/testing-library`.

```tsx
import { renderHook, act } from '@solidjs/testing-library'
import useFormManagement from './useFormManagement'

it('tracks dirty state after a field change', () => {
  const { result } = renderHook(() =>
    useFormManagement({ title: '' }, vi.fn()),
  )
  expect(result.isDirty()).toBe(false)
  act(() => result.setField('title', 'New title'))
  expect(result.isDirty()).toBe(true)
})
```

---

## Effect Tests

Use `testEffect` from `@solidjs/testing-library` for async effect assertions.
The function receives a `done` callback; the test resolves when `done()` is called.

```tsx
import { createSignal } from 'solid-js'
import { testEffect } from '@solidjs/testing-library'

it('effect runs when signal changes', () =>
  testEffect((done) => {
    const [value, setValue] = createSignal(0)
    createEffect((run: number = 0) => {
      if (run === 0) {
        expect(value()).toBe(0)
        setValue(1)
      } else {
        expect(value()).toBe(1)
        done()
      }
      return run + 1
    })
  }),
)
```

---

## Directive Tests

Use `renderDirective` from `@solidjs/testing-library` for testing custom
directives without spinning up a full component:

```tsx
import { renderDirective } from '@solidjs/testing-library'
import { myDirective } from './myDirective'

it('applies directive behavior', () => {
  const { container } = renderDirective(myDirective, { initialValue: true })
  expect(container.firstChild).toHaveAttribute('data-active', 'true')
})
```

---

## Mocking

- Use Mock Service Worker (MSW) for API-level mocks in integration tests.
- Mock repository functions directly in unit tests for service logic.
- When using fake timers, pass `advanceTimers` to `userEvent.setup`:

```ts
const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
vi.useFakeTimers()
```

- Never mock SolidJS primitives themselves.

---

## What Not To Test Here

- Full user journeys — use Playwright E2E instead.
- Implementation internals of signals or store internals.
- Pages that are thin shells composed from already-tested primitives and hooks.
