# Time Capsule — Discovery, Architecture & MVP Plan

_Status: proposal awaiting founder approval · 2026-11-19_

---

## 1. Repository assessment

| Finding | Detail |
|---|---|
| Repos visible to this session | One: `ashwinalur/adbfit` |
| What it is | A **public fork** of Python scripts that parse saved Strava club leaderboard HTML into CSVs for the "Almaden Fit" fitness challenge (Seasons 6–8, last activity Aug 2026). |
| Relevance to Time Capsule | **None.** No shared code, data model, auth, UI or docs. |
| Risks of building here | (1) It is **public**: a product handling the most personal data imaginable must not live in a public repo. (2) It is a **fork**, so it carries an upstream relationship and the fork badge. (3) `main` holds scripts still in seasonal use; rewriting it would break your Strava workflow. |
| Other repos | GitHub search shows nothing else this session can reach. If other relevant repos exist, they aren't connected to this session. |

**Recommendation:** create a **new private repository** (`time-capsule`). Leave `adbfit` alone. I can't create repos from this session, so you'd create an empty private repo and add it to the session (one click), or tell me to proceed on this branch temporarily and migrate the history later.

No existing code, docs or design constrain us. This is greenfield.

---

## 2. Product architecture

### 2.1 The core idea in one sentence
Everything the system knows about a person is a **memory with two timelines**: *when it happened* and *when the person knew or held it*. Every identity (Mirror, Shadow, Time Travel, Projection) is simply **a lens over that memory store**: an anchor age, a viewer, and a set of rules.

This one decision is what makes the product work:
- "Me at 20 shouldn't know what I learned at 41" → filter `known_from_age ≤ 20`.
- "I used to believe X, now I believe Y" → `held_until_age` closes the old belief.
- "Grandpa's war story, which I only heard at 30" → occurred 1944, known from age 30.
- "Projection must never present predictions as memories" → `is_hypothetical` rows are only visible to Projection and are always labelled.
- "Family sees only what I allowed" → visibility filter applied in SQL **before** retrieval, so the model never sees forbidden content.

### 2.2 The four experiences as lenses

| Mode | Anchor age | Who can talk to it | Memory scope | Voice of the persona |
|---|---|---|---|---|
| **Mirror** | Current age | Owner only | Everything currently known/held (incl. private) | "I", reflective, candid |
| **Shadow** | Current age | Owner + authorized people (grants) | Only memories visible to that viewer's circles; never private/sensitive | "I", warm, always discloses it is an AI representation |
| **Time Travel** | Chosen past age (18, 25…) | Owner (optionally granted to others later) | `known_from_age ≤ A` and still held at A; era context ("it's 2003 for you") | Age-appropriate style traits |
| **Projection** | Chosen future age (66) | Owner (optionally granted) | All current memories + owner-written **assumptions** (`is_hypothetical`) | "I imagine / I hope", speculative content flagged in UI |

### 2.3 System overview

```
 ┌───────────── Web app (Next.js, mobile-first PWA) ─────────────┐
 │ Landing · Timeline · Memory capture · Identities · Chat · Circles │
 └───────────────▲───────────────────────────────▲───────────────┘
                 │ server actions / route handlers (streaming)
 ┌───────────────┴──────────── Core domain (packages/core) ────────┐
 │ capsule · memory · timeline · identity · access-policy · audit  │
 │ retrieval (hybrid search + temporal/privacy filters)            │
 │ conversation orchestrator (prompt assembly, citations)          │
 │ ai gateway (interfaces: Chat, Embed, STT, TTS, VoiceClone)      │
 └───────▲──────────────────▲──────────────────▲───────────────────┘
         │                  │                  │
   Postgres + pgvector   Object storage     Job queue (pg-boss,
   (relational, vectors,  (S3-compatible:    Postgres-backed):
    full-text, RLS-ready)  R2 / MinIO local)  embeddings, extraction,
                                              transcription
         AI providers behind adapters: Anthropic (chat), Voyage/OpenAI
         (embeddings), Deepgram/Whisper (STT), ElevenLabs/Cartesia (TTS,
         cloning), Mock provider (offline dev + deterministic tests)
```

**Shape:** a **modular monolith**. One deployable app, with a strict domain package that has no framework imports, so any part (e.g. a voice service or ingestion worker) can be extracted later without a rewrite. For a small team building a product meant to last years, this is the right call. Microservices on day one would be cost without benefit.

### 2.4 Retrieval pipeline (per message)
1. **Resolve lens**: identity → anchor age A, mode, viewer → allowed circles.
2. **Query understanding**: rewrite the user turn into a search query (cheap model; optional).
3. **Hybrid search in one SQL statement**: pgvector similarity + Postgres full-text, fused with Reciprocal Rank Fusion, with hard filters in the `WHERE` clause:
   `capsule_id = ? AND known_from_age <= A AND (held_until_age IS NULL OR held_until_age > A) AND visibility_ok(viewer) AND NOT sealed AND status <> 'rejected' AND (is_hypothetical = false OR mode = 'projection')`
4. **Re-rank & diversify**: importance, verification and MMR, then the top ~12 chunks.
5. **Core self-summary**: a cached, age-bounded "who I am at age A" digest (regenerated when memories change), always included.
6. **Prompt assembly**: stable persona block (cached), knowledge horizon ("you do not know events after year Y"), grounding rules ("if no memory supports it, say you don't remember; never invent memories"), retrieved memories with ids.
7. **Generate (streaming)**: store citations (`message_citations`) so the UI can show *which memories shaped this answer*.
8. **Learn (Mirror only)**: propose new candidate memories from the conversation. They're saved as `pending` until the owner confirms them. Nothing becomes "a memory" silently.

---

## 3. MVP feature breakdown

| # | Feature | Scope in MVP | Explicitly deferred |
|---|---|---|---|
| 1 | **Authentication** | Email + password, magic link, passkeys; sessions; 2FA-ready | Social login, enterprise SSO |
| 2 | **Profile / capsule** | Name, birth date (with precision), short bio, current chapter. Takes about 60 seconds, no questionnaire. | Managing a capsule for someone else (parent) |
| 3 | **Memories & life events** | Quick capture (title + text + approximate date), kinds (event, story, belief, value, opinion, relationship, career, education, preference, trait), fuzzy dates ("summer 2004", "age ~12"), people tags, life chapters, privacy level, source, verification, photo attachment | Bulk import, document parsing, voice notes |
| 4 | **Timeline** | Vertical, age- and year-indexed timeline with chapters; filter by kind, person, privacy; tap to open/edit | Map view, photo-wall view |
| 5 | **Identities** | Mirror & Shadow (auto); create Time Travel (pick age) & Projection (pick age + assumptions); distinct visual theme each | Per-age voice |
| 6 | **Text conversations** | Streaming chat per identity, persistent conversation history, "memories used" panel, speculative-content badges | Voice in/out |
| 7 | **Age/identity-bounded retrieval** | Full pipeline above + an automated **boundary test suite** | LLM "temporal guard" second pass |
| 8 | **Privacy & permissions** | Per-memory visibility (private / circles / all-authorized), sensitivity flags, circles, invite a person by email, grant Shadow access, revoke, access audit log, export & delete-everything | Posthumous release rules, stewards |
| — | **Gradual capture** | "Prompt of the day" (one question at a time), plus memory suggestions from Mirror conversations | Guided interviews, voice interviews |

---

## 4. Technology stack (opinionated)

| Layer | Choice | Why | Main alternative considered |
|---|---|---|---|
| Language | **TypeScript end-to-end** | One language across UI, domain and AI orchestration; strong typing on a data-model-heavy product | Python backend (better ML ecosystem, but we use hosted models; two languages = more friction) |
| Monorepo | **pnpm + Turborepo** | `apps/web`, `packages/core`, `packages/db`, `packages/ai`, later `apps/mobile` | Nx (heavier) |
| Web | **Next.js 15 (App Router) + React 19**, Tailwind CSS v4, Radix primitives, Motion for animation | Mature, SSR + streaming, server actions, great DX, PWA-capable for mobile-first | Remix/React Router 7; SvelteKit |
| Mobile | **PWA first**, **Expo (React Native)** when voice capture needs native APIs (Milestone 9+) | Don't pay for two apps before product-market fit | Native Swift/Kotlin |
| Database | **PostgreSQL 16 + pgvector** | Relational + vector + full-text + JSON in one ACID store; filters and vectors in a single query, which our privacy model depends on | Separate vector DB (Pinecone/Qdrant): adds a sync problem and makes enforcing privacy in a single query harder |
| ORM / migrations | **Drizzle ORM** | SQL-first, typed, supports pgvector, readable migrations | Prisma (weaker raw-SQL/vector ergonomics) |
| Auth | **Better Auth** (self-hosted library, data in our Postgres) | Users table we own (essential for a multi-decade product and data export), passkeys, 2FA, magic links, no per-user pricing | Clerk (fast, but vendor-owned identities and per-MAU cost); Supabase Auth |
| Authorization | Central **policy module** (`can(actor, action, resource)`) + SQL-level visibility filters; Postgres RLS added as defense-in-depth in hardening | Keeps rules in one auditable place | Only RLS (hard to test, tied to DB roles) |
| Files | **S3-compatible**: MinIO locally, **Cloudflare R2** in prod (no egress fees), signed URLs only | Photos/audio grow large; egress costs matter | S3, Supabase Storage |
| Jobs | **pg-boss** (queue in Postgres) | No extra infrastructure; enough for embeddings/extraction/transcription | Inngest / Trigger.dev (nice, but another vendor) |
| AI gateway | Own thin interfaces in `packages/ai`, adapters per provider; official SDKs underneath | Not locked to one vendor; per-task model routing; mock provider for tests | LangChain (too much abstraction for this) |
| Chat LLM | **Claude Opus 5.5** (`claude-opus-5-5`) default for persona conversations; configurable per task | Strong long-context role consistency, nuanced writing, prompt caching makes persona + memory blocks cheap on repeat turns | GPT / Gemini via the same adapter interface |
| Background LLM | Same model by default; optional cheaper model (e.g. Claude Haiku 5.5) for classification/extraction. **Your call on cost.** | Extraction/date-parsing is high-volume and simple | — |
| Embeddings | **Voyage AI** (or OpenAI `text-embedding-3`) via adapter; model id stored on every vector so we can re-embed later | Anthropic doesn't offer embeddings; Voyage is strong for retrieval | Local model (bge/e5) via Ollama: free, good for dev |
| STT (later) | Deepgram or OpenAI transcription; whisper.cpp local option | Accuracy and streaming | AssemblyAI |
| TTS & voice cloning (later) | **ElevenLabs** (professional voice cloning with built-in speaker verification), Cartesia as low-latency option | Quality plus a consent-verification flow | OpenAI TTS (no custom cloning) |
| Hosting (prod) | **Vercel** (web) + **Neon** (Postgres with pgvector, branch per PR) + **R2**; *requires your approval* | Managed, scales to zero, low ops | Fly.io / Railway / AWS (more control, more ops) |
| Observability | Sentry (errors), OpenTelemetry traces for AI calls, structured logs **with PII redaction** | Debug without logging memories | Datadog |
| Testing | Vitest (unit/integration against real Postgres in Docker), Playwright (E2E), retrieval-boundary evals | Boundary correctness is a product promise, so it has to be tested | Jest |
| CI | GitHub Actions: lint, typecheck, test, gitleaks secret scan, migration check | | |

**Local-first development:** the app runs end-to-end with **zero paid services**: Docker Postgres + MinIO plus a deterministic mock AI provider (or local Ollama). Real providers turn on only when you approve keys.

---

## 5. Database & memory model

```text
users                (Better Auth: id, email, …)
capsules             id, owner_user_id, display_name, birth_date, birth_date_precision,
                     bio, created_at                      -- "the person being preserved"
life_chapters        id, capsule_id, title, start_date, end_date, precision, summary, color
people               id, capsule_id, name, relationship, linked_user_id?, notes
memories             id, capsule_id,
                     kind            enum(event, story, belief, value, opinion, fact,
                                          relationship, career, education, preference,
                                          trait, reflection, assumption)
                     title, body, 
                     -- timeline 1: when it happened
                     occurred_start, occurred_end, date_precision enum(day,month,year,decade,approx),
                     age_at_start, age_at_end           (derived, stored)
                     -- timeline 2: when I knew / held it
                     known_from_age   numeric           (default = age_at_start, or "now" for facts learned later)
                     held_until_age   numeric NULL      (beliefs/opinions/traits that changed)
                     is_hypothetical  bool              (projection assumptions only)
                     -- provenance & trust
                     source_type enum(owner_typed, prompt_answer, conversation_extraction,
                                      import_document, voice_transcript, photo_metadata,
                                      family_contribution)
                     source_ref, contributed_by_user_id,
                     verification enum(owner_verified, unverified, pending_review, disputed, rejected)
                     confidence numeric(0..1),
                     -- privacy
                     visibility enum(private, circles, all_authorized),
                     sensitivity text[] (health, finance, intimate, legal, other_people),
                     sealed_until timestamptz NULL      (time-capsule release; post-MVP UI)
                     importance smallint, chapter_id, created_at, updated_at, deleted_at
memory_people        memory_id, person_id
memory_circles       memory_id, circle_id
memory_versions      memory_id, version, body, edited_by, edited_at   (history; nothing silently overwritten)
media_assets         id, capsule_id, storage_key, mime, bytes, sha256, captured_at, exif jsonb,
                     visibility
memory_media         memory_id, media_id
memory_chunks        id, memory_id, chunk_index, content, embedding vector(N),
                     embedding_model, tsv tsvector       (+ denormalised filter columns later)
identities           id, capsule_id, mode enum(mirror, shadow, time_travel, projection),
                     anchor_age NULL (mirror/shadow = live current age), label,
                     style_notes, theme, created_at
self_summaries       capsule_id, anchor_age, viewer_scope, summary, source_hash, generated_at
conversations        id, identity_id, viewer_user_id, title, created_at
messages             id, conversation_id, role, content, model, contains_speculation,
                     token_usage jsonb, created_at
message_citations    message_id, memory_id, score
circles              id, capsule_id, name                 ("Family", "Close friends")
circle_members       circle_id, person_id / user_id
grants               id, capsule_id, grantee_user_id | invite_email, circle_id,
                     allowed_modes text[] (default {shadow}), expires_at, revoked_at
consents             id, user_id, kind (ai_processing, provider:<name>, voice_clone),
                     version, evidence_media_id, granted_at, revoked_at
audit_log            id, capsule_id, actor_user_id, action, target, metadata, at
```

**Why age instead of dates for knowledge boundaries:** ages are how people think about their past ("when I was 25"), they survive fuzzy dates, and they map directly onto identities. Dates are still stored, and ages are derived from them and the birth date.

**Defaults that keep users safe:** new memories default to `private`. Sensitive flags force `private` unless the owner overrides them. AI-extracted memories default to `pending_review` and are excluded from retrieval until confirmed.

---

## 6. Security & privacy considerations

1. **Structural privacy, not prompt privacy.** Access control happens in the SQL query that feeds the model. A Shadow viewer cannot jailbreak their way to a private memory because it is never in context. This is the single most important security property.
2. **Encryption:** TLS everywhere; managed encryption at rest (DB, R2). Post-MVP: envelope encryption (per-capsule data keys in a KMS) for media and `sensitivity`-flagged memories. **Embeddings are treated as sensitive as the text** (they can be partially inverted).
3. **AI providers:** use API tiers that don't train on customer data, and **verify that contractually (DPA, zero-data-retention where available) before production**. Never assume. Each provider used gets a recorded consent entry, and the provider list is visible to the user.
4. **Prompt injection:** imported documents and family contributions are untrusted. They go inside delimited data blocks, never get instruction authority, and can't trigger tools.
5. **AI honesty:** Shadow always discloses it is an AI representation. Projection output is labelled speculative. Grounding rules plus citations reduce invented memories. "I don't remember that" is a feature.
6. **Voice cloning (later):** only the account holder's own voice; recorded consent statement plus provider speaker verification; revocable (deleting it propagates to the provider); voice models never exportable; output disclosure/watermarking; awareness of right-of-publicity and voice laws (e.g. Tennessee ELVIS Act, EU AI Act transparency duties).
7. **Data rights:** full export (JSON + media, open documented format: "your capsule outlives us") and hard delete across DB, storage, vectors and provider-side artifacts. Audit log of every Shadow access.
8. **App security:** passkeys/2FA, rate limiting, CSP, signed short-lived media URLs, least-privilege DB roles, no PII in logs or analytics, gitleaks in CI, secrets only in env/secret manager (`.env` git-ignored, `.env.example` committed).
9. **Users:** 18+ at launch. Content about third parties (people tags) defaults to private.
10. **Emotional safety:** Shadow and Time Travel can touch grief and regret. Gentle framing, an easy "pause" path, and no manipulative engagement mechanics.

---

## 7. Development milestones

| M | Name | Deliverable (each verified, tested, committed) | Size |
|---|---|---|---|
| **M0** | Foundation | Private repo, monorepo, Next.js, Drizzle + Postgres/pgvector (Docker), MinIO, Better Auth (sign up/in/out, passkeys), design system tokens and the four mode themes, CI, test harness, mock AI provider | M |
| **M1** | Capsule & memories | 60-second onboarding, memory capture/edit with fuzzy dates, kinds, people, chapters, privacy, photos, version history, prompt-of-the-day | M |
| **M2** | Timeline | Age/year timeline with chapters, filters, memory detail, landing page with the emotional story | M |
| **M3** | Retrieval core | Embedding jobs, hybrid search, temporal and privacy filters, self-summaries, **boundary test suite** | L |
| **M4** | Identities & conversations | Four modes, persona prompts, streaming chat, citations panel, speculative badges, memory suggestions from Mirror; real LLM adapter (**needs API key approval**) | L |
| **M5** | Shadow & permissions | Circles, invites, grants, viewer experience, revoke, audit log, export/delete | M |
| **M6** | Hardening & private beta | RLS defense-in-depth, rate limits, Sentry, accessibility, performance; deploy to Vercel/Neon/R2 (**needs approval**) | M |
| M7 | Voice I/O | Push-to-talk STT, TTS playback with stock voices | M |
| M8 | Personal voice | Consent flow + verified voice clone, per-identity voice | L |
| M9 | Rich ingestion | Photo EXIF dating, document/journal import, voice-note interviews, guided life-story interviews | L |
| M10 | Mobile app | Expo app (capture-first, offline drafts, recording) | L |
| M11 | Legacy | Sealed memories, posthumous release, stewards/executors, dead-man switch | L |

MVP = M0–M6. Sizes are relative (S < M < L). I'll report back after each milestone with what works, its limits, and the next step.

---

## 8. Complexity & major risks

| Risk | Severity | Mitigation |
|---|---|---|
| **World-knowledge leakage**: "me at 18 in 2003" knows about smartphones because the LLM does | High | Knowledge-horizon instructions + era context; boundary evals; later a cheap "temporal guard" pass that flags anachronisms. It can't be perfect, so the UI frames Time Travel as a reconstruction. |
| **Confabulated memories**: the AI invents plausible life events | High | Grounding rules, citations, "don't remember" behavior, speculative flags, conversation-derived memories require owner approval |
| **Privacy breach** of extremely sensitive data | Critical | Structural retrieval filtering, defaults to private, audit logs, encryption roadmap, minimal third-party surface, security review before beta |
| **Cold start**: thin memory store means a shallow persona | High (product) | Prompt-of-the-day, conversation-to-memory suggestions, low-friction capture; persona quality grows visibly over time |
| **Emotional/ethical harm** (grief, posthumous use, impersonation) | High | Disclosure, consent, revocation, careful copy, no dark patterns, voice cloning only of oneself |
| **Voice-cloning law and misuse** | Medium–High | Consent evidence, provider verification, no export, watermarking, legal review before M8 |
| **Provider cost/lock-in** | Medium | Gateway abstraction, prompt caching of persona blocks, per-task model routing, stored embedding model ids |
| **Long-term durability** (the product must outlive trends) | Medium | Boring, durable tech (Postgres, TS, S3), open export format, owned auth data |
| **Scope creep** | Medium | Strict MVP gate; voice/family/ingestion only after M6 |

---

## Decisions needed from you

1. **Repo:** approve a new **private** repo `time-capsule` (you create it empty and attach it to this session), or allow temporary work on this branch of `adbfit`.
2. **Approve the architecture & roadmap** so M0 can start. M0–M3 cost **$0** (local Docker + mock AI).
3. **Later, at M4:** approval for an Anthropic API key (chat) and an embeddings key (Voyage or OpenAI). Rough cost for one active user in development is a few dollars a month.
