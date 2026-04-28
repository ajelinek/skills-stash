# Component Structure

## Preferred Pattern

Use this default component shape and keep pages thin.

## File Structure

```text
PascalCase/
├── index.tsx
└── styles.module.css
```

For foundational components, place them under `components/foundation/`.
For interactive SolidJS components used in Astro, place them under
`components/dynamic/`.

## Component Definition

- The main component file is `index.tsx`.
- Type props with an explicit interface or type alias.
- Access props as `props.foo` — never destructure props; SolidJS props are
  reactive getters and destructuring breaks reactivity.
- Use `Component<Props>` from `solid-js` for simple components.
- Prefer named exports for foundational components.
- Default exports are acceptable for page-level or dynamic feature components.
- Use `splitProps` when a component spreads native attributes to avoid passing
  custom props through to the DOM element.
- Use `mergeProps` to apply prop defaults without destructuring.

Basic pattern:

```tsx
import type { Component } from 'solid-js'
import styles from './styles.module.css'

type ExampleProps = {
  title: string
  subtitle?: string
}

export const Example: Component<ExampleProps> = (props) => {
  return (
    <div class={styles.container}>
      <h2>{props.title}</h2>
      {props.subtitle && <p>{props.subtitle}</p>}
    </div>
  )
}
```

Pattern with `splitProps` (for components that spread native HTML attributes):

```tsx
import { splitProps, mergeProps } from 'solid-js'
import type { Component, JSX } from 'solid-js'

type ButtonProps = JSX.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary'
}

export const Button: Component<ButtonProps> = (rawProps) => {
  // Apply defaults without destructuring
  const props = mergeProps({ variant: 'primary', type: 'button' } as ButtonProps, rawProps)
  // Separate custom props from native HTML attributes before spreading
  const [local, rest] = splitProps(props, ['variant', 'class'])
  return (
    <button
      {...rest}
      class={`${styles[local.variant!]} ${local.class ?? ''}`}
    />
  )
}
```

## SolidJS Control Flow

Prefer SolidJS built-in control flow components over inline JS patterns:

- `<Show when={condition}>` — conditional rendering instead of `&&` or ternary.
- `<For each={list}>` — list rendering instead of `.map()`.
- `<Switch>` / `<Match when={condition}>` — multi-branch conditionals.
- `<Index each={list}>` — list rendering when index stability matters more than
  item identity (e.g., primitive value lists).
- `<Dynamic component={tag}>` — render a variable component or HTML tag.
- `<Portal>` — render outside the current DOM tree for modals and overlays.
- `<Suspense>` — boundary for lazy-loaded or `createResource`-backed async content.
- `<ErrorBoundary>` — catches errors thrown during rendering and shows a fallback.

```tsx
// Conditional rendering
<Show when={props.isVisible}>
  <Content />
</Show>

// Fallback content
<Show when={data()} fallback={<Loading />}>
  <Content data={data()!} />
</Show>

// List rendering
<For each={items()}>
  {(item) => <ListItem item={item} />}
</For>

// Multi-branch async UI
<Switch fallback={<NotFound />}>
  <Match when={status().isProcessing}>
    <LoadingSpinner />
  </Match>
  <Match when={status().isError}>
    <ErrorMessage />
  </Match>
  <Match when={status().isSuccess}>
    <Content />
  </Match>
</Switch>

// Dynamic component — render based on a variable type
<Dynamic component={props.as ?? 'div'} class={styles.wrapper}>
  {props.children}
</Dynamic>

// Error boundary — wrap async or risky subtrees
<ErrorBoundary fallback={(err) => <p>Something went wrong: {err.message}</p>}>
  <RiskyComponent />
</ErrorBoundary>

// Suspense — show fallback while createResource resolves
<Suspense fallback={<LoadingSpinner />}>
  <DataDrivenComponent />
</Suspense>
```

## Reactivity Rules

- Use `createSignal` for simple local reactive values.
- Use `createStore` from `solid-js/store` for structured or nested state.
- Use `createMemo` for derived values that are expensive or reused in multiple
  places. Do not wrap every computed value in a memo.
- Use `createEffect` for side effects. Register cleanup with `onCleanup`.
- Use `onMount` for DOM-dependent setup (accessing the DOM after first render).
- Use `batch` from `solid-js` to group multiple signal updates without
  triggering intermediate re-renders.

```tsx
import { createSignal, createEffect, onCleanup, onMount } from 'solid-js'

const MyComponent: Component = () => {
  const [count, setCount] = createSignal(0)

  createEffect(() => {
    const id = setInterval(() => setCount(c => c + 1), 1000)
    onCleanup(() => clearInterval(id))
  })

  onMount(() => {
    // DOM is available here
  })

  return <div>{count()}</div>
}
```

## Rules

- Keep components small and single purpose.
- Leverage foundational components as building blocks.
- Use semantic HTML instead of generic wrappers when possible.
- Ensure interactive elements have accessible names.
- Keep component trees as flat as practical.
- Use variables or helpers for complex JSX logic.
- Never read a signal outside a reactive context when reactivity is needed.
- Use `createUniqueId()` from `solid-js` for stable SSR-safe IDs — prefer it over
  `nanoid()` or `Math.random()` for element IDs.

## Anti-Patterns

- Destructuring props: `const { title } = props` — breaks reactivity.
- Using `.map()` for list rendering — use `<For>` instead.
- Using `&&` or ternaries for conditional rendering — use `<Show>` instead.
- Declaring components inside other components.
- Direct DOM manipulation when SolidJS reactive state can handle it.
- Overusing `createMemo` on trivial derived values.
- Prop drilling through more than two levels — use context instead.
- Inline styles.
- Untyped props or event handlers.
- Using `nanoid()` or `Math.random()` for element IDs — use `createUniqueId()`.
- Forgetting `<ErrorBoundary>` around async or third-party subtrees that can throw.

## See Also

- `./foundational-components.md`
- `./state-and-data.md`
- `../examples/service-backed-form-page.tsx`
