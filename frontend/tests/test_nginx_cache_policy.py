"""Route-level regression checks for HTML revalidation and cache boundaries."""
from pathlib import Path
import re
import unittest


CONFIG = (Path(__file__).resolve().parents[1] / "nginx.conf").read_text()


def locations():
    # Read complete location blocks, including the editor's nested host guard.
    result = []
    for match in re.finditer(r"\blocation\s+(?:(=|~)\s+)?([^\s{]+)\s*\{", CONFIG):
        depth, cursor = 1, match.end()
        while depth:
            depth += (CONFIG[cursor] == "{") - (CONFIG[cursor] == "}")
            cursor += 1
        result.append((match[1], match[2], CONFIG[match.end():cursor - 1]))
    return result


def location_for(path):
    """Exact, ordered regex, then longest-prefix selection used by this config."""
    blocks = locations()
    exact = [body for kind, pattern, body in blocks if kind == "=" and path == pattern]
    if exact:
        return exact[0]
    for kind, pattern, body in blocks:
        if kind == "~" and re.search(pattern, path):
            return body
    return max(((pattern, body) for kind, pattern, body in blocks if kind is None and path.startswith(pattern)), key=lambda item: len(item[0]))[1]


class HtmlCachePolicyTests(unittest.TestCase):
    def test_html_routes_revalidate_including_trailing_slash_and_admin(self):
        paths = ["/", "/index.html"]
        for path in ["news", "ticker", "top-deals", "abloesefrei", "deadline-day", "geruechte", "transfers", "suche", "redaktion", "impressum", "ueber-uns", "datenschutz", "admin", "admin/login", "admin/articles", "admin/ad-slots"]:
            paths.extend([f"/{path}", f"/{path}/"])
        for path in paths:
            with self.subTest(path=path):
                self.assertIn('add_header Cache-Control "no-cache, must-revalidate" always;', location_for(path))

    def test_error_html_uses_same_revalidation_policy(self):
        self.assertIn("error_page 404 /index.html;", CONFIG)
        self.assertIn("try_files $uri =404;", location_for("/not-a-route"))
        self.assertIn('Cache-Control "no-cache, must-revalidate" always;', location_for("/index.html"))

    def test_editor_retains_no_store_and_security_headers(self):
        for path in ["/ads-txt-editor", "/ads-txt-editor/"]:
            with self.subTest(path=path):
                body = location_for(path)
                self.assertIn('Cache-Control "no-store" always;', body)
                self.assertNotIn("must-revalidate", body)
                for header in ["X-Robots-Tag", "X-Frame-Options", "Referrer-Policy", "Content-Security-Policy"]:
                    self.assertIn(f"add_header {header} ", body)

    def test_immutable_hashed_assets_preserved(self):
        for path in ["/static/js/main.935aea14.js", "/static/css/main.db4321ee.css"]:
            with self.subTest(path=path):
                body = location_for(path)
                self.assertIn("expires 1y;", body)
                self.assertIn('Cache-Control "public, immutable";', body)
                self.assertNotIn("must-revalidate", body)

    def test_backend_controlled_responses_keep_their_own_policy(self):
        for path in ["/news/fresh-story", "/spieler/player", "/verein/club", "/thema/topic", "/autor/editor", "/wettbewerb/league", "/api/ready", "/ads.txt", "/sitemap.xml"]:
            with self.subTest(path=path):
                body = location_for(path)
                self.assertIn("proxy_pass ", body)
                self.assertNotIn("add_header Cache-Control", body)
                self.assertNotIn("proxy_hide_header Cache-Control", body)


if __name__ == "__main__":
    unittest.main()
