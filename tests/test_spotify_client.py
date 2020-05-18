import asyncio
import os
import random
import unittest

from song_scrounger.spotify_client import SpotifyClient
from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token


@unittest.skip("Skipping integration tests by default.")
class TestSpotifyClient(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # TODO: catch exceptions when loading creds fails
        # TODO: selectively skip tests that require a bearer token
        client_id, secret_key = get_spotify_creds()
        bearer_token = get_spotify_bearer_token()
        cls.spotify_client = SpotifyClient(client_id, secret_key, bearer_token)

    async def test_find_track_verbatim(self):
        track = "Redbone"

        results = await self.spotify_client.find_track()

        self.assertGreater(len(results), 0, "Expected to find at least one match.")
        inexact_matches = [ result for result in results if result.name.lower() != "redbone" ]
        self.assertEqual(
            len(inexact_matches),
            0,
            f"FAIL: found {len(inexact_matches)} songs that don't match track name exactly."
        )

    async def test_create_playlist(self):
        name = f"DELETE ME: created by test_create_playlist in song_scrounger {random.randint(0,10000)}"

        playlist = await self.spotify_client.create_playlist(name)

        self.assertIsNotNone(playlist, "Playlist creation failed: received 'None' as result")

    async def test_add_tracks(self):
        # Named 'Song Scrounger Test Playlist' on Spotify
        playlist_id = "spotify:playlist:1mWKdYnyaejjLrdK7pBg2K"

        # Spotify Track URI for 'Redbone' by Childish Gambino
        await self.spotify_client.add_tracks(playlist_id, ["spotify:track:0wXuerDYiBnERgIpbb3JBR"])

        # NOTE: must go check Spotify playlist to make sure song was added
        # TODO: replace manual check