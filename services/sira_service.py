"""
SIRA orchestration service.
Handles intent analysis, trends, web research, and fact-check synthesis.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import httpx
import pandas as pd

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

try:
    import trafilatura
except ImportError:
    trafilatura = None

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SIRAServiceConfig:
    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_model_intent: str
    openrouter_model_factcheck: str
    openrouter_referer: str
    openrouter_app_title: str
    max_sources_fast: int = 3
    max_sources_deep: int = 5
    max_urls_per_query_fast: int = 3
    max_urls_per_query_deep: int = 5
    cache_ttl_seconds: int = 3600
    deep_timeout_seconds: float = 15.0
    fast_timeout_seconds: float = 6.0


def clean_text(value: str) -> str:
    value = value or ""
    return re.sub(r"\s+", " ", value).strip()


def heuristic_queries(title: str, description: str, max_queries: int = 5) -> List[str]:
    queries: List[str] = []
    if title:
        queries.extend([title, f"{title} latest trends", f"{title} case study"])
    if description:
        excerpt = description[:120]
        queries.extend([excerpt, f"{excerpt} statistics"])

    seen = set()
    deduped = []
    for query in queries:
        cleaned = clean_text(query)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
        if len(deduped) >= max_queries:
            break
    return deduped


def rank_source_credibility(url: str) -> str:
    domain = (url or "").lower()
    if any(x in domain for x in [".gov", ".edu", "who.int", "oecd.org", "worldbank.org"]):
        return "High"
    if any(x in domain for x in ["wikipedia.org", "medium.com", "substack.com"]):
        return "Low"
    return "Medium"


async def _retry_async(
    operation: Callable[[], Any],
    retries: int = 2,
    base_delay: float = 0.4,
) -> Any:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return await operation()
        except Exception as exc:
            last_exc = exc
            if attempt >= retries:
                break
            await asyncio.sleep(base_delay * (2 ** attempt))
    raise last_exc


async def _openrouter_chat_json(
    config: SIRAServiceConfig,
    model: str,
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    schema: Dict[str, Any],
    timeout_seconds: float = 18.0,
) -> Dict[str, Any]:
    if not config.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {config.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    if config.openrouter_referer:
        headers["HTTP-Referer"] = config.openrouter_referer
    if config.openrouter_app_title:
        headers["X-Title"] = config.openrouter_app_title

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        },
        "provider": {"require_parameters": True, "allow_fallbacks": True},
    }

    timeout = httpx.Timeout(timeout_seconds, connect=8.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{config.openrouter_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("OpenRouter returned no choices")

    content = choices[0].get("message", {}).get("content")
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("OpenRouter returned empty content")

    return json.loads(content)


async def _ddgs_search(query: str, max_results: int, timelimit: str) -> List[Dict[str, Any]]:
    if DDGS is None:
        return []

    def _search() -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results, timelimit=timelimit):
                results.append(item)
        return results

    return await asyncio.to_thread(_search)


async def _extract_source_content(url: str, timeout_seconds: float = 7.5) -> Dict[str, Any]:
    source: Dict[str, Any] = {
        "source_title": "",
        "url": url,
        "full_content": "",
        "published_date": None,
    }
    timeout = httpx.Timeout(timeout_seconds, connect=4.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text

    if trafilatura is None:
        source["full_content"] = clean_text(html)[:5000]
        return source

    extracted = trafilatura.extract(
        html,
        output_format="json",
        with_metadata=True,
        include_links=False,
    )
    if not extracted:
        return source

    parsed = json.loads(extracted)
    source["source_title"] = parsed.get("title", "") or ""
    source["full_content"] = (parsed.get("text", "") or "")[:12000]
    source["published_date"] = parsed.get("date")
    return source


async def run_sira_pipeline(
    *,
    title: str,
    description: str,
    geo: str,
    depth: str,
    config: SIRAServiceConfig,
    get_pytrends_client: Callable[[], Any],
) -> Dict[str, Any]:
    title = clean_text(title)
    description = clean_text(description)
    geo = clean_text(geo).upper()
    depth = clean_text(depth).lower() or "deep"
    task_type = "hybrid" if title and description else ("discovery" if title else "verification")

    stage_times: Dict[str, float] = {}
    t0_total = time.perf_counter()
    budget_total = config.deep_timeout_seconds if depth == "deep" else config.fast_timeout_seconds

    max_urls_per_query = config.max_urls_per_query_deep if depth == "deep" else config.max_urls_per_query_fast
    max_sources = config.max_sources_deep if depth == "deep" else config.max_sources_fast
    timelimit = "y" if depth == "deep" else "m"

    intent_data: Dict[str, Any] = {
        "entities": [],
        "claims": [],
        "tone": "neutral",
        "search_queries": heuristic_queries(title, description, max_queries=5),
    }
    analysis_data = {
        "confirmed_facts": [],
        "conflict_points": [],
        "gaps": [],
        "new_insights": [],
        "suggested_h2_headers": [],
    }
    rising_trends: List[str] = []
    top_keywords: List[str] = []
    source_material: List[Dict[str, Any]] = []

    # Stage 1: Intent analysis
    stage_start = time.perf_counter()
    if description and config.openrouter_api_key:
        intent_schema = {
            "type": "object",
            "properties": {
                "entities": {"type": "array", "items": {"type": "string"}},
                "claims": {"type": "array", "items": {"type": "string"}},
                "tone": {"type": "string"},
                "search_queries": {"type": "array", "minItems": 3, "maxItems": 5, "items": {"type": "string"}},
            },
            "required": ["entities", "claims", "tone", "search_queries"],
            "additionalProperties": False,
        }
        try:
            async def _intent_call():
                return await _openrouter_chat_json(
                    config=config,
                    model=config.openrouter_model_intent,
                    system_prompt=(
                        "You are an intent analysis engine for a research API. "
                        "Extract concrete entities, factual claims, tone, and optimized web search queries."
                    ),
                    user_prompt=(
                        f"Title: {title or 'N/A'}\n"
                        f"Description: {description}\n"
                        "Return 3-5 high quality web search queries. Keep queries concise."
                    ),
                    schema_name="intent_analysis",
                    schema=intent_schema,
                )

            intent_data = await asyncio.wait_for(_retry_async(_intent_call, retries=1), timeout=3.5)
        except Exception as exc:
            logger.warning(f"SIRA intent fallback triggered: {exc}")
    stage_times["intent_seconds"] = round(time.perf_counter() - stage_start, 3)

    search_queries = intent_data.get("search_queries") or heuristic_queries(title, description, max_queries=5)
    search_queries = [clean_text(q) for q in search_queries if clean_text(q)]
    if not search_queries:
        search_queries = heuristic_queries(title, description, max_queries=5)

    # Stage 2: Trends pulse
    stage_start = time.perf_counter()
    primary_topic = title or (search_queries[0] if search_queries else "")
    if primary_topic:
        try:
            async def _trend_call():
                def _sync_fetch():
                    pytrends = get_pytrends_client()
                    pytrends.build_payload([primary_topic], timeframe="today 12-m", geo=geo)
                    related = pytrends.related_queries().get(primary_topic, {})
                    rising_df = related.get("rising")
                    top_df = related.get("top")
                    return rising_df, top_df

                return await asyncio.to_thread(_sync_fetch)

            rising_df, top_df = await asyncio.wait_for(_retry_async(_trend_call, retries=1), timeout=4.0)
            if isinstance(rising_df, pd.DataFrame) and not rising_df.empty and "query" in rising_df.columns:
                rising_trends = [str(v) for v in rising_df["query"].head(8).tolist()]
            if isinstance(top_df, pd.DataFrame) and not top_df.empty and "query" in top_df.columns:
                top_keywords = [str(v) for v in top_df["query"].head(8).tolist()]
        except Exception as exc:
            logger.warning(f"SIRA trends stage degraded: {exc}")
    stage_times["trends_seconds"] = round(time.perf_counter() - stage_start, 3)

    # Stage 3: Search discovery
    stage_start = time.perf_counter()
    candidates: List[Dict[str, Any]] = []
    try:
        async def _search_call():
            tasks = [_ddgs_search(query=q, max_results=max_urls_per_query, timelimit=timelimit) for q in search_queries]
            return await asyncio.gather(*tasks, return_exceptions=True)

        search_results_nested = await asyncio.wait_for(_retry_async(_search_call, retries=1), timeout=4.0)
        seen_urls = set()
        for result in search_results_nested:
            if isinstance(result, Exception):
                continue
            for item in result:
                url = clean_text(item.get("href") or item.get("url") or "")
                if not url or url in seen_urls:
                    continue
                if not (url.startswith("http://") or url.startswith("https://")):
                    continue
                seen_urls.add(url)
                candidates.append(
                    {
                        "url": url,
                        "title": clean_text(item.get("title", "")),
                        "snippet": clean_text(item.get("body") or item.get("snippet") or ""),
                    }
                )
                if len(candidates) >= (max_sources * 2):
                    break
            if len(candidates) >= (max_sources * 2):
                break
    except Exception as exc:
        logger.warning(f"SIRA search stage degraded: {exc}")
    stage_times["search_seconds"] = round(time.perf_counter() - stage_start, 3)

    # Stage 4: Extraction
    stage_start = time.perf_counter()
    try:
        semaphore = asyncio.Semaphore(4)

        async def _extract_one(candidate: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    extracted = await _retry_async(
                        lambda: _extract_source_content(candidate["url"], timeout_seconds=7.5),
                        retries=1,
                    )
                    if not extracted.get("full_content"):
                        return None
                    return {
                        "source_title": extracted.get("source_title") or candidate.get("title") or "Untitled Source",
                        "url": extracted.get("url"),
                        "full_content": extracted.get("full_content"),
                        "credibility_score": rank_source_credibility(extracted.get("url")),
                        "published_date": extracted.get("published_date"),
                    }
                except Exception as exc:
                    logger.warning(f"SIRA extraction failed for {candidate.get('url')}: {exc}")
                    return None

        async def _extract_call():
            tasks = [_extract_one(candidate) for candidate in candidates[:max_sources]]
            return await asyncio.gather(*tasks)

        extracted_sources = await asyncio.wait_for(_extract_call(), timeout=6.5)
        source_material = [source for source in extracted_sources if source]
    except Exception as exc:
        logger.warning(f"SIRA extraction stage degraded: {exc}")
    stage_times["extract_seconds"] = round(time.perf_counter() - stage_start, 3)

    # Stage 5: Fact-check synthesis
    stage_start = time.perf_counter()
    if description and source_material and config.openrouter_api_key:
        factcheck_schema = {
            "type": "object",
            "properties": {
                "confirmed_facts": {"type": "array", "items": {"type": "string"}},
                "conflict_points": {"type": "array", "items": {"type": "string"}},
                "gaps": {"type": "array", "items": {"type": "string"}},
                "new_insights": {"type": "array", "items": {"type": "string"}},
                "suggested_h2_headers": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["confirmed_facts", "conflict_points", "gaps", "new_insights", "suggested_h2_headers"],
            "additionalProperties": False,
        }
        try:
            evidence_payload = [
                {
                    "title": source["source_title"],
                    "url": source["url"],
                    "content_excerpt": source["full_content"][:1800],
                }
                for source in source_material
            ]

            async def _factcheck_call():
                return await _openrouter_chat_json(
                    config=config,
                    model=config.openrouter_model_factcheck,
                    system_prompt=(
                        "You are a fact-check and gap-analysis engine. "
                        "Use only provided sources. If evidence is weak, mark as gaps."
                    ),
                    user_prompt=(
                        f"User title: {title or 'N/A'}\n"
                        f"User description: {description}\n"
                        f"Extracted evidence JSON: {json.dumps(evidence_payload)}"
                    ),
                    schema_name="factcheck_analysis",
                    schema=factcheck_schema,
                )

            analysis_data = await asyncio.wait_for(_retry_async(_factcheck_call, retries=1), timeout=4.0)
        except Exception as exc:
            logger.warning(f"SIRA fact-check stage degraded: {exc}")
    stage_times["factcheck_seconds"] = round(time.perf_counter() - stage_start, 3)

    if not analysis_data["suggested_h2_headers"]:
        topic = title or primary_topic or "Topic"
        analysis_data["suggested_h2_headers"] = [
            f"Why {topic} Matters in 2026",
            f"Current Trends Shaping {topic}",
            f"What to Watch Next in {topic}",
        ]

    primary_keywords: List[str] = []
    seen_keywords = set()
    for item in [primary_topic, *top_keywords]:
        cleaned = clean_text(item)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen_keywords:
            continue
        seen_keywords.add(key)
        primary_keywords.append(cleaned)

    total_seconds = round(time.perf_counter() - t0_total, 3)
    timed_out_budget = total_seconds > budget_total

    return {
        "meta": {
            "status": "success",
            "task_type": task_type,
            "research_depth": depth,
            "timestamp": datetime.utcnow().isoformat(),
            "latency_seconds": total_seconds,
            "latency_budget_seconds": budget_total,
            "budget_exceeded": timed_out_budget,
        },
        "intent_analysis": {
            "entities": intent_data.get("entities", []),
            "claims": intent_data.get("claims", []),
            "tone": intent_data.get("tone", "neutral"),
            "search_queries": search_queries,
        },
        "seo_intel": {
            "primary_keywords": primary_keywords[:8],
            "rising_trends": rising_trends[:8],
            "suggested_h2_headers": analysis_data.get("suggested_h2_headers", []),
        },
        "user_context_analysis": {
            "confirmed_facts": analysis_data.get("confirmed_facts", []),
            "conflict_points": analysis_data.get("conflict_points", []),
            "gaps": analysis_data.get("gaps", []),
            "new_insights": analysis_data.get("new_insights", []),
        },
        "source_material": source_material,
        "pipeline": {
            "openrouter_enabled": bool(config.openrouter_api_key),
            "search_enabled": DDGS is not None,
            "extractor_enabled": trafilatura is not None,
            "sources_collected": len(source_material),
            "stage_timings": stage_times,
        },
    }
