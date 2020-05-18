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

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="Mock corpus with \"Mock Track Name\"")
    @patch("song_scrounger.song_scrounger.find_quoted_tokens", return_value=["mock token"])
    async def test_create_playlist(self, mock_find_quoted_tokens, mock_read_file_contents):
        mock_spotify_track = MagicMock(name="Mock Spotify Track")
        self.mock_spotify_client.configure_mock(**{
            "find_track.return_value": [mock_spotify_track]
        })

        mock_spotify_playlist = MagicMock(name="Mock Spotify Playlist")
        self.mock_spotify_client.configure_mock(**{
            "create_playlist.return_value": mock_spotify_playlist
        })

        self.mock_spotify_client.configure_mock(**{
            "add_tracks.return_value": mock_spotify_playlist
        })

        playlist = await self.song_scrounger.create_playlist("mock file path", "Mock Playlist Name")

        mock_read_file_contents.assert_called_once_with("mock file path")
        mock_find_quoted_tokens.assert_called_once_with("Mock corpus with \"Mock Track Name\"")

    async def test_get_tracks__single_track(self):
        mock_spotify_track = MagicMock(name="Mock Spotify Track")
        self.mock_spotify_client.configure_mock(**{
            "find_track.return_value": [mock_spotify_track]
        })
        tracks = await self.song_scrounger._get_tracks(["Mock Song"])

        self.mock_spotify_client.find_track.assert_called_once_with("Mock Song")
        self.assertEqual(len(tracks), 1, "Expected exactly 1 result.")

    async def test_parse_tracks__no_dups(self):
        tracks = self.song_scrounger.parse_tracks("Once \"Redbone\", twice \"Redbone\"")

        self.assertEqual(list(tracks), ["Redbone"], "Expected only one result")

    async def test_get_tracks__multiple_tracks(self):
        mock_spotify_track = MagicMock(name="Mock Spotify Track")
        self.mock_spotify_client.configure_mock(**{
            "find_track.return_value": [mock_spotify_track]
        })
        tracks = await self.song_scrounger._get_tracks(["Mock Song 1", "Mock Song 2", "Mock Song 3"])

        self.mock_spotify_client.find_track.assert_any_call("Mock Song 1")
        self.mock_spotify_client.find_track.assert_any_call("Mock Song 2")
        self.mock_spotify_client.find_track.assert_any_call("Mock Song 3")
        self.assertEqual(len(tracks), 3, "Expected exactly 3 results.")