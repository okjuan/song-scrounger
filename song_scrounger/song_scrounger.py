import asyncio
import sys

from .document_parser import DocumentParser
from .spotify_client import SpotifyClient
from .util import read_file_contents, get_spotify_creds, get_spotify_bearer_token


class SongScrounger:
    def __init__(self, spotify_client):
        self.spotify_client = spotify_client
        self.document_parser = DocumentParser(self.spotify_client)

    async def create_playlist(self, name, song_names):
        """Creates Spotify playlist.

        Params:
            name (str): name for spotify playlist.
            song_names ([str]): e.g. ["Redbone", "Get You"].
        """
        songs = await self._get_songs(song_names)
        playlist = await self.spotify_client.create_playlist(name)
        return await self.spotify_client.add_tracks(playlist, songs)

    async def _get_songs(self, names):
        songs = []
        for name in names:
            if len(name) == 0:
                print(f"WARN: Skipping empty song name.")
                continue

            results = await self.spotify_client.find_track(name)
            song = results[0] if len(results) > 0 else None
            if song is None:
                print(f"ERROR: Could not find song with name '{name}'")
                continue

            songs.append(song)
        return songs

    def find_songs(self, input_file_path):
        """Finds spotify songs based on song names in given input file.

        - Removes duplicates: only the first occurrence of each token is kept.
        - Apart from duplicates, preserves order of tokens
        - Strips whitespace and commas from beginning and end of each song name

        Params:
            input_file_path (str): path to file containing text with song names.

        Returns:
            (str generator): sequence of song names such as "Redbone".
        """
        text = read_file_contents(input_file_path)
        song_names = self.document_parser.find_quoted_tokens(text)
        song_names = map(lambda song_name: song_name.strip(" ,"), song_names)

        def remove_dups(items):
            seen_already = set()
            for item in items:
                if item not in seen_already:
                    seen_already.add(item)
                    yield item
        unique_song_names = remove_dups(song_names)

        return unique_song_names