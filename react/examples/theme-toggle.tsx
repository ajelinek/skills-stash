/**
 * House-style theme toggle example.
 *
 * Expects theme files that map CSS custom properties through
 * `document.documentElement.dataset.theme`.
 */

import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

function initTheme(): Theme {
  const savedTheme = window.localStorage.getItem('theme')
  const nextTheme = savedTheme === 'dark' || savedTheme === 'light' ? savedTheme : 'light'
  document.documentElement.setAttribute('data-theme', nextTheme)
  return nextTheme
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>('light')

  useEffect(() => {
    setTheme(initTheme())
  }, [])

  function toggleTheme() {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', newTheme)
    window.localStorage.setItem('theme', newTheme)
    setTheme(newTheme)
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
    >
      Theme: {theme}
    </button>
  )
}
