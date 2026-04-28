// Counter.tsx — SolidJS island component
//
// CSS Modules work the same way in SolidJS islands as in .astro files:
// import styles from './styles.module.css' and use class={styles.name}
//
// Note: SolidJS uses `class`, not `className`.

import { createSignal } from 'solid-js'
import styles from './styles.module.css'

interface Props {
  initialCount: number
}

export default function Counter(props: Props) {
  const [count, setCount] = createSignal(props.initialCount)

  return (
    <div class={styles.counter} role="group" aria-label="Counter">
      <button
        class={styles.button}
        onClick={() => setCount((c) => c - 1)}
        aria-label="Decrease count"
      >
        −
      </button>
      <output class={styles.output} aria-live="polite" aria-atomic="true">
        {count()}
      </output>
      <button
        class={styles.button}
        onClick={() => setCount((c) => c + 1)}
        aria-label="Increase count"
      >
        +
      </button>
    </div>
  )
}
