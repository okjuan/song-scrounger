import asyncio
import os
import random
import unittest

from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

from song_scrounger.song_scrounger import SongScrounger
from song_scrounger.models.song import Song
from song_scrounger.util import read_file_contents
from tests.helper import get_num_times_called, mock_spotify_artist_factory, mock_spotify_track_factory


class TestSongScrounger(unittest.IsolatedAsyncioTestCase):
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

    async def test_find_song_names__strips_whitespace(self):
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

    async def test_find_song_names__strips_trailing_punctuation(self):
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
    async def test_find_songs__single_song_with_matching_artist__returns_that_version_only(self, mock_read_file_contents):
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
            return_value = set([songs[0]]))
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set([songs[0]]))

        results = await self.song_scrounger.find_songs(input_file_name)

        mock_read_file_contents.assert_called_once_with(input_file_name)
        self.song_scrounger._get_paragraphs.assert_called_once_with(text)
        self.song_scrounger.find_song_names.assert_called_once_with(text)
        self.song_scrounger.search_spotify.assert_called_once_with("Sorry")
        self.song_scrounger.filter_if_any_artists_mentioned.assert_any_call(
            songs, text)
        self.song_scrounger.reduce_by_popularity_per_artist.assert_called_once_with(
            set([songs[0]]))
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set([songs[0]]))

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="\"Sorry\" by Justin Bieber... as I said, \"Sorry\"...")
    async def test_find_songs__same_song_mentioned_twice__returns_only_one_copy(self, mock_read_file_contents):
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
            return_value = set(songs))
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set(songs))

        results = await self.song_scrounger.find_songs(input_file_name)

        mock_read_file_contents.assert_called_once_with(input_file_name)
        self.song_scrounger._get_paragraphs.assert_called_once_with(text)
        self.song_scrounger.find_song_names.assert_called_once_with(text)
        self.song_scrounger.search_spotify.assert_any_call("Sorry")
        self.assertEqual(
            get_num_times_called(self.song_scrounger.search_spotify), 2)
        self.song_scrounger.filter_if_any_artists_mentioned.assert_any_call(
            songs, text)
        self.assertEqual(get_num_times_called(
            self.song_scrounger.filter_if_any_artists_mentioned), 2)
        self.song_scrounger.reduce_by_popularity_per_artist.assert_any_call(
            set(songs))
        self.assertEqual(
            get_num_times_called(self.song_scrounger.reduce_by_popularity_per_artist), 2)
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        self.assertEqual(results["Sorry"], set(songs))

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="\"Sorry\" by Justin Bieber...\n\"Sorry\" by Nothing But Thieves")
    async def test_find_songs__homonym_songs_w_different_artists__returns_both_versions(self, mock_read_file_contents):
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
            return_value = set(songs))
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set(songs))

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
            songs, text)
        self.assertEqual(get_num_times_called(
            self.song_scrounger.filter_if_any_artists_mentioned), 2)
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set(songs))
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 2)
        self.assertEqual(results["Sorry"], set(songs))

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="\"American Pie\" by Don McLean")
    async def test_find_songs__multiple_search_results_w_same_artist__returns_only_one(self, mock_read_file_contents):
        input_file_name = "mock input file"
        text = "\"American Pie\" by Don McLean"
        self.song_scrounger._get_paragraphs = MagicMock(return_value=[text])
        self.song_scrounger.find_song_names = MagicMock(
            return_value = ["American Pie"]
        )
        less_popular_version = Song(
            "American Pie",
            "spotify:track:1fDsrQ23eTAVFElUMaf38X",
            ["Don McLean"],
            popularity=1
        )
        more_popular_version = Song(
            "American Pie",
            "spotify:track:2ZbTw8awL7EFat9Wz1DIHN",
            ["Don McLean"],
            popularity=2
        )
        songs = [less_popular_version, more_popular_version]
        self.song_scrounger.search_spotify = AsyncMock(
            return_value = songs)
        self.song_scrounger.filter_if_any_artists_mentioned = MagicMock(
            return_value = set(songs))
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set([more_popular_version]))

        results = await self.song_scrounger.find_songs(input_file_name)

        mock_read_file_contents.assert_called_once_with(input_file_name)
        self.song_scrounger._get_paragraphs.assert_called_once_with(text)
        self.song_scrounger.find_song_names.assert_called_once_with(
            "\"American Pie\" by Don McLean")
        self.song_scrounger.search_spotify.assert_called_once_with(
            "American Pie")
        self.song_scrounger.filter_if_any_artists_mentioned.assert_called_once_with(
            songs, text)
        self.song_scrounger.reduce_by_popularity_per_artist = MagicMock(
            return_value = set(songs))
        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("American Pie" in results.keys())
        self.assertEqual(len(results["American Pie"]), 1)
        self.assertEqual(results["American Pie"], set([more_popular_version])
        )

    async def test_set_union__no_dups__keeps_all(self):
        song_A = Song("Song A", "URI A", "Artist A")
        song_B = Song("Song B", "URI B", "Artist B")

        set_union = self.song_scrounger.set_union(set([song_A]), set([song_B]))

        self.assertEqual(len(set_union), 2)
        self.assertTrue(song_A in set_union)
        self.assertTrue(song_B in set_union)

    async def test_set_union__all_dups__keeps_one(self):
        song_A = Song("Song A", "URI A", "Artist A")
        song_A_dup = Song("Song A", "URI A", "Artist A")

        set_union = self.song_scrounger.set_union(set([song_A]), set([song_A_dup]))

        self.assertEqual(len(set_union), 1)
        self.assertTrue(song_A in set_union or song_A_dup in set_union)

    async def test_set_union__one_dups__removes_dup_keeps_others(self):
        song_A = Song("Song A", "URI A", "Artist A")
        song_B = Song("Song B", "URI B", "Artist B")
        song_B_dup = Song("Song B", "URI B", "Artist B")
        song_C = Song("Song C", "URI C", "Artist C")

        set_union = self.song_scrounger.set_union(set([song_A, song_B]), set([song_B_dup, song_C]))

        self.assertEqual(len(set_union), 3)
        self.assertTrue(song_A in set_union)
        self.assertTrue(song_B in set_union or song_B_dup in set_union)
        self.assertTrue(song_C in set_union)

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
            mock_spotify_track_factory(
                name="Sorry",
                artists=[mock_spotify_artist_factory(name="Justin Bieber")],
                uri="spotify:track:09CtPGIpYB4BrO8qb1RGsF",
                popularity=None
            ),
            mock_spotify_track_factory(
                name="Sorry",
                artists=[mock_spotify_artist_factory(name="Nothing But Thieves")],
                uri="spotify:track:6rAXHPd18PZ6W8m9EectzH",
                popularity=None
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

    async def test_reduce_by_popularity_per_artist__by_same_artist__reduces_to_one(self):
        songs = [
            Song(
                "American Pie",
                "spotify:track:1fDsrQ23eTAVFElUMaf38X",
                ["Don McLean"]
            ),
            Song(
                "American Pie",
                "spotify:track:4wpuHehFEEpWAlkw3vjH0s",
                ["Don McLean"]
            )
        ]
        self.song_scrounger.pick_most_popular_song = MagicMock(
            return_value = songs[0])

        results = self.song_scrounger.reduce_by_popularity_per_artist(songs)

        self.song_scrounger.pick_most_popular_song.assert_called_once_with(set(songs))
        self.assertEqual(len(results), 1)
        self.assertEqual(results, set([songs[0]]))

    async def test_reduce_by_popularity_per_artist__by_diff_artists__does_not_reduce(self):
        song_by_artist1 = Song(
            "American Pie",
            "spotify:track:1fDsrQ23eTAVFElUMaf38X",
            ["Don McLean"]
        )
        song_by_artist2 = Song(
            "American Pie",
            "spotify:track:1vo6TY0FyLRBTXohxvflhJ",
            ["Madonna"]
        )
        songs = [song_by_artist1, song_by_artist2]
        def pick_most_popular_song__ret_vals(songs):
            songs = list(songs)
            if "Don McLean" in songs[0].artists[0]:
                return song_by_artist1
            elif "Madonna" in songs[0].artists[0]:
                return song_by_artist2
            else:
                raise ValueError(f"Mock did not expect arg: {songs}")
        self.song_scrounger.pick_most_popular_song = MagicMock(
            side_effect = pick_most_popular_song__ret_vals)

        results = self.song_scrounger.reduce_by_popularity_per_artist(songs)

        self.song_scrounger.pick_most_popular_song.assert_any_call(set([song_by_artist1]))
        self.song_scrounger.pick_most_popular_song.assert_any_call(set([song_by_artist2]))
        self.assertEqual(
            get_num_times_called(self.song_scrounger.pick_most_popular_song), 2)
        self.assertEqual(len(results), 2)
        self.assertTrue(song_by_artist1 in results)
        self.assertTrue(song_by_artist2 in results)

    async def test_pick_most_popular_song__two_songs_w_diff_popularity__picks_most_popular(self):
        less_popular_song = Song(
            "some song",
            "some spotify uri",
            ["some artist"],
            popularity=1
        )
        more_popular_song = Song(
            "mock name of more popular version",
            "mock spotify uri of more popular version",
            ["mock artist of more popular version"],
            popularity=2
        )
        mock_songs = [less_popular_song, more_popular_song]

        result = self.song_scrounger.pick_most_popular_song(mock_songs)

        self.assertEqual(result, more_popular_song)

    async def test_pick_most_popular_song__multiple_songs_w_diff_popularity__picks_most_popular(self):
        less_popular_song = Song(
            "some song", "some spotify uri", ["some artist"], popularity=1)
        another_less_popular_song = Song(
            "some song", "some spotify uri", ["some artist"], popularity=25)
        yet_another_less_popular_song = Song(
            "some song", "some spotify uri", ["some artist"], popularity=50)
        more_popular_song = Song(
            "mock name of more popular version",
            "mock spotify uri of more popular version",
            ["mock artist of more popular version"],
            popularity=100
        )
        mock_songs = [
            less_popular_song,
            another_less_popular_song,
            yet_another_less_popular_song,
            more_popular_song
        ]

        result = self.song_scrounger.pick_most_popular_song(mock_songs)

        self.assertEqual(result, more_popular_song)

    async def test_pick_most_popular_song__only_one_song__defaults_to_that_song(self):
        some_song = Song(
            "mock song", "mock spotify uri", ["mock artist"], popularity=1)

        result = self.song_scrounger.pick_most_popular_song([some_song])

        self.assertEqual(result, some_song)

    async def test_pick_most_popular_song__compares_undefined_popularity__raises(self):
        song_w_undefined_popularity = Song(
            "mock song", "mock spotify uri", ["mock artist"], popularity=None)

        with self.assertRaises(ValueError):
            result = self.song_scrounger.pick_most_popular_song([
                song_w_undefined_popularity, song_w_undefined_popularity])

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

    async def test_is_partially_mentioned__tokens_match_separately__counted_as_mention(self):
        # actual example: http://www.dntownsend.com/Site/Rock/3change.htm
        word, text = "Paul Anka", "Paul (\"Put Your Head on My Shoulder\") Anka"

        is_mentioned_in_parts = self.song_scrounger.is_mentioned_in_parts(word, text)

        self.assertTrue(is_mentioned_in_parts)

    # NOTE: Regression Test
    async def test_is_mentioned_in_parts__token_found_as_substr__not_counted_as_mention(self):
        # Bug: 'Stones' matched with 'Stone' and 'allen' with 'challenged'
        word, text = "Allen Stone", "The Rolling Stones challenged the Beatles to a game of foosball"

        is_mentioned_in_parts = self.song_scrounger.is_mentioned_in_parts(word, text)

        self.assertFalse(is_mentioned_in_parts)

    async def test_is_mentioned_as_full_str__mentioned_in_diff_casing__ignores_occurrence(self):
        word, text = "HELLO", "Hello"

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertFalse(is_mentioned)

    async def test_is_mentioned_as_full_str__mentioned_between_spaces__finds_occurrence(self):
        word, text = "The Rolling Stones", "... The Rolling Stones ..."

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned_as_full_str__mentioned_at_end__finds_occurrence(self):
        word, text = "The Rolling Stones", "..by The Rolling Stones"

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned_as_full_str__mentioned_at_beginning__finds_occurrence(self):
        word, text = "The Rolling Stones", "The Rolling Stones played.."

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertTrue(is_mentioned)

    async def test_is_mentioned_as_full_str__mentioned_between_punctuation__finds_occurrence(self):
        word = "The Rolling Stones"
        text_period_comma = ".The Rolling Stones,"
        text_quote_apostrophe = "\"The Rolling Stones's"

        is_mentioned_period_comma = self.song_scrounger.is_mentioned_as_full_str(
            word, text_period_comma)
        is_mentioned_quote_apostrophe = self.song_scrounger.is_mentioned_as_full_str(
            word, text_quote_apostrophe)

        self.assertTrue(is_mentioned_period_comma)
        self.assertTrue(is_mentioned_quote_apostrophe)

    async def test_is_mentioned_as_full_str__mentioned_as_substr__ignores_occurrence(self):
        word, text = "allen", "Challenged"

        is_mentioned = self.song_scrounger.is_mentioned_as_full_str(word, text)

        self.assertFalse(is_mentioned)


    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="When Don McLean recorded \"American Pie\"")
    async def test_find_songs__mocked_spotify_client__song_w_single_artist(self, mock_read_file_contents):
        self.mock_spotify_client.find_track.return_value = [
            mock_spotify_track_factory(
                name="American Pie",
                artists=[mock_spotify_artist_factory(name="Don McLean")],
                uri="spotify:track:1fDsrQ23eTAVFElUMaf38X",
                popularity=None
            ),
        ]

        results = await self.song_scrounger.find_songs("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.mock_spotify_client.find_track.assert_any_call("American Pie")
        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertEqual(len(results["American Pie"]), 1)
        self.assertEqual(
            set([song.spotify_uri for song in results["American Pie"]]),
            set(["spotify:track:1fDsrQ23eTAVFElUMaf38X"]))

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="The song \"Time Is On My Side\" by the Rolling Stones cannot be found verbatim on Spotify")
    async def test_find_songs__spotify_song_title_contains_metadata__song_is_matched_regardless(
        self, mock_read_file_contents):
        self.mock_spotify_client.find_track.return_value = [
            mock_spotify_track_factory(
                name="Time Is On My Side - Mono Version",
                artists=[mock_spotify_artist_factory(name="The Rolling Stones")],
                uri="spotify:track:2jaN6NgXflZTj2z9CWcqaP",
                popularity=None
            ),
            mock_spotify_track_factory(
                name="Time Is On My Side",
                artists=[mock_spotify_artist_factory(name="Irma Thomas")],
                uri="spotify:track:6IpxLzChgCbFSJwso2Q84D",
                popularity=None
            ),
        ]

        results = await self.song_scrounger.find_songs("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.mock_spotify_client.find_track.assert_any_call("Time Is On My Side")
        self.assertEqual(1, len(results.keys()))
        self.assertIn("Time Is On My Side", results.keys())
        self.assertEqual(len(results["Time Is On My Side"]), 1)
        self.assertEqual(
            set([song.spotify_uri for song in results["Time Is On My Side"]]),
            set(["spotify:track:2jaN6NgXflZTj2z9CWcqaP"]))
        self.assertIn("The Rolling Stones", list(results["Time Is On My Side"])[0].artists)

    # NOTE: 'Allen' is a substr of 'challenges', and 'Stone' of 'stoned'
    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="The song \"Satisfaction\" challenges stoned hippies")
    async def test_find_songs__artist_name_appears_as_substr_only__artist_not_matched(
        self, mock_read_file_contents):
        # NOTE: its important that the spotify URIs don't match
        self.mock_spotify_client.find_track.return_value = [
            mock_spotify_track_factory(
                name="Satisfaction",
                artists=[mock_spotify_artist_factory(name="MOCKARTIST")],
                uri="spotify:track:mock1",
                popularity=None
            ),
            mock_spotify_track_factory(
                name="Satisfaction",
                artists=[mock_spotify_artist_factory(name="Allen Stone")],
                uri="spotify:track:mock2",
                popularity=None
            ),
        ]

        results = await self.song_scrounger.find_songs("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.mock_spotify_client.find_track.assert_any_call("Satisfaction")
        self.assertEqual(len(results.keys()), 1)
        self.assertEqual(len(results["Satisfaction"]), 2)
        self.assertIn(
            "MOCKARTIST",
            list(results["Satisfaction"])[0].artists + list(results["Satisfaction"])[1].artists
        )
        self.assertIn(
            "Allen Stone",
            list(results["Satisfaction"])[0].artists + list(results["Satisfaction"])[1].artists
        )

    @patch("song_scrounger.song_scrounger.read_file_contents", return_value="\"Mock Song Name\"")
    async def test_find_songs__song_dups_same_artist__returns_most_popular_version_only(
        self, mock_read_file_contents):
        self.mock_spotify_client.find_track.return_value = [
            mock_spotify_track_factory(
                name="Mock Song Name",
                artists=[mock_spotify_artist_factory(name="MOCKARTIST")],
                uri="spotify:track:mock1",
                popularity=1
            ),
            mock_spotify_track_factory(
                name="Mock Song Name",
                artists=[mock_spotify_artist_factory(name="MOCKARTIST")],
                uri="spotify:track:mock2",
                popularity=50
            ),
            mock_spotify_track_factory(
                name="Mock Song Name",
                artists=[mock_spotify_artist_factory(name="MOCKARTIST")],
                uri="spotify:track:mock3",
                popularity=100
            )
        ]

        results = await self.song_scrounger.find_songs("mock file path")

        mock_read_file_contents.assert_called_once_with("mock file path")
        self.mock_spotify_client.find_track.assert_any_call("Mock Song Name")
        self.assertEqual(len(results.keys()), 1)
        self.assertEqual(len(results["Mock Song Name"]), 1)


    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__song_w_single_artist(self):
        input_file_name = "single_artist_mentioned.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertEqual(len(results["American Pie"]), 1)
        self.assertEqual(
            set([song.spotify_uri for song in results["American Pie"]]),
            set(["spotify:track:1fDsrQ23eTAVFElUMaf38X"])
        )

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__two_artists_one_song(self):
        input_file_name = "two_artists_mentioned.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        self.assertEqual(len(results["American Pie"]), 2)
        self.assertEqual(
            set([song.spotify_uri for song in results["American Pie"]]),
            set([
                "spotify:track:1fDsrQ23eTAVFElUMaf38X",
                "spotify:track:4wpuHehFEEpWAlkw3vjH0s"
            ])
        )

    @unittest.skip("Integration tests disabled by default")
    async def test_find_songs__no_artists_filtered__multiple_results_without_duplicate_artists(self):
        input_file_name = "no_artists_mentioned.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(1, len(results.keys()))
        self.assertIn("American Pie", results.keys())
        artist_count = defaultdict(int)
        for song in results["American Pie"]:
            artist_count["-".join(song.artists)] += 1
        for artist_count, count in artist_count.items():
            self.assertEqual(count, 1, f"{artist_count} has {count}")
        self.assertGreater(len(results["American Pie"]), 10)

    @unittest.skip("Skip integration tests by default")
    async def test_find_songs__for_duplicate_songs(self):
        input_file_name = "test_duplicate_songs.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertGreater(len(results["Sorry"]), 1)
        self.assertIsNotNone(list(results["Sorry"])[0])
        self.assertEqual(list(results["Sorry"])[0].name, "Sorry")
        self.assertIn("spotify:track:", list(results["Sorry"])[0].spotify_uri)
        self.assertGreaterEqual(len(list(results["Sorry"])[0].artists), 1)

    @unittest.skip("Skip integration tests by default")
    async def test_find_songs__simple_artist_detection(self):
        input_file_name = "test_simple_artist_detection.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 1)
        song = list(results["Sorry"])[0]
        self.assertIsNotNone(song)
        self.assertEqual(song.name, "Sorry")
        self.assertEqual(song.spotify_uri, "spotify:track:6rAXHPd18PZ6W8m9EectzH")
        self.assertEqual(len(song.artists), 1)
        self.assertEqual(song.artists, ["Nothing But Thieves"])

    @unittest.skip("Skip integration tests by default")
    async def test_find_songs__multi_paragraph_artist_detection(self):
        input_file_name = "test_multiparagraph_artist_detection.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Sorry" in results.keys())
        self.assertEqual(len(results["Sorry"]), 2)
        song_list = list(results["Sorry"])
        self.assertIsNotNone(song_list[0])
        self.assertIsNotNone(song_list[1])
        self.assertEqual(song_list[0].name, "Sorry")
        self.assertEqual(song_list[1].name, "Sorry")
        self.assertIn(
            "spotify:track:6rAXHPd18PZ6W8m9EectzH",
            [song_list[0].spotify_uri, song_list[1].spotify_uri]
        )
        self.assertIn(
            "spotify:track:09CtPGIpYB4BrO8qb1RGsF",
            [song_list[0].spotify_uri, song_list[1].spotify_uri]
        )
        self.assertEqual(len(song_list[0].artists), 1)
        self.assertEqual(len(song_list[1].artists), 1)
        self.assertIn(
            "Nothing But Thieves",
            [song_list[0].artists[0], song_list[1].artists[0]]
        )
        self.assertIn(
            "Justin Bieber",
            [song_list[0].artists[0], song_list[1].artists[0]]
        )

    @unittest.skip("Skip integration tests by default")
    async def test_find_songs__cross_paragraph_artist_detection(self):
        input_file_name = "test_cross_paragraph_artist_detection.txt"

        results = await self._run_find_songs_test(input_file_name)

        self.assertEqual(len(results.keys()), 1)
        self.assertTrue("Socially Awkward" in results.keys())
        self.assertEqual(len(results["Socially Awkward"]), 1)
        song = list(results["Socially Awkward"])[0]
        self.assertIsNotNone(song)
        self.assertEqual(song.name, "Socially Awkward")
        self.assertEqual(song.spotify_uri, "spotify:track:2yE3omg2KMRfFw4ukBlDIJ")
        self.assertEqual(len(song.artists), 1)
        self.assertEqual(song.artists, ["Kiefer"])

    @unittest.skip("Skip integration tests by default")
    async def test_find_songs__real_world_input_example(self):
        input_file_name = "history_rock_n_roll_ch4_snippet.txt"
        expected_songs = [
            "Heartbreaker", "Satisfaction", "(I Can't Get No) Satisfaction",
            "Doo Doo Doo Doo Doo (Heartbreaker)", "Time is On My Side",
            "Livin' Doll", "Halfway to Paradise", "Rock with the Caveman",
            "Rock Island Line", "Doo Doo Doo Doo Doo",
            """Why don't we put that doo-doo stuff in the title
            so the kids will know which one they're buying?"""
        ].sort()


        results = await self._run_find_songs_test(input_file_name)


        self.assertEqual(len(results.keys()), 11)
        self.assertEqual(list(results.keys()).sort(), expected_songs)

        # PROB: Grand Funk Railroad not detected bc it is mentioned as 'Grank Funk'
        self.assertEqual(len(results["Heartbreaker"]), 1)
        self.assertIn("Led Zeppelin", list(results["Heartbreaker"])[0].artists)

        # PROB: Why is there only one hit here, by [ocean jams]? They're not mentioned...
        # (It's ok that it's not detected as a Rolling Stones song)
        self.assertEqual(len(results["Satisfaction"]), 1)

        self.assertEqual(len(results["(I Can't Get No) Satisfaction"]), 1)
        self.assertIn(
            "The Rolling Stones",
            list(results["(I Can't Get No) Satisfaction"])[0].artists
        )

        self.assertEqual(len(results["Time is On My Side"]), 1)
        self.assertIn(
            "The Rolling Stones",
            list(results["Time is On My Side"])[0].artists
        )

        self.assertEqual(len(results["Halfway to Paradise"]), 1)
        self.assertIn(
            "Billy Fury",
            list(results["Halfway to Paradise"])[0].artists
        )

        self.assertEqual(len(results["Rock with the Caveman"]), 1)
        self.assertIn(
            "Tommy Steele",
            list(results["Rock with the Caveman"])[0].artists
        )

        # PROB: Lonnie Donegan is not matched with Lonnie Donegan & His Skiffle Group
        self.assertEqual(len(results["Rock Island Line"]), 11)

        # PROB: Spotify has the song as "Living Doll"
        self.assertEqual(len(results["Livin' Doll"]), 0)

        self.assertEqual(len(results["Doo Doo Doo Doo Doo"]), 0)
        self.assertEqual(
            len(results["""Why don't we put that doo-doo stuff in the title
                so the kids will know which one they're buying?"""]),
            0
        )

    async def _run_find_songs_test(self, input_file_name):
        from song_scrounger.spotify_client import SpotifyClient
        from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token
        from tests import helper

        spotify_client_id, spotify_secret_key = get_spotify_creds()
        spotify_bearer_token = get_spotify_bearer_token()
        spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key, spotify_bearer_token)

        song_scrounger = SongScrounger(spotify_client)
        input_file_path = helper.get_path_to_test_input_file(input_file_name)
        return await song_scrounger.find_songs(input_file_path)
