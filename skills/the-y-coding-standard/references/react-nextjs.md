# React / Next.js Standards

Yash's opinionated, Vercel-native React + Next.js standard. Read this top to bottom before scaffolding or touching framework code. These are defaults, not suggestions.

## Framework Posture

- Always Next.js App Router. The directory is `app/`. Never `pages/`. Never create new `pages/` routes, not even "just one quick API route." If a project still has `pages/`, plan migration before adding features.
- Use the LATEST stable Next.js at scaffolding time. Verify with WebSearch ("latest stable Next.js release") before running `create-next-app`. Do not trust training data for version numbers.
- React 19+ when available. Use the newer hooks: `useActionState`, `useOptimistic`, `useFormStatus`, `use`. If the project pins React 18, document why in `CLAUDE.md`.
- TypeScript strict mode is mandatory. No `any` without a `// reason:` comment explaining the escape hatch and a TODO to remove it.
- Node 20+ runtime. Vercel functions on Fluid Compute by default.

## Component Classification

Server vs Client is decided at the FILE level. Default is Server Component. Mark client ONLY when one of the following is true:

- React hooks that need a client runtime: `useState`, `useEffect`, `useReducer`, `useRef`, `useLayoutEffect`, `useTransition`, `useDeferredValue`, `useOptimistic`, `useFormStatus`.
- Browser APIs: `window`, `document`, `localStorage`, `navigator`, `IntersectionObserver`, `ResizeObserver`.
- Event listeners attached in JSX: `onClick`, `onChange`, `onSubmit`, `onKeyDown`, etc.
- Third-party libraries that are client-only (chart libs, animation libs that touch the DOM, drag-and-drop libs).

Mark the file with `'use client'` at the very top. Push client components to LEAF positions in the tree. Wrap the smallest possible subtree.

Concrete rule: a dashboard page is a Server Component. Only the filter bar that owns interactive state is a Client Component. The table that renders rows from server data is a Server Component. The row's "delete" button is a tiny Client Component.

If you find yourself slapping `'use client'` on a layout or top-level page, stop. Refactor: lift state into a small client island, keep the shell on the server.

## Folder Structure (App Router)

This is the canonical layout. Do not invent variants without a reason.

```
app/
  (auth)/                    # route group, no URL segment
    login/page.tsx
    register/page.tsx
  (dashboard)/
    layout.tsx
    page.tsx
    settings/
      page.tsx
      loading.tsx            # Suspense fallback
      error.tsx              # error boundary
  api/
    users/route.ts
  layout.tsx                 # root layout
  not-found.tsx
  globals.css

components/
  ui/                        # pure presentational, no data
    Button.tsx
    Modal.tsx
    Input.tsx
  features/                  # domain-aware
    users/
      UserCard.tsx
      UserList.tsx

lib/
  config.ts                  # CENTRALIZED config
  db.ts
  auth.ts
  utils.ts
  validators.ts

hooks/
  useDebounce.ts
  useLocalStorage.ts

actions/
  user.actions.ts            # Server Actions
  order.actions.ts

types/
  user.ts
  order.ts

constants/
  index.ts
  routes.ts

enums/
  index.ts
  user-role.ts
```

Route groups `(name)/` are for organization without URL impact. Use them to separate authenticated vs marketing vs admin areas, each with its own layout. Colocate `loading.tsx`, `error.tsx`, and `not-found.tsx` next to the `page.tsx` they protect.

`components/ui/` holds presentational primitives, no data fetching, no business logic. `components/features/` holds domain components that know about the data shape. Never reach into `features/` from `ui/`.

## Component Size Limit

HARD LIMIT: 400 lines per component file. This is Yash's rule and it matches industry norms (Airbnb 250, Google 400, Vercel internal ~300). 400 is the ceiling, not the target. Aim for under 250.

When a component approaches 400 lines:

- Extract subcomponents into the same folder.
- Move logic to custom hooks in `hooks/`.
- Move types to `types/`.
- Move constants to `constants/`.
- Move pure helpers to `lib/utils.ts` or a feature-local `utils.ts`.

Pages should be slim. A `page.tsx` is composition of features, not a kitchen sink. Heavy logic lives in hooks, services, or server actions. If your `page.tsx` is over 150 lines, you are doing too much in the route file.

## Centralized Config (DRY)

Every project has ONE config module: `lib/config.ts`. Reads env through a `zod` schema. Throws at startup if anything is missing or malformed. Fail fast, fail loud.

```ts
// lib/config.ts
import { z } from 'zod'

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'staging', 'production']),
  DATABASE_URL: z.string().url(),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  ANTHROPIC_API_KEY: z.string().min(1),
})

export const config = envSchema.parse(process.env)
```

Never read `process.env.X` directly outside `lib/config.ts`. Every consumer imports `config` and gets typed, validated values. No string literals scattered across the codebase. No "what was that env var called again?" moments.

For client-exposed values, prefix `NEXT_PUBLIC_` and keep them in the same schema. The `config` object is universal; the bundler tree-shakes correctly because `NEXT_PUBLIC_` keys inline at build time.

## Middleware for Cross-Cutting Concerns

DRY rule: validation, auth, logging, rate limiting belong in middleware or wrappers. Never inline in every handler.

Two layers:

1. Next.js `middleware.ts` at the root. Runs on Vercel Functions (Fluid Compute). Use for auth-gating route segments, geo-routing, A/B test cookie assignment, locale detection.
2. Route Handler composition: small wrapper functions for `api/*` routes that compose auth, validation, error handling.

```ts
// lib/api-handler.ts
type Handler<T> = (req: Request, ctx: { user: User }) => Promise<T>

export function withAuth<T>(handler: Handler<T>) {
  return async (req: Request) => {
    const user = await getCurrentUser(req)
    if (!user) return new Response('Unauthorized', { status: 401 })
    const result = await handler(req, { user })
    return Response.json(result)
  }
}

// app/api/users/route.ts
export const GET = withAuth(async (req, { user }) => {
  return await getUsersForOrg(user.orgId)
})
```

Stack wrappers when needed: `withAuth(withRateLimit(withValidation(schema, handler)))`. Never copy-paste auth checks. If you write `getCurrentUser` inside three handlers, refactor before merging.

## Data Fetching

- Server Components: direct `async/await` with your ORM (Drizzle, Prisma) or `fetch`. No `useEffect` + `useState` for data. Ever.
- Client-interactive data: SWR or React Query (TanStack Query). Pick one per project, never both. Yash defaults to SWR for simple cases, React Query when mutations and cache invalidation get complex.
- Tag fetches for granular invalidation: `fetch(url, { next: { tags: ['users'] } })`.
- Call `revalidateTag('users')` after mutations. Use `revalidatePath` only when a route's full data has to refresh.
- Parallel fetch in Server Components: declare `const [a, b] = await Promise.all([fetchA(), fetchB()])`. Sequential awaits are a perf bug.

If you write `useEffect(() => { fetch(...).then(setState) }, [])` in a new file, delete it before commit. That pattern is banned.

## Server Actions

For mutations. Colocate with the route or put in `actions/<domain>.actions.ts`. Always start with `'use server'`.

```ts
// actions/user.actions.ts
'use server'
import { revalidateTag } from 'next/cache'
import { db } from '@/lib/db'
import { updateUserSchema } from '@/lib/validators'

export async function updateUser(input: unknown) {
  const data = updateUserSchema.parse(input)  // validate at boundary
  await db.user.update({ where: { id: data.id }, data })
  revalidateTag('users')
}
```

Always validate Server Action input with `zod`. Trust nothing from the client. Server Actions are public POST endpoints once compiled; treat them like any other API surface. Auth-check inside the action or wrap the action with a `withAuthAction` helper.

Return typed shapes: `{ ok: true, data } | { ok: false, error }`. Don't throw across the action boundary unless you want a generic error UI.

## State Management Hierarchy (CRITICAL)

In order of preference. ALWAYS use the LOWEST applicable level.

1. URL state (search params). Share-able, bookmarkable, refresh-safe. Use `useSearchParams` + `useRouter`. Filter UIs, pagination, tabs, sort orders all belong here.
2. Server state. Fetch in a Server Component, pass as props. No client state needed.
3. Local component state. `useState` for simple primitives or a single object.
4. Local complex state. `useReducer` when you have 3+ related `useState` calls OR state transitions are non-trivial.
5. Shared state in a subtree. React Context, rarely. If you reach for Context, ask whether server-passed props or a URL param works instead.
6. Global client state. Zustand. Never Redux for new projects. Never MobX.

`useReducer` is REQUIRED when:

- More than 3 `useState` calls in one component that update together.
- State transitions follow a clear set of actions (form wizard, multi-step flow, drag state machine).
- The same state shape lives in multiple components and would otherwise be duplicated.

Example refactor (the useState-explosion smell):

BAD:
```tsx
const [name, setName] = useState('')
const [email, setEmail] = useState('')
const [age, setAge] = useState(0)
const [errors, setErrors] = useState<Record<string, string>>({})
const [isSubmitting, setIsSubmitting] = useState(false)
const [step, setStep] = useState(1)
```

GOOD:
```tsx
type State = {
  name: string
  email: string
  age: number
  errors: Record<string, string>
  status: 'idle' | 'submitting' | 'error'
  step: number
}
type Action =
  | { type: 'set'; field: keyof State; value: unknown }
  | { type: 'submit' }
  | { type: 'success' }
  | { type: 'error'; errors: Record<string, string> }

function reducer(state: State, action: Action): State { /* ... */ }
const [state, dispatch] = useReducer(reducer, initialState)
```

The reducer file gets unit tested independently, the component stays slim, and state transitions become greppable.

## Latest React Hooks

Use these. Do not roll your own. Read the official docs before using; behavior changes between minor releases.

- `useActionState` for Server Action forms. Replaces older `useFormState` + `useFormStatus` combos.
- `useOptimistic` for optimistic UI on Server Actions. Pair with a Server Action that revalidates on success.
- `useFormStatus` for the pending state of an enclosing `<form>`. Lives in a child of the form.
- `use(promise)` for async data unwrapping inside Server Components or client components inside Suspense.
- `useTransition` for non-blocking updates (filter typing, tab switches with heavy children).
- `useDeferredValue` for debouncing inputs without manual `setTimeout` gymnastics.

When unsure about behavior, run WebSearch for the React 19 docs page or the AI SDK v6 reference. Cite the version you targeted in a code comment if behavior is subtle.

## Vercel-Native Patterns (Yash's stack)

- Default to AI SDK v6 for all AI features. Use `"provider/model"` strings routed through AI Gateway so model swaps are config changes, not code changes.
- Default to Fluid Compute. Not Edge Functions, not the older Vercel Edge runtime. Fluid gives you Node APIs, longer timeouts, and better cold-start economics.
- Default function timeout 300s on all plans. Configure in `vercel.ts` (or `vercel.json` if `vercel.ts` is not yet supported in your CLI version).
- Vercel Blob for file storage. Vercel Queues for at-least-once messaging. Vercel Postgres or Neon for databases.
- `vercel.ts` over `vercel.json` when supported by the installed CLI. Typed config catches mistakes.
- Use `next/og` for OG images, served from the same project.

## TypeScript Rules

- `"strict": true` always.
- `"noUncheckedIndexedAccess": true` always. Forces you to handle `undefined` from arrays and records.
- `any` is banned. Use `unknown` and narrow with type guards or `zod`.
- Use `zod` for runtime validation at every trust boundary: API in, API out, Server Actions, env vars, third-party webhook payloads, LLM outputs.
- Branded types for IDs to prevent mixing:
  ```ts
  type UserId = string & { readonly __brand: 'UserId' }
  type OrgId = string & { readonly __brand: 'OrgId' }
  ```
- Prefer `type` over `interface` for non-class shapes. Interfaces for class shapes only. Reason: `type` composes more flexibly, declarations don't merge silently.
- No `enum` keyword. Use string literal unions or `as const` objects:
  ```ts
  export const UserRole = { Admin: 'admin', Member: 'member', Guest: 'guest' } as const
  export type UserRole = (typeof UserRole)[keyof typeof UserRole]
  ```
- Path aliases via `tsconfig.json` `paths`: `@/lib/*`, `@/components/*`. Never deep relative imports like `../../../lib/db`.

## Styling

- Tailwind CSS by default.
- Component library: shadcn/ui, copied into `components/ui/`. Do not install as a runtime dep. Own the source.
- Theming via CSS variables in `globals.css`. Light/dark variants on the `:root` and `.dark` selectors.
- No inline `style={}` except for dynamic values that cannot be Tailwind classes (computed colors, animation delays from props).
- Use `clsx` or `cn()` helper for conditional classes. Avoid string concatenation.
- No CSS-in-JS libs (Emotion, styled-components) for new projects. They lose to Tailwind on bundle size and DX.

## Forms

- React Hook Form with the `zod` resolver. Single source of truth for shape and validation.
- Server Actions for submission. Client-side validation for UX, server-side validation for trust. The same `zod` schema runs in both places.
- No uncontrolled forms in serious code. "It works in the demo" is not a standard.
- Pair `useActionState` with React Hook Form for progressive enhancement when needed.

## Error Boundaries

- `error.tsx` at every route segment that can fail independently. Each route group gets its own.
- `global-error.tsx` at root for the catastrophic case.
- Show user-friendly messages. Log raw error and stack to monitoring (Sentry, Vercel Observability, Axiom).
- Never leak internal error messages or stack traces to the UI. Production users see "Something went wrong, our team has been notified." Development sees the real error.

## Loading States

- `loading.tsx` at every route segment with significant data fetching. The route segment automatically wraps its `page.tsx` in `<Suspense fallback={<Loading/>}>`.
- `<Suspense>` boundaries around independently-loading subtrees inside a page. A slow sidebar shouldn't block the main column.
- Never block the whole page on one slow request. Stream what you can.
- Skeletons over spinners. Match the final layout to avoid layout shift.

## Testing

- Vitest for unit tests. Faster than Jest, ESM-native, same API surface for the parts that matter.
- React Testing Library for component tests. Test behavior, not implementation. No snapshot testing for components.
- Playwright for E2E. Run against the deployed preview URL in CI for true integration.
- Storybook for component dev plus visual regression via Chromatic or Percy.
- Coverage is a signal, not a target. 80% line coverage on a feature that matters beats 100% on the whole codebase.

## Performance Defaults

- `next/image` for all images. Never raw `<img>`. Specify `width`, `height`, and `alt`. Use `priority` for above-the-fold images.
- `next/font` for fonts. Self-host via `next/font/google` or `next/font/local`. Never `<link rel="stylesheet">` to Google Fonts; you eat layout shift and a third-party request.
- Dynamic imports for heavy client-only deps: `dynamic(() => import('@/components/HeavyChart'), { ssr: false })`. Charts, editors, map libs, anything over 50KB minified.
- `@next/bundle-analyzer` enabled and inspected in CI. PRs that add over 20KB to a route bundle need justification.
- Avoid client-side waterfalls. Fetch in parallel, prefetch on hover, use `<Link prefetch>`.

## Authentication

- Auth.js v5+ (NextAuth) OR Clerk OR Vercel Sign In. Pick one per project.
- Never roll your own auth. Not for "just a simple app." Not for "the MVP." Yash has seen this go wrong too many times.
- Sessions in HttpOnly, Secure, SameSite=Lax cookies. Never `localStorage` for tokens. Never `sessionStorage`. Never query params.
- CSRF protection on by default in the chosen library; verify it before going live.
- Rotate refresh tokens. Log security events to monitoring.

## Database

- Drizzle for SQL-first projects where you want raw SQL ergonomics with type safety. Yash's default for new projects.
- Prisma when the team prefers a richer ORM and accepts the larger client bundle.
- Migrations live in `drizzle/` or `prisma/migrations/` and are committed. Never edit applied migrations; write a new one.
- Connection pooling via Vercel Postgres, Neon pooler, or Supabase pooler. Direct connections from serverless functions exhaust limits fast.
- Repository pattern: `lib/repositories/user.repo.ts` exposes typed functions. Server Actions and Route Handlers import from the repo, not the raw client.

## Caching Defaults

- `fetch` in Server Components is no longer cached by default in modern Next.js. Be explicit: `fetch(url, { next: { revalidate: 60, tags: ['users'] } })`.
- Route segment config when needed: `export const revalidate = 3600` for ISR-style behavior on a route.
- `unstable_cache` to memoize expensive DB calls across requests when revalidation tags are enough.
- Never cache personalized data without keying on user ID. Cache poisoning across users is a classic bug.
- Static routes get static rendered automatically. If a route reads cookies, headers, or search params, it becomes dynamic; that's expected, don't fight it.

## API Routes vs Server Actions

Use Server Actions for mutations called from your own UI. Use Route Handlers (`app/api/*/route.ts`) for:

- Public webhooks (Stripe, Clerk, GitHub).
- Third-party integrations that POST to you.
- Endpoints consumed by external clients (mobile apps, partner services).
- Streaming responses that need fine-grained header control.

Inside the same Next.js project, a button calling a Server Action is cleaner than fetching `/api/users`. Server Actions have built-in CSRF protection, typed inputs, and Next.js cache integration. Don't reach for Route Handlers just because it feels familiar.

## Streaming and Suspense Architecture

Streaming is a first-class pattern in App Router. Use it:

- Wrap independently loading sections in `<Suspense fallback={...}>`.
- Push slow data behind Suspense so the shell renders immediately.
- The root layout streams headers and nav. Page content streams after.
- Combine with `loading.tsx` for route-level Suspense and inline `<Suspense>` for component-level.

Bad: a dashboard waits 4 seconds for the slowest widget before rendering anything.
Good: nav and shell appear instantly, each widget streams in with its own skeleton.

## Metadata and SEO

- Export `metadata` from `layout.tsx` or `page.tsx`. Never use `next/head`; that's the old pages router.
- Use `generateMetadata` for dynamic metadata based on params or fetched data.
- `app/sitemap.ts` and `app/robots.ts` for SEO files. Generate them, don't hand-write XML.
- OG images via `app/opengraph-image.tsx` (or `.png`). Static or generated per-route.
- Structured data (JSON-LD) for content sites. Render in the page as a `<script type="application/ld+json">`.

## Internationalization

When i18n is in scope:

- Use `next-intl` for App Router. It integrates with Server Components cleanly.
- Locale segment as a route group: `app/[locale]/...`.
- Middleware redirects to the user's locale based on `Accept-Language` and stored preference.
- Never put translation strings in components. Always in JSON files keyed by namespace.

When i18n is not in scope, do not pre-build the abstraction. Pulling it in later is straightforward; building around imaginary requirements is not.

## AI SDK v6 Conventions (Vercel-Native)

- `generateText`, `streamText`, `generateObject`, `streamObject` from `ai` package. Do not call provider SDKs directly.
- Model strings: `'anthropic/claude-3-5-sonnet'`, routed via AI Gateway. Set the gateway base via env.
- Tool calls defined with `zod` schemas. The SDK validates input and output.
- Streaming responses use `result.toDataStreamResponse()` from a Route Handler. Pair with `useChat` on the client.
- Cache prompts when using Anthropic: pass `providerOptions: { anthropic: { cacheControl: { type: 'ephemeral' } } }` on system prompts and large context blocks.
- Track token usage and cost per request. Log to your observability layer.

## Anti-Patterns to Reject in Review

- `useEffect` + `setState` for initial data fetch in a client component.
- `process.env.X` outside `lib/config.ts`.
- `'use client'` on a layout or root page.
- Auth check copy-pasted in 3+ handlers.
- A component file over 400 lines.
- `any` without a `// reason:` comment.
- `enum` keyword in TypeScript.
- Inline styles for static design tokens.
- A new `pages/` route.
- Raw `<img>` or `<link>` to Google Fonts.
- A Server Action that doesn't validate input with `zod`.
- A client component that imports Node-only modules.
- A Route Handler used for an internal mutation when a Server Action would do.
- A `useState` explosion (5+ related state hooks) that should be a reducer.
- Direct provider SDK calls when AI SDK v6 covers the use case.

If you see any of these in a PR, block it. The standard exists so the code review focuses on the interesting parts, not the basics.

## When to Break the Standard

Standards exist to compress decisions. Break them when the situation demands, but write the reason down. Acceptable reasons:

- A library you must use violates a rule.
- Performance measurement (with numbers) shows the standard pattern is the bottleneck.
- The standard pattern is new and the team hasn't ramped yet.

Unacceptable reasons:

- "It felt faster to do it the old way."
- "I always do it like this."
- "We can refactor later."

Document the deviation in `CLAUDE.md` so future Claude sessions don't fight the codebase.
