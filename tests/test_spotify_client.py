import asyncio
import os
import unittest

from song_scrounger.spotify_client import SpotifyClient
from song_scrounger.util import get_spotify_creds


class TestSpotifyClient(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        client_id, secret_key = get_spotify_creds()
        cls.spotify_client = SpotifyClient(client_id, secret_key)

    async def test_find_track_verbatim(self):
        results = await self.spotify_client.find_track("Redbone")
        inexact_matches = [
            result for result in results if result.name.lower() != "redbone"
        ]

        self.assertEqual(
            len(inexact_matches),
            0,
            f"FAIL: found {len(inexact_matches)} songs that don't match track name exactly."
        )