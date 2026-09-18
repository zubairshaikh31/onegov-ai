# OneGov AI v2 — Full System Audit, Debug & Fix

This document contains a comprehensive audit of all platform subsystems, covering authentication flows, database persistence, CORS configs, AI/RAG grounding, and automated test coverages.

| Feature / Subsystem | Current State | Problem | File | Required Fix | Priority | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Response Interceptor** | Resolved | Legitimate 401s on login/register/forgot-password caused token refresh loops, swallowing the validation errors. | `frontend/src/lib/api/client.ts` | Bypass the refresh token interceptor if request URL matches `/auth/` routes. | Critical | **FIXED** |
| **Database Port Mapping** | Resolved | System PostgreSQL (5432) collision on Windows host. | `docker-compose.yml` | Remapped PostgreSQL host port to 5435. | High | **RESOLVED** |
| **Alembic Migration Host** | Resolved | alembic env.py parsed localhost:5433 from env instead of container host. | `backend/migrations/env.py` | Prioritized `DATABASE_URL` over env variables for container launch. | High | **RESOLVED** |
| **SafeVector DB Binds** | Resolved | custom SQLAlchemy types crashed during pgvector query binds on asyncpg. | `backend/app/models/government.py` | Implemented `bind_processor`, `result_processor`, and `comparator_factory`. | Critical | **RESOLVED** |
| **SQLAlchemy Cache Key** | Resolved | UserDefinedType custom type didn't have cache key set. | `backend/app/models/government.py` | Set `cache_ok = True` on `SafeVector` class. | Medium | **RESOLVED** |
| **NVIDIA Nemotron NIM** | Resolved | NVIDIA LLM provider not implemented or configured. | `ai/services/nvidia_provider.py` | Created `NvidiaProvider` class pointing to integrate.api.nvidia.com. | High | **RESOLVED** |
| **LLM Provider Factory** | Resolved | Provider factory lacked nvidia NIM integration. | `ai/services/factory.py` | Registered `nvidia` and allowed it in settings literal validation. | High | **RESOLVED** |
| **Ollama Healthcheck** | Resolved | curl is missing from official Ollama image, marking it unhealthy. | `docker-compose.yml` | Replaced healthcheck command with `ollama list`. | Medium | **RESOLVED** |
| **React Duplicate Keys** | Resolved | Badges in RAG citation list used indices for keys, causing console warnings. | `frontend/src/app/(dashboard)/ai-chat/page.tsx` | Swapped index keys with stable service/scheme slugs. | Medium | **RESOLVED** |
