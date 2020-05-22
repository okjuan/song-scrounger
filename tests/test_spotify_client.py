import asyncio
import os
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

    async def test_find_track__exact_match(self):
        track = "Redbone"

        results = await self.spotify_client.find_track(track)

        self.assertGreater(len(results), 0, "Expected to find at least one match.")
        for result in results:
            self.assertEqual(
                result.name.lower(),
                "redbone",
                "At least one result does not match song name exactly."
            )

    async def test_find_track__empty_track_name__raises_value_error(self):
        track = ""

        with self.assertRaises(ValueError):
            results = await self.spotify_client.find_track(track)

    async def test_find_track__when_no_exact_match__returns_empty(self):
        track = "nofasdflkdnfasfdbaskdfjabsdfjlkasfd"

        results = await self.spotify_client.find_track(track)

        self.assertEqual([], results, "Should not find any results")

    async def test_create_playlist(self):
        name = f"DELETE ME: test_create_playlist in song_scrounger"
        spotify_uris = [
            "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            "spotify:track:6rAXHPd18PZ6W8m9EectzH"
        ]

        playlist = await self.spotify_client.create_playlist(name, spotify_uris)

        self.assertIsNotNone(playlist, "Playlist creation failed: received 'None' as result")

    async def test_create_empty_playlist(self):
        name = f"DELETE ME: test_create_empty_playlist in song_scrounger"

        playlist = await self.spotify_client.create_empty_playlist(name)

        self.assertIsNotNone(playlist, "Playlist creation failed: received 'None' as result")

    async def test_add_tracks(self):
        # Named 'Song Scrounger Test Playlist' on Spotify
        playlist_id = "spotify:playlist:1mWKdYnyaejjLrdK7pBg2K"

        # Spotify Track URI for 'Redbone' by Childish Gambino
        await self.spotify_client.add_tracks(playlist_id, ["spotify:track:0wXuerDYiBnERgIpbb3JBR"])

        # NOTE: must go check Spotify playlist to make sure song was added
        # TODO: replace manual check