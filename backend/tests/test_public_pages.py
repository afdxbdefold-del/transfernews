"""Offline checks for profile validity, published content, escaping and SPA shell reuse."""
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import AsyncMock, patch

import mongomock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from public_pages import render_public_profile, render_not_found


class Cursor:
    def __init__(self, cursor): self.cursor = cursor
    def sort(self, *args): self.cursor.sort(*args); return self
    def limit(self, count): self.cursor.limit(count); return self
    async def to_list(self, length): return list(self.cursor)[:length]


class Collection:
    def __init__(self, collection): self.raw = collection
    def find(self, *args, **kwargs): return Cursor(self.raw.find(*args, **kwargs))
    async def find_one(self, *args, **kwargs): return self.raw.find_one(*args, **kwargs)


class Database:
    def __init__(self): self.raw = mongomock.MongoClient().public_profiles
    def __getattr__(self, name): return Collection(self.raw[name])


SHELL = ('<!doctype html><html><head><title>Old title</title>'
         '<meta name="robots" content="index,follow"><link href="/static/app.css" rel="stylesheet">'
         '<script defer src="/static/app.js"></script></head><body><div id="root"></div></body></html>')


class PublicPageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = Database()
        self.shell = patch("prerender.get_frontend_shell", AsyncMock(return_value=SHELL))
        self.shell.start()
        self.addCleanup(self.shell.stop)
        network = patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited"))
        network.start()
        self.addCleanup(network.stop)

    async def test_five_supported_profile_types_are_200_with_shell(self):
        self.db.raw.players.insert_one({"slug": "test-player", "name": "Test Player", "id": "p1"})
        self.db.raw.clubs.insert_one({"slug": "test-club", "name": "Test Club", "id": "c1"})
        self.db.raw.authors.insert_one({"slug": "redaktion", "name": "Redaktion", "is_active": True})
        for path in ["/spieler/test-player", "/verein/test-club", "/autor/redaktion", "/wettbewerb/bundesliga", "/thema/leihen"]:
            with self.subTest(path=path):
                html, status = await render_public_profile(self.db, path)
                self.assertEqual(status, 200)
                self.assertIn('id="root"><main id="server-profile"', html)
                self.assertIn('/static/app.js', html)
                self.assertIn('/static/app.css', html)
                self.assertIn('data-rh="true" rel="canonical"', html)
                self.assertIn('"@type": "CollectionPage"', html)
                self.assertNotIn('NewsArticle', html)
                self.assertNotIn('Old title', html)

    async def test_missing_profiles_and_inactive_authors_are_real_404(self):
        self.db.raw.authors.insert_one({"slug": "inactive", "name": "Hidden", "is_active": False})
        # A separate competitions collection does not define the public competition route.
        self.db.raw.competitions.insert_one({"slug": "private-competition", "name": "Private"})
        for path in ["/spieler/missing", "/verein/missing", "/autor/missing", "/autor/inactive",
                     "/wettbewerb/private-competition", "/thema/missing"]:
            with self.subTest(path=path):
                html, status = await render_public_profile(self.db, path)
                self.assertEqual(status, 404)
                self.assertIn('name="robots" content="noindex,follow"', html)
                self.assertIn('Seite nicht gefunden', html)
                self.assertIn('/static/app.js', html)
                self.assertNotIn('rel="canonical"', html)

    async def test_arbitrary_paths_404_without_database_access_or_reflection(self):
        for path in ["/nothing/here", "/", "/spieler/../../private", '/autor/<script>alert(1)</script>', "/thema/leihen?x=1"]:
            html, status = await render_public_profile(None, path)
            self.assertEqual(status, 404)
            self.assertNotIn('alert(1)', html)
            self.assertNotIn('application/ld+json', html)

    async def test_each_kind_lists_only_its_published_articles(self):
        self.db.raw.players.insert_one({"slug": "player", "name": "Player", "id": "p1"})
        self.db.raw.clubs.insert_one({"slug": "club", "name": "Club", "id": "c1"})
        self.db.raw.authors.insert_one({"slug": "author", "name": "Author", "is_active": True})
        common = {"linked_player_ids": ["p1"], "linked_club_ids": ["c1"], "author_slug": "author", "title": "Bayern leihe", "body": "Bayern leihe"}
        self.db.raw.articles.insert_many([
            {**common, "slug": "public-story", "status": "published"},
            {**common, "slug": "secret-draft", "status": "draft"},
            {**common, "slug": 'bad\"onclick=alert(1)', "status": "published"},
            {"slug": "unrelated-story", "status": "published", "title": "Elsewhere"},
        ])
        for path in ["/spieler/player", "/verein/club", "/autor/author", "/wettbewerb/bundesliga", "/thema/leihen"]:
            with self.subTest(path=path):
                html, status = await render_public_profile(self.db, path)
                self.assertEqual(status, 200)
                self.assertIn('href="/news/public-story"', html)
                self.assertNotIn('secret-draft', html)
                self.assertNotIn('unrelated-story', html)
                self.assertNotIn('onclick=', html)

    async def test_profile_fields_are_escaped_and_private_fields_omitted(self):
        self.db.raw.authors.insert_one({"slug": "author", "name": '<script>alert("name")</script>', "is_active": True,
                                        "bio": '</script><img src=x onerror="run()">', "email": "private@example.invalid"})
        html, status = await render_public_profile(self.db, "/autor/author")
        self.assertEqual(status, 200)
        self.assertNotIn('<script>alert(', html)
        self.assertNotIn('<img src=x', html)
        self.assertNotIn('private@example.invalid', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('\\u003c/script\\u003e', html)

    async def test_missing_legacy_id_does_not_query_unrelated_articles(self):
        self.db.raw.players.insert_one({"slug": "no-id", "name": "Legacy Player"})
        self.db.raw.articles.insert_one({"slug": "unrelated", "status": "published", "title": "Unrelated"})
        html, status = await render_public_profile(self.db, "/spieler/no-id")
        self.assertEqual(status, 200)
        self.assertNotIn('/news/unrelated', html)

    async def test_404_has_standalone_html_when_frontend_shell_unavailable(self):
        with patch("prerender.get_frontend_shell", AsyncMock(return_value=None)):
            html, status = await render_not_found()
        self.assertEqual(status, 404)
        self.assertTrue(html.startswith('<!doctype html>'))
        self.assertIn('<html lang="de">', html)
        self.assertIn('Seite nicht gefunden', html)


if __name__ == "__main__":
    unittest.main()
