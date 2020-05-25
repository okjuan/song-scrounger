import asyncio
import os
import unittest

from unittest.mock import AsyncMock, MagicMock, patch

from tests.helper import mock_spotify_track_factory, mock_spotify_artist_factory, get_num_times_called
from song_scrounger.spotify_client import SpotifyClient
from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token


class TestSpotifyClient(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # TODO: catch exceptions when loading creds fails
        # TODO: selectively skip tests that require a bearer token
        client_id, secret_key = get_spotify_creds()
        bearer_token = get_spotify_bearer_token()
        cls.spotify_client = SpotifyClient(client_id, secret_key, bearer_token)

    def _get_inner_client(self, client_ctor):
        return client_ctor.return_value.__aenter__.return_value

    @patch("song_scrounger.spotify_client.Client")
    async def test_find_track__exact_match(self, mock_inner_client_ctor):
        track = "Mock Track"
        mock_spotify_tracks = [mock_spotify_track_factory(
            "Mock Track",
            "Mock URI",
            [mock_spotify_artist_factory("Mock Artist")]
        )]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.search = AsyncMock(return_value=MagicMock(tracks=mock_spotify_tracks))

        results = await self.spotify_client.find_track(track)

        self.assertEqual(get_num_times_called(mock_inner_client_ctor), 1)
        inner_cli.search.assert_called_once_with("Mock Track", types=["track"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Mock Track")
        self.assertEqual(results[0].uri, "Mock URI")
        self.assertEqual(len(results[0].artists), 1)
        self.assertEqual(results[0].artists[0].name, "Mock Artist")

    @patch("song_scrounger.spotify_client.Client")
    async def test_find_track__ignores_partial_matches(self, mock_inner_client_ctor):
        track = "Mock Track"
        mock_spotify_tracks = [mock_spotify_track_factory(
            "Mock Track Partial Match",
            "Mock URI",
            [mock_spotify_artist_factory("Mock Artist")]
        )]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.search = AsyncMock(return_value=MagicMock(tracks=mock_spotify_tracks))

        results = await self.spotify_client.find_track(track)

        self.assertEqual(get_num_times_called(mock_inner_client_ctor), 1)
        inner_cli.search.assert_called_once_with("Mock Track", types=["track"])
        self.assertEqual(len(results), 0)

    @patch("song_scrounger.spotify_client.Client")
    async def test_find_track__exact_and_partial_matches__keeps_exact_match_and_skips_partial_match(
        self, mock_inner_client_ctor
    ):
        track = "Mock Track Exact Match"
        mock_spotify_tracks = [
            mock_spotify_track_factory(
                "Mock Track Exact Match",
                "Mock URI",
                [mock_spotify_artist_factory("Mock Artist")]
            ),
            mock_spotify_track_factory(
                "Mock Track Partial Match",
                "Mock URI",
                [mock_spotify_artist_factory("Mock Artist")]
            )
        ]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.search = AsyncMock(return_value=MagicMock(tracks=mock_spotify_tracks))

        results = await self.spotify_client.find_track(track)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Mock Track Exact Match")
        self.assertEqual(results[0].uri, "Mock URI")
        self.assertEqual(len(results[0].artists), 1)
        self.assertEqual(results[0].artists[0].name, "Mock Artist")

    async def test_find_track__empty_track_name__raises_value_error(self):
        track = ""

        with self.assertRaises(ValueError):
            results = await self.spotify_client.find_track(track)

    @unittest.skip("Integration tests disabled by default.")
    async def test_create_playlist(self):
        name = f"DELETE ME: test_create_playlist in song_scrounger"
        spotify_uris = [
            "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            "spotify:track:6rAXHPd18PZ6W8m9EectzH"
        ]

        playlist = await self.spotify_client.create_playlist(name, spotify_uris)

        self.assertIsNotNone(playlist, "Playlist creation failed: received 'None' as result")

    @unittest.skip("Integration tests disabled by default.")
    async def test_create_empty_playlist(self):
        name = f"DELETE ME: test_create_empty_playlist in song_scrounger"

        playlist = await self.spotify_client.create_empty_playlist(name)

        self.assertIsNotNone(playlist, "Playlist creation failed: received 'None' as result")

    @unittest.skip("Integration tests disabled by default.")
    async def test_add_tracks(self):
        # Named 'Song Scrounger Test Playlist' on Spotify
        playlist_id = "spotify:playlist:1mWKdYnyaejjLrdK7pBg2K"

        # Spotify Track URI for 'Redbone' by Childish Gambino
        await self.spotify_client.add_tracks(playlist_id, ["spotify:track:0wXuerDYiBnERgIpbb3JBR"])

        # NOTE: must go check Spotify playlist to make sure song was added
        # TODO: replace manual check