import asyncio
import re
import sys

from collections import defaultdict
from functools import reduce

from .models.song import Song
from .spotify_client import SpotifyClient
from .util import read_file_contents, get_spotify_creds, get_spotify_bearer_token


class SongScrounger:
    def __init__(self, spotify_client):
        self.spotify_client = spotify_client

    async def find_songs(self, input_file_path):
        """Parses given text for songs, matching with artists if mentioned.

        Each song is searched on Spotify. The artists in the search results
        are searched for in the text as well. Any matches are used for
        song disambiguation.

        Params:
            input_file_path (str): path to text file containing 1 or more
                paragraphs containing song names & perhaps some of their artists.

        Returns:
            (dict): key (str) is song name; val (set(Song)) of matching songs.
        """
        text = read_file_contents(input_file_path)
        results = defaultdict(set)
        paragraphs = self._get_paragraphs(text)
        for paragraph in paragraphs:
            song_names = self.find_song_names(paragraph)
            for song_name in song_names:
                songs = await self.search_spotify(song_name)
                songs = self.filter_if_any_artists_mentioned(songs, text)
                songs = self.reduce_by_popularity_per_artist(songs)
                results[song_name] = self.set_union(results[song_name], songs)
        return results

    def set_union(self, song_set_A, song_set_B):
        spotify_uris_seen_already, union = set(), set()
        for song in song_set_A | song_set_B:
            if song.spotify_uri not in spotify_uris_seen_already:
                union.add(song)
                spotify_uris_seen_already.add(song.spotify_uri)
        return union

    def filter_if_any_artists_mentioned(self, songs, text):
        """
        Params:
            songs (set(Song)).
            text (str).

        Return:
            (set(Song)).
        """
        songs_with_mentioned_artists = self.filter_by_mentioned_artist(songs, text)
        if len(songs_with_mentioned_artists) == 0:
            return set(songs)
        return songs_with_mentioned_artists

    def filter_by_mentioned_artist(self, songs, text):
        """Returns only songs whose artist(s) is/are mentioned in the text.
        Params:
            songs (set(Song)).
            text (str).

        Return:
            (set(Song)).
        """
        songs_whose_artists_are_mentioned = set()
        for song in songs:
            for artist in song.artists:
                if self.is_mentioned(artist, text) or self.is_mentioned_in_parts(artist, text):
                    songs_whose_artists_are_mentioned.add(song)
        return songs_whose_artists_are_mentioned

    async def search_spotify(self, song_name):
        """
        Params:
            song_name (str): e.g. "Sorry".

        Returns:
            (set(Song)).
        """
        tracks = await self.spotify_client.find_track(song_name)
        return {
            Song(
                track.name,
                track.uri,
                [artist.name for artist in track.artists],
                track.popularity
            )
            for track in tracks
        }

    def reduce_by_popularity_per_artist(self, songs):
        cache_key_from_artists = lambda artists: "-".join(artists)
        by_same_artist = defaultdict(set)
        for song in songs:
            by_same_artist[cache_key_from_artists(song.artists)].add(song)
        return set([
            self.pick_most_popular_song(songs_grouped_by_artist)
            for _, songs_grouped_by_artist in by_same_artist.items()
        ])

    def pick_most_popular_song(self, songs):
        def pick_more_popular_song(song1, song2):
            if song1.popularity is None:
                raise ValueError(f"{song1.name}'s popularity is None")
            elif song2.popularity is None:
                raise ValueError(f"{song2.name}'s popularity is None")
            return song1 if song1.popularity >= song2.popularity else song2
        return reduce(pick_more_popular_song, songs)

    def is_mentioned(self, word, text):
        """True iff text contains word, ignoring case.

        Params:
            word (str): e.g. "Hello".
            text (str): e.g. "Hello dear".
        """
        word, text = word.lower(), text.lower()
        return self.is_mentioned_as_full_str(word, text)

    def is_mentioned_in_parts(self, word, text):
        word, text = word.lower(), text.lower()
        word_tokens = word.split(" ")
        for token in word_tokens:
            if not self.is_mentioned_as_full_str(token, text):
                return False
        return True

    def is_mentioned_as_full_str(self, word, text):
        """Returns True iff 'word' occurs in 'text' but not as a substring of another word.

        Case-sensitive. Can be made case-insensitive by lowering args before calling.

        Params:
            word (str): e.g. "Hello".
            text (str): e.g. "Hello, how are you?".
        """
        return len(re.findall(f"(^|[^a-zA-Z]){word}([^a-zA-Z]|$)", text)) > 0

    def _get_paragraphs(self, text):
        "Returns non-empty paragraphs with one or more non-whitespace characters."
        paragraphs = text.split("\n")
        return [p for p in paragraphs if len(p.strip(" ")) > 0]

    def find_song_names(self, text):
        """Parses song names, removing whitespace and punctuation.

        Params:
            text (str): e.g. "I keep using the example \"Sorry\" by Justin Bieber"
        """
        song_names = self.find_quoted_tokens(text)
        song_names = map(lambda song_name: song_name.strip(" "), song_names)
        return map(lambda song_name: song_name.rstrip(",."), song_names)

    def find_quoted_tokens(self, text):
        """Retrieves all quoted strings in the order they occur in the given text.
        Params:
            text (str).

        Returns:
            tokens (list): strings found between quotes.

        Notes:
            - Ignores trailing quote if quotes are unbalanced
            - Skips empty tokens
        """
        tokens = re.findall("\"([^\"]*)\"", text)
        return [token for token in tokens if len(token.strip(" ")) > 0]