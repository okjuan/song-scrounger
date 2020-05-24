import asyncio
import os
import random
import unittest

from collections import namedtuple
from unittest.mock import AsyncMock, MagicMock, patch

from song_scrounger.song_scrounger import SongScrounger
from song_scrounger.models.song import Song
from song_scrounger.util import read_file_contents
from tests.helper import get_num_times_called


class TestSongScrounger(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_spotify_artist_factory = namedtuple("MockSpotifyArtist", ['name'])
        cls.mock_spotify_track_factory = namedtuple(
            "MockSpotifyTrack", ['name', 'uri', 'artists'])

    async def asyncSetUp(self):
        self.mock_spotify_client = AsyncMock()
        self.song_scrounger = SongScrounger(self.mock_spotify_client)

    async def test_find_quoted_tokens__returns_single_token(self):
        text = "Should \"Find this\" at least"

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            ["Find this"],
            "Faild to find only token in text.",
        )

    async def test_find_quoted_tokens(self):
        text = """
            When Don McLean recorded "American Pie" in 1972 he was remembering his own youth and the early innocence of rock 'n' roll fifteen years before; he may not have considered that he was also contributing the most sincere historical treatise ever fashioned on the vast social transition from the 1950s to the 1960s. For the record, "the day the music died" refers to Buddy Holly's February 1959 death in a plane crash in North Dakota that also took the lives of Richie ("La Bamba") Valens and The Big Bopper ("Chantilly Lace"). The rest of "American Pie" describes the major rock stars of the sixties and their publicity-saturated impact on the music scene: the Jester is Bob Dylan, the Sergeants are the Beatles, Satan is Mick Jagger. For 1950s teens who grew up with the phenomenon of primordial rock 'n' roll, the changes of the sixties might have seemed to turn the music into something very different: "We all got up to dance / Oh, but we never got the chance." There's no doubt that
        """

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            set(tokens),
            set(['American Pie', 'the day the music died', 'La Bamba', 'Chantilly Lace', 'American Pie', 'We all got up to dance / Oh, but we never got the chance.']),
            "Failed to find all tokens.",
        )

    async def test_find_quoted_tokens__no_tokens__returns_empty(self):
        text = "Nothing to see here."

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            [],
            "Should not have found any tokens.",
        )

    async def test_find_quoted_tokens__ignores_unbalanced(self):
        text = "For \" there is no closing quote"

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            [],
            "Should not have found any tokens."
        )

    async def test_find_quoted_tokens__ignores_final_unbalanced_quote(self):
        text = "Here's \"a token\" but for \" there is no closing quote"

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            ["a token"],
            "Should not have found any tokens."
        )

    async def test_find_quoted_tokens__preserves_order(self):
        text = "\"first token\" and \"second token\""

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(
            tokens[0],
            "first token",
            "Did not find first token in expected position."
        )
        self.assertEqual(
            tokens[1],
            "second token",
            "Did not find second token in expected position."
        )

    async def test_find_quoted_tokens__preserves_dups(self):
        text = "\"repeat token\" again \"repeat token\" again \"repeat token\""

        tokens = self.song_scrounger.find_quoted_tokens(text)

        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0], "repeat token")
        self.assertEqual(tokens[1], "repeat token")
        self.assertEqual(tokens[2], "repeat token")

    async def test_find_songs_names__strips_whitespace(self):
        text = MagicMock()
        self.song_scrounger.find_quoted_tokens = MagicMock(return_value = [
            "  leading",
            "trailing   ",
            "  both   ",
        ])

        song_names = self.song_scrounger.find_song_names(text)

        song_names_list = list(song_names)
        self.assertEqual(len(song_names_list), 3)
        self.assertEqual(set(song_names_list), set(["leading", "trailing", "both"]))

    async def test_find_songs_names__strips_trailing_punctuation(self):
        text = MagicMock()
        self.song_scrounger.find_quoted_tokens = MagicMock(return_value = [
            ",leading",
            "trailing.",
            ".both,",
        ])

        song_names = self.song_scrounger.find_song_names(text)

        song_names_list = list(song_names)
        self.assertEqual(len(song_names_list), 3)
        self.assertEqual(set(song_names_list), set([",leading", "trailing", ".both"]))

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="\"Sorry\" by Justin Bieber.")
    async def test_find_songs__returns_only_filtered_songs(self, mock_read_file_contents):
        input_file_name = "mock input file"
        text = "\"Sorry\" by Justin Bieber."
        songs = [
            Song(
                "Sorry",
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                ["Justin Bieber"]
            ),
            Song(
                "Sorry",
                "spotify:track:6rAXHPd18PZ6W8m9EectzH",
                ["Nothing But Thieves"]
            )
        ]
        self.song_scrounger._get_paragraphs = MagicMock(
            return_value=[text]
        )
        self.song_scrounger.find_song_names = MagicMock(
            return_value = ["Sorry"]
        )
        self.song_scrounger.search_spotify = AsyncMock(
            return_value = songs
        )
        self.song_scrounger.filter_if_any_artists_mentioned = MagicMock(
            return_value = set([songs[0]])
        )

        results = await self.song_scrounger.find_songs(input_file_name)

        mock_read_file_contents.assert_called_once_with(input_file_name)
        self.song_scrounger._get_paragraphs.assert_called_once_with(text)
        self.song_scrounger.find_song_names.assert_called_once_with(text)
        self.song_scrounger.search_spotify.assert_called_once_with("Sorry")
        self.song_scrounger.filter_if_any_artists_mentioned.assert_any_call(
            songs, text
        )
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set(["spotify:track:09CtPGIpYB4BrO8qb1RGsF"]))

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="\"Sorry\" by Justin Bieber... as I said, \"Sorry\"...")
    async def test_find_songs__duplicate_finds__returns_only_one(self, mock_read_file_contents):
        input_file_name = "mock input file"
        text = "\"Sorry\" by Justin Bieber... as I said, \"Sorry\"..."
        self.song_scrounger._get_paragraphs = MagicMock(
            return_value=[text]
        )
        self.song_scrounger.find_song_names = MagicMock(
            return_value = ["Sorry", "Sorry"]
        )
        songs = [
            Song(
                "Sorry",
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                ["Justin Bieber"]
            )
        ]
        self.song_scrounger.search_spotify = AsyncMock(
            return_value = songs
        )
        self.song_scrounger.filter_if_any_artists_mentioned = MagicMock(
            return_value = set(songs)
        )

        results = await self.song_scrounger.find_songs(input_file_name)

        mock_read_file_contents.assert_called_once_with(input_file_name)
        self.song_scrounger._get_paragraphs.assert_called_once_with(text)
        self.song_scrounger.find_song_names.assert_called_once_with(text)
        self.song_scrounger.search_spotify.assert_any_call("Sorry")
        self.assertEqual(
            get_num_times_called(self.song_scrounger.search_spotify), 2)
        self.song_scrounger.filter_if_any_artists_mentioned.assert_any_call(
            songs, text
        )
        self.assertEqual(get_num_times_called(
            self.song_scrounger.filter_if_any_artists_mentioned), 2)
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set(["spotify:track:09CtPGIpYB4BrO8qb1RGsF"]))

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="\"Sorry\" by Justin Bieber...\n\"Sorry\" by Nothing But Thieves")
    async def test_find_songs__multiple_finds_w_different_artists__merges_results(self, mock_read_file_contents):
        input_file_name = "mock input file"
        text = "\"Sorry\" by Justin Bieber...\n\"Sorry\" by Nothing But Thieves"
        self.song_scrounger._get_paragraphs = MagicMock(return_value=[
            "\"Sorry\" by Justin Bieber...", "\"Sorry\" by Nothing But Thieves"])
        self.song_scrounger.find_song_names = MagicMock(
            return_value = ["Sorry"]
        )
        songs = [
            Song(
                "Sorry",
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                ["Justin Bieber"]
            ),
            Song(
                "Sorry",
                "spotify:track:6rAXHPd18PZ6W8m9EectzH",
                ["Nothing But Thieves"]
            )
        ]
        self.song_scrounger.search_spotify = AsyncMock(
            return_value = songs
        )
        self.song_scrounger.filter_if_any_artists_mentioned = MagicMock(
            return_value = set(songs)
        )

        results = await self.song_scrounger.find_songs(input_file_name)

        mock_read_file_contents.assert_called_once_with(input_file_name)
        self.song_scrounger._get_paragraphs.assert_called_once_with(text)
        self.assertEqual(
            get_num_times_called(self.song_scrounger.find_song_names), 2)
        self.song_scrounger.find_song_names.assert_any_call(
            "\"Sorry\" by Justin Bieber...")
        self.song_scrounger.find_song_names.assert_any_call(
            "\"Sorry\" by Nothing But Thieves")
        self.assertEqual(
            get_num_times_called(self.song_scrounger.find_song_names), 2)
        self.song_scrounger.search_spotify.assert_any_call("Sorry")
        self.assertEqual(
            get_num_times_called(self.song_scrounger.search_spotify), 2)
        self.song_scrounger.filter_if_any_artists_mentioned.assert_any_call(
            songs, text
        )
        self.assertEqual(get_num_times_called(
            self.song_scrounger.filter_if_any_artists_mentioned), 2)
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 2)
        self.assertEqual(
            results["Sorry"],
            set([
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                "spotify:track:6rAXHPd18PZ6W8m9EectzH"
            ])
        )

    async def test_filter_if_any_artists_mentioned__only_keeps_mentioned_artist(self):
        text = "\"Sorry\""
        songs = [
            Song(
                "Sorry",
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                ["Justin Bieber"]
            ),
            Song(
                "Sorry",
                "spotify:track:6rAXHPd18PZ6W8m9EectzH",
                ["Nothing But Thieves"]
            )
        ]
        self.song_scrounger.filter_by_mentioned_artist = MagicMock(
            return_value = set([songs[0]])
        )

        filtered_songs = self.song_scrounger.filter_if_any_artists_mentioned(songs, text)

        self.song_scrounger.filter_by_mentioned_artist.assert_called_once_with(
            songs, text
        )
        self.assertEqual(filtered_songs, set([songs[0]]))

    async def test_filter_if_any_artists_mentioned__no_artist_mentioned__keeps_all_songs(self):
        text = "\"Sorry\""
        songs = [
            Song(
                "Sorry",
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                ["Justin Bieber"]
            ),
            Song(
                "Sorry",
                "spotify:track:6rAXHPd18PZ6W8m9EectzH",
                ["Nothing But Thieves"]
            )
        ]
        self.song_scrounger.filter_by_mentioned_artist = MagicMock(
            return_value = set()
        )

        filtered_songs = self.song_scrounger.filter_if_any_artists_mentioned(songs, text)

        self.song_scrounger.filter_by_mentioned_artist.assert_called_once_with(
            songs, text
        )
        self.assertEqual(filtered_songs, set(songs))

    async def test_filter_by_mentioned_artist__only_returns_song_by_mentioned_artist(self):
        text = "\"Sorry\" by Justin Bieber"
        song_by_mentioned_artist = Song(
            "Sorry",
            "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            artists=["Justin Bieber"]
        )
        song_by_unmentioned_artist = Song(
            "Sorry",
            "spotify:track:6rAXHPd18PZ6W8m9EectzH",
            artists=["Nothing But Thieves"]
        )
        # returns True on first call, but False on second
        self.song_scrounger.is_mentioned = MagicMock(side_effect=[True, False])

        filtered_songs = self.song_scrounger.filter_by_mentioned_artist(
            [song_by_mentioned_artist, song_by_unmentioned_artist], text)

        self.song_scrounger.is_mentioned.assert_any_call("Justin Bieber", text)
        self.song_scrounger.is_mentioned.assert_any_call("Nothing But Thieves", text)
        self.assertEqual(len(filtered_songs), 1)
        self.assertEqual(list(filtered_songs)[0], song_by_mentioned_artist)

    async def test_filter_by_mentioned_artist__no_artists_mentioned__returns_empty_set(self):
        text = "\"Sorry\" by ... someone"
        songs = [Song(
            "Sorry",
            "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            artists=["Justin Bieber"]
        )]
        self.song_scrounger.is_mentioned = MagicMock(return_value=False)

        filtered_songs = self.song_scrounger.filter_by_mentioned_artist(songs, text)

        self.song_scrounger.is_mentioned.assert_called_once_with("Justin Bieber", text)
        self.assertEqual(len(filtered_songs), 0)

    async def test_filter_by_mentioned_artist__multiple_artist_per_song__skips_duplicates(self):
        text = "\"Sorry\" by Billie Eilish and brother Finneas O'Connell"
        songs = [Song(
            "bad guy",
            "spotify:track:2Fxmhks0bxGSBdJ92vM42m",
            ["Billie Eilish", "Finneas O'Connell"]
        )]
        self.song_scrounger.is_mentioned = MagicMock(return_value=True)

        filtered_songs = self.song_scrounger.filter_by_mentioned_artist(songs, text)

        self.assertTrue(
            get_num_times_called(self.song_scrounger.is_mentioned) >= 1)
        self.assertEqual(len(filtered_songs), 1)
        filtered_songs_list = list(filtered_songs)
        self.assertEqual(filtered_songs_list[0].name, "bad guy")
        self.assertEqual(
            filtered_songs_list[0].spotify_uri,
            "spotify:track:2Fxmhks0bxGSBdJ92vM42m"
        )
        self.assertEqual(
            filtered_songs_list[0].artists,
            ["Billie Eilish", "Finneas O'Connell"]
        )

    @unittest.skip("Enable when implemented")
    async def test_filter_by_mentioned_artist__song_name_artist_name_clash(self):
        # TODO: what if a song name is found as an artist name?
        pass

    async def test_search_spotify__returns_song_objects(self):
        song = "Sorry"
        self.mock_spotify_client.find_track.return_value = [
            self.mock_spotify_track_factory(
                name="Sorry",
                artists=[self.mock_spotify_artist_factory(name="Justin Bieber")],
                uri="spotify:track:09CtPGIpYB4BrO8qb1RGsF"
            ),
            self.mock_spotify_track_factory(
                name="Sorry",
                artists=[self.mock_spotify_artist_factory(name="Nothing But Thieves")],
                uri="spotify:track:6rAXHPd18PZ6W8m9EectzH",
            )
        ]
        expected_songs = [
            Song(
                "Sorry",
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                ["Justin Bieber"]
            ),
            Song(
                "Sorry",
                "spotify:track:6rAXHPd18PZ6W8m9EectzH",
                ["Nothing But Thieves"]
            )
        ]

        songs = await self.song_scrounger.search_spotify(song)

        self.mock_spotify_client.find_track.assert_called_once_with("Sorry")
        self.assertEqual(len(songs), 2)
        # TODO: once Song.__eq__ is implemented, compare songs normally
        songs_list = list(songs)
        self.assertIn(songs_list[0].name, [expected_songs[0].name, expected_songs[1].name])
        self.assertIn(
            songs_list[0].spotify_uri,
            [expected_songs[0].spotify_uri, expected_songs[1].spotify_uri]
        )
        self.assertIn(
            songs_list[0].artists,
            [expected_songs[0].artists, expected_songs[1].artists]
        )
        self.assertIn(songs_list[1].name, [expected_songs[0].name, expected_songs[1].name])
        self.assertIn(
            songs_list[1].spotify_uri,
            [expected_songs[0].spotify_uri, expected_songs[1].spotify_uri]
        )
        self.assertIn(
            songs_list[0].artists,
            [expected_songs[0].artists, expected_songs[1].artists]
        )

    async def test_search_spotify__multiple_artists_per_song(self):
        song = "bad guy"
        self.mock_spotify_client.find_track.return_value = [
            self.mock_spotify_track_factory(
                name="bad guy",
                artists=[
                    self.mock_spotify_artist_factory(name="Billie Eilish"),
                    self.mock_spotify_artist_factory(name="Finneas O'Connell")
                ],
                uri="spotify:track:2Fxmhks0bxGSBdJ92vM42m",
            ),
        ]
        expected_songs = [Song(
            "bad guy",
            "spotify:track:2Fxmhks0bxGSBdJ92vM42m",
            ["Billie Eilish", "Finneas O'Connell"]
        )]

        songs = await self.song_scrounger.search_spotify(song)

        self.mock_spotify_client.find_track.assert_called_once_with("bad guy")
        self.assertEqual(len(songs), 1)
        # TODO: once Song.__eq__ is implemented, compare songs normally
        songs_list = list(songs)
        self.assertEqual(songs_list[0].name, expected_songs[0].name)
        self.assertEqual(songs_list[0].spotify_uri, expected_songs[0].spotify_uri)
        self.assertEqual(songs_list[0].artists, expected_songs[0].artists)

    async def test_get_paragraphs__no_newlines(self):
        text = "Only paragraph"

        paragraphs = self.song_scrounger._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 1)
        self.assertEqual(paragraphs[0], "Only paragraph")

    async def test_get_paragraphs__splits_by_newline(self):
        text = "Paragraph one\nParagraph two"

        paragraphs = self.song_scrounger._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], "Paragraph one")
        self.assertEqual(paragraphs[1], "Paragraph two")

    async def test_get_paragraphs__omits_empty_paragraph(self):
        text = "Paragraph one\n\nParagraph two"

        paragraphs = self.song_scrounger._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], "Paragraph one")
        self.assertEqual(paragraphs[1], "Paragraph two")

    async def test_get_paragraphs__omits_whitespace_paragraph(self):
        text = "Paragraph one\n   \nParagraph two"

        paragraphs = self.song_scrounger._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], "Paragraph one")
        self.assertEqual(paragraphs[1], "Paragraph two")

    async def test_is_mentioned__true(self):
        word, text = "Justin Bieber", "Hey, it's Justin Bieber"

        is_mentioned = self.song_scrounger.is_mentioned(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned__ignores_case(self):
        word, text = "JUSTIN bieber", "Hey, it's Justin Bieber"

        is_mentioned = self.song_scrounger.is_mentioned(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned__false(self):
        word, text = "Justin Bieber", "Oh no, it's Justin Timberlake"

        is_mentioned = self.song_scrounger.is_mentioned(word, text)

        self.assertFalse(is_mentioned)

    async def test_is_mentioned__tokens_match_but_whole_word_is_not_substr(self):
        # actual example: http://www.dntownsend.com/Site/Rock/3change.htm
        word, text = "Paul Anka", "Paul (\"Put Your Head on My Shoulder\") Anka"

        is_mentioned = self.song_scrounger.is_mentioned(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned__regression(self):
        word, text = 'Don McLean', 'When Don McLean recorded "American Pie"\n'

        is_mentioned = self.song_scrounger.is_mentioned(word, text)

        self.assertTrue(is_mentioned)

    @unittest.skip("Enable when implemented")
    async def test_is_mentioned__whole_word(self):
        word, text = "Hell", "Hello"

        is_mentioned = self.song_scrounger.is_mentioned(word, text)

        self.assertFalse(is_mentioned)

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__mocked_spotify_client(self):
        from tests import helper
        input_file_name = "text_mini.txt"
        self.mock_spotify_client.find_track.return_value = [
            self.mock_spotify_track_factory(
                name="American Pie",
                artists=[self.mock_spotify_artist_factory(name="Don McLean")],
                uri="spotify:track:1fDsrQ23eTAVFElUMaf38X"
            ),
        ]

        input_file_path = helper.get_path_to_test_input_file("single_artist_mentioned.txt")
        results = await self.song_scrounger.find_songs(input_file_path)

        self.mock_spotify_client.find_track.assert_any_call("American Pie")
        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertEqual(len(results["American Pie"]), 1)
        self.assertEqual(results["American Pie"], set(["spotify:track:1fDsrQ23eTAVFElUMaf38X"]))

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__no_mocks__simple(self):
        from song_scrounger.spotify_client import SpotifyClient
        from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token
        from tests import helper

        spotify_client_id, spotify_secret_key = get_spotify_creds()
        spotify_bearer_token = get_spotify_bearer_token()
        spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key, spotify_bearer_token)

        song_scrounger = SongScrounger(spotify_client)

        input_file_path = helper.get_path_to_test_input_file("single_artist_mentioned.txt")
        results = await song_scrounger.find_songs(input_file_path)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertEqual(len(results["American Pie"]), 1)
        self.assertEqual(results["American Pie"], set(["spotify:track:1fDsrQ23eTAVFElUMaf38X"]))

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__no_mocks__two_artists(self):
        from song_scrounger.spotify_client import SpotifyClient
        from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token
        from tests import helper

        spotify_client_id, spotify_secret_key = get_spotify_creds()
        spotify_bearer_token = get_spotify_bearer_token()
        spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key, spotify_bearer_token)

        song_scrounger = SongScrounger(spotify_client)

        input_file_path = helper.get_path_to_test_input_file("two_artists_mentioned.txt")
        results = await song_scrounger.find_songs(input_file_path)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertEqual(len(results["American Pie"]), 2)
        self.assertEqual(
            set(results["American Pie"]),
            set([
                "spotify:track:1fDsrQ23eTAVFElUMaf38X",
                "spotify:track:4wpuHehFEEpWAlkw3vjH0s"
            ])
        )

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__no_mocks__no_artists_filtered(self):
        from song_scrounger.spotify_client import SpotifyClient
        from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token
        from tests import helper

        spotify_client_id, spotify_secret_key = get_spotify_creds()
        spotify_bearer_token = get_spotify_bearer_token()
        spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key, spotify_bearer_token)

        song_scrounger = SongScrounger(spotify_client)

        input_file_path = helper.get_path_to_test_input_file("no_artists_mentioned.txt")
        results = await song_scrounger.find_songs(input_file_path)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertGreater(len(results["American Pie"]), 10)

    @unittest.skip("Skip integration tests by default")
    async def test_end_to_end__for_duplicate_songs(self):
        input_file_name = "test_duplicate_songs.txt"
        playlist_name = "Duplicate Song Test: should not repeat any artist"
        await self._run_end_to_end_test(input_file_name, playlist_name)

    @unittest.skip("Skip integration tests by default")
    async def test_end_to_end__simple_artist_detection(self):
        input_file_name = "test_simple_artist_detection.txt"
        playlist_name = "Simple Artist Detection Song: Nothing But Thieves"
        await self._run_end_to_end_test(input_file_name, playlist_name)

    @unittest.skip("Skip integration tests by default")
    async def test_end_to_end__multi_paragraph_artist_detection(self):
        input_file_name = "test_multiparagraph_artist_detection.txt"
        playlist_name = "Multi-Paragraph Artist Detection Song: JB and Nothing But Thieves"
        await self._run_end_to_end_test(input_file_name, playlist_name)
        "test_multiparagraph_artist_detection.txt"

    @unittest.skip("Skip integration tests by default")
    async def test_end_to_end__cross_paragraph_artist_detection(self):
        input_file_name = "test_cross_paragraph_artist_detection.txt"
        playlist_name = "Cross-Paragraph Artist Detection Song: Kiefer"
        await self._run_end_to_end_test(input_file_name, playlist_name)

    async def _run_end_to_end_test(self, input_file_name, playlist_name):
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
