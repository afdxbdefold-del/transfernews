"""Escaped public sitemap output. Publication timestamps support BSON and ISO dates."""
from datetime import datetime, timezone, timedelta
import os
from urllib.parse import quote, urlsplit
from xml.etree import ElementTree as ET

SITE_URL = os.environ.get("SITE_URL", "https://transfernews.de").rstrip("/")
if urlsplit(SITE_URL).scheme not in {"https", "http"} or not urlsplit(SITE_URL).hostname:
    raise RuntimeError("SITE_URL must be an absolute HTTP(S) origin")
PUBLICATION_NAME = "TransferNews.de"
PUBLICATION_LANGUAGE = "de"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
NEWS_NS = "http://www.google.com/schemas/sitemap-news/0.9"
ET.register_namespace("", NS)
ET.register_namespace("news", NEWS_NS)


def parse_publication_date(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def canonical_url(path):
    return SITE_URL + "/" + path.lstrip("/")


def _field(parent, name, text, namespace=NS):
    ET.SubElement(parent, "{" + namespace + "}" + name).text = str(text)


def _xml(root):
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


async def generate_news_sitemap(db):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=48)
    articles = await db.articles.find({
        "status": "published",
        "$or": [{"published_at": {"$gte": cutoff}}, {"published_at": {"$gte": cutoff.isoformat()}}],
    }, {"_id": 0, "slug": 1, "title": 1, "published_at": 1}).sort("published_at", -1).limit(1000).to_list(1000)
    root = ET.Element("{" + NS + "}urlset")
    seen = set()
    for article in articles:
        published = parse_publication_date(article.get("published_at"))
        if not article.get("slug") or not published or not cutoff <= published <= now:
            continue
        url = canonical_url("news/" + quote(article["slug"], safe=""))
        if url in seen: continue
        seen.add(url)
        node = ET.SubElement(root, "{" + NS + "}url")
        _field(node, "loc", url)
        news = ET.SubElement(node, "{" + NEWS_NS + "}news")
        publication = ET.SubElement(news, "{" + NEWS_NS + "}publication")
        _field(publication, "name", PUBLICATION_NAME, NEWS_NS)
        _field(publication, "language", PUBLICATION_LANGUAGE, NEWS_NS)
        _field(news, "publication_date", published.isoformat(), NEWS_NS)
        _field(news, "title", article.get("title", ""), NEWS_NS)
    return _xml(root)


async def generate_sitemap(db):
    root = ET.Element("{" + NS + "}urlset")
    seen = set()
    def add(path, date=None):
        url = canonical_url(path)
        if url in seen: return
        seen.add(url)
        node = ET.SubElement(root, "{" + NS + "}url")
        _field(node, "loc", url)
        parsed = parse_publication_date(date)
        if parsed:
            _field(node, "lastmod", parsed.isoformat())
    for path in ("", "transfers", "geruechte", "ticker", "top-deals", "abloesefrei", "deadline-day", "redaktion", "impressum", "datenschutz", "ueber-uns"):
        add(path)
    for collection, prefix, query, maximum in (
        (db.articles, "news", {"status": "published"}, 45000),
        (db.players, "spieler", {}, 3500),
        (db.clubs, "verein", {}, 1000),
        (db.competitions, "wettbewerb", {}, 400),
    ):
        docs = await collection.find(query, {"_id": 0, "slug": 1, "updated_at": 1, "published_at": 1}).limit(maximum).to_list(maximum)
        for item in docs:
            if item.get("slug"):
                add(prefix + "/" + quote(item["slug"], safe=""), item.get("updated_at") or item.get("published_at"))
    return _xml(root)


async def generate_sitemap_index():
    root = ET.Element("{" + NS + "}sitemapindex")
    for filename in ("sitemap.xml", "news-sitemap.xml"):
        node = ET.SubElement(root, "{" + NS + "}sitemap")
        _field(node, "loc", canonical_url(filename))
    return _xml(root)


def generate_robots_txt():
    return ("User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\n"
            f"Sitemap: {SITE_URL}/sitemap-index.xml\n")


async def ping_google_sitemap(sitemap_url=None):
    """Compatibility shim: Google retired the sitemap ping endpoint."""
    return False


async def ping_google_news_sitemap():
    return False


async def ping_google_sitemaps():
    return {"main_sitemap": False, "news_sitemap": False, "reason": "deprecated_endpoint"}


async def track_article_update(db, article_id, update_type, details=None):
    now = datetime.now(timezone.utc).isoformat()
    await db.articles.update_one({"id": article_id}, {
        "$push": {"update_history": {"article_id": article_id, "update_type": update_type, "details": details, "timestamp": now}},
        "$set": {"updated_at": now},
    })
