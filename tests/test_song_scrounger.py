import asyncio
import os
import random
import unittest

from unittest.mock import AsyncMock, MagicMock, patch

from song_scrounger.song_scrounger import SongScrounger


class TestSongScrounger(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_spotify_client = AsyncMock()
        self.song_scrounger = SongScrounger(self.mock_spotify_client)

    async def test_create_playlist(self):
        # TODO: set up mocks to return based on what they are called with
        # e.g. create_playlist to return whatever playlist it is initially given

        self.mock_spotify_client.configure_mock(**{
            "create_playlist.return_value": "Mock Playlist Name"
        })
        self.mock_spotify_client.configure_mock(**{
            "add_tracks.return_value": "Mock Playlist Name"
        })
        self.song_scrounger._get_tracks = AsyncMock(return_value=["Mock Spotify Track"])

        playlist = await self.song_scrounger.create_playlist("Mock Playlist Name", ["mock track"])

        self.mock_spotify_client.create_playlist.assert_called_once_with("Mock Playlist Name")
        self.mock_spotify_client.add_tracks.assert_called_once_with("Mock Playlist Name", ["Mock Spotify Track"])

    async def test_find_tracks(self):
        self.mock_spotify_client.configure_mock(**{
            "find_track.return_value": ["Mock Spotify Track"]
        })

        playlist = await self.song_scrounger._get_tracks(["mock track"])

        self.mock_spotify_client.find_track.assert_called_once_with("mock track")

    async def test_get_tracks__single_track(self):
        mock_spotify_track = MagicMock(name="Mock Spotify Track")
        self.mock_spotify_client.configure_mock(**{
            "find_track.return_value": [mock_spotify_track]
        })
        mock_song = ["Mock Song"]

        tracks = await self.song_scrounger._get_tracks(mock_song)

        self.mock_spotify_client.find_track.assert_called_once_with("Mock Song")
        self.assertEqual(len(tracks), 1, "Expected exactly 1 result.")

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="Once \"Redbone\", twice \"Redbone\"")
    async def test_parse_tracks__no_dups(self, mock_read_file_contents):
        tracks = self.song_scrounger.parse_tracks("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.assertEqual(list(tracks), ["Redbone"], "Expected only one result")

    async def test_get_tracks__multiple_tracks(self):
        mock_spotify_track = MagicMock(name="Mock Spotify Track")
        self.mock_spotify_client.configure_mock(**{
            "find_track.return_value": [mock_spotify_track]
        })
        mock_tracks = ["Mock Song 1", "Mock Song 2", "Mock Song 3"]

        tracks = await self.song_scrounger._get_tracks(mock_tracks)

        self.mock_spotify_client.find_track.assert_any_call("Mock Song 1")
        self.mock_spotify_client.find_track.assert_any_call("Mock Song 2")
        self.mock_spotify_client.find_track.assert_any_call("Mock Song 3")
        self.assertEqual(len(tracks), 3, "Expected exactly 3 results.")

    @unittest.skip("Skip integration tests by default")
    async def test_end_to_end__for_duplicate_songs(self):
        input_file_name = "test_duplicate_songs.txt"
        playlist_name = "Duplicate Song Test: should contain 4 songs (DELETE ME)"
        await self._run_integration_test(input_file_name, playlist_name)

    @unittest.skip("Skip integration tests by default")
    async def test_end_to_end__for_artist_detection(self):
        input_file_name = "test_artist_detection.txt"
        playlist_name = "Artist Detection Song: JB, Bey, and Kiefer (DELETE ME)"
        await self._run_integration_test(input_file_name, playlist_name)

    async def _run_integration_test(self, input_file_name, playlist_name):
        from song_scrounger.spotify_client import SpotifyClient
        from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token
        from tests import helper

        spotify_client_id, spotify_secret_key = get_spotify_creds()
        spotify_bearer_token = get_spotify_bearer_token()
        spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key, spotify_bearer_token)

        song_scrounger = SongScrounger(spotify_client)
        input_file_path = helper.get_path_to_test_input_file(input_file_name)
        tracks = song_scrounger.parse_tracks(input_file_path)

        await song_scrounger.create_playlist(playlist_name, tracks)
