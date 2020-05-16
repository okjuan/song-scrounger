import asyncio
import os
import random
import unittest

from song_scrounger.spotify_client import SpotifyClient
from song_scrounger.util import get_spotify_creds


@unittest.skip("Skipping integration tests by default.")
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

    async def test_create_playlist(self):
        name = f"created by test_create_playlist in song_scrounger {random.randint(0,10000)}"
        playlist = await self.spotify_client.create_playlist(name)
        self.assertIsNotNone(playlist, "Playlist creation failed: received 'None' as result")