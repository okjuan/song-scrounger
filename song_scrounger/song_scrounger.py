import asyncio
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

    def parse_tracks(self, text):
        """Finds tracks in given text.

        - Removes duplicates: only the first occurrence of each token is kept.
        - Apart from duplicates, preserves order of tokens
        - Strips whitespace and commas from beginning and end of each track name

        Params:
            text (str): text in which to search for track names.

        Returns:
            (str generator): sequence of track names such as "Redbone".
        """
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