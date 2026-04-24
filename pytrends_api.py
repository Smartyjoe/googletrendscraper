"""
Google Trends API - Comprehensive Edition
Production-ready FastAPI service with caching, all endpoints, and comprehensive research capability
"""

from fastapi import FastAPI, Request, HTTPException, Security, status, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pytrends.request import TrendReq
from pydantic import BaseModel, Field, root_validator
from typing import Optional, List, Dict, Any
import logging
from logging.handlers import RotatingFileHandler
import os
from secrets import compare_digest
from datetime import datetime
import sys
import random
import time
import pandas as pd
from dotenv import load_dotenv
import certifi
load_dotenv()

# Fix for SSL: CERTIFICATE_VERIFY_FAILED on cloud environments like Render
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
import requests
from urllib3.exceptions import InsecureRequestWarning
print(f"SSL CA Bundle set to: {certifi.where()}")

# Optional: Disable SSL verification if explicitly requested (debugging only)
if os.getenv("VERIFY_SSL", "true").lower() == "false":
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    # Monkey patch requests to default verify=False
    _original_request = requests.Session.request
    def _new_request(self, *args, **kwargs):
        kwargs.setdefault('verify', False)
        return _original_request(self, *args, **kwargs)
    requests.Session.request = _new_request
    print("WARNING: SSL Verification is DISABLED globally!")


# Import cache manager
from cache_manager import cache
from services.sira_service import SIRAServiceConfig, clean_text, run_sira_pipeline
from services import sira_service
from proxy_manager import proxy_manager

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load secret from environment variable
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "YOUR_SECRET_KEY_CHANGE_THIS")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL_INTENT = os.getenv("OPENROUTER_MODEL_INTENT", "openai/gpt-4o-mini")
OPENROUTER_MODEL_FACTCHECK = os.getenv("OPENROUTER_MODEL_FACTCHECK", "openai/gpt-4o-mini")
OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER", "")
OPENROUTER_APP_TITLE = os.getenv("OPENROUTER_APP_TITLE", "PyTrends SIRA API")

# Validate that secret has been changed
if API_SECRET_KEY == "YOUR_SECRET_KEY_CHANGE_THIS":
    print("WARNING: Using default API secret key! Set API_SECRET_KEY environment variable.")

# Cache TTL settings (in seconds)
CACHE_TTL_SHORT = 1800      # 30 minutes - for trending/realtime data
CACHE_TTL_MEDIUM = 3600     # 1 hour - for most queries
CACHE_TTL_LONG = 7200       # 2 hours - for historical data
SIRA_MAX_SOURCES_FAST = 3
SIRA_MAX_SOURCES_DEEP = 5
SIRA_MAX_URLS_PER_QUERY_FAST = 3
SIRA_MAX_URLS_PER_QUERY_DEEP = 5

# ============================================================================
# LOGGING SETUP
# ============================================================================

log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            os.path.join(log_dir, "pytrends_api.log"),
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler(sys.stdout)

    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Google Trends API - Comprehensive Edition",
    description="Production-ready API for fetching Google Trends data with caching and all available endpoints",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_pytrends_client(proxy_url: Optional[str] = None) -> TrendReq:
    """
    Initialize and return a pytrends client with proxy support.
    """
    if proxy_url is None:
        proxy_url = proxy_manager.get_proxy()

    if proxy_url:
        proxies = [proxy_url]
        logger.debug(f"PyTrends client using proxy: {proxy_url[:40]}...")
    else:
        proxies = ''
        logger.warning("No proxy configured — direct cloud requests may trigger Google 429 rate limits.")

    return TrendReq(
        hl='en-US',
        tz=360,
        timeout=(10, 25),
        retries=3,
        backoff_factor=1.0,
        proxies=proxies
    )

def execute_with_proxy_retry(operation_fn, max_retries: int = 3):
    """
    Execute a pytrends operation with automatic proxy rotation.
    """
    last_error = None
    current_proxy = proxy_manager.get_proxy()

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(random.uniform(2, 5) * attempt)
            pytrends = get_pytrends_client(proxy_url=current_proxy)
            return operation_fn(pytrends)
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            is_rate_limit = any(x in error_str for x in ['429', 'too many', 'sorry', 'responseerror'])
            if is_rate_limit and attempt < max_retries - 1:
                proxy_manager.mark_failed(current_proxy)
                current_proxy = proxy_manager.rotate()
            else:
                raise
    raise last_error

def safe_dataframe_to_dict(df) -> List[Dict[str, Any]]:
    """Safely convert pandas DataFrame to list of dictionaries"""
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        return []
    
    try:
        result = df.reset_index().to_dict(orient='records')
        cleaned_records = []
        for record in result:
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value):
                    cleaned_record[key] = None
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)
        return cleaned_records
    except Exception as e:
        logger.error(f"Error converting DataFrame to dict: {e}")
        return []

def dataframe_to_json_serializable(df) -> Dict[str, Any]:
    
    try:
        # Reset index to include date/time as a column
        df_reset = df.reset_index()
        
        # Convert to dictionary
        result = df_reset.to_dict(orient='records')
        
        # Clean NaN values
        cleaned = []
        for record in result:
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value):
                    cleaned_record[key] = None
                elif isinstance(value, pd.Timestamp):
                    cleaned_record[key] = value.isoformat()
                else:
                    cleaned_record[key] = value
            cleaned.append(cleaned_record)
        
        return cleaned
    except Exception as e:
        logger.error(f"Error converting DataFrame: {e}")
        return {}

# ============================================================================
# AUTHENTICATION
# ============================================================================

# Security scheme exposed in OpenAPI/Swagger (shows Authorize button)
api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    auto_error=False
)

async def verify_api_key(request: Request, api_key: Optional[str] = Security(api_key_header)):
    """Verify API key from request headers"""
    if not api_key:
        logger.warning(f"Missing API key from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header."
        )
    
    if not compare_digest(api_key, API_SECRET_KEY):
        logger.warning(f"Invalid API key attempt from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class InterestOverTimeRequest(BaseModel):
    """Request model for interest over time"""
    keywords: List[str] = Field(..., min_items=1, max_items=5, description="1-5 keywords to compare")
    timeframe: str = Field(default="today 12-m", description="Time period (e.g., 'today 12-m', 'now 7-d', 'all')")
    geo: str = Field(default="", description="Geographic location (e.g., 'US', 'GB', '' for worldwide)")
    gprop: str = Field(default="", description="Google property filter (e.g., '', 'images', 'news', 'youtube', 'froogle')")

class InterestByRegionRequest(BaseModel):
    """Request model for interest by region"""
    keywords: List[str] = Field(..., min_items=1, max_items=5)
    timeframe: str = Field(default="today 12-m")
    geo: str = Field(default="", description="Country code for sub-region data")
    resolution: str = Field(default="COUNTRY", description="COUNTRY, REGION, CITY, or DMA")
    inc_low_vol: bool = Field(default=True, description="Include low volume regions")
    inc_geo_code: bool = Field(default=False, description="Include geographic codes")

class RelatedQueriesRequest(BaseModel):
    """Request model for related queries"""
    keyword: str = Field(..., min_length=1, max_length=200)
    timeframe: str = Field(default="today 12-m")
    geo: str = Field(default="")

class RelatedTopicsRequest(BaseModel):
    """Request model for related topics"""
    keyword: str = Field(..., min_length=1, max_length=200)
    timeframe: str = Field(default="today 12-m")
    geo: str = Field(default="")

class TrendingSearchesRequest(BaseModel):
    """Request model for trending searches"""
    pn: str = Field(default="united_states", description="Country name (e.g., 'united_states', 'japan', 'india')")

class SuggestionsRequest(BaseModel):
    """Request model for keyword suggestions"""
    keyword: str = Field(..., min_length=1, max_length=200)

class ComprehensiveResearchRequest(BaseModel):
    """Request model for comprehensive research endpoint"""
    keywords: List[str] = Field(..., min_items=1, max_items=3, description="1-3 keywords for comprehensive analysis")
    timeframe: str = Field(default="today 12-m")
    geo: str = Field(default="")
    include_related: bool = Field(default=True, description="Include related queries and topics")
    include_regional: bool = Field(default=True, description="Include regional interest data")
    include_trending: bool = Field(default=False, description="Include trending searches for the country")

class SIRAResearchRequest(BaseModel):
    """Request model for Smart Intelligence Research API endpoint."""
    title: Optional[str] = Field(default=None, max_length=240, description="Article/blog title or main topic")
    description: Optional[str] = Field(default=None, max_length=4000, description="User context and claims")
    geo: str = Field(default="", description="Country code like US, GB, IN (optional)")
    research_depth: str = Field(default="deep", description="fast or deep")

    @root_validator
    def validate_payload(cls, values):
        title = clean_text(values.get("title") or "")
        description = clean_text(values.get("description") or "")
        research_depth = values.get("research_depth")
        if not title and not description:
            raise ValueError("At least one of title or description must be provided.")
        if research_depth not in {"fast", "deep"}:
            raise ValueError("research_depth must be either 'fast' or 'deep'.")
        return values

# ============================================================================
# API ENDPOINTS - HEALTH & INFO
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Google Trends API - Comprehensive Edition",
        "version": "2.0.0",
        "status": "active",
        "features": {
            "caching": "enabled (in-memory with optional Redis)",
            "endpoints": 14,
            "comprehensive_research": "enabled",
            "sira_research": "enabled"
        },
        "endpoints": {
            "interest_over_time": "/api/interest-over-time (POST)",
            "interest_by_region": "/api/interest-by-region (POST)",
            "related_queries": "/api/related-queries (POST)",
            "related_topics": "/api/related-topics (POST)",
            "trending_searches": "/api/trending-searches (POST)",
            "today_searches": "/api/today-searches (GET)",
            "realtime_trending": "/api/realtime-trending (GET)",
            "suggestions": "/api/suggestions (POST)",
            "categories": "/api/categories (GET)",
            "comprehensive_research": "/api/research (POST) - AI Blog Writer Optimized",
            "sira_research": "/api/sira/research (POST) - Smart Intelligence Research API",
            "cache_stats": "/api/cache/stats (GET)",
            "cache_clear": "/api/cache/clear (POST)",
            "health": "/health (GET)",
            "docs": "/docs (GET)"
        }
    }

@app.get("/api/debug/proxy")
async def debug_proxy(authenticated: bool = Security(verify_api_key)):
    """Debug endpoint to verify proxy configuration and connectivity."""
    import requests
    status = proxy_manager.get_status()
    proxy = proxy_manager.get_proxy()
    
    test_result = {"proxy_used": proxy[:30] + "..." if proxy else None}
    
    if proxy:
        try:
            # Try a simple request through the proxy
            proxies = {"http": proxy, "https": proxy}
            res = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
            test_result["connectivity"] = "success"
            test_result["proxy_ip"] = res.json().get("origin")
        except Exception as e:
            test_result["connectivity"] = "failed"
            test_result["error"] = str(e)
    
    return {
        "proxy_manager_status": status,
        "test_connection": test_result
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Google Trends API",
        "cache": cache.get_stats()
    }

# ============================================================================
# API ENDPOINTS - PYTRENDS METHODS
# ============================================================================

@app.post("/api/interest-over-time")
async def interest_over_time(
    request: InterestOverTimeRequest,
    authenticated: bool = Security(verify_api_key)
):
    """
    Get interest over time for keywords
    Returns historical indexed data showing popularity over time
    """
    cache_key = f"interest_over_time_{request.keywords}_{request.timeframe}_{request.geo}_{request.gprop}"
    
    # Check cache
    cached = cache.get("interest_over_time", 
                      keywords=request.keywords,
                      timeframe=request.timeframe,
                      geo=request.geo,
                      gprop=request.gprop)
    if cached:
        logger.info(f"Cache hit: interest_over_time for {request.keywords}")
        return cached
    
    try:
        def _fetch(pt):
            pt.build_payload(
                request.keywords,
                timeframe=request.timeframe,
                geo=request.geo,
                gprop=request.gprop
            )
            return pt.interest_over_time()
            
        df = execute_with_proxy_retry(_fetch)
        
        # Convert to JSON-serializable format
        data = dataframe_to_json_serializable(df)
        
        response = {
            "success": True,
            "keywords": request.keywords,
            "timeframe": request.timeframe,
            "geo": request.geo or "worldwide",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache the response
        cache.set(response, "interest_over_time", ttl=CACHE_TTL_MEDIUM,
                 keywords=request.keywords,
                 timeframe=request.timeframe,
                 geo=request.geo,
                 gprop=request.gprop)
        
        logger.info(f"Successfully fetched interest_over_time for {request.keywords}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching interest_over_time: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )

@app.post("/api/interest-by-region")
async def interest_by_region(
    request: InterestByRegionRequest,
    authenticated: bool = Security(verify_api_key)
):
    """
    Get interest by geographic region
    Returns popularity data broken down by location
    """
    # Check cache
    cached = cache.get("interest_by_region",
                      keywords=request.keywords,
                      timeframe=request.timeframe,
                      geo=request.geo,
                      resolution=request.resolution)
    if cached:
        logger.info(f"Cache hit: interest_by_region for {request.keywords}")
        return cached
    
    try:
        def _fetch(pt):
            pt.build_payload(
                request.keywords,
                timeframe=request.timeframe,
                geo=request.geo
            )
            return pt.interest_by_region(
                resolution=request.resolution,
                inc_low_vol=request.inc_low_vol,
                inc_geo_code=request.inc_geo_code
            )
            
        df = execute_with_proxy_retry(_fetch)
        
        # Convert to JSON-serializable format
        data = dataframe_to_json_serializable(df)
        
        response = {
            "success": True,
            "keywords": request.keywords,
            "timeframe": request.timeframe,
            "geo": request.geo or "worldwide",
            "resolution": request.resolution,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache the response
        cache.set(response, "interest_by_region", ttl=CACHE_TTL_MEDIUM,
                 keywords=request.keywords,
                 timeframe=request.timeframe,
                 geo=request.geo,
                 resolution=request.resolution)
        
        logger.info(f"Successfully fetched interest_by_region for {request.keywords}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching interest_by_region: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )

@app.post("/api/related-queries")
async def related_queries(
    request: RelatedQueriesRequest,
    authenticated: bool = Security(verify_api_key)
):
    """
    Get related queries (rising and top)
    Essential for discovering trending related keywords
    """
    # Check cache
    cached = cache.get("related_queries",
                      keyword=request.keyword,
                      timeframe=request.timeframe,
                      geo=request.geo)
    if cached:
        logger.info(f"Cache hit: related_queries for {request.keyword}")
        return cached
    
    try:
        pytrends = get_pytrends_client()
        pytrends.build_payload(
            [request.keyword],
            timeframe=request.timeframe,
            geo=request.geo
        )
        
        related = pytrends.related_queries()
        keyword_data = related.get(request.keyword, {})
        
        rising_df = keyword_data.get("rising")
        top_df = keyword_data.get("top")
        
        response = {
            "success": True,
            "keyword": request.keyword,
            "timeframe": request.timeframe,
            "geo": request.geo or "worldwide",
            "rising_queries": safe_dataframe_to_dict(rising_df),
            "top_queries": safe_dataframe_to_dict(top_df),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache the response
        cache.set(response, "related_queries", ttl=CACHE_TTL_MEDIUM,
                 keyword=request.keyword,
                 timeframe=request.timeframe,
                 geo=request.geo)
        
        logger.info(f"Successfully fetched related_queries for {request.keyword}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching related_queries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )

@app.post("/api/related-topics")
async def related_topics(
    request: RelatedTopicsRequest,
    authenticated: bool = Security(verify_api_key)
):
    """
    Get related topics (rising and top)
    Useful for discovering broader topic trends
    """
    # Check cache
    cached = cache.get("related_topics",
                      keyword=request.keyword,
                      timeframe=request.timeframe,
                      geo=request.geo)
    if cached:
        logger.info(f"Cache hit: related_topics for {request.keyword}")
        return cached
    
    try:
        def _fetch(pt):
            pt.build_payload(
                [request.keyword],
                timeframe=request.timeframe,
                geo=request.geo
            )
            return pt.related_topics()
            
        related = execute_with_proxy_retry(_fetch)
        keyword_data = related.get(request.keyword, {})
        
        rising_df = keyword_data.get("rising")
        top_df = keyword_data.get("top")
        
        response = {
            "success": True,
            "keyword": request.keyword,
            "timeframe": request.timeframe,
            "geo": request.geo or "worldwide",
            "rising_topics": safe_dataframe_to_dict(rising_df),
            "top_topics": safe_dataframe_to_dict(top_df),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache the response
        cache.set(response, "related_topics", ttl=CACHE_TTL_MEDIUM,
                 keyword=request.keyword,
                 timeframe=request.timeframe,
                 geo=request.geo)
        
        logger.info(f"Successfully fetched related_topics for {request.keyword}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching related_topics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )

@app.post("/api/trending-searches")
async def trending_searches(
    request: TrendingSearchesRequest,
    authenticated: bool = Security(verify_api_key)
):
    """
    Get daily trending searches for a specific country
    Returns list of currently trending search terms
    """
    cached = cache.get("trending_searches", pn=request.pn)
    if cached:
        logger.info(f"Cache hit: trending_searches for {request.pn}")
        return cached
    
    try:
        # Pytrends trending_searches requires full country names, not codes.
        # We normalize here to prevent common 200/404 errors.
        country_map = {
            "US": "united_states", "GB": "united_kingdom", "IN": "india",
            "CA": "canada", "AU": "australia", "JP": "japan", "DE": "germany",
            "FR": "france", "BR": "brazil", "IT": "italy", "ES": "spain",
            "NG": "nigeria", "ZA": "south_africa", "KE": "kenya"
        }
        
        pn_normalized = request.pn.lower().replace(" ", "_")
        # If it looks like a 2-letter code, try to map it
        if len(pn_normalized) == 2:
            pn_normalized = country_map.get(pn_normalized.upper(), pn_normalized)
            
        logger.info(f"Fetching trending_searches for {pn_normalized} (original: {request.pn})")

        def _fetch(pt):
            return pt.trending_searches(pn=pn_normalized)
            
        df = execute_with_proxy_retry(_fetch)
        trending_list = df[0].tolist() if not df.empty else []
        
        response = {
            "success": True,
            "country": request.pn,
            "trending_searches": trending_list,
            "count": len(trending_list),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        cache.set(response, "trending_searches", ttl=CACHE_TTL_SHORT, pn=request.pn)
        logger.info(f"Successfully fetched trending_searches for {request.pn}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching trending_searches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )

@app.get("/api/today-searches")
async def today_searches(
    geo: str = Query(default="US", description="Country code (e.g., 'US', 'GB', 'IN')"),
    authenticated: bool = Security(verify_api_key)
):
    """
    Get today's trending searches
    Returns realtime trending topics for the specified country
    """
    cached = cache.get("today_searches", geo=geo)
    if cached:
        logger.info(f"Cache hit: today_searches for {geo}")
        return cached
    
    try:
        pytrends = get_pytrends_client()
        df = pytrends.today_searches(pn=geo)
        today_list = df[0].tolist() if not df.empty else []
        
        response = {
            "success": True,
            "country": geo,
            "today_searches": today_list,
            "count": len(today_list),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        cache.set(response, "today_searches", ttl=CACHE_TTL_SHORT, geo=geo)
        logger.info(f"Successfully fetched today_searches for {geo}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching today_searches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )

@app.get("/api/realtime-trending")
async def realtime_trending(
    geo: str = Query(default="US", description="Country code"),
    category: str = Query(default="all", description="Category (e.g., 'all', 'b', 'e', 'h', etc.)"),
    authenticated: bool = Security(verify_api_key)
):
    """
    Get realtime trending searches
    Returns the most current trending data available
    """
    cached = cache.get("realtime_trending", geo=geo, category=category)
    if cached:
        logger.info(f"Cache hit: realtime_trending for {geo}")
        return cached
    
    try:
        pytrends = get_pytrends_client()
        df = pytrends.realtime_trending_searches(pn=geo, cat=category)
        data = safe_dataframe_to_dict(df)
        
        response = {
            "success": True,
            "country": geo,
            "category": category,
            "realtime_trending": data,
            "count": len(data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        cache.set(response, "realtime_trending", ttl=900, geo=geo, category=category)
        logger.info(f"Successfully fetched realtime_trending for {geo}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching realtime_trending: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )

@app.post("/api/suggestions")
async def suggestions(
    request: SuggestionsRequest,
    authenticated: bool = Security(verify_api_key)
):
    """
    Get keyword suggestions from Google
    Useful for keyword expansion and research
    """
    cached = cache.get("suggestions", keyword=request.keyword)
    if cached:
        logger.info(f"Cache hit: suggestions for {request.keyword}")
        return cached
    
    try:
        pytrends = get_pytrends_client()
        suggestions = pytrends.suggestions(keyword=request.keyword)
        
        response = {
            "success": True,
            "keyword": request.keyword,
            "suggestions": suggestions,
            "count": len(suggestions) if suggestions else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        cache.set(response, "suggestions", ttl=CACHE_TTL_LONG, keyword=request.keyword)
        logger.info(f"Successfully fetched suggestions for {request.keyword}")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )

@app.get("/api/categories")
async def get_categories(authenticated: bool = Security(verify_api_key)):
    """
    Get all available Google Trends categories
    Use these category IDs when building payloads
    """
    cached = cache.get("categories")
    if cached:
        logger.info("Cache hit: categories")
        return cached
    
    try:
        def _fetch(pt):
            return pt.categories()
        categories = execute_with_proxy_retry(_fetch)
        
        response = {
            "success": True,
            "categories": categories,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        cache.set(response, "categories", ttl=86400)
        logger.info("Successfully fetched categories")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data: {str(e)}"
        )

# ============================================================================
# COMPREHENSIVE RESEARCH ENDPOINT - AI BLOG WRITER OPTIMIZED
# ============================================================================

@app.post("/api/research")
async def comprehensive_research(
    request: ComprehensiveResearchRequest,
    background_tasks: BackgroundTasks,
    authenticated: bool = Security(verify_api_key)
):
    """
    ?? COMPREHENSIVE RESEARCH ENDPOINT - Optimized for AI Blog Writers
    
    Returns ALL relevant data for blog content creation in a single request:
    - Interest over time (historical trends)
    - Related queries (rising and top)
    - Related topics (rising and top)
    - Regional interest data (optional)
    - Trending searches (optional)
    
    This endpoint is designed to give your AI blog writer everything it needs
    to create well-researched, SEO-optimized content.
    """
    cached = cache.get("comprehensive_research",
                      keywords=request.keywords,
                      timeframe=request.timeframe,
                      geo=request.geo,
                      include_related=request.include_related,
                      include_regional=request.include_regional)
    if cached:
        logger.info(f"Cache hit: comprehensive_research for {request.keywords}")
        return cached
    
    try:
        def _fetch_all(pt):
            pt.build_payload(request.keywords, timeframe=request.timeframe, geo=request.geo)
            
            res = {
                "success": True,
                "keywords": request.keywords,
                "timeframe": request.timeframe,
                "geo": request.geo or "worldwide",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 1. Interest Over Time
            try:
                df_interest = pt.interest_over_time()
                res["interest_over_time"] = dataframe_to_json_serializable(df_interest)
            except Exception as e:
                logger.warning(f"Failed to fetch interest_over_time: {e}")
                res["interest_over_time"] = []
            return res, pt

        fetch_res, pytrends = execute_with_proxy_retry(_fetch_all)
        response = fetch_res
        
        # 2. Related Queries and Topics
        if request.include_related:
            response["related_data"] = {}
            
            for keyword in request.keywords:
                response["related_data"][keyword] = {
                    "queries": {"rising": [], "top": []},
                    "topics": {"rising": [], "top": []}
                }
                
                try:
                    related_queries = pytrends.related_queries()
                    keyword_queries = related_queries.get(keyword, {})
                    response["related_data"][keyword]["queries"]["rising"] = safe_dataframe_to_dict(
                        keyword_queries.get("rising")
                    )
                    response["related_data"][keyword]["queries"]["top"] = safe_dataframe_to_dict(
                        keyword_queries.get("top")
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch related_queries for {keyword}: {e}")
                
                try:
                    related_topics = pytrends.related_topics()
                    keyword_topics = related_topics.get(keyword, {})
                    response["related_data"][keyword]["topics"]["rising"] = safe_dataframe_to_dict(
                        keyword_topics.get("rising")
                    )
                    response["related_data"][keyword]["topics"]["top"] = safe_dataframe_to_dict(
                        keyword_topics.get("top")
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch related_topics for {keyword}: {e}")
        
        # 3. Regional Interest
        if request.include_regional:
            try:
                df_region = pytrends.interest_by_region(resolution="COUNTRY", inc_low_vol=True)
                response["interest_by_region"] = dataframe_to_json_serializable(df_region)
            except Exception as e:
                logger.warning(f"Failed to fetch interest_by_region: {e}")
                response["interest_by_region"] = []
        
        # 4. Trending Searches
        if request.include_trending and request.geo:
            try:
                country_map = {
                    "US": "united_states", "GB": "united_kingdom", "IN": "india",
                    "CA": "canada", "AU": "australia", "JP": "japan", "DE": "germany",
                    "FR": "france", "BR": "brazil", "IT": "italy", "ES": "spain"
                }
                country_name = country_map.get(request.geo.upper(), "united_states")
                df_trending = pytrends.trending_searches(pn=country_name)
                response["trending_searches"] = df_trending[0].tolist() if not df_trending.empty else []
            except Exception as e:
                logger.warning(f"Failed to fetch trending_searches: {e}")
                response["trending_searches"] = []
        
        cache.set(response, "comprehensive_research", ttl=CACHE_TTL_MEDIUM,
                 keywords=request.keywords, timeframe=request.timeframe, geo=request.geo,
                 include_related=request.include_related, include_regional=request.include_regional)
        
        logger.info(f"Successfully completed comprehensive research for {request.keywords}")
        return response
        
    except Exception as e:
        logger.error(f"Error in comprehensive_research: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching comprehensive data: {str(e)}"
        )

# ============================================================================
# SIRA ENDPOINT - SMART INTELLIGENCE RESEARCH API
# ============================================================================

@app.post("/api/sira/research")
async def sira_research(
    request: SIRAResearchRequest,
    authenticated: bool = Security(verify_api_key)
):
    """
    Smart Intelligence Research API endpoint.
    Combines intent analysis, market pulse, web extraction, and fact-check summary.
    """
    title = clean_text(request.title or "")
    description = clean_text(request.description or "")
    geo = clean_text(request.geo or "").upper()
    depth = request.research_depth

    cached = cache.get("sira_research", title=title, description=description, geo=geo, depth=depth)
    if cached:
        logger.info("Cache hit: sira_research")
        return cached

    config = SIRAServiceConfig(
        openrouter_api_key=OPENROUTER_API_KEY,
        openrouter_base_url=OPENROUTER_BASE_URL,
        openrouter_model_intent=OPENROUTER_MODEL_INTENT,
        openrouter_model_factcheck=OPENROUTER_MODEL_FACTCHECK,
        openrouter_referer=OPENROUTER_REFERER,
        openrouter_app_title=OPENROUTER_APP_TITLE,
        max_sources_fast=SIRA_MAX_SOURCES_FAST,
        max_sources_deep=SIRA_MAX_SOURCES_DEEP,
        max_urls_per_query_fast=SIRA_MAX_URLS_PER_QUERY_FAST,
        max_urls_per_query_deep=SIRA_MAX_URLS_PER_QUERY_DEEP,
        cache_ttl_seconds=CACHE_TTL_MEDIUM
    )

    response = await run_sira_pipeline(
        title=title,
        description=description,
        geo=geo,
        depth=depth,
        config=config,
        get_pytrends_client=get_pytrends_client
    )

    cache.set(
        response,
        "sira_research",
        ttl=CACHE_TTL_MEDIUM,
        title=title,
        description=description,
        geo=geo,
        depth=depth
    )
    return response

# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/cache/stats")
async def cache_stats(authenticated: bool = Security(verify_api_key)):
    """Get cache statistics"""
    stats = cache.get_stats()
    return {
        "success": True,
        "cache_stats": stats,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/cache/clear")
async def cache_clear(authenticated: bool = Security(verify_api_key)):
    """Clear all cached data"""
    try:
        cache.clear_all()
        return {
            "success": True,
            "message": "Cache cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache: {str(e)}"
        )

# ============================================================================
# BACKGROUND TASKS & EVENT HANDLERS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("=" * 60)
    logger.info("Google Trends API - Comprehensive Edition Starting")
    logger.info(f"Version: 2.0.0")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Cache: Enabled (in-memory + optional Redis)")
    logger.info(f"API Key: {'Configured' if API_SECRET_KEY != 'YOUR_SECRET_KEY_CHANGE_THIS' else 'DEFAULT (CHANGE THIS!)'}")
    logger.info(f"OpenRouter: {'Configured' if OPENROUTER_API_KEY else 'Not configured (SIRA will use fallbacks)'}")
    logger.info(
        f"SIRA optional deps: ddgs={'yes' if sira_service.DDGS is not None else 'no'}, "
        f"trafilatura={'yes' if sira_service.trafilatura is not None else 'no'}"
    )
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("Google Trends API shutting down")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "pytrends_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
