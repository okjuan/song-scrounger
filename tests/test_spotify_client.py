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
    async def test_find_song__two_songs(self, mock_inner_client_ctor):
        song = "Sorry"
        mock_spotify_tracks = [
            mock_spotify_track_factory(
                "Sorry",
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                [mock_spotify_artist_factory("Justin Bieber")],
                popularity=1,
                album=None,
            ),
            mock_spotify_track_factory(
                "Sorry",
                "spotify:track:6rAXHPd18PZ6W8m9EectzH",
                [mock_spotify_artist_factory("Nothing But Thieves")],
                popularity=2,
                album=None,
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
    async def test_find_song__multiple_artists(self, mock_inner_client_ctor):
        song = "bad guy"
        mock_spotify_tracks = [
            mock_spotify_track_factory(
                name="bad guy",
                artists=[
                    mock_spotify_artist_factory(name="Billie Eilish"),
                    mock_spotify_artist_factory(name="Finneas O'Connell")
                ],
                uri="spotify:track:2Fxmhks0bxGSBdJ92vM42m",
                popularity=None,
                album=None,
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
            popularity=None,
            album=None,
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
            popularity=None,
            album=None,
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
                popularity=None,
                album=None,
            ),
            mock_spotify_track_factory(
                "Mock Track Partial Match",
                "Mock URI",
                [mock_spotify_artist_factory("Mock Artist")],
                popularity=None,
                album=None,
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
    async def test_find_album(self, mock_inner_client_ctor):
        album = "Sweetener"
        mock_spotify_albums = [
            mock_spotify_album_factory(
                "Sweetener",
                "spotify:album:3tx8gQqWbGwqIGZHqDNrGe",
                [mock_spotify_artist_factory("Ariana Grande")],
                songs=[],
                popularity=1
            )
        ]
        inner_cli = self._get_inner_client(mock_inner_client_ctor)
        inner_cli.search = AsyncMock(return_value=MagicMock(albums=mock_spotify_albums))
        inner_cli.get_albums = AsyncMock(return_value=mock_spotify_albums)

        albums = list(await self.spotify_client.find_album(album))

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

    async def test__to_song__no_album(self):
        mock_spotify_track = mock_spotify_track_factory(
            "Sorry",
            "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            [mock_spotify_artist_factory("Justin Bieber")],
            popularity=51,
            album=None,
        )

        song = await self.spotify_client._to_song(mock_spotify_track)

        self.assertEqual("Sorry", song.name)
        self.assertEqual("spotify:track:09CtPGIpYB4BrO8qb1RGsF", song.spotify_uri)
        self.assertEqual(["Justin Bieber"], song.artists)
        self.assertEqual(51, song.popularity)
        self.assertIsNone(song.album)

    async def test__to_song__w_album(self):
        mock_album = Album(
            "Sweetener",
            "spotify:album:3tx8gQqWbGwqIGZHqDNrGe",
            [mock_spotify_artist_factory("Ariana Grande")],
            songs=[],
            popularity=100
        )
        mock_spotify_track = mock_spotify_track_factory(
            "successful",
            "spotify:track:5YeHLHDdQ4nKHk81XFWhCU",
            [mock_spotify_artist_factory("Ariana Grande")],
            popularity=99,
            album=mock_album,
        )
        self.spotify_client._to_album = AsyncMock(return_value=mock_album)

        song = await self.spotify_client._to_song(mock_spotify_track)

        self.assertEqual("successful", song.name)
        self.assertEqual("spotify:track:5YeHLHDdQ4nKHk81XFWhCU", song.spotify_uri)
        self.assertEqual(["Ariana Grande"], song.artists)
        self.assertEqual(99, song.popularity)
        self.assertIsNotNone(song.album)
        self.assertEqual("Sweetener", song.album.name)
        self.assertEqual("spotify:album:3tx8gQqWbGwqIGZHqDNrGe", song.album.spotify_uri)
        self.assertEqual(100, song.album.popularity)
        self.assertEqual([], song.album.songs)

    async def test__order_album_songs__full_album(self):
        songs_w_number = [
            (Song("Good Day Sunshine - Remastered 2009", "", []), (8)),
            (Song("And Your Bird Can Sing - Remastered 2009", "", []), (9)),
            (Song("For No One - Remastered 2009", "", []), (10)),
            (Song("Doctor Robert - Remastered 2009", "", []), (11)),
            (Song("I Want To Tell You - Remastered 2009", "", []), (12)),
            (Song("Got To Get You Into My Life - Remastered 2009", "", []), (13)),
            (Song("Tomorrow Never Knows - Remastered 2009", "", []), (14)),
            (Song("Taxman - Remastered 2009", "", []), (1)),
            (Song("Eleanor Rigby - Remastered 2009", "", []), (2)),
            (Song("I'm Only Sleeping - Remastered 2009", "", []), (3)),
            (Song("Love You To - Remastered 2009", "", []), (4)),
            (Song("Here, There And Everywhere - Remastered 2009", "", []), (5)),
            (Song("Yellow Submarine - Remastered 2009", "", []), (6)),
            (Song("She Said She Said - Remastered 2009", "", []), (7)),
        ]
        expected_album_song_list = [
            "Taxman - Remastered 2009",
            "Eleanor Rigby - Remastered 2009",
            "I'm Only Sleeping - Remastered 2009",
            "Love You To - Remastered 2009",
            "Here, There And Everywhere - Remastered 2009",
            "Yellow Submarine - Remastered 2009",
            "She Said She Said - Remastered 2009",
            "Good Day Sunshine - Remastered 2009",
            "And Your Bird Can Sing - Remastered 2009",
            "For No One - Remastered 2009",
            "Doctor Robert - Remastered 2009",
            "I Want To Tell You - Remastered 2009",
            "Got To Get You Into My Life - Remastered 2009",
            "Tomorrow Never Knows - Remastered 2009",
        ]

        ordered_songs = self.spotify_client._order_album_songs(songs_w_number)

        self.assertEqual([song.name for song in ordered_songs], expected_album_song_list)

    async def test__order_album_songs__incomplete_album(self):
        songs_w_number = [
            (Song("Got To Get You Into My Life - Remastered 2009", "", []), (13)),
            (Song("Tomorrow Never Knows - Remastered 2009", "", []), (14)),
            (Song("Taxman - Remastered 2009", "", []), (1)),
        ]
        expected_album_song_list = [
            "Taxman - Remastered 2009",
            "Got To Get You Into My Life - Remastered 2009",
            "Tomorrow Never Knows - Remastered 2009",
        ]

        ordered_songs = self.spotify_client._order_album_songs(songs_w_number)

        self.assertEqual([song.name for song in ordered_songs], expected_album_song_list)

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
        self.assertTrue(found_childish_gambino_song, "Expected to find 'Redbone' by Childish Gambino")

    @unittest.skip("Integration tests disabled by default.")
    async def test_find_song__regression_test(self):
        results = list(await self.spotify_client.find_song("American Pie"))

        self.assertLessEqual(1, len(results))
        found_catch_22_song = TestSpotifyClientHelper.is_one_of_the_artists(
            results, "Catch 22")
        self.assertTrue(found_catch_22_song, "Expected to find 'American Pie' by Catch 22")

    @unittest.skip("Integration tests disabled by default.")
    async def test_find_album__gets_songs(self):
        results = await self.spotify_client.find_album("Sweetener")

        self.assertLessEqual(1, len(results))
        self.assertIsNotNone(list(results)[0].popularity)
        found_ariana_grande_album = TestSpotifyClientHelper.is_one_of_the_artists(
            results, "Ariana Grande")
        self.assertTrue(found_ariana_grande_album, "Expected to find 'Sweetener' by Ariana Grande")
        ariana_grande_album = TestSpotifyClientHelper.get_by_uri(results, "spotify:album:3tx8gQqWbGwqIGZHqDNrGe")
        self.assertEqual(15, len(ariana_grande_album.songs))

    @unittest.skip("Integration tests disabled by default.")
    async def test__get_album_songs(self):
        songs = await self.spotify_client._get_album_songs("Sweetener", ["Ariana Grande"], "spotify:album:3tx8gQqWbGwqIGZHqDNrGe")

        self.assertEqual(15, len(songs))
        self.assertIsNotNone(list(songs)[0].popularity)
        album_name_matches, err_msg = TestSpotifyClientHelper.each_song(songs, lambda song: song.album.name == "Sweetener")
        self.assertTrue(album_name_matches, err_msg)
        self.assertTrue(TestSpotifyClientHelper.each_song(songs, lambda song: "Ariana Grande" in song.artists))
        album_uri_matches, err_msg = TestSpotifyClientHelper.each_song(
            songs, lambda song: song.album.spotify_uri == "spotify:album:3tx8gQqWbGwqIGZHqDNrGe")
        self.assertTrue(album_uri_matches, err_msg)

    @unittest.skip("Integration tests disabled by default.")
    async def test__get_album_songs__by_multiple_artists(self):
        songs = await self.spotify_client._get_album_songs(
            "Yes Lawd!",
            ["NxWorries", "Anderson .Paak", "Knxwledge"],
            "spotify:album:0K3FiXt6ekJTWaUku3LpHL")

        self.assertEqual(19, len(songs))
        popularity_not_none, err_msg = TestSpotifyClientHelper.each_song(
            songs, lambda song: song.popularity is not None)
        self.assertTrue(popularity_not_none, err_msg)
        album_name_matches, err_msg = TestSpotifyClientHelper.each_song(songs, lambda song: song.album.name == "Yes Lawd!")
        self.assertTrue(album_name_matches, err_msg)
        self.assertTrue(TestSpotifyClientHelper.each_song(
            songs, lambda song: sorted(["NxWorries", "Anderson .Paak", "Knxwledge"]) == sorted(song.artists)))
        album_uri_matches, err_msg = TestSpotifyClientHelper.each_song(
            songs, lambda song: song.album.spotify_uri == "spotify:album:0K3FiXt6ekJTWaUku3LpHL")
        self.assertTrue(album_uri_matches, err_msg)

    @unittest.skip("Integration tests disabled by default.")
    async def test__get_album_songs__tracks_are_in_order(self):
        expected_album_song_list = [
            "Taxman - Remastered 2009",
            "Eleanor Rigby - Remastered 2009",
            "I'm Only Sleeping - Remastered 2009",
            "Love You To - Remastered 2009",
            "Here, There And Everywhere - Remastered 2009",
            "Yellow Submarine - Remastered 2009",
            "She Said She Said - Remastered 2009",
            "Good Day Sunshine - Remastered 2009",
            "And Your Bird Can Sing - Remastered 2009",
            "For No One - Remastered 2009",
            "Doctor Robert - Remastered 2009",
            "I Want To Tell You - Remastered 2009",
            "Got To Get You Into My Life - Remastered 2009",
            "Tomorrow Never Knows - Remastered 2009",
        ]

        songs = await self.spotify_client._get_album_songs(
            "Revolver",
            ["The Beatles"],
            "spotify:album:3PRoXYsngSwjEQWR5PsHWR")

        self.assertEqual(14, len(songs))
        popularity_not_none, err_msg = TestSpotifyClientHelper.each_song(
            songs, lambda song: song.popularity is not None, "Popularity not None.")
        self.assertTrue(popularity_not_none, err_msg)
        album_name_matches, err_msg = TestSpotifyClientHelper.each_song(
            songs, lambda song: song.album.name == "Revolver (Remastered)", "Album name should be 'Revolver (Remastered)'")
        self.assertTrue(album_name_matches, err_msg)
        self.assertTrue(TestSpotifyClientHelper.each_song(
            songs, lambda song: ["Revolver"] == song.artists))
        album_uri_matches, err_msg = TestSpotifyClientHelper.each_song(
            songs,
            lambda song: song.album.spotify_uri == "spotify:album:3PRoXYsngSwjEQWR5PsHWR",
            "Album uri == spotify:album:3PRoXYsngSwjEQWR5PsHWR")
        self.assertTrue(album_uri_matches, err_msg)
        self.assertEqual([song.name for song in songs], expected_album_song_list)


class TestSpotifyClientHelper():
    @classmethod
    def is_one_of_the_artists(cls, songs_or_albums, artist_name):
        for album in songs_or_albums:
            if artist_name in [artist for artist in album.artists]:
                return True
        return False

    @classmethod
    def get_by_uri(cls, songs_or_albums, spotify_uri):
        for song_or_album in songs_or_albums:
            if song_or_album.spotify_uri == spotify_uri:
                return song_or_album
        return None

    @classmethod
    def each_song(cls, songs, matches_criteria, criteria_str="does not match criteria"):
        for song in songs:
            if not matches_criteria(song):
                return False, f"Song '{song.name}' ({song.album.name}, {song.spotify_uri}): {criteria_str}"
        return True, None