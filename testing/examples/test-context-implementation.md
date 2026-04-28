# TestContext System: Implementation Guide

This guide walks through building the 8-module TestContext system from scratch. Follow phases in order.

---

## Step 0: Data Model Discovery

**Before writing any code**, you need a clear data model. The rest of this
guide is template code — it cannot be filled in meaningfully until you know
your entities, their fields, their foreign keys, and their dependency order.

### Option A — The user provides a data model

Ask the user directly:

> "To build the TestContext I need your data model. Please share it — a schema
> file, an ERD, a list of tables/collections, or even a rough description of
> your entities and how they relate. If you have a `Data_Model.md`,
> `schema.prisma`, `schema.ts`, migration files, or similar, paste or point me
> to it."

Accept any of the following as input:
- A prose description of entities and relationships
- A list of types or interfaces from the codebase
- A Prisma schema, SQL DDL, or Mongoose/Firestore schema file
- A markdown data model document
- A rough diagram description

### Option B — No data model exists; analyze the codebase

If the user cannot provide one, analyze the codebase to infer it:

1. Search for type definitions, interfaces, and schema files:
   - `*.schema.ts`, `*.model.ts`, `*.entity.ts`
   - `schema.prisma`, migration files (`*.sql`)
   - Firestore collection references (`db.collection(...)`)
   - Mongoose model definitions (`mongoose.model(...)`)
   - TypeScript `type` / `interface` blocks that look like DB rows

2. Look for existing test data to understand what shape data already takes:
   - Existing `baseData` or `testData` objects in test files
   - Existing generator functions in a `generators/` directory
   - Existing fixtures or factories

3. Synthesize and present a proposed data model to the user for confirmation
   before proceeding. Do not generate code based on an unconfirmed inference.

### What to extract from the data model

Once you have the data model (from the user or inferred), extract:

| What | Why |
|---|---|
| Entity names + primary key fields | Generator function signatures, `types.ts` |
| All fields + types (required vs optional) | Generator defaults, partial types |
| Foreign key relationships | `bulkAdd` dependency order, generator validation |
| Composite-key entities | Index strategy, `mergeData` switch cases |
| Nested entities (stored separately, embedded in parent) | Stitching logic in `Scenario.build()` |
| Enum values | Generator defaults and type definitions |

### Dependency order derivation

From the foreign key map, derive insertion order:

1. Entities with **no foreign keys** — insert first
2. Entities whose FKs reference only group 1 — insert second
3. Continue until all entities are placed
4. **Composite-key / junction tables** — always last (all their references must exist)
5. **Nested entities** that are stitched into a parent — generate before the parent

Write out the derived order explicitly and confirm it with the user before
starting Phase 4 (Generators). This order must be consistent across
`Scenario.bulkAdd()`, `DatabaseAdapter.upsertGeneratedData()`, and
`DatabaseAdapter.deleteGeneratedData()` (reversed).

**Example output to share with user before proceeding**:

```
Proposed insertion order for your data model:

1. Role, Label           (no FKs; nested into Community)
2. Community             (no FKs; stitched from roles/labels)
3. Person                (no FKs)
4. Event                 (FK → Community)
5. CommunityAdmin        (composite: personId + communityId)
6. PersonEvent           (composite: personId + eventId)

Does this look right? Any entities missing?
```

Only proceed to Phase 1 once the data model and dependency order are confirmed.

---

## Architecture

```
TestContext.create(db)         ← facade; accepts DatabaseAdapter interface
  Scenario.bulkAdd(data)       ← dependency-ordered generation; uses IdProvider
  Scenario.build()             ← stitches nested entities; returns Selector
  DatabaseAdapter.upsertGeneratedData()  ← inserts to DB
  setupEnv()                   ← optional auth (Firebase only)
```

**8 Modules**:

| Module | File | Purpose |
|---|---|---|
| IdProvider | `src/test-context/IdProvider.ts` | Maps shorthand IDs (`'C1'`) → real UUIDs |
| Generators | `src/generators/[entity].ts` | Create realistic entity data via faker |
| Scenario | `src/test-context/Scenario.ts` | Orchestrates generation in dependency order |
| Selector | `src/test-context/Selector.ts` | Pre-computed indexes + relationship traversal |
| DataMerger | `src/test-context/DataMerger.ts` | Pure merge of baseData + testData |
| DatabaseAdapter | `src/database/adapter.ts` | Concrete DB writes (Firestore / Postgres / Mongo) |
| DatabaseReader | `src/test-context/DatabaseReader.ts` | DB reads via interface (NOT concrete type) |
| AuthManager | `src/test-context/AuthManager.ts` | Firebase Auth user creation + page auth |
| TestContext | `src/test-context/TestContext.ts` | Main facade coordinating all modules |

**DB-agnostic design**: `DatabaseReader` and `TestContext` accept interfaces (`DatabaseReadOperations`, `DatabaseAdapter`). Only `adapter.ts` imports concrete database types.

---

## File Structure

```
packages/test-tools/
├── package.json
├── tsconfig.json
└── src/
    ├── index.ts
    ├── generators/
    │   ├── index.ts
    │   ├── helpers.ts
    │   └── [entity].ts        ← one file per entity
    ├── test-context/
    │   ├── index.ts
    │   ├── IdProvider.ts
    │   ├── Scenario.ts
    │   ├── Selector.ts
    │   ├── TestContext.ts
    │   ├── DataMerger.ts
    │   ├── AuthManager.ts     ← Firebase only
    │   ├── DatabaseReader.ts
    │   ├── indexUtils.ts
    │   └── types.ts
    └── database/
        ├── types.ts           ← CREATE THIS FIRST
        └── adapter.ts
```

---

## Phase 1: Project Setup

At this point you have completed Step 0 — the data model is known and the
dependency order is confirmed. Use those outputs to fill in every placeholder
in the phases below. Every reference to `[entity]`, `entityId`, `parentId`,
etc. in these templates should be replaced with your actual entity names and
field names from the confirmed data model.

---

## Phase 2: Core Utilities

### IdProvider (`src/test-context/IdProvider.ts`)

```typescript
export type IdProvider = (str?: string, options?: IdProviderOptions) => string

type IdProviderOptions = {
  exact?: boolean   // resolve without creating new mapping
  log?: boolean     // debug: print the id map
  type?: 'uuid' | 'numeric'
}

export function IdProvider() {
  const idMap = new Map<string, string>()

  return function ID(str?: string, options: IdProviderOptions = {}): string {
    const { exact = false, log = false, type = 'uuid' } = options

    if (log) { console.log(idMap); return '' }

    if (str && idMap.has(str)) return idMap.get(str)!
    if (exact && str) return str

    const newId = type === 'uuid' ? generateUuid() : generateNumericId()

    if (!str) { idMap.set(newId, newId); return newId }
    if (str.length > 10) { idMap.set(str, str); return str }  // treat long strings as real IDs

    idMap.set(str, newId)
    return newId
  }
}

function generateUuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

function generateNumericId(): string {
  return Math.random().toString().slice(2, 12)
}
```

### Index Utilities (`src/test-context/indexUtils.ts`)

```typescript
export function indexByKey<T extends Record<string, unknown>>(
  array: T[] | undefined, key: string
): Record<string, T> {
  if (!array) return {}
  return array.reduce((acc, item) => ({ ...acc, [String(item[key])]: item }), {} as Record<string, T>)
}

export function indexByCompositeKey<T extends Record<string, unknown>>(
  array: T[] | undefined, keys: string[]
): Record<string, T> {
  if (!array) return {}
  return array.reduce((acc, item) => {
    const k = keys.map(k => String(item[k])).join(':')
    return { ...acc, [k]: item }
  }, {} as Record<string, T>)
}

export function groupByKey<T extends Record<string, unknown>>(
  array: T[] | undefined, key: string
): Record<string, T[]> {
  if (!array) return {}
  return array.reduce((acc, item) => {
    const k = String(item[key])
    return { ...acc, [k]: [...(acc[k] ?? []), item] }
  }, {} as Record<string, T[]>)
}
```

---

## Phase 3: Types (`src/test-context/types.ts`)

```typescript
// Match your database schema exactly
export type dbEntity = {
  entityId: string
  name: string
  description: string | null
  insertTimestamp: string
  updateTimestamp: string
}

// Partials allow shorthand IDs and optional overrides
export type EntityPartial = Partial<dbEntity>

// Full generated data structure
export type GeneratedTableArrays = {
  entities: dbEntity[]
  // ... one array per entity type
}

export type GeneratedTableArraysPartials = {
  entities?: EntityPartial[]
  // ...
}

export type DataGenObject = Partial<GeneratedTableArraysPartials>

// Firebase Auth user (Firebase projects only)
export type TestUser = {
  userId: string
  displayName: string
  email: string
  password: string
  photoURL?: string
}
```

---

## Phase 4: Database Abstraction (`src/database/types.ts`)

**Create this BEFORE the adapter.**

```typescript
import type { GeneratedTableArrays } from '../test-context/types'

export interface DatabaseReadOperations {
  readDocument<T>(collection: string, docId: string): Promise<T | null>
  readDocumentsByField<T>(collection: string, field: string, value: unknown): Promise<T[]>
  getDatabaseClient(): unknown
}

export interface DatabaseWriteOperations {
  upsertDocument(collection: string, docId: string, data: unknown): Promise<void>
  deleteDocument(collection: string, docId: string): Promise<void>
  getMaxBatchSize(): number
}

export interface DatabaseAdapter extends DatabaseReadOperations, DatabaseWriteOperations {
  upsertGeneratedData(data: GeneratedTableArrays): Promise<void>
  deleteGeneratedData(data: GeneratedTableArrays): Promise<void>
}
```

---

## Phase 5: Generators (`src/generators/[entity].ts`)

**Simple entity** (no FKs):
```typescript
export function generateEntity(
  options: EntityPartial = {},
  ID: ReturnType<typeof IdProvider> = IdProvider()
): dbEntity {
  return {
    entityId: ID(options.entityId),
    name: options.name ?? faker.company.name(),
    description: options.description !== undefined ? options.description : null,
    insertTimestamp: options.insertTimestamp ?? new Date().toISOString(),
    updateTimestamp: options.updateTimestamp ?? new Date().toISOString(),
  }
}
```

**Entity with FK** (throw if required FK is missing):
```typescript
export function generateChildEntity(
  options: ChildPartial = {},
  ID: ReturnType<typeof IdProvider> = IdProvider()
): dbChild {
  if (!options.parentId) throw new Error('generateChildEntity requires parentId')
  return {
    childId: ID(options.childId),
    parentId: ID(options.parentId),   // resolves shorthand → real ID
    // ...
  }
}
```

**Entity with multiple outputs** (person + Firebase user):
```typescript
export function generatePerson(
  ID: ReturnType<typeof IdProvider> = IdProvider(),
  options: PersonPartial = {}
): { person: dbPerson; firebaseUser?: TestUser } {
  const personId = ID(options.personId)
  const email = options.email ?? faker.internet.email()
  const person: dbPerson = { personId, email, authUserId: null, /* ... */ }

  let firebaseUser: TestUser | undefined
  if (options.password !== undefined) {
    firebaseUser = { userId: personId, email, password: options.password, displayName: '' }
    person.authUserId = personId
  }

  return { person, firebaseUser }
}
```

**Composite key entity** (no single PK):
```typescript
export function generateMembership(
  options: MembershipPartial = {},
  ID: ReturnType<typeof IdProvider> = IdProvider()
): dbMembership {
  if (!options.personId || !options.groupId) {
    throw new Error('generateMembership requires personId and groupId')
  }
  return {
    personId: ID(options.personId),
    groupId: ID(options.groupId),
    role: options.role ?? 'member',
  }
}
```

---

## Phase 6: Scenario (`src/test-context/Scenario.ts`)

```typescript
export class Scenario {
  readonly ID: ReturnType<typeof IdProvider>
  private data: GeneratedTableArrays = { entities: [], children: [], memberships: [] }
  private firebaseUsers: TestUser[] = []

  constructor(idProvider: ReturnType<typeof IdProvider>) {
    if (!idProvider) throw new Error('Scenario requires an IdProvider')
    this.ID = idProvider
  }

  // Process in dependency order — nested first, composite last
  bulkAdd(data: Partial<GeneratedTableArraysPartials>): this {
    const ID = this.ID

    // 1. Nested entities
    data.nestedEntities?.forEach(opt => this.data.nestedEntities.push(generateNested(opt, ID)))

    // 2. Independent entities
    data.entities?.forEach(opt => this.data.entities.push(generateEntity(opt, ID)))

    // 3. Dependent entities with FKs
    data.children?.forEach(opt => this.data.children.push(generateChild(opt, ID)))

    // 4. Entities with multiple outputs
    data.persons?.forEach(opt => {
      const { person, firebaseUser } = generatePerson(ID, opt)
      this.data.persons.push(person)
      if (firebaseUser) this.firebaseUsers.push(firebaseUser)
    })

    // 5. Composite key entities
    data.memberships?.forEach(opt => this.data.memberships.push(generateMembership(opt, ID)))

    return this
  }

  build(): Selector {
    // Stitch nested entities into parents
    this.data.entities.forEach(entity => {
      entity.nested = this.data.nestedEntities.filter(n => n.entityId === entity.entityId)
    })

    return new Selector(this.data, this.ID, this.firebaseUsers)
  }
}
```

---

## Phase 7: Selector (`src/test-context/Selector.ts`)

```typescript
export class Selector {
  readonly data: GeneratedTableArrays
  private idProvider?: ReturnType<typeof IdProvider>
  private firebaseUsers: TestUser[]

  // Pre-computed indexes
  readonly entities: Record<string, dbEntity>
  readonly memberships: Record<string, dbMembership>       // composite key
  readonly childrenByEntityId: Record<string, dbChild[]>  // relationship index

  constructor(
    data: GeneratedTableArrays,
    idProvider?: ReturnType<typeof IdProvider>,
    firebaseUsers: TestUser[] = []
  ) {
    this.data = data
    this.idProvider = idProvider
    this.firebaseUsers = firebaseUsers

    this.entities = indexByKey(data.entities, 'entityId')
    this.memberships = indexByCompositeKey(data.memberships, ['personId', 'groupId'])
    this.childrenByEntityId = groupByKey(data.children, 'entityId')
  }

  private resolveId(id: string): string {
    return this.idProvider ? this.idProvider(id, { exact: true }) : id
  }

  getEntity(id: string): dbEntity | undefined {
    return this.entities[this.resolveId(id)]
  }

  getMembership(personId: string, groupId: string): dbMembership | undefined {
    const key = `${this.resolveId(personId)}:${this.resolveId(groupId)}`
    return this.memberships[key]
  }

  getChildrenByEntity(entityId: string): dbChild[] {
    return this.childrenByEntityId[this.resolveId(entityId)] ?? []
  }

  getRawTestData(): GeneratedTableArrays { return this.data }
  allFirebaseUsers(): TestUser[] { return this.firebaseUsers }
}
```

---

## Phase 8: DataMerger (`src/test-context/DataMerger.ts`)

```typescript
export function mergeData(baseData: DataGenObject, testData: DataGenObject): DataGenObject {
  const merged: DataGenObject = { ...baseData }

  for (const key of Object.keys(testData) as (keyof DataGenObject)[]) {
    const base = baseData[key]
    const test = testData[key]
    if (Array.isArray(base) && Array.isArray(test)) {
      merged[key] = mergeArrayByKey(base as Record<string, unknown>[], test as Record<string, unknown>[], key as string) as never
    } else if (test !== undefined) {
      merged[key] = test
    }
  }

  return merged
}

function mergeArrayByKey<T extends Record<string, unknown>>(base: T[], test: T[], entityType: string): T[] {
  const result = [...base]
  test.forEach(item => {
    const i = findMatchIndex(result, item, entityType)
    if (i !== -1) result[i] = item
    else result.push(item)
  })
  return result
}

function findMatchIndex<T extends Record<string, unknown>>(array: T[], item: T, entityType: string): number {
  return array.findIndex(a => {
    switch (entityType) {
      case 'entities': return a.entityId === item.entityId
      case 'memberships': return a.personId === item.personId && a.groupId === item.groupId
      // add cases for all entity types
      default: return false
    }
  })
}
```

---

## Phase 9: DatabaseAdapter (`src/database/adapter.ts`)

The adapter is the only file that imports concrete database types. Choose the implementation for your DB:

**Firestore**:
```typescript
import type { Firestore } from 'firebase-admin/firestore'
import type { DatabaseAdapter as IAdapter } from './types'

export default class FirestoreAdapter implements IAdapter {
  constructor(private db: Firestore) {}

  getDatabaseClient() { return this.db }
  getMaxBatchSize() { return 500 }

  async readDocument<T>(collection: string, docId: string): Promise<T | null> {
    const snap = await this.db.collection(collection).doc(docId).get()
    return snap.exists ? snap.data() as T : null
  }

  async readDocumentsByField<T>(collection: string, field: string, value: unknown): Promise<T[]> {
    const snap = await this.db.collection(collection).where(field, '==', value).get()
    return snap.docs.map(d => d.data() as T)
  }

  async upsertDocument(collection: string, docId: string, data: unknown): Promise<void> {
    await this.db.collection(collection).doc(docId).set(data)
  }

  async deleteDocument(collection: string, docId: string): Promise<void> {
    await this.db.collection(collection).doc(docId).delete()
  }

  async upsertGeneratedData(data: GeneratedTableArrays): Promise<void> {
    let batch = this.db.batch()
    let count = 0

    const add = async (col: string, id: string, doc: unknown) => {
      if (count >= 500) { await batch.commit(); batch = this.db.batch(); count = 0 }
      batch.set(this.db.collection(col).doc(id), doc)
      count++
    }

    // Insert in dependency order — match Scenario.bulkAdd order
    for (const e of data.entities ?? []) await add('entities', e.entityId, e)
    for (const c of data.children ?? []) await add('children', c.childId, c)
    for (const m of data.memberships ?? []) await add('memberships', `${m.personId}:${m.groupId}`, m)

    if (count > 0) await batch.commit()
  }

  async deleteGeneratedData(data: GeneratedTableArrays): Promise<void> {
    // Delete in reverse dependency order
    // ... same pattern, reversed
  }
}
```

**PostgreSQL**: Use `Pool` + `BEGIN`/`COMMIT` transactions.  
**MongoDB**: Use `MongoClient` + `session.withTransaction()`.

---

## Phase 10: DatabaseReader (`src/test-context/DatabaseReader.ts`)

**Never import concrete database types here.** Use `DatabaseReadOperations`.

```typescript
import type { DatabaseReadOperations } from '../database/types'
import type { IdProvider } from './IdProvider'

export class DatabaseReader {
  constructor(
    private db: DatabaseReadOperations,   // ← interface, NOT Firestore/Pool/MongoClient
    private idProvider?: ReturnType<typeof IdProvider>
  ) {}

  private resolveId(id: string): string {
    return this.idProvider ? this.idProvider(id, { exact: true }) : id
  }

  async getEntity(entityId: string): Promise<dbEntity | null> {
    return this.db.readDocument<dbEntity>('entities', entityId)
  }

  // Retrieve methods resolve shorthand IDs first
  async retrieveEntity(shortId: string): Promise<dbEntity | null> {
    return this.getEntity(this.resolveId(shortId))
  }

  // Stitch nested entities for parent reads
  async getParentWithNested(parentId: string): Promise<dbParent | null> {
    const parent = await this.db.readDocument<dbParent>('parents', parentId)
    if (!parent) return null
    parent.nested = await this.db.readDocumentsByField('nested', 'parentId', parentId)
    return parent
  }
}
```

---

## Phase 11: AuthManager (`src/test-context/AuthManager.ts`)

Firebase projects only. Skip for other auth systems.

```typescript
import type { Auth } from 'firebase-admin/auth'
import type { Page } from '@playwright/test'
import type { TestUser } from './types'

export class AuthManager {
  constructor(private auth: Auth) {
    if (!auth) throw new Error('AuthManager requires Auth instance')
  }

  async createAuthUser(user: TestUser): Promise<string> {
    try {
      return (await this.auth.getUserByEmail(user.email)).uid
    } catch {
      try {
        return (await this.auth.createUser({ uid: user.userId, email: user.email, password: user.password, displayName: user.displayName })).uid
      } catch (err: unknown) {
        if (typeof err === 'object' && err !== null && 'code' in err && err.code === 'auth/uid-already-exists') {
          return (await this.auth.getUser(user.userId)).uid
        }
        throw err
      }
    }
  }

  async generateCustomToken(userId: string): Promise<string> {
    return this.auth.createCustomToken(userId)
  }

  async authenticatePage(page: Page, user: TestUser): Promise<void> {
    const token = await this.generateCustomToken(user.userId)
    await page.evaluate(signInWithCustomToken, { token, emulatorHost: process.env.FIREBASE_AUTH_EMULATOR_HOST ?? 'localhost:9099' })
  }
}

// Runs in browser context
async function signInWithCustomToken({ token, emulatorHost }: { token: string; emulatorHost: string }) {
  // Load Firebase compat SDK if not present, then signInWithCustomToken
  // (see full implementation in source pattern)
}
```

---

## Phase 12: TestContext (`src/test-context/TestContext.ts`)

**Never import concrete adapter classes here.** Use `DatabaseAdapter` interface.

```typescript
import type { DatabaseAdapter } from '../database/types'   // ← interface, not class

export class TestContext {
  readonly dbReader: DatabaseReader
  private scenario: Scenario
  private selector?: Selector
  private authManager?: AuthManager
  readonly idProvider: ReturnType<typeof IdProvider>

  private constructor(private db: DatabaseAdapter) {
    if (!db) throw new Error('TestContext requires DatabaseAdapter')
    this.idProvider = IdProvider()
    this.dbReader = new DatabaseReader(db, this.idProvider)
    this.scenario = new Scenario(this.idProvider)
    // initialize AuthManager conditionally if Firebase available
  }

  static async create(db: DatabaseAdapter): Promise<TestContext> {
    return new TestContext(db)
  }

  mergeData(base: DataGenObject, test: DataGenObject): DataGenObject {
    return mergeData(base, test)
  }

  bulkAdd(data: DataGenObject): this {
    this.scenario.bulkAdd(data)
    this.selector = this.scenario.build()
    return this
  }

  getSelector(): Selector {
    if (!this.selector) this.selector = this.scenario.build()
    return this.selector
  }

  async insert(): Promise<void> {
    if (!this.selector) throw new Error('Call bulkAdd() before insert()')
    // create Firebase auth users first
    for (const user of this.selector.allFirebaseUsers()) {
      await this.authManager?.createAuthUser(user)
    }
    await this.db.upsertGeneratedData(this.selector.getRawTestData())
  }

  async setupEnv(options: {
    baseData: DataGenObject
    testData?: DataGenObject
    page?: Page
    authPersonId?: string
  }): Promise<{ selector: Selector; authUser?: TestUser }> {
    const merged = this.mergeData(options.baseData, options.testData ?? {})
    await this.bulkAdd(merged).insert()
    const selector = this.getSelector()
    // resolve auth user if requested
    return { selector }
  }
}
```

---

## Phase 13: Exports

**`src/index.ts`**:
```typescript
export * from './test-context'
export * from './generators'
export { default as FirestoreAdapter } from './database/adapter'
export type { DatabaseAdapter, DatabaseReadOperations } from './database/types'
```

**`src/test-context/index.ts`**:
```typescript
export { TestContext } from './TestContext'
export { Scenario } from './Scenario'
export { Selector } from './Selector'
export { IdProvider } from './IdProvider'
export { DatabaseReader } from './DatabaseReader'
export { mergeData } from './DataMerger'
export * from './types'
```

---

## Usage Example

```typescript
import { TestContext } from '@project/test-tools'
import FirestoreAdapter from '@project/test-tools/database'

const db = new FirestoreAdapter(firestoreInstance)
const ctx = await TestContext.create(db)

const { selector } = await ctx.setupEnv({
  baseData: {
    entities: [{ entityId: 'E1', name: 'Test Entity' }],
    persons: [{ personId: 'P1', password: 'password123' }],
    memberships: [{ personId: 'P1', groupId: 'E1' }],
  },
  testData: {
    entities: [{ entityId: 'E1', name: 'Override Name' }],  // overrides by ID
  },
  page,
  authPersonId: 'P1',
})

const entity = selector.getEntity('E1')      // shorthand ID lookup
const members = selector.getChildrenByEntity('E1')
```

---

## Critical Rules

- **Interfaces first**: Create `src/database/types.ts` before `adapter.ts`
- **No concrete types in core**: `DatabaseReader` and `TestContext` use interfaces only
- **Dependency order**: `bulkAdd()` and `upsertGeneratedData()` must process entities in the same order
- **Reverse for delete**: `deleteGeneratedData()` deletes in reverse dependency order
- **Composite key format**: Use `key1:key2` as the document ID for composite-key entities
- **Merge semantics are explicit**: If `mergeData()` supports key-based override, reusing the same shorthand ID in `baseData` and `testData` replaces the matching entity. This is usually replace-by-key, not deep merge.
- **Nested entities before parent**: Generate nested entities before stitching them into the parent in `Scenario.build()`
