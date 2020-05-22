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
        self.song_scrounger.document_parser = AsyncMock()
        self.mock_document_parser = self.song_scrounger.document_parser

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="\"Redbone\" by Childish Gambino")
    async def test_find_songs(self, mock_read_file_contents):
        self.mock_document_parser.find_songs = AsyncMock(
            return_value = {"Redbone": ["spotify:track:0wXuerDYiBnERgIpbb3JBR"]}
        )

        results = await self.song_scrounger.find_songs("mock file path")

        self.mock_document_parser.find_songs.assert_called_once_with(
            "\"Redbone\" by Childish Gambino"
        )
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Redbone" in results)
        self.assertEqual(results["Redbone"], ["spotify:track:0wXuerDYiBnERgIpbb3JBR"])

    @unittest.skip("Skip integration tests by default")
    async def test_end_to_end__for_duplicate_songs(self):
        input_file_name = "test_duplicate_songs.txt"
        playlist_name = "Duplicate Song Test: should not repeat any artist"
        await self._run_integration_test(input_file_name, playlist_name)

    @unittest.skip("Skip integration tests by default")
    async def test_end_to_end__simple_artist_detection(self):
        input_file_name = "test_simple_artist_detection.txt"
        playlist_name = "Simple Artist Detection Song: Nothing But Thieves"
        await self._run_integration_test(input_file_name, playlist_name)

    @unittest.skip("Skip integration tests by default")
    async def test_end_to_end__multi_paragraph_artist_detection(self):
        input_file_name = "test_multiparagraph_artist_detection.txt"
        playlist_name = "Multi-Paragraph Artist Detection Song: JB and Nothing But Thieves"
        await self._run_integration_test(input_file_name, playlist_name)
        "test_multiparagraph_artist_detection.txt"

    @unittest.skip("Disabled until implemented")
    async def test_end_to_end__cross_paragraph_artist_detection(self):
        input_file_name = "test_cross_paragraph_artist_detection.txt"
        playlist_name = "Cross-Paragraph Artist Detection Song: Kiefer"
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
        songs = await song_scrounger.find_songs(input_file_path)

        all_matching_spotify_uris = []
        for _, spotify_uris in songs.items():
            all_matching_spotify_uris.extend(list(spotify_uris))
        await spotify_client.create_playlist(playlist_name, all_matching_spotify_uris)
