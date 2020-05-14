import asyncio
import os
import util

from spotify_client import SpotifyClient


async def test_find_track_verbatim(spotify_client):
    results = await spotify_client.find_track("Redbone")
    inexact_matches = [
        result for result in results if result.name.lower() != "redbone"
    ]
    if len(inexact_matches) != 0:
        print(f"FAIL: found {len(inexact_matches)} songs that don't match track name exactly.")
        return False
    return True

async def main():
    client_id, secret_key = util.get_spotify_creds()
    client = SpotifyClient(client_id, secret_key)

    test_passed = await test_find_track_verbatim(client)
    if test_passed:
        print("Ok.")
    else:
        print("Test failed.")


if __name__ == "__main__":
    asyncio.run(main())