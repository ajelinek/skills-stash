# TSConfig And Modules

Use this reference when the task involves compiler flags, imports and exports,
module configuration, build mode, or repository-scale structure.

## Compiler Defaults

- Start with `strict` unless the codebase has a concrete reason not to.
- Consider stricter companion flags where they materially improve correctness:
  - `exactOptionalPropertyTypes`
  - `noUncheckedIndexedAccess`
  - `noPropertyAccessFromIndexSignature`
  - `noImplicitOverride`
- Use `tsc --noEmit` when the repo needs a straightforward typecheck-only CI step.
- Use `tsc -b` when the repo uses project references and build mode.

## Imports And Exports

- Use `import type` and `export type` when a symbol is type-only.
- Keep exported module surfaces intentional and small.
- Avoid import tricks that make code appear valid to TypeScript but not to the
  actual runtime or build tool.

## Module Configuration

- Choose `module` and `moduleResolution` to match the runtime and build tool in
  use.
- Do not treat module settings as style preferences.
- Prefer predictable emit over accidental compatibility.
- Consider `verbatimModuleSyntax` when the project owns its compiler behavior
  and wants explicit, unsurprising import and export emit.

## Path Aliases

- Do not add `baseUrl` or `paths` just to make imports look cleaner.
- Path aliases do not rewrite emitted import paths.
- If aliases are used, they must reflect real runtime or build-tool resolution.
- Do not use `paths` to fake package resolution across a large repo when real
  workspace or package boundaries are the correct model.

## Project References

Project references are a scaling tool, not a default requirement.

Use them when the repo has:

- multiple TypeScript packages or layers
- slow typechecking caused by project size
- a real need for declaration boundaries and `tsc -b`

Skip them when a single-project `tsconfig` is simpler and sufficient.

If you do use them:

- referenced projects need `composite`
- declaration output must be enabled
- the repo should standardize on `tsc -b` workflows

## Official Guidance

- TSConfig reference: `https://www.typescriptlang.org/tsconfig/`
- Module reference: `https://www.typescriptlang.org/docs/handbook/modules/reference.html`
- Project references: `https://www.typescriptlang.org/docs/handbook/project-references.html`
- `baseUrl` guidance: `https://www.typescriptlang.org/tsconfig/#baseUrl`
- `verbatimModuleSyntax`: `https://www.typescriptlang.org/tsconfig/#verbatimModuleSyntax`
