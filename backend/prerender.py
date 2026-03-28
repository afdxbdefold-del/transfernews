"""
TransferNews.de - Pre-Rendering Service
Dynamisches Pre-Rendering für Google News Optimierung

Features:
- Rendert Seiten mit Playwright/Chromium
- Cached HTML-Output für schnelle Auslieferung
- Trigger nach Artikel-Publish
- Meta-Daten im HTML (title, description, og:image, canonical)
- Fallback auf normale SPA wenn Pre-Render fehlschlägt
"""

import asyncio
import logging
import os
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Pre-Render Cache Directory
CACHE_DIR = Path("/app/backend/prerender_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
SITE_URL = os.environ.get("SITE_URL", "https://transfernews.de")
INTERNAL_URL = "http://localhost:3000"  # Internal frontend URL
CACHE_TTL_HOURS = 24  # Cache validity in hours

# ========================
# PRE-RENDER ENGINE
# ========================

class PreRenderEngine:
    """
    Pre-renders React pages to static HTML using Playwright
    """
    
    def __init__(self):
        self.browser = None
        self.context = None
    
    async def init_browser(self):
        """Initialize headless browser"""
        if self.browser:
            return
        
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # Use explicit chromium path if available
            chromium_path = "/pw-browsers/chromium-1208/chrome-linux/chrome"
            import os
            
            if os.path.exists(chromium_path):
                self.browser = await self.playwright.chromium.launch(
                    executable_path=chromium_path,
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
            else:
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='TransferNews-PreRenderer/1.0'
            )
            logger.info("Pre-render browser initialized")
        except Exception as e:
            logger.error(f"Failed to init browser: {e}")
            raise
    
    async def close_browser(self):
        """Close browser connection"""
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            self.browser = None
            self.context = None
    
    async def render_page(self, path: str, timeout: int = 30000) -> Optional[str]:
        """
        Render a page and return HTML with all meta tags
        
        Args:
            path: URL path (e.g., "/news/spieler-wechselt")
            timeout: Max render time in ms
            
        Returns:
            Full HTML string or None on error
        """
        await self.init_browser()
        
        page = None
        try:
            page = await self.context.new_page()
            
            # Navigate to page
            url = f"{INTERNAL_URL}{path}"
            logger.info(f"Pre-rendering: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=timeout)
            
            # Wait for React to render
            await page.wait_for_timeout(2000)
            
            # Wait for specific content indicators
            try:
                await page.wait_for_selector('[data-testid]', timeout=5000)
            except:
                pass  # Continue even if no testid found
            
            # Get rendered HTML
            html = await page.content()
            
            # Inject canonical URL with production domain
            canonical_path = path.rstrip('/')
            canonical_url = f"{SITE_URL}{canonical_path}"
            
            # Ensure canonical is in HTML
            if '<link rel="canonical"' not in html:
                html = html.replace(
                    '</head>',
                    f'<link rel="canonical" href="{canonical_url}" />\n</head>'
                )
            else:
                # Update existing canonical to use production URL
                import re
                html = re.sub(
                    r'<link rel="canonical" href="[^"]*"',
                    f'<link rel="canonical" href="{canonical_url}"',
                    html
                )
            
            # Add prerender indicator
            html = html.replace(
                '</head>',
                '<meta name="prerender-status" content="success" />\n</head>'
            )
            
            logger.info(f"Pre-rendered successfully: {path}")
            return html
            
        except Exception as e:
            logger.error(f"Pre-render failed for {path}: {e}")
            return None
            
        finally:
            if page:
                await page.close()
    
    def get_cache_path(self, path: str) -> Path:
        """Get cache file path for a URL"""
        # Create hash of path for filename
        path_hash = hashlib.md5(path.encode()).hexdigest()
        return CACHE_DIR / f"{path_hash}.html"
    
    def get_cache_meta_path(self, path: str) -> Path:
        """Get cache metadata file path"""
        path_hash = hashlib.md5(path.encode()).hexdigest()
        return CACHE_DIR / f"{path_hash}.meta"
    
    async def get_cached_html(self, path: str) -> Optional[str]:
        """Get cached HTML if valid"""
        cache_path = self.get_cache_path(path)
        meta_path = self.get_cache_meta_path(path)
        
        if not cache_path.exists() or not meta_path.exists():
            return None
        
        try:
            # Check cache validity
            with open(meta_path) as f:
                cached_at = datetime.fromisoformat(f.read().strip())
            
            if datetime.now(timezone.utc) - cached_at > timedelta(hours=CACHE_TTL_HOURS):
                return None  # Cache expired
            
            # Return cached HTML
            with open(cache_path, encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            logger.warning(f"Cache read error for {path}: {e}")
            return None
    
    async def cache_html(self, path: str, html: str):
        """Save rendered HTML to cache"""
        try:
            cache_path = self.get_cache_path(path)
            meta_path = self.get_cache_meta_path(path)
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            with open(meta_path, 'w') as f:
                f.write(datetime.now(timezone.utc).isoformat())
            
            logger.info(f"Cached: {path}")
            
        except Exception as e:
            logger.error(f"Cache write error for {path}: {e}")
    
    async def invalidate_cache(self, path: str):
        """Invalidate cache for a specific path"""
        cache_path = self.get_cache_path(path)
        meta_path = self.get_cache_meta_path(path)
        
        for p in [cache_path, meta_path]:
            if p.exists():
                p.unlink()
        
        logger.info(f"Cache invalidated: {path}")
    
    async def prerender_and_cache(self, path: str) -> bool:
        """Pre-render a page and cache it"""
        html = await self.render_page(path)
        if html:
            await self.cache_html(path, html)
            return True
        return False


# Global engine instance
_prerender_engine: Optional[PreRenderEngine] = None


async def get_prerender_engine() -> PreRenderEngine:
    """Get or create pre-render engine"""
    global _prerender_engine
    if _prerender_engine is None:
        _prerender_engine = PreRenderEngine()
    return _prerender_engine


# ========================
# PRE-RENDER TRIGGERS
# ========================

async def prerender_article(slug: str) -> bool:
    """
    Pre-render a single article page
    Called after article publish/update
    """
    engine = await get_prerender_engine()
    path = f"/news/{slug}"
    return await engine.prerender_and_cache(path)


async def prerender_player(slug: str) -> bool:
    """Pre-render a player page"""
    engine = await get_prerender_engine()
    path = f"/spieler/{slug}"
    return await engine.prerender_and_cache(path)


async def prerender_club(slug: str) -> bool:
    """Pre-render a club page"""
    engine = await get_prerender_engine()
    path = f"/verein/{slug}"
    return await engine.prerender_and_cache(path)


async def prerender_homepage() -> bool:
    """Pre-render homepage"""
    engine = await get_prerender_engine()
    return await engine.prerender_and_cache("/")


async def prerender_all_articles(db: AsyncIOMotorDatabase, limit: int = 100) -> Dict:
    """
    Pre-render all published articles
    Used for initial cache warm-up
    """
    result = {"success": 0, "failed": 0, "skipped": 0}
    engine = await get_prerender_engine()
    
    articles = await db.articles.find(
        {"status": "published"},
        {"_id": 0, "slug": 1}
    ).sort("published_at", -1).limit(limit).to_list(limit)
    
    for article in articles:
        slug = article.get("slug")
        if not slug:
            result["skipped"] += 1
            continue
        
        path = f"/news/{slug}"
        
        # Check if already cached
        cached = await engine.get_cached_html(path)
        if cached:
            result["skipped"] += 1
            continue
        
        # Pre-render
        success = await engine.prerender_and_cache(path)
        if success:
            result["success"] += 1
        else:
            result["failed"] += 1
        
        # Small delay to not overload
        await asyncio.sleep(0.5)
    
    # Also pre-render homepage
    await engine.prerender_and_cache("/")
    
    return result


async def get_prerendered_html(path: str) -> Optional[str]:
    """
    Get pre-rendered HTML for a path
    Returns None if not cached (fallback to SPA)
    """
    engine = await get_prerender_engine()
    return await engine.get_cached_html(path)


# ========================
# CLEANUP
# ========================

async def cleanup_old_cache(max_age_hours: int = 48):
    """Remove cache files older than max_age"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    removed = 0
    
    for meta_path in CACHE_DIR.glob("*.meta"):
        try:
            with open(meta_path) as f:
                cached_at = datetime.fromisoformat(f.read().strip())
            
            if cached_at < cutoff:
                # Remove both meta and html
                html_path = meta_path.with_suffix('.html')
                meta_path.unlink()
                if html_path.exists():
                    html_path.unlink()
                removed += 1
        except:
            pass
    
    logger.info(f"Cleaned up {removed} old cache entries")
    return removed
