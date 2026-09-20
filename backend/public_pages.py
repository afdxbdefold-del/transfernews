"""Public profile HTML and real 404s, using the same records as the public API."""
from html import escape
import re

from prerender import SITE_URL, compose_public_document, safe_json_ld
from trending import COMPETITIONS, THEMES


_PROFILE_PATH = re.compile(r"/(spieler|verein|wettbewerb|autor|thema)/([A-Za-z0-9_-]{1,240})")
_ARTICLE_SLUG = re.compile(r"[A-Za-z0-9_-]{1,240}")
_ARTICLE_FIELDS = {"_id": 0, "title": 1, "slug": 1, "excerpt": 1, "status": 1}


def _head(title, description, canonical=None, *, missing=False):
    head = (f'<title data-rh="true">{escape(title)}</title>'
            f'<meta data-rh="true" name="description" content="{escape(description, quote=True)}">'
            f'<meta data-rh="true" name="robots" content="{"noindex,follow" if missing else "index,follow"}">')
    if canonical:
        head += (f'<link data-rh="true" rel="canonical" href="{escape(canonical, quote=True)}">'
                 '<meta data-rh="true" property="og:type" content="website">'
                 f'<meta data-rh="true" property="og:title" content="{escape(title, quote=True)}">'
                 f'<meta data-rh="true" property="og:description" content="{escape(description, quote=True)}">'
                 f'<meta data-rh="true" property="og:url" content="{escape(canonical, quote=True)}">')
    return head


async def render_not_found(path="/"):
    """Keep the SPA assets so React can show its normal error page after loading."""
    head = _head("Seite nicht gefunden | transfernews.de", "Diese Seite wurde nicht gefunden.", missing=True)
    body = ('<main id="server-not-found"><a href="/">transfernews.de</a>'
            '<h1>Seite nicht gefunden</h1><p>Die gesuchte Seite ist nicht verfügbar.</p>'
            '<a href="/">Zur Startseite</a></main>')
    return await compose_public_document(head, body), 404


async def _profile_data(db, kind, slug):
    """No network access: profile validity follows each corresponding public API."""
    if kind in {"spieler", "verein", "autor"}:
        collection = {"spieler": db.players, "verein": db.clubs, "autor": db.authors}[kind]
        query = {"slug": slug}
        if kind == "autor":
            query["is_active"] = True
        # Select public display fields explicitly; never render a full database record.
        profile = await collection.find_one(query, {"_id": 0, "id": 1, "name": 1, "bio": 1,
                                                    "meta_title": 1, "seo_title": 1, "meta_description": 1})
        if profile is None:
            return None
        name = str(profile.get("name") or slug)
        heading = name if kind == "autor" else f"{name} Transfer-News"
        title = str(profile.get("seo_title") or profile.get("meta_title") or f"{heading} | transfernews.de")
        description = str(profile.get("meta_description") or profile.get("bio") or
                          (f"Alle Artikel von {name}." if kind == "autor" else f"Aktuelle Transfer-News und Gerüchte zu {name}."))
        if kind == "autor":
            article_query = {"author_slug": slug, "status": "published"}
        elif profile.get("id"):
            field = "linked_player_ids" if kind == "spieler" else "linked_club_ids"
            article_query = {field: profile["id"], "status": "published"}
        else:
            # A malformed legacy record still exists, but must not match unrelated null IDs.
            return heading, title, description, []
    else:
        profile = (COMPETITIONS if kind == "wettbewerb" else THEMES).get(slug)
        if profile is None:
            return None
        name = profile["name"]
        heading = f"{name} Transfer-News" if kind == "wettbewerb" else name
        title = f"{heading} | transfernews.de"
        description = (f"Aktuelle Transfer-News, Gerüchte und bestätigte Wechsel aus der {name}. Alle Transfers im Überblick."
                       if kind == "wettbewerb" else profile["description"])
        terms = profile["clubs"] if kind == "wettbewerb" else profile["keywords"]
        article_query = {"status": "published"}
        if terms:
            pattern = "|".join(re.escape(term) for term in terms)
            article_query["$or"] = [{"title": {"$regex": pattern, "$options": "i"}},
                                    {"body": {"$regex": pattern, "$options": "i"}}]
    articles = await db.articles.find(article_query, _ARTICLE_FIELDS).sort("published_at", -1).limit(20).to_list(20)
    return heading, title, description, articles


async def render_public_profile(db, path):
    """Return (HTML, HTTP status); missing or unsupported profiles are genuine 404s."""
    match = _PROFILE_PATH.fullmatch(path)
    if not match:
        return await render_not_found(path)
    data = await _profile_data(db, *match.groups())
    if data is None:
        return await render_not_found(path)
    heading, title, description, articles = data
    canonical = SITE_URL.rstrip("/") + path
    body = ('<main id="server-profile"><a href="/">transfernews.de</a>'
            f'<h1>{escape(heading)}</h1><p>{escape(description)}</p>')
    items = []
    links = []
    for article in articles:
        slug = article.get("slug")
        if article.get("status") != "published" or not isinstance(slug, str) or not _ARTICLE_SLUG.fullmatch(slug):
            continue
        label = str(article.get("title") or "Transfer-News")
        url = "/news/" + slug
        links.append(f'<li><a href="{escape(url, quote=True)}">{escape(label)}</a></li>')
        items.append({"@type": "ListItem", "position": len(items) + 1, "url": SITE_URL.rstrip("/") + url, "name": label})
    if links:
        body += "<h2>Aktuelle Artikel</h2><ul>" + "".join(links) + "</ul>"
    else:
        body += "<p>Aktuell sind keine Artikel verfügbar.</p>"
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": heading,
              "description": description, "url": canonical,
              "mainEntity": {"@type": "ItemList", "itemListElement": items}}
    body += '<script type="application/ld+json">' + safe_json_ld(schema) + '</script></main>'
    return await compose_public_document(_head(title, description, canonical), body), 200
