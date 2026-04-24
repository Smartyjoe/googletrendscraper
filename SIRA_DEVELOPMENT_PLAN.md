# SIRA Development Plan

## Goal
Build a Smart Intelligence Research API that turns `title` and/or `description` into a grounded research bundle for AI content generation.

## Phase 1 (Implemented in this commit)
1. Add new endpoint: `POST /api/sira/research`.
2. Add polymorphic input model:
   - `title` optional
   - `description` optional
   - at least one required
3. Add OpenRouter client utility with structured JSON schema output.
4. Add intent analysis stage:
   - entities
   - claims
   - tone
   - 3-5 search queries
5. Add market pulse stage with pytrends rising/top related queries.
6. Add web discovery and extraction stage:
   - DDGS query fan-out
   - URL dedupe
   - Trafilatura text extraction
7. Add fact-check and gap-analysis stage through OpenRouter (with fallback).
8. Add response bundle structure with:
   - `meta`
   - `intent_analysis`
   - `seo_intel`
   - `user_context_analysis`
   - `source_material`

## Phase 2 (Next)
1. Split SIRA logic into `services/` modules (`openrouter`, `search`, `extract`, `factcheck`).
2. Add async connection reuse (`httpx.AsyncClient` lifecycle on startup/shutdown).
3. Add source quality scoring:
   - domain trust
   - recency
   - cross-source corroboration count
4. Add query strategy by mode:
   - title-only discovery
   - description-only verification
   - hybrid mode
5. Add max-content/token guards and truncation policy.

## Current Status (2026-02-28)
1. `POST /api/sira/research` implemented and live in `pytrends_api.py`.
2. SIRA orchestration extracted to `services/sira_service.py`.
3. Retries/backoff and per-stage timeout budgets added in the orchestration pipeline.
4. Stage timing telemetry now included in `response.pipeline.stage_timings`.
5. Endpoint tests added for title-only, description-only, and hybrid request modes (`tests/test_sira_endpoint.py`).

## Phase 3 (Reliability + Performance)
1. Add retries/backoff for OpenRouter, pytrends, and web fetches.
2. Add strict stage time budgets and degraded return path.
3. Add observability:
   - request id
   - stage timing
   - cache hit/miss
4. Add tiered caching:
   - intent cache
   - search cache
   - extraction cache
   - final bundle cache

## Phase 4 (Testing + Release)
1. Add automated tests for:
   - title-only / description-only / hybrid
   - schema validation
   - fallback behavior when dependencies are missing
2. Update API docs and example payloads.
3. Staging soak test and latency baseline.
4. Production rollout behind feature flag.

## Success Criteria
1. Endpoint returns source-grounded bundle with provenance URLs.
2. P95 latency:
   - fast mode: <= 6s
   - deep mode: <= 15s
3. Graceful degradation when optional services fail.
4. Repeat queries hit cache and complete substantially faster.
