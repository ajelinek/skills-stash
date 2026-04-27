---
name: typescript-engineering
description: >
  Use this skill when implementing, refactoring, debugging, or reviewing
  TypeScript in applications, libraries, packages, or monorepos. Trigger on
  requests to write TypeScript, improve types, design domain models, refine
  imports and exports, tighten `tsconfig` settings, or improve narrowing and
  maintainability.
---

# TypeScript Engineering

Use this skill to produce TypeScript that is strongly typed, easy to change,
and safe under change.

Keep the top-level approach simple: work from the existing code, make the
smallest correct change, and tighten types, naming, and boundaries where they
materially improve correctness or maintenance.

The best code is the code not written. Do not add new modules, helpers,
wrappers, or abstractions by default. Favor small, well-judged edits to
existing cohesive modules when that keeps the design cleaner and avoids code
bloat.

## Workflow

### 1. Start from the real code

- Read the surrounding implementation before changing anything.
- Match established architecture unless it is clearly causing a bug,
  maintenance problem, or safety issue.
- Prefer the smallest change that fully solves the task.
- Prefer changing an existing cohesive module over adding a new file or layer
  when the change naturally belongs there.
- Remove failed or superseded approaches instead of layering partial fixes.
- Avoid speculative abstractions, compatibility code, and helper sprawl unless
  there is a concrete need.

### 2. Model important invariants in types

- Prefer `unknown` over `any` at boundaries, then narrow explicitly.
- Use the simplest type construct that fits the problem.
- All types belong in a top-level `types/` folder. Do not co-locate types inside
  domain modules, feature folders, or subfolders. Import from `types/`.
- Prefer `type` for new modeling work. Use `interface` only when you specifically
  need interface behavior such as declaration merging or class implementation
  patterns already established in the codebase.
- Favor composition over inheritance.
- Prefer discriminated unions for variant states and result types.
- Prefer narrowing and control flow over assertions.
- Treat non-null assertions as a last resort, not a default pattern.

Read `./references/type-modeling.md` when the task is mostly about domain
modeling, type design, narrowing, result types, or assertion strategy.

### 3. Keep implementation small and legible

- Give each module one clear purpose.
- Favor smaller modules over larger ones.
- Keep normal modules around 200 lines of implementation code or less.
- Once a module grows past roughly 200 lines of implementation code, stop and
  ask whether it is carrying more than one responsibility.
- If a module grows past roughly 300 lines of implementation code, split it
  unless the file is unusually cohesive, mostly declarative, or generated.
- Prefer small modules and single-purpose functions.
- Keep most functions around 20 lines of implementation code or less.
- Once a function grows past roughly 20 lines of implementation code, treat that
  as a strong sign to extract helpers or simplify control flow.
- If a function grows past roughly 30 lines of implementation code, decompose it
  unless the structure is still unusually flat and obvious.
- Use the `function` keyword for named function declarations. Do not assign
  arrow functions to `const` for named, standalone functions.
- Use `const` by default. Use `let` only when the value must be reassigned.
  Never use `var`.
- Single-level ternaries are allowed. Never nest ternaries. Extract a variable
  or helper function for anything more complex.
- Use clear names instead of abbreviations that hide intent.
- Use guard clauses to keep the main path obvious.
- Avoid nesting deeper than 2 levels.
- Never pass more than 3 parameters to a function; wrap additional values in
  an object parameter.
- Place exported/public functions at the top of a file; helpers at the bottom.
- Keep code DRY, but do not extract helpers prematurely.

Read `./references/code-shape-and-naming.md` when the task involves structure,
identifiers, exports, comments, or code organization.

### 4. Make module and config choices intentionally

- Start from `strict` unless the project has a concrete reason not to.
- Consider high-value companion flags when they improve correctness, such as
  stricter optional-property and indexed-access behavior.
- Use `import type` and `export type` when a symbol is type-only.
- Match module configuration to the runtime and build tool actually in use.
- Treat path aliases with care; they should reflect real runtime resolution, not
  just nicer-looking imports.
- Use project references when repository scale and build boundaries justify
  them, not as a default for every repo.

Read `./references/tsconfig-and-modules.md` when the task involves compiler
flags, imports and exports, module configuration, path aliases, or project
references.

## Quality Bar

- The change follows the existing architecture or intentionally improves it.
- All types are in the `types/` folder, not scattered across domain modules.
- Types make important invariants clearer instead of adding ceremony.
- Narrowing does the real safety work instead of broad assertions.
- Naming and exports are consistent across the codebase.
- Module configuration matches how the project actually resolves imports.
- Type checking passes with the command that fits the repo structure, such as
  `tsc --noEmit` or `tsc -b`.
- Comments explain non-obvious reasoning, not obvious mechanics.
