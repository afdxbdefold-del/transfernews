"""Offline ASGI regression tests. Never start jobs or access a real database/network."""
import asyncio
import copy
import importlib
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import httpx
import jwt
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from security import load_jwt_secret, issue_token, ISSUER, AUDIENCE, LoginAttemptLimiter
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError


class Cursor:
    def __init__(self, rows): self.rows = copy.deepcopy(rows)
    def sort(self, *a): return self
    def skip(self, count): self.rows = self.rows[count:]; return self
    def limit(self, count): self.rows = self.rows[:count]; return self
    async def to_list(self, count): return self.rows[:count]


class Collection:
    def __init__(self, rows=()): self.rows = copy.deepcopy(list(rows)); self.writes = 0
    def find(self, query, *a):
        return Cursor([r for r in self.rows if all(k.startswith('$') or r.get(k) == v for k,v in query.items())])
    async def find_one(self, query, *a):
        return next((copy.deepcopy(r) for r in self.rows if all(r.get(k) == v for k,v in query.items())), None)
    async def update_one(self, *a, **kw): self.writes += 1; raise AssertionError('Unexpected write')
    async def insert_one(self, *a, **kw): self.writes += 1; raise AssertionError('Unexpected write')


class Database:
    def __init__(self):
        self.users = Collection([
            dict(id='admin', email='admin@example.test', name='Fixture admin', role='admin', is_active=True),
            dict(id='editor', email='editor@example.test', name='Fixture editor', role='editor', is_active=True),
            dict(id='disabled', email='disabled@example.test', name='Fixture disabled', role='admin', is_active=False),
        ])
        self.articles = Collection([
            dict(id='published', title='Published fixture', slug='published-fixture', status='published', body='Public fixture', published_at=datetime.now(timezone.utc)),
            dict(id='draft', title='Private fixture', slug='draft-fixture', status='draft', body='Private fixture'),
        ])
        self.players = Collection(); self.clubs = Collection(); self.competitions = Collection(); self.settings = Collection()
        self.authors = Collection(); self.aliases = Collection(); self.transfers = Collection()
        self.fail_ping = False
    async def command(self, command):
        assert command == 'ping'
        if self.fail_ping: raise RuntimeError('synthetic dependency failure')
        return {'ok': 1}


class PasswordUsers(Collection):
    async def update_one(self, query, update):
        for row in self.rows:
            if all(row.get(k)==v for k,v in query.items()):
                row.update(update['$set'])
                self.writes += 1
                return SimpleNamespace(modified_count=1)
        return SimpleNamespace(modified_count=0)


@pytest.fixture(scope='module')
def app_module(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    root = tmp_path_factory.mktemp('security')
    mp.setenv('JWT_SECRET_KEY', secrets.token_urlsafe(48))
    mp.delenv('JWT_SECRET_FILE', raising=False)
    mp.setenv('MONGO_URL', 'mongodb://127.0.0.1:1')
    mp.setenv('DB_NAME', 'isolated_security_test')
    mp.setenv('SCHEDULER_ENABLED', 'false')
    mp.setenv('MEDIA_ROOT', str(root / 'media'))
    mp.setenv('PRERENDER_CACHE_DIR', str(root / 'cache'))
    module = importlib.import_module('server')
    module.client.close()
    yield module
    mp.undo()


@pytest.fixture
def app(app_module, monkeypatch):
    database = Database()
    monkeypatch.setattr(app_module, 'db', database)
    monkeypatch.setattr(app_module, 'get_scheduler_status', lambda: {'running': False})
    return app_module


def request(app, method, path, **kwargs):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app.app), base_url='http://isolated.test') as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(run())


def headers(app, subject='admin', role='admin'):
    return {'Authorization': 'Bearer ' + issue_token(app.JWT_SECRET, subject, 'fixture@example.test', role)}


@pytest.mark.parametrize('env', [{}, {'JWT_SECRET_KEY':'short'}, {'JWT_SECRET_KEY':'a'*64}, {'JWT_SECRET_FILE':'/nonexistent/audit-key'}])
def test_missing_or_weak_signing_configuration_fails_closed(env):
    with pytest.raises(RuntimeError): load_jwt_secret(env)


def test_secret_file_support(tmp_path):
    key = secrets.token_urlsafe(48)
    f = tmp_path/'key'; f.write_text(key+'\n')
    assert load_jwt_secret({'JWT_SECRET_FILE':str(f)}) == key


def test_login_attempts_are_limited_and_expire():
    limiter=LoginAttemptLimiter(window=60, account_limit=2)
    limiter.check('fixture@example.test','first',now=1)
    limiter.check('fixture@example.test','second',now=2)
    with pytest.raises(HTTPException) as err:
        limiter.check('fixture@example.test','third',now=3)
    assert err.value.status_code == 429
    limiter.check('fixture@example.test','third',now=63)


def test_auth_requires_real_active_user_and_current_role(app):
    assert request(app,'GET','/api/users').status_code == 401
    assert request(app,'GET','/api/users',headers=headers(app)).status_code == 200
    assert request(app,'GET','/api/users',headers=headers(app,'does-not-exist')).status_code == 401
    assert request(app,'GET','/api/users',headers=headers(app,'disabled')).status_code == 401
    assert request(app,'GET','/api/users',headers=headers(app,'editor','admin')).status_code == 403


def test_missing_expiry_expired_wrong_signature_and_issuer_rejected(app):
    payload={'sub':'admin','role':'admin','iat':datetime.now(timezone.utc),'iss':ISSUER,'aud':AUDIENCE,'jti':'fixture','auth_version':0}
    for changes,key in [({},app.JWT_SECRET),({'exp':datetime.now(timezone.utc)-timedelta(seconds=1)},app.JWT_SECRET),
                        ({'exp':datetime.now(timezone.utc)+timedelta(minutes=1)},secrets.token_urlsafe(48)),
                        ({'exp':datetime.now(timezone.utc)+timedelta(minutes=1),'iss':'other'},app.JWT_SECRET)]:
        token=jwt.encode({**payload,**changes},key,algorithm='HS256')
        assert request(app,'GET','/api/users',headers={'Authorization':'Bearer '+token}).status_code == 401


def test_password_change_verifies_current_secret_and_revokes_all_old_tokens(app):
    old_password='Isolated-original-password-123!'
    new_password='Isolated-replacement-password-456!'
    app.db.users=PasswordUsers(app.db.users.rows)
    app.db.users.rows[0]['password_hash']=app.pwd_context.hash(old_password)
    old_headers=headers(app)
    assert request(app,'POST','/api/auth/change-password',json={'current_password':old_password,'new_password':new_password}).status_code==401
    assert request(app,'POST','/api/auth/change-password',headers=old_headers,json={'current_password':'wrong','new_password':new_password}).status_code==400
    assert request(app,'POST','/api/auth/change-password',headers=old_headers,json={'current_password':old_password,'new_password':'short'}).status_code==422
    response=request(app,'POST','/api/auth/change-password',headers=old_headers,json={'current_password':old_password,'new_password':new_password})
    assert response.status_code==200
    assert app.pwd_context.verify(new_password,app.db.users.rows[0]['password_hash'])
    assert app.db.users.rows[0]['auth_version']==1
    assert request(app,'GET','/api/users',headers=old_headers).status_code==401
    fresh={'Authorization':'Bearer '+response.json()['access_token']}
    assert request(app,'GET','/api/users',headers=fresh).status_code==200


def test_publication_visibility_and_authenticated_editor_view(app):
    response=request(app,'GET','/api/articles?status=draft')
    assert response.status_code == 200
    assert all(item['status']=='published' for item in response.json())
    for path in ['/api/articles/draft','/api/articles/slug/draft-fixture']:
        assert request(app,'GET',path).status_code == 404
        assert request(app,'GET',path,headers=headers(app,'editor','editor')).status_code == 200
    assert len(request(app,'GET','/api/articles',headers=headers(app)).json()) == 2


def test_unauthenticated_management_routes_cannot_write(app):
    for method,path in [('POST','/api/players/enrich-images'),('POST','/api/players/fixture/update-image'),('GET','/api/settings/internal')]:
        assert request(app,method,path).status_code == 401
    assert request(app,'POST','/api/init/admin').status_code == 404
    assert request(app,'GET','/api/download-db-export').status_code == 404
    assert app.db.players.writes == 0


def test_duplicate_database_identity_returns_conflict_without_database_details(app):
    class DuplicateArticles(Collection):
        async def insert_one(self,*a,**kw):
            raise DuplicateKeyError('sensitive database index details')
    app.db.articles=DuplicateArticles()
    response=request(app,'POST','/api/articles',headers=headers(app),json={'title':'Fixture','slug':'fixture'})
    assert response.status_code==409
    assert 'sensitive' not in response.text


def test_readiness_reports_failed_dependencies_and_scheduler(app, monkeypatch):
    assert request(app,'GET','/api/ready').status_code == 200
    app.db.fail_ping=True
    assert request(app,'GET','/api/ready').status_code == 503
    assert request(app,'GET','/api/health').status_code == 200
    app.db.fail_ping=False
    monkeypatch.setenv('SCHEDULER_ENABLED','true')
    assert request(app,'GET','/api/ready').status_code == 503


def test_article_html_is_publication_checked_escaped_and_preserves_shell(app,monkeypatch):
    import prerender
    async def shell(): return '<!doctype html><html><head><title>Generic</title><script defer src="/static/js/app.js"></script><link href="/static/css/app.css" rel="stylesheet"></head><body><div id="root"></div></body></html>'
    monkeypatch.setattr(prerender,'get_frontend_shell',shell)
    app.db.articles.rows[0]['title']='Safe </script><img src=x onerror=bad()> & title'
    response=request(app,'GET','/api/ssr/news/published-fixture')
    assert response.status_code == 200
    assert '/static/js/app.js' in response.text and '/static/css/app.css' in response.text
    assert 'id="server-article"' in response.text
    assert '<img src=x onerror=bad()>' not in response.text
    assert '\\u003c/script' in response.text
    assert '<link data-rh="true" rel="canonical" href="https://transfernews.de/news/published-fixture">' in response.text
    assert request(app,'GET','/api/ssr/news/draft-fixture').status_code == 404
    assert request(app,'GET','/api/ssr/news/missing').status_code == 404
    assert request(app,'GET','/api/ssr/http://example.invalid').status_code == 404
    assert request(app,'GET','/api/ssr/news/encoded%22marker').status_code == 404


def test_profile_dispatch_and_player_aliases_return_real_status_and_safe_redirects(app,monkeypatch):
    import prerender
    async def shell(): return '<!doctype html><html><head><title>Generic</title></head><body><div id="root"></div><script src="/static/app.js"></script></body></html>'
    monkeypatch.setattr(prerender,'get_frontend_shell',shell)
    app.db.players.rows=[{'id':'canonical-player','slug':'wirtz','name':'Florian Wirtz'}]
    app.db.aliases.rows=[{'entity_type':'player','entity_id':'canonical-player','normalized_alias':'florian-wirtz'}]
    canonical=request(app,'GET','/api/ssr/spieler/wirtz')
    assert canonical.status_code==200
    assert 'Florian Wirtz Transfer-News' in canonical.text
    assert 'https://transfernews.de/spieler/wirtz' in canonical.text
    assert 'CollectionPage' in canonical.text and 'NewsArticle' not in canonical.text
    assert '/static/app.js' in canonical.text
    for source,target in [('/api/ssr/spieler/florian-wirtz','/spieler/wirtz'),
                          ('/api/players/slug/florian-wirtz','/api/players/slug/wirtz'),
                          ('/api/players/slug/florian-wirtz/transfers','/api/players/slug/wirtz/transfers')]:
        response=request(app,'GET',source)
        assert response.status_code==301
        assert response.headers['location']==target
    missing=request(app,'GET','/api/ssr/spieler/missing')
    assert missing.status_code==404 and 'noindex' in missing.text
    app.db.players.rows[0]['slug']='//evil.invalid'
    assert request(app,'GET','/api/ssr/spieler/florian-wirtz').status_code==404
    assert request(app,'GET','/api/players/slug/florian-wirtz').status_code==404


def test_standalone_html_fallback_and_path_validation(app,monkeypatch):
    import prerender
    async def missing_shell(): return None
    monkeypatch.setattr(prerender,'get_frontend_shell',missing_shell)
    assert '<h1>Published fixture</h1>' in request(app,'GET','/api/ssr/news/published-fixture').text
    for path in ['//evil.test','/admin','/api/health','/news/../admin','/news/a?url=evil','/news/a"onclick=x']:
        with pytest.raises(ValueError): prerender.validate_public_path(path)


def test_sitemaps_escape_xml_support_dates_and_exclude_old_news(app):
    import sitemap
    now=datetime.now(timezone.utc)
    app.db.articles.rows=[
        dict(slug='new-a',title='A & <B>',status='published',published_at=now-timedelta(minutes=1)),
        dict(slug='new-b',title='String date',status='published',published_at=(now-timedelta(minutes=2)).isoformat()),
        dict(slug='new-a',title='Duplicate URL',status='published',published_at=now-timedelta(minutes=3)),
        dict(slug='old',title='Old',status='published',published_at=(now-timedelta(days=4)).isoformat()),
        dict(slug='draft',title='Draft',status='draft',published_at=now.isoformat()),
    ]
    xml=asyncio.run(sitemap.generate_news_sitemap(app.db))
    root=ET.fromstring(xml)
    assert len(root)==2
    assert 'A &amp; &lt;B&gt;' in xml
    assert '/news/old' not in xml and '/news/draft' not in xml
    sitemap_root=ET.fromstring(asyncio.run(sitemap.generate_sitemap(app.db)))
    locations=[element.text for element in sitemap_root.iter('{'+sitemap.NS+'}loc')]
    assert len(locations)==len(set(locations))
    assert 'Disallow: /admin' in sitemap.generate_robots_txt()
