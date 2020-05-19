import asyncio
import sys

from .document_parser import find_quoted_tokens
from .spotify_client import SpotifyClient
from .util import read_file_contents, get_spotify_creds, get_spotify_bearer_token


class SongScrounger:
    def __init__(self, spotify_client):
        self.spotify_client = spotify_client

    async def create_playlist(self, name, track_names):
        """Creates Spotify playlist.

        Params:
            name (str): name for spotify playlist.
            track_names ([str]): e.g. ["Redbone", "Get You"].
        """
        tracks = await self._get_tracks(track_names)
        playlist = await self.spotify_client.create_playlist(name)
        return await self.spotify_client.add_tracks(playlist, tracks)

    async def _get_tracks(self, names):
        tracks = []
        for name in names:
            if len(name) == 0:
                print(f"WARN: Skipping empty track name.")
                continue

            results = await self.spotify_client.find_track(name)
            track = results[0] if len(results) > 0 else None
            if track is None:
                print(f"ERROR: Could not find song with name '{name}'")
                continue

            tracks.append(track)
        return tracks

    def parse_tracks(self, input_file_path):
        """Finds tracks in given input file.

        - Removes duplicates: only the first occurrence of each token is kept.
        - Apart from duplicates, preserves order of tokens
        - Strips whitespace and commas from beginning and end of each track name

        Params:
            input_file_path (str): path to file containing text with track names.

        Returns:
            (str generator): sequence of track names such as "Redbone".
        """
        text = read_file_contents(input_file_path)
        track_names = find_quoted_tokens(text)
        track_names = map(lambda track_name: track_name.strip(" ,"), track_names)

        def remove_dups(items):
            seen_already = set()
            for item in items:
                if item not in seen_already:
                    seen_already.add(item)
                    yield item
        unique_track_names = remove_dups(track_names)

        return unique_track_names