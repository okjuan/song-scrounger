import asyncio
import os
import unittest

from unittest.mock import AsyncMock, MagicMock, patch

from song_scrounger.models.song import Song
from song_scrounger.models.album import Album
from tests.helper import (
    mock_spotify_track_factory,
    mock_spotify_artist_factory,
    mock_spotify_album_factory,
    get_num_times_called
)
from song_scrounger.spotify_client import SpotifyClient
from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token


class TestSpotifyClient(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # TODO: catch exceptions when loading creds fails
        # TODO: selectively skip tests that require a bearer token
        cls.client_id, cls.secret_key = get_spotify_creds()
        cls.bearer_token = get_spotify_bearer_token()

    async def asyncSetUp(self):
        self.spotify_client = SpotifyClient(
            self.client_id, self.secret_key, self.bearer_token)

    def _get_inner_client(self, client_ctor):
        return client_ctor.return_value.__aenter__.return_value

    @patch("song_scrounger.spotify_client.Client")
    async def test_find_songs__two_songs(self, mock_inner_client_ctor):
        song = "Sorry"
        mock_spotify_tracks = [
            mock_spotify_track_factory(
                "Sorry",
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                [mock_spotify_artist_factory("Justin Bieber")],
                popularity=1
            ),
            mock_spotify_track_factory(
                "Sorry",
                "spotify:track:6rAXHPd18PZ6W8m9EectzH",
                [mock_spotify_artist_factory("Nothing But Thieves")],
                popularity=2
            ),
        ]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.search = AsyncMock(return_value=MagicMock(tracks=mock_spotify_tracks))

        songs = await self.spotify_client.find_song(song)

        inner_cli.search.assert_called_once_with("Sorry", types=["track"])
        self.assertEqual(len(songs), 2)
        songs_list = list(songs)
        self.assertEqual(songs_list[0].name, "Sorry")
        self.assertEqual(songs_list[1].name, "Sorry")
        self.assertIn(songs_list[0].spotify_uri,
            ["spotify:track:09CtPGIpYB4BrO8qb1RGsF", "spotify:track:6rAXHPd18PZ6W8m9EectzH"])
        self.assertIn(
            songs_list[1].spotify_uri,
            ["spotify:track:09CtPGIpYB4BrO8qb1RGsF", "spotify:track:6rAXHPd18PZ6W8m9EectzH"])
        self.assertIn(
            songs_list[0].artists[0],
            ["Justin Bieber", "Nothing But Thieves"])
        self.assertIn(
            songs_list[1].artists[0],
            ["Justin Bieber", "Nothing But Thieves"])
        self.assertIn(songs_list[0].popularity, [1,2])
        self.assertIn(songs_list[1].popularity, [1,2])

    @patch("song_scrounger.spotify_client.Client")
    async def test_find_songs__multiple_artists(self, mock_inner_client_ctor):
        song = "bad guy"
        mock_spotify_tracks = [
            mock_spotify_track_factory(
                name="bad guy",
                artists=[
                    mock_spotify_artist_factory(name="Billie Eilish"),
                    mock_spotify_artist_factory(name="Finneas O'Connell")
                ],
                uri="spotify:track:2Fxmhks0bxGSBdJ92vM42m",
                popularity=None
            ),
        ]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.search = AsyncMock(return_value=MagicMock(tracks=mock_spotify_tracks))

        songs = await self.spotify_client.find_song(song)

        inner_cli.search.assert_called_once_with("bad guy", types=["track"])
        self.assertEqual(len(songs), 1)
        songs_list = list(songs)
        self.assertEqual(songs_list[0].name, "bad guy")
        self.assertEqual(songs_list[0].spotify_uri, "spotify:track:2Fxmhks0bxGSBdJ92vM42m")
        self.assertEqual(songs_list[0].artists, ["Billie Eilish", "Finneas O'Connell"])

    @patch("song_scrounger.spotify_client.Client")
    async def test_find_song__exact_match(self, mock_inner_client_ctor):
        track = "Mock Track"
        mock_spotify_tracks = [mock_spotify_track_factory(
            "Mock Track",
            "Mock URI",
            [mock_spotify_artist_factory("Mock Artist")],
            popularity=None
        )]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.search = AsyncMock(return_value=MagicMock(tracks=mock_spotify_tracks))
        def _strip_song_metadata(track_name):
            return track_name
        self.spotify_client._strip_song_metadata = MagicMock(
            side_effect=_strip_song_metadata)

        results = list(await self.spotify_client.find_song(track))

        self.assertEqual(get_num_times_called(mock_inner_client_ctor), 1)
        inner_cli.search.assert_called_once_with("Mock Track", types=["track"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Mock Track")
        self.assertEqual(results[0].spotify_uri, "Mock URI")
        self.assertEqual(len(results[0].artists), 1)
        self.assertEqual(results[0].artists[0], "Mock Artist")

    @patch("song_scrounger.spotify_client.Client")
    async def test_find_song__ignores_partial_matches(self, mock_inner_client_ctor):
        track = "Mock Track"
        mock_spotify_tracks = [mock_spotify_track_factory(
            "Mock Track Partial Match",
            "Mock URI",
            [mock_spotify_artist_factory("Mock Artist")],
            popularity=None
        )]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.search = AsyncMock(return_value=MagicMock(tracks=mock_spotify_tracks))
        def _strip_song_metadata(track_name):
            return track_name
        self.spotify_client._strip_song_metadata = MagicMock(
            side_effect=_strip_song_metadata)

        results = list(await self.spotify_client.find_song(track))

        self.assertEqual(get_num_times_called(mock_inner_client_ctor), 1)
        inner_cli.search.assert_called_once_with("Mock Track", types=["track"])
        self.assertEqual(len(results), 0)

    @patch("song_scrounger.spotify_client.Client")
    async def test_find_song__exact_and_partial_matches__keeps_exact_match_and_skips_partial_match(
        self, mock_inner_client_ctor
    ):
        track = "Mock Track Exact Match"
        mock_spotify_tracks = [
            mock_spotify_track_factory(
                "Mock Track Exact Match",
                "Mock URI",
                [mock_spotify_artist_factory("Mock Artist")],
                popularity=None
            ),
            mock_spotify_track_factory(
                "Mock Track Partial Match",
                "Mock URI",
                [mock_spotify_artist_factory("Mock Artist")],
                popularity=None
            )
        ]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.search = AsyncMock(return_value=MagicMock(tracks=mock_spotify_tracks))
        def _strip_song_metadata(track_name):
            return track_name
        self.spotify_client._strip_song_metadata = MagicMock(
            side_effect=_strip_song_metadata)

        results = list(await self.spotify_client.find_song(track))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Mock Track Exact Match")
        self.assertEqual(results[0].spotify_uri, "Mock URI")
        self.assertEqual(len(results[0].artists), 1)
        self.assertEqual(results[0].artists[0], "Mock Artist")

    @patch("song_scrounger.spotify_client.Client")
    async def test_find_albums(self, mock_inner_client_ctor):
        album = "Sweetener"
        mock_spotify_albums = [
            mock_spotify_album_factory(
                "Sweetener",
                "spotify:album:3tx8gQqWbGwqIGZHqDNrGe",
                [mock_spotify_artist_factory("Ariana Grande")],
                popularity=1
            )
        ]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.get_albums = AsyncMock(return_value=mock_spotify_albums)

        albums = list(await self.spotify_client.find_album(album))

        inner_cli.search.assert_called_once_with("Sweetener", types=["album"])
        self.assertEqual(len(albums), 1)
        albums_list = list(albums)
        self.assertEqual(albums_list[0].name, "Sweetener")
        self.assertIn(albums_list[0].spotify_uri, "spotify:album:3tx8gQqWbGwqIGZHqDNrGe")
        self.assertEqual(albums_list[0].popularity, 1)

    async def test_find_song__empty_track_name__raises_value_error(self):
        track = ""

        with self.assertRaises(ValueError):
            results = await self.spotify_client.find_song(track)

    async def test_strip_song_metadata__name_contains_metadata__removes_metadata(self):
        track_name = "Satisfaction - Mono Version"

        cleaned_track_name = self.spotify_client._strip_song_metadata(track_name)

        self.assertEqual(cleaned_track_name, "Satisfaction")

    async def test_strip_song_metadata__name_contains_parentheses_at_beginning__does_not_edit(self):
        track_name = "(I Can't Get No) Satisfaction"

        cleaned_track_name = self.spotify_client._strip_song_metadata(track_name)

        self.assertEqual(cleaned_track_name, "(I Can't Get No) Satisfaction")

    async def test_strip_song_metadata__strips_whitespace(self):
        track_name = "   Satisfaction "

        cleaned_track_name = self.spotify_client._strip_song_metadata(track_name)

        self.assertEqual(cleaned_track_name, "Satisfaction")

    async def test_strip_album_metadata__name_contains_parentheses_at_end__removes_paren(self):
        track_name = "Revolver (Remastered)"

        cleaned_track_name = self.spotify_client._strip_album_metadata(track_name)

        self.assertEqual(cleaned_track_name, "Revolver")

    async def test_strip_album_metadata__strips_whitespace(self):
        track_name = "   Satisfaction "

        cleaned_track_name = self.spotify_client._strip_album_metadata(track_name)

        self.assertEqual(cleaned_track_name, "Satisfaction")

    @unittest.skip("Integration tests disabled by default.")
    async def test_create_playlist(self):
        name = f"DELETE ME: test_create_playlist in song_scrounger"
        spotify_uris = [
            "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            "spotify:track:6rAXHPd18PZ6W8m9EectzH"
        ]

        playlist = await self.spotify_client.create_playlist(name, spotify_uris)

        self.assertIsNotNone(playlist, "Playlist creation failed: received 'None' as result")
        # TODO: verify with call to spotify
        self.assertTrue(False, "Go check that a playlist w/ 2 songs called 'Sorry' was created w name: 'DELETE ME: test_create_playlist in song_scrounger'")

    @unittest.skip("Integration tests disabled by default.")
    async def test_create_empty_playlist(self):
        name = f"DELETE ME: test_create_empty_playlist in song_scrounger"

        playlist = await self.spotify_client.create_empty_playlist(name)

        self.assertIsNotNone(playlist, "Playlist creation failed: received 'None' as result")
        # TODO: verify with call to spotify
        self.assertTrue(False, "Go check that an empty playlist was created w name: 'DELETE ME: test_create_empty_playlist in song_scrounger'")

    @unittest.skip("Integration tests disabled by default.")
    async def test_add_tracks(self):
        # Named 'Song Scrounger Test Playlist' on Spotify
        playlist_id = "spotify:playlist:1mWKdYnyaejjLrdK7pBg2K"

        # Spotify Track URI for 'Redbone' by Childish Gambino
        await self.spotify_client.add_tracks(
            playlist_id,
            [
                "spotify:track:0wXuerDYiBnERgIpbb3JBR",
                "spotify:track:0wXuerDYiBnERgIpbb3JBR",
                "spotify:track:0wXuerDYiBnERgIpbb3JBR"
            ])

        # TODO: verify with call to spotify
        self.assertTrue(False, "Go check that 'Redbone' x3 (three times) was added to 'Song Scrounger Test Playlist'.")

    @unittest.skip("Integration tests disabled by default.")
    async def test_find_song(self):
        results = list(await self.spotify_client.find_song("Redbone"))

        self.assertLessEqual(1, len(results))
        found_childish_gambino_song = TestSpotifyClientHelper.is_one_of_the_artists(
            results, "Childish Gambino")
        self.assertTrue(found_childish_gambino_song, "Expected to find 'Sweetener' by Ariana Grande")

    @unittest.skip("Integration tests disabled by default.")
    async def test_find_album(self):
        results = await self.spotify_client.find_album("Sweetener")

        self.assertLessEqual(1, len(results))
        self.assertIsNotNone(list(results)[0].popularity)
        found_ariana_grande_album = TestSpotifyClientHelper.is_one_of_the_artists(
            results, "Ariana Grande")
        self.assertTrue(found_ariana_grande_album, "Expected to find 'Sweetener' by Ariana Grande")

class TestSpotifyClientHelper():
    @classmethod
    def is_one_of_the_artists(cls, songs_or_albums, artist_name):
        for album in songs_or_albums:
            if artist_name in [artist for artist in album.artists]:
                return True
        return False