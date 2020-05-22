import unittest

from collections import namedtuple
from unittest.mock import AsyncMock, MagicMock, patch

from song_scrounger.document_parser import DocumentParser
from song_scrounger.models.song import Song
from song_scrounger.util import read_file_contents
from tests.helper import get_num_times_called


class TestDocumentParser(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_spotify_artist_factory = namedtuple("MockSpotifyArtist", ['name'])
        cls.mock_spotify_track_factory = namedtuple(
            "MockSpotifyTrack", ['name', 'uri', 'artists'])

    async def asyncSetUp(self):
        self.mock_spotify_client = AsyncMock()
        self.document_parser = DocumentParser(self.mock_spotify_client)

    async def test_find_quoted_tokens__returns_single_token(self):
        text = "Should \"Find this\" at least"

        tokens = self.document_parser.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            ["Find this"],
            "Faild to find only token in text.",
        )

    async def test_find_quoted_tokens(self):
        text = """
            When Don McClean recorded "American Pie" in 1972 he was remembering his own youth and the early innocence of rock 'n' roll fifteen years before; he may not have considered that he was also contributing the most sincere historical treatise ever fashioned on the vast social transition from the 1950s to the 1960s. For the record, "the day the music died" refers to Buddy Holly's February 1959 death in a plane crash in North Dakota that also took the lives of Richie ("La Bamba") Valens and The Big Bopper ("Chantilly Lace"). The rest of "American Pie" describes the major rock stars of the sixties and their publicity-saturated impact on the music scene: the Jester is Bob Dylan, the Sergeants are the Beatles, Satan is Mick Jagger. For 1950s teens who grew up with the phenomenon of primordial rock 'n' roll, the changes of the sixties might have seemed to turn the music into something very different: "We all got up to dance / Oh, but we never got the chance." There's no doubt that
        """

        tokens = self.document_parser.find_quoted_tokens(text)

        self.assertEqual(
            set(tokens),
            set(['American Pie', 'the day the music died', 'La Bamba', 'Chantilly Lace', 'American Pie', 'We all got up to dance / Oh, but we never got the chance.']),
            "Failed to find all tokens.",
        )

    async def test_find_quoted_tokens__no_tokens__returns_empty(self):
        text = "Nothing to see here."

        tokens = self.document_parser.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            [],
            "Should not have found any tokens.",
        )

    async def test_find_quoted_tokens__ignores_unbalanced(self):
        text = "For \" there is no closing quote"

        tokens = self.document_parser.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            [],
            "Should not have found any tokens."
        )

    async def test_find_quoted_tokens__ignores_final_unbalanced_quote(self):
        text = "Here's \"a token\" but for \" there is no closing quote"

        tokens = self.document_parser.find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            ["a token"],
            "Should not have found any tokens."
        )

    async def test_find_quoted_tokens__preserves_order(self):
        text = "\"first token\" and \"second token\""

        tokens = self.document_parser.find_quoted_tokens(text)

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

        tokens = self.document_parser.find_quoted_tokens(text)

        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0], "repeat token")
        self.assertEqual(tokens[1], "repeat token")
        self.assertEqual(tokens[2], "repeat token")

    async def test_find_songs__returns_only_filtered_songs(self):
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
        self.document_parser._get_paragraphs = MagicMock(
            return_value=[text]
        )
        self.document_parser.find_quoted_tokens = MagicMock(
            return_value = ["Sorry"]
        )
        self.document_parser.search_spotify = AsyncMock(
            return_value = songs
        )
        self.document_parser.filter_if_any_artists_mentioned = MagicMock(
            return_value = set([songs[0]])
        )

        results = await self.document_parser.find_songs(text)

        self.document_parser._get_paragraphs.assert_called_once_with(text)
        self.document_parser.find_quoted_tokens.assert_called_once_with(text)
        self.document_parser.search_spotify.assert_called_once_with("Sorry")
        self.document_parser.filter_if_any_artists_mentioned.assert_any_call(
            songs, text
        )
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set(["spotify:track:09CtPGIpYB4BrO8qb1RGsF"]))

    async def test_find_songs__duplicate_finds__returns_only_one(self):
        text = "\"Sorry\" by Justin Bieber... as I said, \"Sorry\"..."
        self.document_parser._get_paragraphs = MagicMock(
            return_value=[text]
        )
        self.document_parser.find_quoted_tokens = MagicMock(
            return_value = ["Sorry", "Sorry"]
        )
        songs = [
            Song(
                "Sorry",
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                ["Justin Bieber"]
            )
        ]
        self.document_parser.search_spotify = AsyncMock(
            return_value = songs
        )
        self.document_parser.filter_if_any_artists_mentioned = MagicMock(
            return_value = set(songs)
        )

        results = await self.document_parser.find_songs(text)

        self.document_parser._get_paragraphs.assert_called_once_with(text)
        self.document_parser.find_quoted_tokens.assert_called_once_with(text)
        self.document_parser.search_spotify.assert_any_call("Sorry")
        self.assertEqual(
            get_num_times_called(self.document_parser.search_spotify), 2)
        self.document_parser.filter_if_any_artists_mentioned.assert_any_call(
            songs, text
        )
        self.assertEqual(get_num_times_called(
            self.document_parser.filter_if_any_artists_mentioned), 2)
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set(["spotify:track:09CtPGIpYB4BrO8qb1RGsF"]))

    async def test_find_songs__multiple_finds_w_different_artists__merges_results(self):
        text = "\"Sorry\" by Justin Bieber...\n\"Sorry\" by Nothing But Thieves"
        self.document_parser._get_paragraphs = MagicMock(return_value=[
            "\"Sorry\" by Justin Bieber...", "\"Sorry\" by Nothing But Thieves"])
        self.document_parser.find_quoted_tokens = MagicMock(
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
        self.document_parser.search_spotify = AsyncMock(
            return_value = songs
        )
        self.document_parser.filter_if_any_artists_mentioned = MagicMock(
            return_value = set(songs)
        )

        results = await self.document_parser.find_songs(text)

        self.document_parser._get_paragraphs.assert_called_once_with(text)
        self.document_parser.find_quoted_tokens.assert_any_call(
            "\"Sorry\" by Justin Bieber...")
        self.document_parser.find_quoted_tokens.assert_any_call(
            "\"Sorry\" by Nothing But Thieves")
        self.assertEqual(
            get_num_times_called(self.document_parser.find_quoted_tokens), 2)
        self.document_parser.search_spotify.assert_any_call("Sorry")
        self.assertEqual(
            get_num_times_called(self.document_parser.search_spotify), 2)
        self.document_parser.filter_if_any_artists_mentioned.assert_any_call(
            songs, text
        )
        self.assertEqual(get_num_times_called(
            self.document_parser.filter_if_any_artists_mentioned), 2)
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
        self.document_parser.filter_by_mentioned_artist = MagicMock(
            return_value = set([songs[0]])
        )

        filtered_songs = self.document_parser.filter_if_any_artists_mentioned(songs, text)

        self.document_parser.filter_by_mentioned_artist.assert_called_once_with(
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
        self.document_parser.filter_by_mentioned_artist = MagicMock(
            return_value = set()
        )

        filtered_songs = self.document_parser.filter_if_any_artists_mentioned(songs, text)

        self.document_parser.filter_by_mentioned_artist.assert_called_once_with(
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
        self.document_parser.is_mentioned = MagicMock(side_effect=[True, False])

        filtered_songs = self.document_parser.filter_by_mentioned_artist(
            [song_by_mentioned_artist, song_by_unmentioned_artist], text)

        self.document_parser.is_mentioned.assert_any_call("Justin Bieber", text)
        self.document_parser.is_mentioned.assert_any_call("Nothing But Thieves", text)
        self.assertEqual(len(filtered_songs), 1)
        self.assertEqual(list(filtered_songs)[0], song_by_mentioned_artist)

    async def test_filter_by_mentioned_artist__no_artists_mentioned__returns_empty_set(self):
        text = "\"Sorry\" by ... someone"
        songs = [Song(
            "Sorry",
            "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            artists=["Justin Bieber"]
        )]
        self.document_parser.is_mentioned = MagicMock(return_value=False)

        filtered_songs = self.document_parser.filter_by_mentioned_artist(songs, text)

        self.document_parser.is_mentioned.assert_called_once_with("Justin Bieber", text)
        self.assertEqual(len(filtered_songs), 0)

    async def test_filter_by_mentioned_artist__multiple_artist_per_song__skips_duplicates(self):
        text = "\"Sorry\" by Billie Eilish and brother Finneas O'Connell"
        songs = [Song(
            "bad guy",
            "spotify:track:2Fxmhks0bxGSBdJ92vM42m",
            ["Billie Eilish", "Finneas O'Connell"]
        )]
        self.document_parser.is_mentioned = MagicMock(return_value=True)

        filtered_songs = self.document_parser.filter_by_mentioned_artist(songs, text)

        self.assertTrue(
            get_num_times_called(self.document_parser.is_mentioned) >= 1)
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

        songs = await self.document_parser.search_spotify(song)

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

        songs = await self.document_parser.search_spotify(song)

        self.mock_spotify_client.find_track.assert_called_once_with("bad guy")
        self.assertEqual(len(songs), 1)
        # TODO: once Song.__eq__ is implemented, compare songs normally
        songs_list = list(songs)
        self.assertEqual(songs_list[0].name, expected_songs[0].name)
        self.assertEqual(songs_list[0].spotify_uri, expected_songs[0].spotify_uri)
        self.assertEqual(songs_list[0].artists, expected_songs[0].artists)

    async def test_get_paragraphs__no_newlines(self):
        text = "Only paragraph"

        paragraphs = self.document_parser._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 1)
        self.assertEqual(paragraphs[0], "Only paragraph")

    async def test_get_paragraphs__splits_by_newline(self):
        text = "Paragraph one\nParagraph two"

        paragraphs = self.document_parser._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], "Paragraph one")
        self.assertEqual(paragraphs[1], "Paragraph two")

    async def test_get_paragraphs__omits_empty_paragraph(self):
        text = "Paragraph one\n\nParagraph two"

        paragraphs = self.document_parser._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], "Paragraph one")
        self.assertEqual(paragraphs[1], "Paragraph two")

    async def test_get_paragraphs__omits_whitespace_paragraph(self):
        text = "Paragraph one\n   \nParagraph two"

        paragraphs = self.document_parser._get_paragraphs(text)

        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], "Paragraph one")
        self.assertEqual(paragraphs[1], "Paragraph two")

    async def test_is_mentioned__true(self):
        word, text = "Justin Bieber", "Hey, it's Justin Bieber"

        is_mentioned = self.document_parser.is_mentioned(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned__ignores_case(self):
        word, text = "JUSTIN bieber", "Hey, it's Justin Bieber"

        is_mentioned = self.document_parser.is_mentioned(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned__false(self):
        word, text = "Justin Bieber", "Oh no, it's Justin Timberlake"

        is_mentioned = self.document_parser.is_mentioned(word, text)

        self.assertFalse(is_mentioned)

    async def test_is_mentioned__tokens_match_but_whole_word_is_not_substr(self):
        # actual example: http://www.dntownsend.com/Site/Rock/3change.htm
        word, text = "Paul Anka", "Paul (\"Put Your Head on My Shoulder\") Anka"

        is_mentioned = self.document_parser.is_mentioned(word, text)

        self.assertTrue(is_mentioned)

    @unittest.skip("Enable when implemented")
    async def test_is_mentioned__whole_word(self):
        word, text = "Hell", "Hello"

        is_mentioned = self.document_parser.is_mentioned(word, text)

        self.assertFalse(is_mentioned)

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__mocked_spotify_client(self):
        text = "\"Sorry\" by Justin Bieber."
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

        results = await self.document_parser.find_songs(text)

        self.mock_spotify_client.find_track.assert_any_call("Sorry")
        self.assertEqual(1, len(results.keys()))
        self.assertIn("Sorry", results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set(["spotify:track:09CtPGIpYB4BrO8qb1RGsF"]))

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__no_mocks__simple(self):
        from song_scrounger.spotify_client import SpotifyClient
        from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token

        spotify_client_id, spotify_secret_key = get_spotify_creds()
        spotify_bearer_token = get_spotify_bearer_token()
        spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key, spotify_bearer_token)

        text = "\"Sorry\" by Justin Bieber."
        document_parser = DocumentParser(spotify_client)
        results = await document_parser.find_songs(text)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("Sorry", results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set(["spotify:track:09CtPGIpYB4BrO8qb1RGsF"]))

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__no_mocks__two_artists(self):
        from song_scrounger.spotify_client import SpotifyClient
        from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token
        from tests import helper

        spotify_client_id, spotify_secret_key = get_spotify_creds()
        spotify_bearer_token = get_spotify_bearer_token()
        spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key, spotify_bearer_token)

        document_parser = DocumentParser(spotify_client)

        text = "\"Sorry\" by Justin Bieber or Nothing But Thieves."
        results = await document_parser.find_songs(text)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("Sorry", results.keys())
        self.assertEqual(len(results["Sorry"]), 2)
        self.assertEqual(
            set(results["Sorry"]),
            set([
                "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                "spotify:track:6rAXHPd18PZ6W8m9EectzH"
            ])
        )

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__no_mocks__no_artists_filtered(self):
        from song_scrounger.spotify_client import SpotifyClient
        from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token

        spotify_client_id, spotify_secret_key = get_spotify_creds()
        spotify_bearer_token = get_spotify_bearer_token()
        spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key, spotify_bearer_token)

        document_parser = DocumentParser(spotify_client)

        text = "\"Sorry\"... by certain artists"
        results = await document_parser.find_songs(text)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("Sorry", results.keys())
        self.assertGreater(len(results["Sorry"]), 10)