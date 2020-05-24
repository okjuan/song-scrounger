import asyncio
import re
import sys

from collections import defaultdict

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
            (dict): key (str) is song name; val (set(str)) is spotify URIs
                of matching songs, empty if no matching artist mentioned.
        """
        text = read_file_contents(input_file_path)
        results = defaultdict(set)
        paragraphs = self._get_paragraphs(text)
        for paragraph in paragraphs:
            song_names = self.find_song_names(paragraph)
            for song_name in song_names:
                songs = await self.search_spotify(song_name)
                filtered_songs = self.filter_if_any_artists_mentioned(songs, text)
                spotify_uris = set([song.spotify_uri for song in filtered_songs])
                results[song_name] |= spotify_uris
        return results

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
                if self.is_mentioned(artist, text):
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
                [artist.name for artist in track.artists]
            )
            for track in tracks
        }

    def is_mentioned(self, word, text):
        """True iff text contains word, ignoring case.

        Params:
            word (str): e.g. "Hello".
            text (str): e.g. "Hello dear".
        """
        word, text = word.lower(), text.lower()
        if text.find(word) != -1:
            return True

        word_tokens = word.split(" ")
        for token in word_tokens:
            if text.find(token) == -1:
                return False
        return True

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