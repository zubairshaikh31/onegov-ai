# ONEGOV AI V2 — PROJECT BRAIN

## 1. Project Overview
OneGov AI v2 is a unified public access portal for Indian citizens to discover, understand, and apply for central and state government services and welfare schemes. It combines high-reliability PostgreSQL relational storage with semantic hybrid search (pgvector + FTS) and RAG-powered AI consultations.

## 2. Current Architecture
The system consists of a multi-container Docker Compose stack fronted by an Nginx reverse proxy.
- **Client Traffic**: Hits Nginx on port `80`.
- **Frontend App**: Routed to Next.js App Router on port `3000`.
- **Backend API**: Routed to FastAPI on port `8000`.
- **Caching & Lock Store**: Redis on port `6379`.
- **Primary Database**: PostgreSQL 16 (with pgvector) mapped to host port `5435` in development.
- **Local AI Engine**: Ollama on port `11434` for embedding fallbacks and local generation.

## 3. Technology Stack
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, React Query, Axios, Zustand.
- **Backend**: FastAPI, Python 3.12, SQLAlchemy 2.0 (async), PostgreSQL (pgvector), Redis (asyncio), Pydantic v2.
- **AI/RAG**: NVIDIA NIM (Nemotron-3.5-Lightning-30b-A3B), Ollama fallback, cosine similarity, FTS keyword matching.
- **Security**: JWT (HttpOnly cookie for refresh token, in-memory for access token), Google Identity Services OAuth 2.0, OTP email/phone verification.

## 4. Frontend Architecture
- **Structure**: Next.js App Router.
- **Routing Rules** (defined in `src/middleware.ts`):
  - **Public Routes**: `/`, `/about`, `/contact`, `/faq`, `/privacy`, `/terms`.
  - **Public Auth Pages**: `/login`, `/register`, `/verify-otp`, `/forgot-password` (redirect to dashboard/admin if logged in).
  - **Protected User Routes**: `/dashboard`, `/profile`, `/ai-chat`, `/services`, `/schemes`, `/search`, `/bookmarks`, `/notifications`, `/settings` (redirect to `/login` if unauthenticated).
  - **Admin-Only Routes**: `/admin` and subpaths (redirect to `/dashboard` if logged-in but non-admin).
- **State Management**: Zustand store (`useAuthStore`) with local storage persistence.
- **Network Layer**: Axios instance with a request interceptor for attaching JWT Bearer tokens and a response interceptor managing an synchronized token refresh queue on 401 errors.

## 5. Backend Architecture
- **Factory Pattern**: FastAPI app initialized via `create_app()` in `app/main.py`.
- **Lifespan Operations**: Handles logging setup, roles seeding on startup, and cleanup of Redis/SQLAlchemy connections on shutdown.
- **Exception Handling**: Standardized response wrapper `ApiResponse` with automated mapping of internal errors via `OneGovError`.
- **Rate Limiting**: Integrated via slowapi (stored in Redis).
- **Authentication**: Admin privileges verified via FastAPI dependencies checking roles association.

## 6. Database Architecture
PostgreSQL database leveraging `pgvector` for similarity calculations.
- **Custom Types**: `SafeVector` custom type dynamically compiles to `VECTOR(dim)` when pgvector is enabled, falling back to `FLOAT[]` (double precision array) otherwise.
- **Casting**: JSONB list columns (like `tags` and `search_keywords`) cast to `VARCHAR` using `sqlalchemy.String` for keyword search queries.

## 7. AI Architecture
- **Primary LLM**: `nvidia/nemotron-3.5-lightning-30b-a3b` hosted via NVIDIA NIM API.
- **System Prompt**: Enforces rigorous linear/startup style formatting and includes an explicit negative constraint at the absolute top of `SYSTEM_RAG_PROMPT` to suppress verbose model reasoning/thinking monologue from appearing in user outputs.
- **Fallback**: Fallback to local Ollama container if NVIDIA NIM responds with an error or times out.

## 8. RAG Architecture
- **Embeddings**: Generated using local Ollama model `nomic-embed-text` (768 dimensions).
- **Retriever**: Queries PostgreSQL using pgvector similarity calculations to retrieve top 5 matches.
- **Citations**: Sources and URLs mapped directly to response payloads.

## 9. Authentication Architecture
- **Access Token**: Short-lived JWT (30 mins), stored strictly in frontend memory.
- **Refresh Token**: Long-lived JWT (7 days), stored in a secure, `HttpOnly`, `SameSite=Lax` cookie (`refresh_token`) to prevent XSS theft.
- **Authorization Header**: Passed as `Authorization: Bearer <access_token>` in all Axios requests.

## 10. Google OAuth
- **SDK**: Google Identity Services client-side popup.
- **Verification**: Verified server-side via `google-auth` library against the configured client ID.
- **User Creation**: Unregistered Google users are automatically created with default `user` roles. Existing users are logged in.

## 11. Email / OTP
- **Verification**: 6-digit OTP code sent during registration or password resets.
- **Mocking**: Enabled in local development environments via `ECHO_DEV_OTP=True` (OTPs printed to server logs).
- **SMTP**: Email dispatch via SMTP server config.

## 12. Search Architecture
- **Hybrid Search**: Leverages typo-tolerant ILIKE queries on service names, descriptions, categories, and tags combined with pgvector semantic similarity.
- **Trending Searches**: Frequently typed queries (len >= 4) queried from the last 30 days of `SearchHistory`. Padded with defaults to prevent showing truncated keystroke garbage.

## 13. Government Services
- **Records**: 830 services seeded.
- **Relations**: 80 custom services have fully populated required documents, application steps, and FAQs. The remaining 750 services act as index cards directing citizens to official portal links.

## 14. Government Schemes
- **Records**: 108 schemes seeded.
- **State Classification**: Grouped under central level or state level.

## 15. Knowledge Base
- **Knowledge Chunks**: 938 chunks seeded in the database.
- **Embeddings**: 100% populated with 768-dimension vectors.

## 16. YouTube Integration
- **Videos**: 4 verified tutorial videos seeded.
- **Service Mappings**: 325 links mapped to various services.
- **Frontend**: Responsive YouTube embedded iframe component rendered inside a dynamic "Video Tutorials" tab on `/services/[slug]`.

## 17. Admin System
- **Routes**: Admin dashboard with user lists, analytics charts, AI log viewer, and feedback manager.
- **Authentication**: Protected via role checks.

## 18. Docker / Infrastructure
- **Containers**:
  - `onegov_nginx` (Port 80)
  - `onegov_frontend` (Port 3000)
  - `onegov_backend` (Port 8000)
  - `onegov_postgres` (Port 5435 -> 5432)
  - `onegov_redis` (Port 6379)
  - `onegov_ollama` (Port 11434)

## 19. Environment Variables
- `APP_ENV`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `NVIDIA_API_KEY`
- `NVIDIA_BASE_URL`
- `NVIDIA_MODEL`
- `OLLAMA_BASE_URL`

## 20. Current Database Statistics
- **Users**: 3
- **Roles**: 3
- **Ministries**: 35
- **Departments**: 28
- **Categories**: 18
- **Required Documents**: 150
- **Service Documents**: 263
- **Application Steps**: 275
- **Bookmarks**: 1
- **Notifications**: 0
- **Search History**: 4
- **AI Chat History**: 44
- **Feedback**: 0
- **FAQs**: 930
- **Services**: 830
- **Schemes**: 108
- **Knowledge Chunks**: 938
- **Videos**: 4
- **Service Videos**: 325
- **Audit Logs**: 147

## 21. Feature Status Matrix
- **Email/Password Login**: COMPLETE
- **Google OAuth Login**: COMPLETE
- **Global Search API & UI**: COMPLETE
- **Service Details & Tutorials**: COMPLETE
- **AI Chatbot & RAG**: COMPLETE
- **Admin Dashboard**: COMPLETE
- **JWT token rotation**: COMPLETE

## 22. Known Bugs
- *None.* (All critical search typecast failures, trending term garbage, and authentication header issues have been audited and repaired).

## 23. Known Limitations
- **Intelligence Layer Integration**: The robust `/intelligence/*` endpoints are fully functional on the backend, but the frontend currently does not call them.

## 24. Security Status
- **Access Tokens**: Local in-memory storage (safe from XSS/local storage leaks).
- **Refresh Tokens**: HttpOnly cookie configuration.
- **Credentials**: Google token audience matches configured Client ID.

## 25. Testing Status
- **Backend pytest**: 32 / 32 Passed
- **TypeScript**: 0 compiler errors (`tsc --noEmit` verified)
- **Next.js Build**: Generation successful

## 26. Production Readiness
- **Status**: **PRODUCTION READY** (End-to-end verification succeeds)

## 27. Architecture Decisions
1. **HttpOnly Cookies**: Refresh token is isolated from JS runtime to prevent data theft.
2. **In-Memory Access Tokens**: Prevent security leaks through localStorage.
3. **Typo Tolerant Casting**: PostgreSQL typecasts JSONB arrays case-insensitively using standard varchar cast mappings.
4. **Reasoning Suppression & Query Classification**: Used `enable_thinking: False` in `chat_template_kwargs` to suppress internal reasoning monologues, combined with a lightweight pipeline classification router (GENERAL vs GOVERNMENT) to allow standard general knowledge chats alongside grounded government RAG answers.

## 28. Development Rules
- **RULE 1**: Every AI coding session MUST read BRAIN.md first.
- **RULE 2**: BRAIN.md is project development memory.
- **RULE 3**: Do not repeat a complete project audit for every small change.
- **RULE 4**: Use BRAIN.md to identify the affected subsystem.
- **RULE 5**: Only inspect the relevant code for normal feature changes.
- **RULE 6**: If BRAIN.md conflicts with the actual code, verify ONLY the conflicting subsystem and update BRAIN.md.
- **RULE 7**: Never assume something works simply because BRAIN.md says it works.
- **RULE 8**: When modifying a feature, perform targeted verification.
- **RULE 9**: When an architectural change occurs, update BRAIN.md.
- **RULE 10**: When a feature is added, update BRAIN.md.
- **RULE 11**: When a bug is fixed, update BRAIN.md.
- **RULE 12**: When a dependency changes, update BRAIN.md.
- **RULE 13**: When database schema changes, update BRAIN.md.
- **RULE 14**: When AI provider/model changes, update BRAIN.md.
- **RULE 15**: Never store secrets inside BRAIN.md.
- **RULE 16**: Never claim production-ready without evidence.
- **RULE 17**: Never invent government services, government URLs, fees, eligibility criteria, documents, helplines or YouTube videos.
- **RULE 18**: Government information must be sourced from reliable/official sources when verification is required.
- **RULE 19**: Every future feature should preserve existing functionality and improve the relevant area rather than simply patching it.
- **RULE 20**: Every meaningful upgrade must include appropriate testing.

## 29. Future Upgrade Roadmap
1. **Integrate Intelligence Layer**: Render citizen journeys, life events, and deterministic eligibility calculator on the frontend.
2. **Push Notifications**: Connect the notifications store to real-time events.

## 30. Change Log
- **2026-08-30**: Fixed Axios Interceptor refresh loop bypass for public auth routes.
- **2026-08-31**: Resolved search 500 error, filtered popular searches from typing garbage, and integrated YouTube tutorials to services details dynamically. Upgraded chatbot with a query classification layer (GENERAL vs GOVERNMENT), query expansion in RAG retriever, and reasoning trace suppression parameters.
