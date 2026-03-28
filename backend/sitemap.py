"""
TransferNews.de - Sitemap Generator
- Standard Sitemap für alle Seiten
- News Sitemap für Google News (letzte 48h)
- Automatische Updates bei neuen Artikeln
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import aiohttp

logger = logging.getLogger(__name__)

# ========================
# CONFIGURATION
# ========================

SITE_URL = "https://transfernews.de"
PUBLICATION_NAME = "TransferNews.de"
PUBLICATION_LANGUAGE = "de"

# ========================
# NEWS SITEMAP (Google News)
# ========================

async def generate_news_sitemap(db: AsyncIOMotorDatabase) -> str:
    """
    Generate Google News Sitemap XML
    - Only articles from last 48 hours
    - Max 1000 URLs
    - Required fields: publication_date, title, publication name
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    
    articles = await db.articles.find(
        {
            "status": "published",
            "published_at": {"$gte": cutoff.isoformat()}
        },
        {"_id": 0, "slug": 1, "title": 1, "published_at": 1, "updated_at": 1}
    ).sort("published_at", -1).limit(1000).to_list(1000)
    
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">'
    ]
    
    for article in articles:
        pub_date = article.get("published_at", "")
        if isinstance(pub_date, str):
            # Parse ISO string to datetime for formatting
            try:
                pub_dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                pub_date_formatted = pub_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            except:
                pub_date_formatted = pub_date
        else:
            pub_date_formatted = pub_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        
        title = article.get("title", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        xml_parts.append(f'''  <url>
    <loc>{SITE_URL}/news/{article.get("slug")}</loc>
    <news:news>
      <news:publication>
        <news:name>{PUBLICATION_NAME}</news:name>
        <news:language>{PUBLICATION_LANGUAGE}</news:language>
      </news:publication>
      <news:publication_date>{pub_date_formatted}</news:publication_date>
      <news:title>{title}</news:title>
    </news:news>
  </url>''')
    
    xml_parts.append('</urlset>')
    
    return '\n'.join(xml_parts)


# ========================
# STANDARD SITEMAP
# ========================

async def generate_sitemap(db: AsyncIOMotorDatabase) -> str:
    """
    Generate standard sitemap.xml
    - All published articles
    - All players
    - All clubs
    - All competitions
    - Static pages
    """
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Static pages
    static_pages = [
        ("", "daily", "1.0"),
        ("/news", "hourly", "0.9"),
        ("/transfers", "daily", "0.8"),
        ("/geruechte", "daily", "0.8"),
        ("/suche", "weekly", "0.5"),
    ]
    
    for path, freq, priority in static_pages:
        xml_parts.append(f'''  <url>
    <loc>{SITE_URL}{path}</loc>
    <lastmod>{now}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>''')
    
    # Articles (last 1000)
    articles = await db.articles.find(
        {"status": "published"},
        {"_id": 0, "slug": 1, "updated_at": 1, "published_at": 1}
    ).sort("published_at", -1).limit(1000).to_list(1000)
    
    for article in articles:
        lastmod = article.get("updated_at") or article.get("published_at") or now
        if isinstance(lastmod, datetime):
            lastmod = lastmod.strftime("%Y-%m-%d")
        elif isinstance(lastmod, str):
            lastmod = lastmod[:10]  # Just date part
        
        xml_parts.append(f'''  <url>
    <loc>{SITE_URL}/news/{article.get("slug")}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>''')
    
    # Players
    players = await db.players.find(
        {},
        {"_id": 0, "slug": 1, "updated_at": 1}
    ).limit(500).to_list(500)
    
    for player in players:
        lastmod = player.get("updated_at")
        if isinstance(lastmod, datetime):
            lastmod = lastmod.strftime("%Y-%m-%d")
        elif isinstance(lastmod, str):
            lastmod = lastmod[:10]
        else:
            lastmod = now
        
        xml_parts.append(f'''  <url>
    <loc>{SITE_URL}/spieler/{player.get("slug")}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>''')
    
    # Clubs
    clubs = await db.clubs.find(
        {},
        {"_id": 0, "slug": 1, "updated_at": 1}
    ).limit(200).to_list(200)
    
    for club in clubs:
        lastmod = club.get("updated_at")
        if isinstance(lastmod, datetime):
            lastmod = lastmod.strftime("%Y-%m-%d")
        elif isinstance(lastmod, str):
            lastmod = lastmod[:10]
        else:
            lastmod = now
        
        xml_parts.append(f'''  <url>
    <loc>{SITE_URL}/verein/{club.get("slug")}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>''')
    
    # Competitions
    competitions = await db.competitions.find(
        {},
        {"_id": 0, "slug": 1, "updated_at": 1}
    ).limit(50).to_list(50)
    
    for comp in competitions:
        lastmod = comp.get("updated_at")
        if isinstance(lastmod, datetime):
            lastmod = lastmod.strftime("%Y-%m-%d")
        elif isinstance(lastmod, str):
            lastmod = lastmod[:10]
        else:
            lastmod = now
        
        xml_parts.append(f'''  <url>
    <loc>{SITE_URL}/wettbewerb/{comp.get("slug")}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>''')
    
    xml_parts.append('</urlset>')
    
    return '\n'.join(xml_parts)


# ========================
# SITEMAP INDEX
# ========================

async def generate_sitemap_index() -> str:
    """
    Generate sitemap index pointing to all sitemaps
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>{SITE_URL}/sitemap.xml</loc>
    <lastmod>{now}</lastmod>
  </sitemap>
  <sitemap>
    <loc>{SITE_URL}/news-sitemap.xml</loc>
    <lastmod>{now}</lastmod>
  </sitemap>
</sitemapindex>'''


# ========================
# GOOGLE PING (Crawl Trigger)
# ========================

async def ping_google_sitemap(sitemap_url: str = None) -> bool:
    """
    Ping Google to inform about sitemap update
    This triggers faster crawling
    """
    if not sitemap_url:
        sitemap_url = f"{SITE_URL}/sitemap.xml"
    
    ping_url = f"https://www.google.com/ping?sitemap={sitemap_url}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ping_url, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"Google sitemap ping successful: {sitemap_url}")
                    return True
                else:
                    logger.warning(f"Google ping returned status {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Google sitemap ping failed: {e}")
        return False


async def ping_google_news_sitemap() -> bool:
    """Ping Google specifically for news sitemap"""
    return await ping_google_sitemap(f"{SITE_URL}/news-sitemap.xml")


# ========================
# ARTICLE UPDATE TRACKER
# ========================

async def track_article_update(db: AsyncIOMotorDatabase, article_id: str, update_type: str, details: str = None):
    """
    Track article updates for transparency
    Helps Google understand article evolution
    """
    update_entry = {
        "article_id": article_id,
        "update_type": update_type,  # "status_change", "content_update", "correction"
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Add to article's update history
    await db.articles.update_one(
        {"id": article_id},
        {
            "$push": {"update_history": update_entry},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    logger.info(f"Tracked article update: {article_id} - {update_type}")


# ========================
# ROBOTS.TXT GENERATOR
# ========================

def generate_robots_txt() -> str:
    """
    Generate optimized robots.txt for Google News
    """
    return f'''# TransferNews.de Robots.txt
# Optimized for Google News & Discover

User-agent: *
Allow: /

# Sitemaps (via /api/ prefix for backend routing)
Sitemap: {SITE_URL}/api/sitemap.xml
Sitemap: {SITE_URL}/api/news-sitemap.xml

# Allow all crawlers full access
User-agent: Googlebot
Allow: /

User-agent: Googlebot-News
Allow: /

# No crawl delays - we want fast indexing
# Crawl-delay: 0
'''
