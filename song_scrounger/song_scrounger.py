import asyncio
import os
import sys

from .document_parser import find_quoted_tokens
from .spotify_client import SpotifyClient
from .util import read_file_contents, get_spotify_creds, get_spotify_bearer_token


class SongScrounger:
    def __init__(self, spotify_client):
        self.spotify_client = spotify_client

    async def create_playlist(self, input_filename, playlist_name):
        file_contents = read_file_contents(input_filename)
        track_names = self.parse_tracks(file_contents)
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

    def parse_tracks(self, corpus):
        """
        Params:
            corpus (str): text in which to search for track names.

        Returns:
            (Iterator of str): sequence of track names e.g. ["Redbone", "Hotline Bling"].
        """
        track_names = find_quoted_tokens(corpus)
        return map(lambda track_name: track_name.strip(" ,"), track_names)

async def main(input_file, playlist_name):
    client_id, secret_key = get_spotify_creds()
    bearer_token = get_spotify_bearer_token()
    song_scrounger = SongScrounger(SpotifyClient(client_id, secret_key, bearer_token))
    await song_scrounger.create_playlist(input_file, playlist_name)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python song_scrounger.py <path-to-input-file> <playlist-name>")
        exit()
    asyncio.run(main(sys.argv[1], sys.argv[2]))