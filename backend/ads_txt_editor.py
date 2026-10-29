"""Independent password-protected, append-only ads.txt editor.

No application, scheduler, database-network or provider imports. SQLite revisions
are the user's undo history, not scheduled backups. Seed explicitly before use.
"""
import argparse
import asyncio
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import functools
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from urllib.parse import urlsplit

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool


MAX_PASTE_BYTES = 512 * 1024
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
MAX_JSON_BYTES = MAX_PASTE_BYTES * 3 + 4096
SESSION_SECONDS = 8 * 60 * 60
ANONYMOUS_SECONDS = 15 * 60
LOGIN_WINDOW = 15 * 60
LOGIN_ATTEMPTS = 8
COOKIE_NAME = "__Host-tn_ads_session"
DEFAULT_DB_PATH = "/app/ads_txt/editor.sqlite3"
SCRYPT_N, SCRYPT_R, SCRYPT_P = 32768, 8, 1


class EditorError(Exception):
    def __init__(self, status, code, **fields):
        self.status, self.code, self.fields = status, code, fields


def _timestamp(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def hash_password(password):
    if not isinstance(password, str) or not 1 <= len(password.encode("utf-8")) <= 1024:
        raise ValueError("invalid_password_length")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N,
                            r=SCRYPT_R, p=SCRYPT_P, dklen=32, maxmem=64 * 1024 * 1024)
    return "scrypt$32768$8$1$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()


def _password_parts(encoded):
    try:
        kind, n, r, p, salt, digest = encoded.split("$")
        if (kind, n, r, p) != ("scrypt", "32768", "8", "1"):
            raise ValueError
        salt, digest = base64.b64decode(salt, altchars=b"-_", validate=True), base64.b64decode(digest, altchars=b"-_", validate=True)
        if len(salt) != 16 or len(digest) != 32:
            raise ValueError
        return salt, digest
    except (ValueError, TypeError, AttributeError):
        raise EditorError(503, "configuration_unavailable") from None


def verify_password(password, encoded):
    salt, expected = _password_parts(encoded)
    actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N,
                            r=SCRYPT_R, p=SCRYPT_P, dklen=32, maxmem=64 * 1024 * 1024)
    return hmac.compare_digest(actual, expected)


def _load_password_hash(explicit=None):
    if explicit is not None:
        encoded = explicit
    else:
        path = os.environ.get("ADS_TXT_EDITOR_PASSWORD_HASH_FILE")
        try:
            if path:
                with open(path, "r", encoding="ascii") as stream:
                    encoded = stream.read(4097).strip()
            else:
                encoded = os.environ.get("ADS_TXT_EDITOR_PASSWORD_HASH", "").strip()
        except (OSError, UnicodeError):
            raise EditorError(503, "configuration_unavailable") from None
    if len(encoded) > 4096:
        raise EditorError(503, "configuration_unavailable")
    _password_parts(encoded)
    return encoded


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _valid_domain(domain):
    labels = domain.split(".")
    return (len(domain) <= 253 and len(labels) >= 2 and all(re.fullmatch(
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label) for label in labels))


def _printable_token(value):
    return len(value) <= 256 and all(33 <= ord(c) <= 126 and c not in ",#" for c in value)


def _directive_key(record):
    """IAB ads.txt 1.1 section 3.5; domains are compared case-insensitively."""
    name, value = (part.strip() for part in record.split("=", 1))
    name = name.upper()
    if name not in {"CONTACT", "SUBDOMAIN", "INVENTORYPARTNERDOMAIN", "OWNERDOMAIN", "MANAGERDOMAIN"}:
        return None, "unknown_directive"
    if not value:
        return None, "invalid_directive"
    if name == "CONTACT":
        return ("directive", name, value), None
    fields = [part.strip() for part in value.split(",")]
    if name == "MANAGERDOMAIN":
        if len(fields) not in (1, 2) or (len(fields) == 2 and fields[1] and not re.fullmatch(r"[A-Za-z]{2}", fields[1])):
            return None, "invalid_directive"
        country = fields[1].upper() if len(fields) == 2 else ""
    else:
        if len(fields) != 1:
            return None, "invalid_directive"
        country = ""
    if not _valid_domain(fields[0]):
        return None, "invalid_directive"
    return ("directive", name, fields[0].lower(), country), None


def _exclusive_directive_slot(key):
    if key and key[0] == "directive" and key[1] in {"OWNERDOMAIN", "MANAGERDOMAIN"}:
        return (key[1], key[3])
    return None


def _row_key(line):
    """Semantic comparison never changes the accepted source line itself."""
    if any(ord(c) < 32 and c != "\t" or ord(c) == 127 for c in line):
        return None, "control_character"
    record = line.split("#", 1)[0].strip()
    if not record:
        return None, None
    if re.match(r"^[A-Za-z][A-Za-z0-9_]*\s*=", record):
        return _directive_key(record)
    fields = [field.strip() for field in record.split(",")]
    if len(fields) not in (3, 4):
        return None, "field_count"
    domain, account, relationship = fields[:3]
    if not _valid_domain(domain):
        return None, "invalid_domain"
    if not account or not _printable_token(account):
        return None, "invalid_account"
    if relationship.upper() not in {"DIRECT", "RESELLER"}:
        return None, "invalid_relationship"
    # Certification is optional and not necessarily a TAG ID or 16 hex digits.
    if len(fields) == 4 and not _printable_token(fields[3]):
        return None, "invalid_certification"
    return (domain.lower(), account, relationship.upper(), fields[3] if len(fields) == 4 else ""), None


def preview_append(original, text):
    if not isinstance(text, str):
        raise EditorError(422, "invalid_request")
    try:
        submitted = text.encode("utf-8")
    except UnicodeError:
        raise EditorError(422, "invalid_request") from None
    if len(submitted) > MAX_PASTE_BYTES:
        raise EditorError(413, "paste_too_large")
    if len(original) > MAX_DOCUMENT_BYTES:
        raise EditorError(503, "document_too_large")
    existing = original.decode("utf-8")
    known, exclusive = set(), {}
    for line in re.split(r"\r\n|\r|\n", existing.lstrip("\ufeff")):
        key, error = _row_key(line)
        if key is not None and error is None:
            known.add(key)
            if _exclusive_directive_slot(key):
                exclusive.setdefault(_exclusive_directive_slot(key), key)
    endings = re.findall(r"\r\n|\r|\n", existing)
    newline = max(dict.fromkeys(endings), key=endings.count) if endings else "\n"
    parts = re.split(r"(\r\n|\r|\n)", text)
    accepted, errors = [], []
    counts = {"added_rows": 0, "duplicate_rows": 0, "comment_lines": 0, "blank_lines": 0}
    for offset in range(0, len(parts), 2):
        line = parts[offset]
        terminator = parts[offset + 1] if offset + 1 < len(parts) else ""
        if not line and not terminator:  # Not a synthetic extra trailing line.
            continue
        key, error = _row_key(line)
        if error:
            errors.append({"line": offset // 2 + 1, "code": error})
            continue
        if key is not None:
            if key in known:
                counts["duplicate_rows"] += 1
                continue
            slot = _exclusive_directive_slot(key)
            if slot and slot in exclusive and exclusive[slot] != key:
                errors.append({"line": offset // 2 + 1, "code": "conflicting_directive"})
                continue
            if slot:
                exclusive[slot] = key
            known.add(key)
            counts["added_rows"] += 1
        elif line.lstrip().startswith("#"):
            counts["comment_lines"] += 1
        else:
            counts["blank_lines"] += 1
        accepted.append(line + (newline if terminator else ""))
    if errors:
        raise EditorError(422, "invalid_rows", errors=errors[:100], invalid_count=len(errors))
    addition = "".join(accepted)
    if addition and original and not original.endswith((b"\r", b"\n")):
        addition = newline + addition
    combined = original + addition.encode("utf-8")
    if len(combined) > MAX_DOCUMENT_BYTES:
        raise EditorError(413, "document_too_large")
    return {**counts, "content": combined.decode("utf-8"), "appended_text": addition,
            "bytes": len(combined), "can_apply": combined != original}


SCHEMA = """
CREATE TABLE IF NOT EXISTS revisions (
 revision INTEGER PRIMARY KEY AUTOINCREMENT, content BLOB NOT NULL, sha256 TEXT NOT NULL,
 created_at TEXT NOT NULL, action TEXT NOT NULL, parent_revision INTEGER, restored_from INTEGER,
 added_rows INTEGER NOT NULL DEFAULT 0, duplicate_rows INTEGER NOT NULL DEFAULT 0
);
CREATE TRIGGER IF NOT EXISTS revisions_no_update BEFORE UPDATE ON revisions
 BEGIN SELECT RAISE(ABORT, 'immutable_revision'); END;
CREATE TRIGGER IF NOT EXISTS revisions_no_delete BEFORE DELETE ON revisions
 BEGIN SELECT RAISE(ABORT, 'immutable_revision'); END;
CREATE TABLE IF NOT EXISTS current_revision (singleton INTEGER PRIMARY KEY CHECK(singleton=1), revision INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, csrf_token TEXT NOT NULL, authenticated INTEGER NOT NULL,
 expires_at REAL NOT NULL, password_fingerprint TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS login_attempts (
 client_hash TEXT PRIMARY KEY, window_started REAL NOT NULL, attempts INTEGER NOT NULL
);
"""


class AdsTxtStore:
    def __init__(self, path=None, clock=time.time):
        self.path = Path(path or os.environ.get("ADS_TXT_EDITOR_DB_PATH", DEFAULT_DB_PATH))
        self.clock = clock

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        connection = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            os.chmod(self.path, 0o600)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.executescript(SCHEMA)
            yield connection
        finally:
            connection.close()

    def _current(self, connection):
        row = connection.execute("SELECT r.* FROM revisions r JOIN current_revision c ON r.revision=c.revision WHERE c.singleton=1").fetchone()
        if row is None:
            raise EditorError(503, "not_initialized")
        return row

    @staticmethod
    def _document(row, content=True):
        result = {key: row[key] for key in ("revision", "sha256", "created_at", "action", "parent_revision",
                                          "restored_from", "added_rows", "duplicate_rows")}
        result["bytes"] = len(row["content"])
        if content:
            result["content"] = bytes(row["content"]).decode("utf-8")
        return result

    def _insert(self, connection, content, action, parent=None, restored_from=None, counts=None):
        counts = counts or {}
        cursor = connection.execute(
            "INSERT INTO revisions(content,sha256,created_at,action,parent_revision,restored_from,added_rows,duplicate_rows) VALUES(?,?,?,?,?,?,?,?)",
            (content, hashlib.sha256(content).hexdigest(), _timestamp(self.clock()), action, parent, restored_from,
             counts.get("added_rows", 0), counts.get("duplicate_rows", 0)))
        revision = cursor.lastrowid
        connection.execute("INSERT INTO current_revision(singleton,revision) VALUES(1,?) ON CONFLICT(singleton) DO UPDATE SET revision=excluded.revision", (revision,))
        return self._document(connection.execute("SELECT * FROM revisions WHERE revision=?", (revision,)).fetchone())

    def seed(self, content, expected_sha256):
        if not isinstance(content, bytes) or len(content) > MAX_DOCUMENT_BYTES:
            raise EditorError(413, "document_too_large")
        content.decode("utf-8")  # Preserve valid UTF-8 bytes, including a pre-existing BOM.
        if not hmac.compare_digest(hashlib.sha256(content).hexdigest(), expected_sha256.lower()):
            raise EditorError(409, "baseline_hash_mismatch")
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM revisions LIMIT 1").fetchone():
                raise EditorError(409, "already_initialized")
            result = self._insert(connection, content, "seed")
            connection.commit()
            return result

    def document(self, revision=None):
        if not self.path.exists():
            raise EditorError(503, "not_initialized")
        with self.connection() as connection:
            row = self._current(connection) if revision is None else connection.execute(
                "SELECT * FROM revisions WHERE revision=?", (revision,)).fetchone()
            if row is None:
                raise EditorError(404, "revision_not_found")
            return self._document(row)

    def history(self, before=None, limit=100):
        with self.connection() as connection:
            self._current(connection)
            rows = connection.execute("SELECT revision,sha256,created_at,action,parent_revision,restored_from,added_rows,duplicate_rows,length(content) AS bytes FROM revisions WHERE revision < ? ORDER BY revision DESC LIMIT ?",
                                      (before or 9223372036854775807, limit + 1)).fetchall()
            return {"revisions": [dict(row) for row in rows[:limit]],
                    "next_before": rows[limit - 1]["revision"] if len(rows) > limit else None}

    def preview(self, text, expected_revision):
        with self.connection() as connection:
            row = self._current(connection)
            if row["revision"] != expected_revision:
                raise EditorError(409, "revision_conflict", current_revision=row["revision"])
            return {"base_revision": row["revision"], **preview_append(bytes(row["content"]), text)}

    def append(self, text, expected_revision):
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._current(connection)
            if row["revision"] != expected_revision:
                raise EditorError(409, "revision_conflict", current_revision=row["revision"])
            preview = preview_append(bytes(row["content"]), text)
            if not preview["can_apply"]:
                raise EditorError(422, "no_changes")
            result = self._insert(connection, preview["content"].encode("utf-8"), "append", row["revision"], counts=preview)
            connection.commit()
            return {**result, "comment_lines": preview["comment_lines"], "blank_lines": preview["blank_lines"]}

    def rollback(self, target_revision, expected_revision):
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = self._current(connection)
            if current["revision"] != expected_revision:
                raise EditorError(409, "revision_conflict", current_revision=current["revision"])
            target = connection.execute("SELECT * FROM revisions WHERE revision=?", (target_revision,)).fetchone()
            if target is None:
                raise EditorError(404, "revision_not_found")
            if target["content"] == current["content"]:
                raise EditorError(422, "no_changes")
            result = self._insert(connection, bytes(target["content"]), "rollback", current["revision"], target_revision)
            connection.commit()
            return result

    def new_session(self, password_hash, authenticated=False, old_token=None):
        token, csrf, now = secrets.token_urlsafe(32), secrets.token_urlsafe(32), self.clock()
        expires = now + (SESSION_SECONDS if authenticated else ANONYMOUS_SECONDS)
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM sessions WHERE expires_at<=?", (now,))
            if old_token:
                connection.execute("DELETE FROM sessions WHERE token_hash=?", (_token_hash(old_token),))
            connection.execute("INSERT INTO sessions VALUES(?,?,?,?,?)", (_token_hash(token), csrf, int(authenticated), expires, _token_hash(password_hash)))
            connection.execute("DELETE FROM sessions WHERE authenticated=0 AND token_hash NOT IN (SELECT token_hash FROM sessions WHERE authenticated=0 ORDER BY expires_at DESC LIMIT 2000)")
            connection.commit()
        return token, {"authenticated": authenticated, "csrf_token": csrf, "expires_at": _timestamp(expires)}

    def session(self, token, password_hash):
        if not token or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
            return None
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM sessions WHERE token_hash=?", (_token_hash(token),)).fetchone()
            if row is None:
                return None
            if row["expires_at"] <= self.clock() or not hmac.compare_digest(row["password_fingerprint"], _token_hash(password_hash)):
                connection.execute("DELETE FROM sessions WHERE token_hash=?", (_token_hash(token),))
                return None
            return {"authenticated": bool(row["authenticated"]), "csrf_token": row["csrf_token"], "expires_at": _timestamp(row["expires_at"])}

    def logout(self, token):
        with self.connection() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash=?", (_token_hash(token),))

    def record_login_attempt(self, client_ip):
        now, key = self.clock(), _token_hash(client_ip)
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM login_attempts WHERE window_started<=?", (now - LOGIN_WINDOW,))
            row = connection.execute("SELECT * FROM login_attempts WHERE client_hash=?", (key,)).fetchone()
            if row and row["attempts"] >= LOGIN_ATTEMPTS:
                raise EditorError(429, "rate_limited", retry_after=max(1, int(row["window_started"] + LOGIN_WINDOW - now)))
            connection.execute("INSERT INTO login_attempts VALUES(?,?,1) ON CONFLICT(client_hash) DO UPDATE SET attempts=attempts+1", (key, now))
            connection.commit()


class EditorRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        @functools.wraps(handler)
        async def guarded(request):
            try:
                response = await handler(request)
            except EditorError as exc:
                response = JSONResponse({"error": exc.code, **exc.fields}, status_code=exc.status)
                if exc.status == 429:
                    response.headers["Retry-After"] = str(exc.fields["retry_after"])
            except (sqlite3.Error, OSError, UnicodeError):
                response = JSONResponse({"error": "storage_unavailable"}, status_code=503)
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response
        return guarded


async def _body(request, maximum=MAX_JSON_BYTES):
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise EditorError(422, "invalid_json")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > maximum:
            raise EditorError(413, "paste_too_large")
        data.extend(chunk)
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError, RecursionError):
        raise EditorError(422, "invalid_json") from None
    if not isinstance(value, dict):
        raise EditorError(422, "invalid_request")
    return value


def _revision(value):
    if type(value) is not int or not 1 <= value < 9223372036854775807:
        raise EditorError(422, "invalid_request")
    return value


def create_ads_txt_routers(store=None, password_hash=None, origin=None):
    """Construct routers without starting services or opening a database."""
    store = store or AdsTxtStore()
    origin = origin or os.environ.get("ADS_TXT_EDITOR_ORIGIN", "https://transfernews.de")
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise ValueError("ADS_TXT_EDITOR_ORIGIN must be an HTTPS origin")
    editor = APIRouter(prefix="/api/ads-txt-editor", route_class=EditorRoute)
    public = APIRouter(route_class=EditorRoute)
    password_slots = asyncio.Semaphore(2)

    async def authentication(request, required=True, mutate=False):
        if mutate and (request.headers.get("origin") != origin or request.headers.get("sec-fetch-site") == "cross-site"):
            raise EditorError(403, "origin_forbidden")
        encoded = _load_password_hash(password_hash)
        token = request.cookies.get(COOKIE_NAME)
        session = await run_in_threadpool(store.session, token, encoded)
        if required and (not session or not session["authenticated"]):
            raise EditorError(401, "authentication_required")
        if mutate:
            csrf = request.headers.get("x-csrf-token", "")
            if not session or not re.fullmatch(r"[A-Za-z0-9_-]{43}", csrf) or not hmac.compare_digest(csrf, session["csrf_token"]):
                raise EditorError(403, "csrf_failed")
        return encoded, token, session

    def session_response(token, session):
        response = JSONResponse(session)
        response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS if session["authenticated"] else ANONYMOUS_SECONDS,
                            secure=True, httponly=True, samesite="strict", path="/")
        return response

    @editor.get("/session")
    async def get_session(request: Request):
        encoded, token, session = await authentication(request, required=False)
        if session:
            return session
        token, session = await run_in_threadpool(store.new_session, encoded)
        return session_response(token, session)

    @editor.post("/login")
    async def login(request: Request):
        encoded, old_token, _ = await authentication(request, required=False, mutate=True)
        body = await _body(request, maximum=8192)
        password = body.get("password")
        # Never trust user-controlled forwarding headers. The server must also
        # leave untrusted proxy-header rewriting disabled for request.client.
        client_ip = request.client.host if request.client else "unknown"
        await run_in_threadpool(store.record_login_attempt, client_ip)
        if not isinstance(password, str) or not 1 <= len(password.encode("utf-8")) <= 1024:
            raise EditorError(401, "invalid_credentials")
        async with password_slots:
            if not await run_in_threadpool(verify_password, password, encoded):
                raise EditorError(401, "invalid_credentials")
        token, session = await run_in_threadpool(store.new_session, encoded, True, old_token)
        return session_response(token, session)

    @editor.post("/logout")
    async def logout(request: Request):
        _, token, _ = await authentication(request, mutate=True)
        await _body(request, maximum=8192)
        await run_in_threadpool(store.logout, token)
        response = JSONResponse({"authenticated": False})
        response.delete_cookie(COOKIE_NAME, path="/", secure=True, httponly=True, samesite="strict")
        return response

    @editor.get("/document")
    async def document(request: Request):
        await authentication(request)
        return await run_in_threadpool(store.document)

    @editor.get("/history")
    async def history(request: Request, before: int = None):
        await authentication(request)
        if before is not None:
            _revision(before)
        return await run_in_threadpool(store.history, before)

    @editor.get("/revisions/{revision}")
    async def revision_document(request: Request, revision: int):
        await authentication(request)
        return await run_in_threadpool(store.document, _revision(revision))

    async def append_request(request, apply):
        await authentication(request, mutate=True)
        body = await _body(request)
        expected = _revision(body.get("expected_revision"))
        return await run_in_threadpool(store.append if apply else store.preview, body.get("text"), expected)

    @editor.post("/preview")
    async def preview(request: Request):
        return await append_request(request, False)

    @editor.post("/append")
    async def append(request: Request):
        return await append_request(request, True)

    @editor.post("/rollback")
    async def rollback(request: Request):
        await authentication(request, mutate=True)
        body = await _body(request, maximum=8192)
        return await run_in_threadpool(store.rollback, _revision(body.get("target_revision")), _revision(body.get("expected_revision")))

    @public.api_route("/ads.txt", methods=["GET", "HEAD"])
    @public.api_route("/api/ads-txt/public", methods=["GET", "HEAD"])
    async def public_document(request: Request):
        document = await run_in_threadpool(store.document)
        etag = '"' + document["sha256"] + '"'
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag})
        content = document["content"].encode("utf-8")
        return Response(content=b"" if request.method == "HEAD" else content, media_type="text/plain",
                        headers={"ETag": etag, "Content-Length": str(len(content))})

    return editor, public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("seed")
    seed.add_argument("--baseline", type=Path, required=True)
    seed.add_argument("--expected-sha256", required=True)
    seed.add_argument("--db", default=os.environ.get("ADS_TXT_EDITOR_DB_PATH", DEFAULT_DB_PATH))
    password = commands.add_parser("hash-password")
    password.add_argument("--output", type=Path)
    password.add_argument("--stdin", action="store_true", help="Read one password line from protected stdin, never argv")
    args = parser.parse_args()
    try:
        if args.command == "seed":
            if not re.fullmatch(r"[a-fA-F0-9]{64}", args.expected_sha256):
                raise EditorError(422, "invalid_baseline_hash")
            with args.baseline.open("rb") as stream:
                content = stream.read(MAX_DOCUMENT_BYTES + 1)
            result = AdsTxtStore(args.db).seed(content, args.expected_sha256)
            result.pop("content")
            print(json.dumps(result))
        else:
            if args.stdin:
                import sys
                entered = sys.stdin.readline(2048).rstrip("\r\n")
            else:
                entered = getpass.getpass("Editor password: ")
                if not hmac.compare_digest(entered.encode("utf-8"), getpass.getpass("Repeat password: ").encode("utf-8")):
                    raise EditorError(422, "password_mismatch")
            encoded = hash_password(entered)
            if args.output:
                fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w", encoding="ascii") as stream:
                    stream.write(encoded + "\n")
                print(json.dumps({"password_hash_written": True}))
            else:
                print(encoded)
        return 0
    except EditorError as exc:
        print(json.dumps({"error": exc.code}))
        return 1
    except (OSError, ValueError, UnicodeError, sqlite3.Error):
        print(json.dumps({"error": "operation_failed"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
