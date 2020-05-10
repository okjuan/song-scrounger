import asyncio
import os

from document_parser import find_quoted_tokens
from spotify_client import SpotifyClient
from util import read_file_contents


class SongScrounger:
    def __init__(self, client_id, secret_key, bearer_token):
        self.spotify_client = SpotifyClient(client_id, secret_key, bearer_token)

    async def create_playlist(self, input_filename, playlist_name):
        track_names = find_quoted_tokens(read_file_contents(input_filename))
        track_names = map(lambda track_name: track_name.strip(" ,"), track_names)
        tracks = await self._get_tracks(track_names)
        playlist = await self.spotify_client.create_playlist(playlist_name)
        return await self.spotify_client.add_tracks(playlist, tracks)

    async def _get_tracks(self, track_names):
        tracks = []
        for track_name in track_names:
            if len(track_name) == 0:
                print(f"WARN: Skipping empty track name.")
                continue

            results = await self.spotify_client.find_track(track_name)
            track = results[0] if len(results) > 0 else None
            if track is None:
                print(f"ERROR: Could not find song with name '{track_name}'")
                continue

            tracks.append(track)
        return tracks