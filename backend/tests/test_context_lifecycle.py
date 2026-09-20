"""Offline browser lifecycle regressions; no browser launch or external requests."""
import asyncio
from pathlib import Path
import socket
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from context_scraper import TransfermarktScraper


class ContextLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.page = types.SimpleNamespace(
            goto=AsyncMock(), wait_for_timeout=AsyncMock(), close=AsyncMock(),
            query_selector=AsyncMock(return_value=None), query_selector_all=AsyncMock(return_value=[]))
        self.scraper = TransfermarktScraper()
        self.scraper._get_browser = AsyncMock(return_value=types.SimpleNamespace(new_page=AsyncMock(return_value=self.page)))
        delay = patch("context_scraper.random_delay", AsyncMock())
        delay.start()
        self.addCleanup(delay.stop)
        network = patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited"))
        network.start()
        self.addCleanup(network.stop)

    async def test_missing_market_value_does_not_break_birth_date_parsing(self):
        link = types.SimpleNamespace(get_attribute=AsyncMock(return_value="/fixture/profil/spieler/1"))
        self.page.query_selector.side_effect = [link, None, None]
        self.page.query_selector_all.side_effect = [
            [types.SimpleNamespace(text_content=AsyncMock(return_value="01.01.2000 (26)"))],
            [types.SimpleNamespace(text_content=AsyncMock(return_value="Geburtsdatum"))],
        ]
        result = await self.scraper.get_player("Fixture Player")
        self.assertTrue(result.found)
        self.assertEqual(result.age, 26)
        self.assertEqual(result.birth_year, 2000)
        self.assertFalse(result.market_value)
        self.page.close.assert_awaited_once()

    async def test_navigation_timeout_closes_page(self):
        self.page.goto.side_effect = TimeoutError("Synthetic timeout")
        result = await self.scraper.get_player("Fixture Player")
        self.assertFalse(result.found)
        self.page.close.assert_awaited_once()

    async def test_cancelled_context_lookup_closes_page_and_propagates_cancellation(self):
        entered = asyncio.Event()
        async def navigation(*args, **kwargs):
            entered.set()
            await asyncio.Event().wait()
        self.page.goto.side_effect = navigation
        task = asyncio.create_task(self.scraper.get_player("Fixture Player"))
        await asyncio.wait_for(entered.wait(), timeout=1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.page.close.assert_awaited_once()
        self.assertNotIn("tm:Fixture Player", self.scraper.cache)

    async def test_missing_profile_closes_page_once(self):
        result = await self.scraper.get_player("Fixture Player")
        self.assertFalse(result.found)
        self.page.close.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
