# Code Shape And Naming

Use this reference when the task is mostly about code structure, readability,
exports, or naming consistency.

## Code Shape

- Each module should have one clear purpose.
- Favor smaller modules over larger ones.
- Keep normal modules around 200 lines of implementation code or less.
- Once a module grows past roughly 200 lines of implementation code, stop and
  ask whether it is carrying more than one responsibility.
- Split modules above roughly 300 lines unless they are mostly declarations,
  lookup tables, generated code, or another unusually cohesive format.
- Prefer small modules and single-purpose functions.
- Most functions should fit comfortably on a screen and stay focused on one
  intention.
- Keep most functions around 20 lines of implementation code or less.
- Start simplifying or extracting once a function grows past roughly 20 lines of
  implementation code.
- Split functions above roughly 30 lines unless the structure is unusually flat
  and obvious.
- Use guard clauses to keep the happy path obvious.
- Keep code DRY, but do not extract helpers until duplication is real and the
  shared behavior is stable.
- Use object parameters when a function would otherwise need too many positional
  or optional arguments.
- Export only what needs to be shared across modules.
- Add comments only when the reasoning or invariant is not obvious from the code
  itself.

## Naming Defaults

- `camelCase` for TypeScript fields and JSON fields
- `PascalCase` for types, interfaces, classes, and enums
- Prefer entity-specific identifiers such as `userId` or `accountId` instead of
  a bare `id` outside narrow local scope
- Prefix booleans with `is`, `has`, or `can`
- Use descriptive timestamp fields such as `createdAt`, `updatedAt`, or
  `lastSyncedAt`
- Use whole words where practical instead of project-local abbreviations

## Why This Matters

The same concept should keep the same name and shape across the codebase.
Inconsistent naming creates unnecessary translation logic, avoidable review
friction, and bugs that TypeScript cannot prevent on its own.

## Good Examples

- Good identifier: `projectId`
- Good boolean: `hasWriteAccess`
- Good timestamp: `archivedAt`

## Avoid

- Generic names like `data`, `info`, or `item` when the real concept is known
- Bare `id` fields in shared or transport-facing shapes when the entity is not
  obvious
- Naming drift between related types, functions, and exports

## Engineering Notes

- Do not let line counts override cohesion, clarity, or a clearly better design.
- Prefer readability and local clarity over style dogma.
- Favor minimal comments and minimal code that still make the intent obvious.

## Why These Size Targets Exist

- Function-size guidance is stronger than file-size guidance. Multiple
  maintainability sources treat long methods as an immediate smell, while file
  size is more context-dependent.
- ESLint documents common file-size recommendations in the 100-500 line range,
  which supports using 200 lines as a strong target rather than an arbitrary
  hard law.
- ESLint's `max-lines-per-function` rule defaults to 50 lines, which is a useful
  upper-bound smell threshold, not a healthy everyday target.
- Google code review guidance treats code that cannot be understood quickly as
  too complex, and explicitly calls out 50-line methods as something that may
  need to be broken up.
- Martin Fowler argues for very small functions and treats anything beyond a few
  lines as worth questioning when intention is no longer obvious.

## Practical Interpretation

- Default target: keep normal modules around 200 lines of implementation code or
  less.
- Review modules once they move past 200 lines and split them if more than one
  purpose is emerging.
- Split modules above 300 lines unless they are mostly declarations, lookup
  tables, generated code, or another unusually cohesive format.
- Default target: keep most functions around 20 lines of implementation code or
  less.
- Review functions once they move past 20 lines and simplify them aggressively.
- Split functions above 30 lines unless the structure is unusually flat and
  obvious.

## Research Notes

- ESLint `max-lines`: `https://eslint.org/docs/latest/rules/max-lines`
- ESLint `max-lines-per-function`: `https://eslint.org/docs/latest/rules/max-lines-per-function`
- Google code review guidance: `https://google.github.io/eng-practices/review/reviewer/looking-for.html`
- Martin Fowler on function length: `https://martinfowler.com/bliki/FunctionLength.html`
- SourceMaking long method smell: `https://sourcemaking.com/refactoring/smells/long-method`
- SourceMaking large class smell: `https://sourcemaking.com/refactoring/smells/large-class`
