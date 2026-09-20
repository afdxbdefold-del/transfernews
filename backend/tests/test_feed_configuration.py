"""Offline regression tests for verified feeds, source scope and disabled status."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_import import RSSFeedScraper, import_rss_events
from pipeline_state import utcnow


class FeedConfigurationTests(unittest.IsolatedAsyncioTestCase):
    def test_source_keys_stay_stable_and_replacements_are_football_feeds(self):
        self.assertEqual(set(RSSFeedScraper.FEEDS), {
            'caughtoffside', '90min', 'footballtransfers', 'goal_com', 'sky_sports_uk',
            'bbc_football', 'teamtalk', 'marca', 'as_spain', 'mundo_deportivo',
            'gazzetta', 'corriere_sport', 'tuttosport', 'lequipe', 'rmc_sport',
            'foot_mercato', 'bild_fussball', 'kicker', 'sport1',
        })
        expected = {
            'foot_mercato': 'https://www.footmercato.net/flux-rss',
            'bild_fussball': 'https://www.bild.de/feed/sport.xml',
            'sky_sports_uk': 'https://www.skysports.com/rss/11095',
            'marca': 'https://objetos.estaticos-marca.com/rss/futbol/primera-division.xml',
            'gazzetta': 'https://www.gazzetta.it/dynamic-feed/rss/section/Calcio.xml',
        }
        for key, url in expected.items():
            self.assertEqual(RSSFeedScraper.active_feeds()[key]['url'], url)
        self.assertEqual(len(RSSFeedScraper.active_feeds()), 14)

    async def test_disabled_sources_are_never_requested(self):
        scraper = RSSFeedScraper()
        with patch('data_import.aiohttp.ClientSession', side_effect=AssertionError('Network forbidden')) as session:
            for key, metadata in scraper.DISABLED_FEEDS.items():
                self.assertTrue(metadata['reason'])
                self.assertEqual(await scraper.fetch_feed(key), [])
            session.assert_not_called()
        with patch.object(scraper, 'fetch_feed', AsyncMock(return_value=[])) as fetch:
            self.assertEqual(await scraper.fetch_all_feeds(), [])
            fetched = {call.args[0] for call in fetch.await_args_list}
        self.assertEqual(fetched, set(scraper.active_feeds()))
        self.assertTrue(fetched.isdisjoint(scraper.DISABLED_FEEDS))

    def test_bild_scope_rejects_other_sports_and_host_lookalikes(self):
        info = RSSFeedScraper.FEEDS['bild_fussball']
        self.assertTrue(RSSFeedScraper._entry_in_scope(info, 'https://www.bild.de/sport/fussball/transfer-123'))
        for url in ['https://www.bild.de/sport/mehr-sport/transfer-123',
                    'https://www.bild.de/video/football',
                    'https://www.bild.de.evil.invalid/sport/fussball/article',
                    'https://www.bild.de@evil.invalid/sport/fussball/article',
                    'https://evil.invalid/sport/fussball/article',
                    '/sport/fussball/article', 'javascript:alert(1)', None]:
            self.assertFalse(RSSFeedScraper._entry_in_scope(info, url))

    async def test_mixed_bild_feed_only_emits_football_transfer_event(self):
        urls = ['https://www.bild.de/sport/fussball/transfer-one',
                'https://www.bild.de/sport/mehr-sport/transfer-two',
                'https://www.bild.de/video/transfer-three']
        items = ''.join(f'<item><title>Spieler Transfer {i}</title><description>Verein verpflichtet Spieler</description><link>{url}</link><pubDate>Sun, 20 Sep 2026 17:00:00 +0000</pubDate></item>' for i, url in enumerate(urls))
        xml = ('<rss version="2.0"><channel><title>Mixed sport fixture</title>' + items + '</channel></rss>').encode()
        async def chunks(size):
            yield xml
        response = SimpleNamespace(status=200, content=SimpleNamespace(iter_chunked=chunks))
        class Context:
            async def __aenter__(self): return response
            async def __aexit__(self, *args): pass
        class Session:
            def __init__(self, **kwargs): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            def get(self, url, **kwargs): return Context()
        with patch('data_import.aiohttp.ClientSession', Session):
            events = await RSSFeedScraper().fetch_feed('bild_fussball')
        self.assertEqual([e['source_url'] for e in events], urls[:1])
        self.assertEqual(events[0]['source_key'], 'bild_fussball')

    async def test_import_reports_active_counts_and_preserves_existing_source_id(self):
        source = {'id': 'existing-bild-source-id', 'slug': 'bild_fussball'}
        sources = SimpleNamespace(find_one=AsyncMock(return_value=source), insert_one=AsyncMock())
        events = SimpleNamespace(find_one=AsyncMock(return_value=None), insert_one=AsyncMock())
        db = SimpleNamespace(sources=sources, events=events)
        fixture = {'headline_raw': 'Spieler Transfer', 'summary': 'Verein verpflichtet Spieler',
                   'source_key': 'bild_fussball', 'source_name': 'BILD',
                   'source_url': 'https://www.bild.de/sport/fussball/transfer-one',
                   'dedupe_key': 'fixture-key', 'source_published_at': utcnow(),
                   'language': 'de', 'category': 'tier_1'}
        with patch.object(RSSFeedScraper, 'fetch_all_feeds', AsyncMock(return_value=[fixture])):
            result = await import_rss_events(db)
        self.assertEqual(result['feeds_checked'], 14)
        self.assertEqual(set(result['disabled_feeds']), set(RSSFeedScraper.DISABLED_FEEDS))
        self.assertEqual(result['feed_errors'], {})
        self.assertEqual(result['new_events'], 1)
        sources.insert_one.assert_not_awaited()
        self.assertEqual(events.insert_one.await_args.args[0]['source_id'], source['id'])
        queried = [call.args[0]['slug'] for call in sources.find_one.await_args_list]
        self.assertTrue(set(queried).isdisjoint(RSSFeedScraper.DISABLED_FEEDS))


if __name__ == '__main__':
    unittest.main()
