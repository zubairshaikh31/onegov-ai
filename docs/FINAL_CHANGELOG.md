# OneGov AI v2 — Final Changelog

## Files Changed
- `frontend/src/lib/api/client.ts`: Fixed token refresh interceptor to prevent intercepting public `/auth/` endpoints.
- `backend/app/models/government.py`:
  - Implemented parameter serialization handlers (`bind_processor`, `result_processor`, `comparator_factory`) for the custom `SafeVector` class.
  - Set `cache_ok = True` to enable SQLAlchemy statement caching.
- `backend/app/core/config.py`: Added Pydantic Settings attributes for the `nvidia` primary LLM provider.
- `ai/services/nvidia_provider.py`: Created the OpenAI-compatible Nvidia NIM client.
- `ai/services/factory.py`: Registered the new `nvidia` provider.
- `docker-compose.yml`:
  - Remapped host PostgreSQL port to `5435` to avoid collisions.
  - Configured environment variables overrides for containerized communication.
  - Updated `onegov_ollama` health check to use `ollama list`.
- `backend/migrations/env.py`: Modified `get_url()` to prioritize `DATABASE_URL`.
- `frontend/src/app/(dashboard)/ai-chat/page.tsx`: Fixed index-based keys in React lists.
- `backend/tests/unit/test_nvidia_provider.py`: Added unit tests for `NvidiaProvider`.

## Database Changes
- Custom `SafeVector` fully serializes vector array inputs to text string representation for pgvector database compatibility on asyncpg.
- Enabled SQLAlchemy Statement Caching for vector type operations.

## API Changes
- Added `/api/v1/ai/health` validation status checks for `nvidia` primary and `ollama` fallback services.
- Corrected `/auth/refresh` validation payloads by allowing empty payloads (resolving to cookies).

## Frontend Changes
- Fixed Axios request and response interceptors to prevent circular redirects on public authentication routes.
- Wiped React key index warnings.

## AI & RAG Changes
- Configured NVIDIA NIM (Nemotron-3.5-Lightning-30b-A3B) as primary LLM.
- Set up local Llama 3.2 container as resilient fallback.
- Filtered out the `reasoning_content` parameter in NIM streams.

## Security Changes
- Bypassed storing raw access tokens in browser `localStorage`.
- Ensured Google OAuth OAuth token verification fails closed when no server client ID is configured.

## Docker Changes
- Remapped host-bound database port and enabled service name networking.
- Fixed Ollama image health checking logic.

## Tests Added
- `backend/tests/unit/test_nvidia_provider.py` (3 test cases covering initialization, chat, and stream token extraction/reasoning filtering).
