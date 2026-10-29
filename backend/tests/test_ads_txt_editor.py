"""Isolated SQLite/ASGI tests; never import the application or start jobs."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import httpx
from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ads_txt_editor import (AdsTxtStore, EditorError, COOKIE_NAME, SESSION_SECONDS, LOGIN_WINDOW,
                            MAX_JSON_BYTES, MAX_DOCUMENT_BYTES, MAX_PASTE_BYTES,
                            create_ads_txt_routers, hash_password, verify_password, preview_append, main)


BASELINE = b"# Existing exact bytes\r\nGoogle.com, pub-123, DIRECT, f08c47fec0942fa0\r\nlegacy-directive=leave-exactly\r\n"
NEW_ROW = "example.com, account-1, DIRECT, f08c47fec0942fa0"
ORIGIN = "https://transfernews.de"
PASSWORD = "isolated-test-password-only"


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "editor.sqlite3"
        self.store = AdsTxtStore(self.path)
        self.store.seed(BASELINE, hashlib.sha256(BASELINE).hexdigest())

    def test_exact_seed_utf8_bom_missing_newline_and_all_newline_styles(self):
        self.assertEqual(self.store.document()["content"].encode(), BASELINE)
        for original in (b"# one\r\n", b"# one\n", b"# one\r", b"# no final newline", b"\xef\xbb\xbf# existing"):
            with self.subTest(original=original):
                result = preview_append(original, NEW_ROW + "\n# inserted\n")
                output = result["content"].encode()
                self.assertTrue(output.startswith(original))
                expected_newline = b"\r\n" if original.endswith(b"\r\n") else b"\r" if original.endswith(b"\r") else b"\n"
                self.assertTrue(output.endswith(NEW_ROW.encode() + expected_newline + b"# inserted" + expected_newline))

    def test_semantic_duplicates_removed_without_rewriting_accepted_text(self):
        text = "  google.COM , pub-123 , direct , f08c47fec0942fa0 # duplicate\n" + NEW_ROW + "\n" + NEW_ROW.upper().replace("ACCOUNT-1", "account-1").replace("F08C47FEC0942FA0", "f08c47fec0942fa0") + "\n# note\n\n"
        preview = self.store.preview(text, 1)
        self.assertEqual((preview["added_rows"], preview["duplicate_rows"], preview["comment_lines"], preview["blank_lines"]), (1, 2, 1, 1))
        result = self.store.append(text, 1)
        self.assertEqual(result["content"].encode(), BASELINE + NEW_ROW.encode() + b"\r\n# note\r\n\r\n")
        self.assertEqual(result["sha256"], hashlib.sha256(result["content"].encode()).hexdigest())

    def test_account_and_certification_case_not_silently_collapsed(self):
        preview = self.store.preview("google.com, PUB-123, DIRECT, f08c47fec0942fa0\n", 1)
        self.assertEqual(preview["added_rows"], 1)

    def test_iab_directives_and_optional_arbitrary_certification(self):
        original = (b"OWNERDOMAIN=transfernews.de\r\nMANAGERDOMAIN=themoneytizer.com\r\n"
                    b"blueroostermedia.com, 1022, DIRECT,\r\n")
        paste = ("ownerdomain = TRANSFERNEWS.DE\nmanagerdomain = THEMONEYTIZER.COM,\n"
                 "blueroostermedia.com, 1022, direct\n"
                 "greenadexchange.com, XF7342, DIRECT, 5jyxf8k54\n"
                 "CONTACT=Advertising team +49 123 456\nSUBDOMAIN=ads.example.com\n"
                 "INVENTORYPARTNERDOMAIN=partner.example.com\nMANAGERDOMAIN=regional.example.com, de\n")
        result = preview_append(original, paste)
        self.assertEqual((result["duplicate_rows"], result["added_rows"]), (3, 5))
        self.assertTrue(result["content"].encode().startswith(original))
        self.assertIn("5jyxf8k54\r\n", result["appended_text"])
        self.assertIn("MANAGERDOMAIN=regional.example.com, de\r\n", result["appended_text"])

    def test_bad_or_conflicting_directive_is_atomic(self):
        original = b"OWNERDOMAIN=owner.example\nMANAGERDOMAIN=manager.example, DE\n"
        cases = (("OWNERDOMAIN=https://example.com", "invalid_directive"),
                 ("MANAGERDOMAIN=example.com, DEU", "invalid_directive"),
                 ("CONTACT=", "invalid_directive"), ("UNKNOWNVARIABLE=x", "unknown_directive"),
                 ("OWNERDOMAIN=other.example", "conflicting_directive"),
                 ("MANAGERDOMAIN=other.example, de", "conflicting_directive"))
        for row, code in cases:
            with self.subTest(row=row), self.assertRaises(EditorError) as failure:
                preview_append(original, NEW_ROW + "\n" + row)
            self.assertEqual(failure.exception.fields["errors"], [{"line": 2, "code": code}])
        self.assertEqual(preview_append(original, "MANAGERDOMAIN=other.example, FR")["added_rows"], 1)

    def test_invalid_rows_fail_atomically_and_keep_existing_legacy_lines(self):
        cases = {"field_count": "example.com, x", "invalid_domain": "https://example.com, x, DIRECT",
                 "invalid_account": "example.com, two words, DIRECT", "invalid_relationship": "example.com, x, MAYBE",
                 "invalid_certification": "example.com, x, DIRECT, two words", "control_character": "# comment\x00"}
        for code, row in cases.items():
            with self.subTest(code=code), self.assertRaises(EditorError) as failure:
                self.store.append(NEW_ROW + "\n" + row, 1)
            self.assertEqual(failure.exception.fields["errors"], [{"line": 2, "code": code}])
            self.assertEqual(self.store.document()["revision"], 1)
            self.assertEqual(self.store.document()["content"].encode(), BASELINE)

    def test_append_and_rollback_are_new_immutable_revisions(self):
        second = self.store.append(NEW_ROW, 1)
        restored = self.store.rollback(1, second["revision"])
        self.assertEqual((restored["revision"], restored["parent_revision"], restored["restored_from"]), (3, 2, 1))
        self.assertEqual(restored["content"].encode(), BASELINE)
        self.assertEqual(self.store.document(2), {k: v for k, v in second.items() if k not in {"comment_lines", "blank_lines"}})
        self.assertEqual([r["revision"] for r in self.store.history()["revisions"]], [3, 2, 1])
        self.assertTrue(all("content" not in r for r in self.store.history()["revisions"]))
        with self.store.connection() as connection:
            for query in ("UPDATE revisions SET content=X'00' WHERE revision=1", "DELETE FROM revisions WHERE revision=1"):
                with self.subTest(query=query), self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(query)

    def test_persistent_history_and_session_state_survive_reopening_store(self):
        second = self.store.append(NEW_ROW, 1)
        self.assertEqual(AdsTxtStore(self.path).document(), {k: v for k, v in second.items() if k not in {"comment_lines", "blank_lines"}})

    def test_transactional_compare_and_set_under_concurrent_appends(self):
        barrier = threading.Barrier(2)
        def contender(account):
            barrier.wait(timeout=5)
            try:
                return AdsTxtStore(self.path).append(f"example.com, {account}, DIRECT", 1)["revision"]
            except EditorError as exc:
                return exc.status
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(contender, ("one", "two")))
        self.assertEqual(sorted(results), [2, 409])
        self.assertEqual(len(self.store.history()["revisions"]), 2)
        self.assertTrue(self.store.document()["content"].encode().startswith(BASELINE))

    def test_preview_stale_append_stale_rollback_and_noop_do_not_write(self):
        self.store.append(NEW_ROW, 1)
        for fn, args in ((self.store.preview, (NEW_ROW, 1)), (self.store.append, (NEW_ROW, 1)),
                         (self.store.rollback, (1, 1))):
            with self.subTest(fn=fn.__name__), self.assertRaises(EditorError) as failure:
                fn(*args)
            self.assertEqual(failure.exception.status, 409)
        preview = self.store.preview(NEW_ROW, 2)
        self.assertFalse(preview["can_apply"])
        with self.assertRaises(EditorError) as failure:
            self.store.append(NEW_ROW, 2)
        self.assertEqual(failure.exception.code, "no_changes")
        self.assertEqual(len(self.store.history()["revisions"]), 2)

    def test_seed_requires_matching_hash_and_empty_database(self):
        empty = AdsTxtStore(Path(self.temp.name) / "unseeded.sqlite3")
        with self.assertRaises(EditorError) as mismatch:
            empty.seed(BASELINE, "0" * 64)
        self.assertEqual(mismatch.exception.code, "baseline_hash_mismatch")
        with self.assertRaises(EditorError) as missing:
            empty.document()
        self.assertEqual(missing.exception.status, 503)
        with self.assertRaises(EditorError) as repeat:
            self.store.seed(BASELINE, hashlib.sha256(BASELINE).hexdigest())
        self.assertEqual(repeat.exception.code, "already_initialized")

    def test_paste_and_document_limits_are_atomic(self):
        with self.assertRaises(EditorError) as paste:
            self.store.append("#" + "x" * MAX_PASTE_BYTES, 1)
        self.assertEqual(paste.exception.status, 413)
        almost_full = b"#" + b"x" * (MAX_DOCUMENT_BYTES - 2)
        with self.assertRaises(EditorError) as full:
            preview_append(almost_full, NEW_ROW)
        self.assertEqual(full.exception.code, "document_too_large")
        self.assertEqual(self.store.document()["revision"], 1)

    def test_cli_unicode_password_confirmation_and_exclusive_output(self):
        path = Path(self.temp.name) / "password-hash"
        output = io.StringIO()
        with patch.object(sys, "argv", ["ads_txt_editor.py", "hash-password", "--output", str(path)]), \
                patch("ads_txt_editor.getpass.getpass", return_value="Prüfung-mit-Ümlaut"), contextlib.redirect_stdout(output):
            self.assertEqual(main(), 0)
        self.assertTrue(verify_password("Prüfung-mit-Ümlaut", path.read_text().strip()))
        self.assertNotIn("Prüfung", output.getvalue())
        original = path.read_bytes()
        with patch.object(sys, "argv", ["ads_txt_editor.py", "hash-password", "--output", str(path)]), \
                patch("ads_txt_editor.getpass.getpass", return_value="other-password"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 1)
        self.assertEqual(path.read_bytes(), original)

    def test_cli_seed_proves_original_bytes_and_refuses_existing_revision(self):
        baseline = Path(self.temp.name) / "original-ads.txt"
        baseline.write_bytes(BASELINE)
        target = Path(self.temp.name) / "seeded.sqlite3"
        argv = ["ads_txt_editor.py", "seed", "--baseline", str(baseline), "--db", str(target),
                "--expected-sha256", hashlib.sha256(BASELINE).hexdigest()]
        for expected in (0, 1):
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), expected)
        self.assertEqual(AdsTxtStore(target).document()["content"].encode(), BASELINE)


class EditorApiTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password(PASSWORD)

    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = [1800000000.0]
        self.store = AdsTxtStore(Path(self.temp.name) / "editor.sqlite3", clock=lambda: self.now[0])
        self.store.seed(BASELINE, hashlib.sha256(BASELINE).hexdigest())
        self.app = self.make_app()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app, client=("192.0.2.10", 1234)), base_url=ORIGIN)
        self.addAsyncCleanup(self.client.aclose)

    def make_app(self, password_hash="use-test", store=None):
        app = FastAPI()
        routers = create_ads_txt_routers(store=store or self.store,
                                        password_hash=self.password_hash if password_hash == "use-test" else password_hash)
        for router in routers:
            app.include_router(router)
        return app

    async def bootstrap(self, client=None):
        response = await (client or self.client).get("/api/ads-txt-editor/session")
        self.assertEqual(response.status_code, 200)
        return response

    async def login(self, client=None):
        client = client or self.client
        session = (await self.bootstrap(client)).json()
        response = await client.post("/api/ads-txt-editor/login", json={"password": PASSWORD},
                                     headers={"Origin": ORIGIN, "X-CSRF-Token": session["csrf_token"]})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}

    async def test_login_session_rotation_cookie_flags_hashed_storage_and_logout(self):
        before = await self.bootstrap()
        old_token = self.client.cookies.get(COOKIE_NAME)
        self.assertFalse(before.json()["authenticated"])
        headers = await self.login()
        token = self.client.cookies.get(COOKIE_NAME)
        self.assertNotEqual(token, old_token)
        cookie = before.headers["set-cookie"].lower()
        for flag in ("secure", "httponly", "samesite=strict", "path=/"):
            self.assertIn(flag, cookie)
        self.assertNotIn("domain=", cookie)
        with self.store.connection() as connection:
            rows = connection.execute("SELECT token_hash FROM sessions").fetchall()
        self.assertNotIn(token, str(rows))
        self.assertIn(hashlib.sha256(token.encode()).hexdigest(), [row[0] for row in rows])
        self.assertEqual((await self.client.get("/api/ads-txt-editor/document")).status_code, 200)
        self.assertEqual((await self.client.post("/api/ads-txt-editor/logout", json={}, headers=headers)).status_code, 200)
        self.assertEqual((await self.client.get("/api/ads-txt-editor/document")).status_code, 401)
        self.client.cookies.set(COOKIE_NAME, token, domain="transfernews.de", path="/")
        self.assertEqual((await self.client.get("/api/ads-txt-editor/document")).status_code, 401)

    async def test_login_requires_origin_and_csrf_and_wrong_password_is_generic(self):
        session = (await self.bootstrap()).json()
        for headers, error in (({}, "origin_forbidden"), ({"Origin": ORIGIN}, "csrf_failed"),
                               ({"Origin": "https://transfernews.de.evil", "X-CSRF-Token": session["csrf_token"]}, "origin_forbidden")):
            with self.subTest(error=error):
                response = await self.client.post("/api/ads-txt-editor/login", json={"password": PASSWORD}, headers=headers)
                self.assertEqual((response.status_code, response.json()["error"]), (403, error))
        response = await self.client.post("/api/ads-txt-editor/login", json={"password": "incorrect-test"},
                                         headers={"Origin": ORIGIN, "X-CSRF-Token": session["csrf_token"]})
        self.assertEqual(response.json(), {"error": "invalid_credentials"})

    async def test_all_mutations_check_csrf_and_origin(self):
        headers = await self.login()
        bodies = {"preview": {"text": NEW_ROW, "expected_revision": 1}, "append": {"text": NEW_ROW, "expected_revision": 1},
                  "rollback": {"target_revision": 1, "expected_revision": 1}, "logout": {}}
        for action, body in bodies.items():
            for invalid in ({"Origin": ORIGIN}, {**headers, "Origin": "https://other.invalid"}):
                with self.subTest(action=action, invalid=invalid):
                    response = await self.client.post("/api/ads-txt-editor/" + action, json=body, headers=invalid)
                    self.assertEqual(response.status_code, 403)
        self.assertEqual(self.store.document()["revision"], 1)

    async def test_public_exact_get_head_etag_and_missing_seed_fails_closed(self):
        for path in ("/api/ads-txt/public", "/ads.txt"):
            response = await self.client.get(path)
            self.assertEqual(response.content, BASELINE)
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(response.headers["content-type"], "text/plain; charset=utf-8")
            head = await self.client.head(path)
            self.assertEqual(head.content, b"")
            self.assertEqual(int(head.headers["content-length"]), len(BASELINE))
            self.assertEqual((await self.client.get(path, headers={"If-None-Match": response.headers["etag"]})).status_code, 304)
        empty = AdsTxtStore(Path(self.temp.name) / "missing.sqlite3")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.make_app(store=empty)), base_url=ORIGIN) as client:
            response = await client.get("/api/ads-txt/public")
            self.assertEqual((response.status_code, response.json()["error"]), (503, "not_initialized"))

    async def test_api_preview_append_history_and_rollback(self):
        headers = await self.login()
        preview = await self.client.post("/api/ads-txt-editor/preview", json={"text": NEW_ROW, "expected_revision": 1}, headers=headers)
        self.assertEqual(preview.json()["base_revision"], 1)
        self.assertEqual(self.store.document()["revision"], 1)
        applied = await self.client.post("/api/ads-txt-editor/append", json={"text": NEW_ROW, "expected_revision": 1}, headers=headers)
        self.assertEqual(applied.json()["revision"], 2)
        stale = await self.client.post("/api/ads-txt-editor/append", json={"text": NEW_ROW, "expected_revision": 1}, headers=headers)
        self.assertEqual(stale.status_code, 409)
        history = (await self.client.get("/api/ads-txt-editor/history")).json()
        self.assertEqual(len(history["revisions"]), 2)
        prior = (await self.client.get("/api/ads-txt-editor/revisions/1")).json()
        self.assertEqual(prior["content"].encode(), BASELINE)
        rollback = await self.client.post("/api/ads-txt-editor/rollback", json={"target_revision": 1, "expected_revision": 2}, headers=headers)
        self.assertEqual((rollback.status_code, rollback.json()["revision"]), (200, 3))
        self.assertEqual((await self.client.get("/api/ads-txt/public")).content, BASELINE)

    async def test_session_expires_after_eight_hours_without_sliding_renewal(self):
        await self.login()
        self.now[0] += SESSION_SECONDS - 1
        self.assertTrue((await self.bootstrap()).json()["authenticated"])
        self.now[0] += 2
        self.assertEqual((await self.client.get("/api/ads-txt-editor/document")).status_code, 401)

    async def test_rate_limit_is_persistent_ignores_forwarding_and_recovers(self):
        session = (await self.bootstrap()).json()
        headers = {"Origin": ORIGIN, "X-CSRF-Token": session["csrf_token"]}
        for count in range(8):
            result = await self.client.post("/api/ads-txt-editor/login", json={"password": "wrong"},
                                            headers={**headers, "X-Forwarded-For": f"192.0.2.{count + 20}"})
            self.assertEqual(result.status_code, 401)
        # A reconstructed store/process observes the same durable rate bucket.
        with self.assertRaises(EditorError) as limited:
            AdsTxtStore(self.store.path, clock=lambda: self.now[0]).record_login_attempt("192.0.2.10")
        self.assertEqual(limited.exception.status, 429)
        response = await self.client.post("/api/ads-txt-editor/login", json={"password": PASSWORD}, headers=headers)
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response.headers["retry-after"]), 0)
        self.now[0] += LOGIN_WINDOW + 1
        await self.login()

    async def test_missing_or_malformed_password_config_fails_closed_public_still_works(self):
        for encoded in ("", "scrypt$999999999$8$1$x$x"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.make_app(password_hash=encoded)), base_url=ORIGIN) as client:
                self.assertEqual((await client.get("/api/ads-txt-editor/session")).status_code, 503)
                self.assertEqual((await client.get("/api/ads-txt/public")).content, BASELINE)

    async def test_runtime_hash_file_precedence_and_rotation_revokes_existing_sessions(self):
        path = Path(self.temp.name) / "hash"
        path.write_text(self.password_hash, encoding="ascii")
        with patch.dict(os.environ, {"ADS_TXT_EDITOR_PASSWORD_HASH_FILE": str(path), "ADS_TXT_EDITOR_PASSWORD_HASH": "invalid-env"}):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.make_app(password_hash=None)), base_url=ORIGIN) as client:
                await self.login(client)
                path.write_text(hash_password("different-isolated-password"), encoding="ascii")
                self.assertEqual((await client.get("/api/ads-txt-editor/document")).status_code, 401)
                path.unlink()
                self.assertEqual((await client.get("/api/ads-txt-editor/session")).status_code, 503)

    async def test_stream_limit_rejects_before_json_parsing(self):
        headers = await self.login()
        async def oversized():
            yield b" " * MAX_JSON_BYTES
            yield b"x"
        with patch("ads_txt_editor.json.loads", side_effect=AssertionError("must not parse oversized JSON")):
            response = await self.client.post("/api/ads-txt-editor/append", content=oversized(),
                                             headers={**headers, "Content-Type": "application/json"})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.store.document()["revision"], 1)

    async def test_invalid_revision_and_rows_do_not_write(self):
        headers = await self.login()
        for expected in (True, -1, "1", None):
            response = await self.client.post("/api/ads-txt-editor/append", json={"text": NEW_ROW, "expected_revision": expected}, headers=headers)
            self.assertEqual(response.status_code, 422)
        response = await self.client.post("/api/ads-txt-editor/append", json={"text": NEW_ROW + "\ninvalid", "expected_revision": 1}, headers=headers)
        self.assertEqual(response.json()["errors"], [{"line": 2, "code": "field_count"}])
        self.assertEqual(self.store.document()["revision"], 1)

    def test_password_hash_helper_uses_salted_scrypt_and_constant_time_digest_check(self):
        other = hash_password(PASSWORD)
        self.assertNotEqual(other, self.password_hash)
        self.assertTrue(verify_password(PASSWORD, other))
        self.assertFalse(verify_password("incorrect", other))


if __name__ == "__main__":
    unittest.main()
