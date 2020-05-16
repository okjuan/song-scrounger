import asyncio
import os
import random
import unittest

from song_scrounger.song_scrounger import SongScrounger
from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token


class TestSongScrounger(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        client_id, secret_key = get_spotify_creds()
        bearer_token = get_spotify_bearer_token()
        cls.song_scrounger = SongScrounger(client_id, secret_key, bearer_token)

    @classmethod
    def _get_path_to_test_input_file(cls, name):
        # Relative from repo root
        return os.path.abspath(f"tests/test_inputs/{name}")

    async def test_create_playlist(self):
        name = f"Song Scrounger {random.randint(0,10000)}"
        playlist = await self.song_scrounger.create_playlist(
            TestSongScrounger._get_path_to_test_input_file("test_mini.txt"), name)

        # TODO: use spotify_client to check if new playlist exists
        pass

    async def test_get_tracks(self):
        song_name = "Redbone"
        tracks = await self.song_scrounger._get_tracks([song_name])

        self.assertGreater(
            len(tracks),
            0,
            f"Did not find any results for song '{song_name}'.",
        )