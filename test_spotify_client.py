import asyncio
import os

from spotify_client import SpotifyClient


async def test_find_track(spotify_client):
    results = await spotify_client.find_track("Redbone")
    inexact_matches = [
        result for result in results if result.name.lower() != "redbone"
    ]
    if len(inexact_matches) != 0:
        print(f"FAIL: found {len(inexact_matches)} songs that don't match track name exactly.")
    else:
        print("Test passed!")

async def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIFY_SECRET_KEY")
    if client_id is None or secret_key is None:
        raise Exception("Env vars 'SPOTIFY_CLIENT_ID' and 'SPOTIFY_SECRET_KEY' must be set.")

    client = SpotifyClient(client_id, secret_key)

    await test_find_track(client)


if __name__ == "__main__":
    asyncio.run(main())