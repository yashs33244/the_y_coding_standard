# JavaScript and TypeScript Standards (Yash Edition)

## When to load this reference

Load this file when working on:

- Pure Node.js services (Express, Fastify, Hono, raw HTTP)
- CLI tools (Commander, Yargs, oclif, custom)
- npm packages and TypeScript libraries
- Workers, scripts, cron jobs, queue consumers
- SDK clients and API wrappers
- Anything backend or runtime-agnostic written in TypeScript

Do NOT load this for React or Next.js work. For frontend, components, hooks, App Router, server actions, RSC, or anything browser-facing, load `references/react-nextjs.md` instead. This file is the non-React JS/TS standard.

For classes, inheritance, dependency injection, and SOLID details, cross-reference `references/oop.md`. Do not duplicate that content here.

## Non-Negotiables (Yash Rules)

These are not preferences. They are mandatory.

1. TypeScript strict mode. No exceptions. No `any`. Ever.
2. No em dashes (the unicode character) anywhere. Not in code, not in comments, not in strings, not in docs, not in commit messages. Use a regular hyphen or rewrite the sentence.
3. Files must stay under 400 lines. Hard limit. If a file crosses 400 lines, split it before continuing.
4. Enums live in `enums.ts`. Constants live in `constants.ts`. Types live in `types.ts`. Each in its own file. Do not inline these in service or route files.
5. All environment config goes through `lib/config.ts`, validated with zod at startup. No `process.env.X` reads outside that file.
6. Cross-cutting concerns (auth, logging, rate limiting, error handling, tracing) go through middleware. Do not sprinkle them across handlers.
7. Validate all external input at the boundary with zod. Never trust the network, the database, or the filesystem.
8. Use pnpm. Not npm, not yarn. Lockfile committed.
9. Named exports only. Default exports are banned in non-React code.
10. No emojis in source code, comments, or commits.

## TypeScript Configuration

Mandatory `tsconfig.json` compiler options:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler"
  }
}
```

Never use `any`. If you reach for `any`, you have not understood the type yet. Use `unknown` and narrow with a type guard, a zod schema, or a discriminated union.

```ts
// Banned
function handle(payload: any) { /* ... */ }

// Required
function handle(payload: unknown) {
  const parsed = PayloadSchema.parse(payload)
  // parsed is now typed
}
```

## Types vs Interfaces

- `interface` for objects that represent domain entities and may be extended.
- `type` for unions, intersections, mapped types, primitives, and function signatures.
- Never use the TypeScript `enum` keyword. Use `as const` objects instead. Put them in `enums.ts`.

```ts
// enums.ts
export const UserRole = {
  Admin: 'admin',
  Member: 'member',
  Viewer: 'viewer',
} as const
export type UserRole = typeof UserRole[keyof typeof UserRole]
```

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Variables, functions | camelCase | `getUserById` |
| Classes, interfaces, types | PascalCase | `UserService`, `ApiResponse` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Files | kebab-case | `user-service.ts` |
| Private class members | `#` (hard private) | `#sessionToken` |
| Booleans | `is`, `has`, `can`, `should` prefix | `isActive`, `hasAccess` |
| Async functions | verb first | `fetchUser`, `syncOrders` |

## File-Level Organization

Each module follows the same shape. Do not collapse these into a single file.

```
src/features/users/
├── user.service.ts        # business logic (class or functions)
├── user.repository.ts     # data access only
├── user.routes.ts         # transport layer (HTTP/CLI/queue)
├── user.middleware.ts     # cross-cutting for this feature
├── types.ts               # interfaces and types for this feature
├── enums.ts               # const-object enums for this feature
├── constants.ts           # SCREAMING_SNAKE_CASE constants
├── user.schema.ts         # zod schemas (input + output validation)
├── user.utils.ts          # pure helpers
└── user.test.ts           # colocated tests
```

## Project Structure

Feature-based, not layer-based. Layers belong inside features.

```
src/
├── features/
│   ├── users/
│   ├── orders/
│   └── billing/
├── lib/
│   ├── config.ts          # zod-validated env, single source of truth
│   ├── logger.ts
│   ├── db.ts
│   └── errors.ts          # base error classes
├── middleware/            # global cross-cutting middleware
│   ├── auth.ts
│   ├── error-handler.ts
│   ├── rate-limit.ts
│   └── request-id.ts
├── shared/
│   ├── types.ts
│   ├── enums.ts
│   └── constants.ts
└── index.ts               # entry point only, wires middleware + routes
```

## Centralized Config (Mandatory)

Every project has exactly one `lib/config.ts`. It loads `process.env`, validates with zod, and exports a typed `config` object. Nothing else reads `process.env` directly.

```ts
// lib/config.ts
import { z } from 'zod'

const ConfigSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']),
  PORT: z.coerce.number().int().positive(),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
})

const parsed = ConfigSchema.safeParse(process.env)
if (!parsed.success) {
  console.error('Invalid environment configuration', parsed.error.flatten())
  process.exit(1)
}

export const config = parsed.data
export type Config = z.infer<typeof ConfigSchema>
```

If a new service needs an env variable, it gets added to this schema. No exceptions.

## Middleware Pattern

Cross-cutting concerns go through middleware. Never inline auth, logging, validation, or error handling inside route handlers or service methods.

```ts
// middleware/auth.ts
export const requireAuth: Middleware = async (ctx, next) => {
  const token = ctx.headers.authorization?.replace('Bearer ', '')
  if (!token) throw new UnauthorizedError()
  ctx.user = await verifyToken(token)
  await next()
}

// usage
app.use('/api/users', requireAuth, userRoutes)
```

If you find yourself copying the same `if (!ctx.user) return 401` into multiple handlers, that is a middleware that has not been written yet.

## Module Patterns

- Named exports only. Default exports are banned outside React component files.
- Barrel files (`index.ts`) re-export the public API of a feature. Never re-export internals.
- Circular dependencies are a code smell. If A imports B and B imports A, extract the shared piece into C.

```ts
// features/users/index.ts - explicit public API
export { UserService } from './user.service'
export type { User, CreateUserInput } from './types'
export { UserSchema } from './user.schema'
// internal helpers stay internal
```

## Functions

- Pure functions preferred. Isolate side effects at the edges.
- Max 30 lines per function. If longer, extract sub-functions with descriptive names.
- Early returns over nested conditionals. Flat code beats pyramid code.
- Single responsibility per function. If you need "and" to describe what it does, split it.

```ts
// Bad
function process(user: User) {
  if (user) {
    if (user.isActive) {
      if (user.subscription) {
        // 40 lines of logic buried three levels deep
      }
    }
  }
}

// Good
function process(user: User): ProcessResult {
  if (!user) return { ok: false, reason: 'no-user' }
  if (!user.isActive) return { ok: false, reason: 'inactive' }
  if (!user.subscription) return { ok: false, reason: 'no-subscription' }

  return runProcessing(user)
}
```

## Classes

When you reach for a class, load `references/oop.md` for the full SOLID rules. Quick summary:

- Constructor injection only. No `new` inside class methods for collaborators.
- Depend on interfaces, not concrete classes.
- One reason to change per class.
- Private state uses `#` (hard private), not `_` prefix.
- No God classes. If a class has more than 7 public methods, split it.

## Error Handling

- Never swallow errors silently. `catch (e) {}` is a bug.
- Use typed error classes. Extend a project-wide `BaseError` so handlers can discriminate.

```ts
// lib/errors.ts
export class BaseError extends Error {
  constructor(message: string, public readonly code: string, public readonly statusCode = 500) {
    super(message)
    this.name = this.constructor.name
  }
}

export class UserNotFoundError extends BaseError {
  constructor(id: string) {
    super(`User ${id} not found`, 'USER_NOT_FOUND', 404)
  }
}
```

- At service boundaries, catch and re-throw with context.
- At transport boundaries (HTTP, CLI exit codes, queue ACKs), the error-handler middleware maps domain errors to the right response.
- Never expose raw error messages to clients. Map to a stable error code.

## Async

- `async/await` only. Never chain `.then().catch()`.
- Never `await` inside a loop when the iterations are independent. Use `Promise.all` or `Promise.allSettled`.
- No fire-and-forget without a comment explaining why. Unhandled promise rejections crash the process.

```ts
// Bad
for (const id of userIds) {
  await fetchUser(id)
}

// Good
const users = await Promise.all(userIds.map(fetchUser))

// Acceptable with reasoning
const results = await Promise.allSettled(userIds.map(fetchUser))
```

## Validation at Boundaries

Every external input gets parsed with zod. This includes:

- HTTP request bodies, query params, headers
- CLI flags and positional args
- Environment variables (handled in `lib/config.ts`)
- Database rows that come from raw queries
- Messages pulled from queues
- File contents read from disk

```ts
// user.schema.ts
import { z } from 'zod'

export const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(['admin', 'member', 'viewer']),
})

export type CreateUserInput = z.infer<typeof CreateUserSchema>
```

Inside the service layer, types are trusted. The schema is the only place that trust is established.

## Imports Order

1. Node built-ins (`node:fs`, `node:path`)
2. External packages (`zod`, `express`)
3. Internal absolute imports (`@/features/...`, `@/lib/...`)
4. Relative imports (`./utils`, `../shared`)
5. Type-only imports last (`import type { ... }`)

Blank line between each group. Use a linter to enforce this. Do not arrange imports by hand.

## Logging

- Use a structured logger (pino preferred). Never `console.log` in production code.
- Log levels are real: `debug`, `info`, `warn`, `error`. Use them correctly.
- Every log line gets a request ID via middleware so traces are reconstructable.
- Never log secrets, tokens, full request bodies, or PII without scrubbing.

## Testing

- Colocate tests next to source: `user.service.ts` and `user.service.test.ts` live together.
- Use Vitest. Integration tests over unit tests where the boundary makes integration easier.
- Mock at the edges (network, filesystem, time). Do not mock your own service layer.

## Package Manager

pnpm. Always. Commit `pnpm-lock.yaml`. CI runs `pnpm install --frozen-lockfile`.

```bash
pnpm add zod
pnpm add -D vitest @types/node
```

## When this reference loads

Trigger phrases that should pull this file in:

- "Node service", "Node.js app", "Express", "Fastify", "Hono"
- "CLI tool", "command line", "TypeScript CLI"
- "npm package", "TypeScript library", "SDK"
- "worker", "queue consumer", "background job", "cron"
- "API server" (when not Next.js)
- "TypeScript backend"
- Any TypeScript work where React is not involved

If the project is React or Next.js, load `references/react-nextjs.md` instead. If classes are central, also load `references/oop.md`.
