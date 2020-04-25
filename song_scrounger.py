import asyncio
import os

from document_parser import find_quoted_tokens
from spotify_client import SpotifyClient
from util import read_file_contents

async def create_playlist(input_filename, client_id, secret_key):
    spotify_client = SpotifyClient(client_id, secret_key)
    track_names = find_quoted_tokens(read_file_contents(input_filename))
    track_names = map(lambda track_name: track_name.strip(" ,"), track_names)
    tracks = await _get_tracks(track_names, spotify_client)
    print(tracks)

async def _get_tracks(track_names, spotify_client):
    tracks = []
    for track_name in track_names:
        if len(track_name) == 0:
            print(f"WARN: Skipping empty track name.")
            continue

        results = await spotify_client.find_track(track_name)
        track = results[0] if len(results) > 0 else None
        if track is None:
            print(f"ERROR: Could not find song with name '{track_name}'")
            continue

        tracks.append(track)
    return tracks

async def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIFY_SECRET_KEY")
    if client_id is None or secret_key is None:
        raise Exception("Env vars 'SPOTIFY_CLIENT_ID' and 'SPOTIFY_SECRET_KEY' must be set.")

    await create_playlist("tests/test.txt", client_id, secret_key)

if __name__ == "__main__":
    asyncio.run(main())