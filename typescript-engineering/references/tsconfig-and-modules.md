# tsconfig and Modules

## Compiler defaults

Start every project with `"strict": true`. Consider these high-value companion flags:

- `exactOptionalPropertyTypes` — distinguishes missing from explicitly `undefined`
- `noUncheckedIndexedAccess` — index signatures return `T | undefined`, not just `T`
- `noPropertyAccessFromIndexSignature` — forces bracket notation on index-signed types
- `noImplicitOverride` — requires `override` on subclass method overrides
- `useUnknownInCatchVariables` — catch bindings become `unknown` instead of `any`

Use `tsc --noEmit` for type-checking only, or `tsc -b` for project references build mode.

## Imports and exports

- Use `import type` for type-only imports.
- Use `export type` for type-only exports and re-exports.
- Keep exported surfaces small and intentional — export only what callers need.

```ts
import type { User } from './types'
export type { User, UserSummary }
```

## Module configuration

Match `module` and `moduleResolution` to the actual runtime and build tool in use. Do not guess or copy from another project without checking.

Consider `verbatimModuleSyntax` to enforce consistent `import type` / `export type` usage at the compiler level.

## Path aliases

Prefer setting `baseUrl` to the source root for source-root-relative imports. This avoids `../../` traversal and works cleanly with bundler-based projects.

Use `paths` selectively — only for a handful of stable cross-cutting roots. Do not use `paths` to fake package boundaries in monorepos; use proper workspaces instead.

Avoid barrel (`index.ts`) files in application code. They cause circular imports, slow dev servers, and defeat bundler tree-shaking. Barrels are appropriate only at a library's single public entry point.

Do not name source directories the same as `node_modules` packages.

## Project references

Use project references only when the repository has multiple TypeScript packages, slow type-checking warrants build boundaries, or there is a real need for declaration boundaries. Requires `composite: true`, `declaration`, and `declarationMap` per package, and a root config with `"files": []` and a `references` list. Build with `tsc -b`.

Do not use project references as a default for every repo — they add overhead that only pays off at scale.
