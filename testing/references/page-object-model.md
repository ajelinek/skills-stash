# Page Object Model

## Purpose

Page objects isolate all knowledge of how to interact with a page from the
test logic that decides what to verify. Spec files describe behavior; page
objects describe mechanics.

This separation means that when the UI changes, only the page object changes —
not every test that uses it.

## Structure Order

Every page object must follow this exact order:

1. **Selectors** — private lazy getters at the top
2. **Action Functions** — methods that perform operations
3. **Assertion Functions** — methods that verify state (multi-step only)

## Selectors

All locators are private arrow function properties on the class. They are
never returned from methods and never appear in spec files.

```typescript
class LoginPage {
  constructor(private page: Page) {}

  // Form fields
  private usernameInput = () => this.page.getByLabel('Username')
  private passwordInput = () => this.page.getByLabel('Password')

  // Buttons
  private submitButton = () => this.page.getByRole('button', { name: 'Sign in' })
  private cancelButton = () => this.page.getByRole('button', { name: 'Cancel' })

  // Links
  private forgotPasswordLink = () => this.page.getByRole('link', { name: 'Forgot password' })
}
```

### Selector Priority Order (mandatory)

Use selectors in this order of preference. Only move to the next when the
previous genuinely does not apply to the element.

1. `getByRole()` — best for interactive elements; matches accessibility semantics
2. `getByLabel()` — for form inputs with associated labels
3. `getByText()` — for text content and link text
4. `getByPlaceholder()` — for inputs identified only by placeholder
5. `getByAltText()` — for images
6. `getByTitle()` — for elements with title attributes
7. `getByTestId()` — **last resort only**; requires `data-testid` on the element;
   ask before adding a `data-testid` to production code

### Parameterized Selectors

For dynamic elements, parameterize the locator function:

```typescript
private deleteButton = (itemName: string) =>
  this.page.getByRole('button', { name: `Delete ${itemName}` })

private editButton = (itemName: string) =>
  this.page.getByRole('button', { name: `Edit ${itemName}` })
```

## Action Functions

Action methods perform operations on the page. They must:
- Use `@step` decorators
- Not return locators
- Not contain conditional logic
- Not use explicit waits

```typescript
@step('Navigate to login page')
async navigateTo() {
  await this.page.goto('/login')
}

@step('Fill username with {username}')
async fillUsername(username: string) {
  await this.usernameInput().fill(username)
}

@step('Click sign in button')
async clickSignIn() {
  await this.submitButton().click()
}

@step('Delete item {itemName}')
async deleteItem(itemName: string) {
  await this.deleteButton(itemName).click()
}
```

## Assertion Functions

Put multi-step assertions in page object methods **only when**:
- The assertion involves multiple `expect()` calls, and
- That combination is reused across multiple tests

Single-line assertions always go directly in the spec file.

```typescript
// Multi-step assertion: belongs in page object
@step('Verify login form is visible')
async verifyLoginFormVisible() {
  await expect(this.usernameInput()).toBeVisible()
  await expect(this.passwordInput()).toBeVisible()
  await expect(this.submitButton()).toBeVisible()
}

// Single-line assertion: goes in the spec file, NOT the page object
// await expect(loginPage.submitButton()).toBeVisible()  ← do not do this
```

## Step Decorator Setup

```typescript
// utils/step.ts
export { step } from '@cerios/playwright-step-decorator'
```

In `tsconfig.json`:
```json
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  }
}
```

Import and use:
```typescript
import { step } from '../../utils/step'

class MyPage {
  @step('Perform action')
  async someAction() { ... }
}
```

## Complete Page Object Template

```typescript
import { Page, expect } from '@playwright/test'
import { step } from '../../utils/step'

export class DashboardPage {
  constructor(private page: Page) {}

  // ── Selectors ────────────────────────────────────────────────────────────

  private userMenuButton = () => this.page.getByRole('button', { name: 'User menu' })
  private signOutLink = () => this.page.getByRole('link', { name: 'Sign out' })
  private pageHeading = () => this.page.getByRole('heading', { name: 'Dashboard' })
  private createServiceButton = () => this.page.getByRole('button', { name: 'Create service' })

  private serviceRow = (serviceName: string) =>
    this.page.getByRole('row', { name: serviceName })

  // ── Actions ──────────────────────────────────────────────────────────────

  @step('Navigate to dashboard')
  async navigateTo() {
    await this.page.goto('/dashboard')
  }

  @step('Open user menu')
  async openUserMenu() {
    await this.userMenuButton().click()
  }

  @step('Sign out')
  async signOut() {
    await this.openUserMenu()
    await this.signOutLink().click()
  }

  @step('Click create service')
  async clickCreateService() {
    await this.createServiceButton().click()
  }

  // ── Assertions ───────────────────────────────────────────────────────────

  @step('Verify dashboard is loaded')
  async verifyLoaded() {
    await expect(this.pageHeading()).toBeVisible()
    await expect(this.createServiceButton()).toBeVisible()
  }

  @step('Verify service row exists for {serviceName}')
  async verifyServiceRow(serviceName: string) {
    await expect(this.serviceRow(serviceName)).toBeVisible()
  }
}
```

## Forbidden Patterns

- No conditional statements (`if`, `switch`, ternary) in page objects
- No `page.waitForTimeout()` or `page.waitForSelector()` anywhere
- No locators returned from methods — actions perform operations, not expose handles
- No `data-testid` selectors without first exhausting the role/label/text options
- No mixing of Selectors → Actions → Assertions order

## See Also

- `./examples/page-object.ts` — complete copyable page object with all sections
- `./e2e-playwright.md` — E2E test file structure and tagging
