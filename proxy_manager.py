"""
Proxy Manager for Google Trends API
=====================================
Handles proxy rotation to avoid Google 429 rate limiting.

Supported proxy providers:
  1. ScraperAPI    - set SCRAPER_API_KEY in .env (free tier: 1000 req/month)
  2. Webshare      - set WEBSHARE_API_KEY in .env
  3. Custom list   - set PROXY_LIST in .env as comma-separated URLs

Priority order: ScraperAPI > Webshare > Custom List > No proxy (last resort)

Usage:
    from proxy_manager import proxy_manager
    proxies = proxy_manager.get_proxy()       # returns one proxy string or None
    proxy_manager.mark_failed(proxy)          # mark a proxy as temporarily bad
    proxy_manager.rotate()                    # get next proxy in rotation
"""

import os
import random
import time
import logging
from typing import Optional, List
from threading import Lock
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Thread-safe rotating proxy manager.
    Tracks failures and temporarily blacklists bad proxies.
    """

    def __init__(self):
        self._lock = Lock()
        self._proxies: List[str] = []
        self._failed: dict = {}           # proxy -> datetime when it failed
        self._BLACKLIST_DURATION = 300    # seconds to blacklist a failed proxy (5 min)
        self._current_index = 0
        self._initialized = False

    def _build_proxy_list(self) -> List[str]:
        """Build proxy list from environment variables."""
        proxies = []

        # --- 1. ScraperAPI (Best option for Google Trends) ---
        scraper_api_key = os.getenv("SCRAPER_API_KEY", "").strip()
        if scraper_api_key:
            # ScraperAPI handles Google consent + residential IPs automatically
            proxy_url = f"http://scraperapi:{scraper_api_key}@proxy-server.scraperapi.com:8001"
            proxies.append(proxy_url)
            logger.info("ProxyManager: ScraperAPI proxy configured.")

        # --- 2. Webshare Rotating Proxy ---
        webshare_user = os.getenv("WEBSHARE_PROXY_USER", "").strip()
        webshare_pass = os.getenv("WEBSHARE_PROXY_PASS", "").strip()
        if webshare_user and webshare_pass:
            proxy_url = f"http://{webshare_user}:{webshare_pass}@p.webshare.io:80"
            proxies.append(proxy_url)
            logger.info("ProxyManager: Webshare proxy configured.")

        # --- 3. Custom proxy list (comma-separated URLs in env) ---
        # Format: http://user:pass@host:port,http://user:pass@host2:port2
        custom_proxies_raw = os.getenv("PROXY_LIST", "").strip()
        if custom_proxies_raw:
            custom_proxies = [p.strip() for p in custom_proxies_raw.split(",") if p.strip()]
            proxies.extend(custom_proxies)
            logger.info(f"ProxyManager: {len(custom_proxies)} custom proxies loaded.")

        if not proxies:
            logger.warning(
                "ProxyManager: No proxies configured! "
                "Set SCRAPER_API_KEY, WEBSHARE_PROXY_USER/PASS, or PROXY_LIST in your .env. "
                "Google will likely rate-limit direct cloud server requests."
            )

        return proxies

    def _ensure_initialized(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._proxies = self._build_proxy_list()
                    self._initialized = True

    def _is_blacklisted(self, proxy: str) -> bool:
        """Returns True if the proxy is in the temporary blacklist."""
        if proxy not in self._failed:
            return False
        failed_at = self._failed[proxy]
        if datetime.utcnow() - failed_at > timedelta(seconds=self._BLACKLIST_DURATION):
            # Blacklist expired — give it another chance
            del self._failed[proxy]
            return False
        return True

    def get_proxy(self) -> Optional[str]:
        """
        Returns a proxy URL string to use, or None if no proxies are available.
        Automatically skips blacklisted proxies.
        """
        self._ensure_initialized()

        with self._lock:
            if not self._proxies:
                return None

            # Try all proxies, skip blacklisted ones
            for _ in range(len(self._proxies)):
                proxy = self._proxies[self._current_index % len(self._proxies)]
                self._current_index += 1
                if not self._is_blacklisted(proxy):
                    return proxy

            # All proxies are blacklisted — clear and return the first one anyway
            logger.error("ProxyManager: All proxies are blacklisted! Clearing blacklist and retrying.")
            self._failed.clear()
            return self._proxies[0] if self._proxies else None

    def mark_failed(self, proxy: str):
        """Mark a proxy as failed. It will be skipped for BLACKLIST_DURATION seconds."""
        if proxy:
            with self._lock:
                self._failed[proxy] = datetime.utcnow()
                logger.warning(f"ProxyManager: Marked proxy as failed: {proxy[:40]}...")

    def rotate(self) -> Optional[str]:
        """
        Force rotation to the next proxy.
        Call this after a 429 response.
        """
        self._ensure_initialized()
        with self._lock:
            if self._proxies:
                self._current_index += 1
        return self.get_proxy()

    def get_requests_proxies_dict(self, proxy_url: Optional[str] = None) -> Optional[dict]:
        """
        Returns a dict formatted for the `requests` library:
        {"http": "...", "https": "..."}
        """
        if proxy_url is None:
            proxy_url = self.get_proxy()
        if not proxy_url:
            return None
        return {"http": proxy_url, "https": proxy_url}

    def get_status(self) -> dict:
        """Returns a status dict for health checks and debugging."""
        self._ensure_initialized()
        return {
            "total_proxies": len(self._proxies),
            "blacklisted": len(self._failed),
            "active": len(self._proxies) - len(self._failed),
            "providers": {
                "scraperapi": bool(os.getenv("SCRAPER_API_KEY")),
                "webshare": bool(os.getenv("WEBSHARE_PROXY_USER")),
                "custom": bool(os.getenv("PROXY_LIST")),
            }
        }


# Singleton instance — import this everywhere
proxy_manager = ProxyManager()
