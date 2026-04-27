# E2E Testing with Playwright

## Mandatory File Structure

All E2E tests must follow this exact layout:

```
tests/
├── spec/                    ← ALL test files live here
│   ├── auth/
│   │   ├── login.spec.ts
│   │   └── logout.spec.ts
│   ├── dashboard/
│   │   └── navigation.spec.ts
│   └── services/
│       └── management.spec.ts
└── page-objects/            ← ALL locators and interactions live here
    ├── LoginPage.ts
    ├── DashboardPage.ts
    └── ServicesPage.ts
```

Rules that are not optional:
- Every test file ends with `.spec.ts`
- Every test file lives under `tests/spec/`
- No locators anywhere in spec files — they all belong in page objects
- No direct page interactions in spec files — use page objects only

## Test Setup Pattern

```typescript
import { test, expect } from '@e2e/fixtures'
import { apiBasedLogin } from '@e2e/utils/authentication'
import { DashboardPage } from '../../page-objects/DashboardPage'

async function setUp(page: Page, ctx: TestContext, testData: DataGenObject = {}) {
  const baseData = {
    orgs: [{ _id: 'O1' }],
    users: [{ _id: 'U1', orgId: 'O1' }],
    userDetails: [{ _id: 'U1' }],
  }

  const { selector, authUser } = await ctx.setupEnv(baseData, testData, page, 'U1', apiBasedLogin)
  const dashboardPage = new DashboardPage(page)

  return { dashboardPage, authUser, selector }
}
```

The `ctx` fixture is provided by the Playwright fixtures file. Never call
`TestContext.create()` directly in a spec file.

For tests that do not require authentication, omit the `page`, auth shorthand,
and login function arguments from `ctx.setupEnv()`.

## Tagging System

Every test must include at least one feature tag, one test type tag, and a
unique `@TS#` identifier at the end of its description string.

### Feature Tags (choose one or more)

| Tag | Use for |
| --- | --- |
| `@auth` | Authentication and authorization flows |
| `@dashboard` | Dashboard display and navigation |
| `@service-management` | Service creation, editing, deletion |
| `@service-entry` | Service entry form and validation |
| `@targets` | Target display and progress tracking |
| `@user-groups` | User group management and switching |
| `@user-settings` | User account settings and preferences |
| `@navigation` | Page navigation and routing |
| `@services` | Services listing and filtering |
| `@sponsors` | Sponsor display and rotation |

### Test Type Tags (choose one)

| Tag | Use for |
| --- | --- |
| `@happyPath` | Standard user workflow testing |
| `@errorPath` | Error handling and edge cases |
| `@integration` | Cross-component integration testing |
| `@list` | List display and data presentation |
| `@filter` | Filtering and search functionality |
| `@create` | Creation functionality |
| `@edit` | Editing functionality |
| `@delete` | Deletion functionality |
| `@empty-state` | Empty state handling |
| `@email` | Tests that send or validate emails |

### Tagging Examples

```typescript
test('should login and view dashboard @auth @happyPath @TS1')
test('should create service and send notification @service-management @create @email @TS2')
test('should handle invalid credentials @auth @errorPath @TS3')
test('should display empty service list @services @empty-state @TS4')
```

Tag placement rules:
- Tags always go at the end of the test description string
- Include `@TS#` with a unique sequential number
- Add `@email` to any test that sends real emails or calls email service APIs

## Core Rules

- **No `describe` blocks** — keep spec files flat; split by feature into separate files
- **No `beforeEach` for setup** — call `setUp()` inside each test
- **No `page.waitForTimeout()`** — never use hardcoded waits
- **No fragile selectors** — CSS classes, IDs, and complex selectors break silently
- **No conditional logic** — each test proves one specific path
- **No mocks** — test against real services and real data
- **Viewport testing** — only test different viewports when functionality actually
  differs, not for visual-only changes

## Assertions in Spec Files

Single-line assertions belong in the spec file, using locators exposed by the
page object (not raw `page.locator()` calls):

```typescript
test('should show user name after login @auth @happyPath @TS5', async ({ page, ctx }) => {
  const { dashboardPage, authUser } = await setUp(page, ctx)

  await dashboardPage.navigateTo()

  // Single-line assertions go directly in the test
  await expect(page.getByText(authUser.firstName)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
})
```

Multi-step reusable assertions (verifying several elements together across
multiple tests) belong in page object methods with `@step` decorators.

## See Also

- `./page-object-model.md` — Page Object Pattern, `@step` decorators, selector rules
- `./test-context-system.md` — TestContext fixture, shorthand IDs, `setupEnv()` usage
- `./examples/e2e-test.spec.ts` — complete copyable spec file
- `./examples/page-object.ts` — complete copyable page object
