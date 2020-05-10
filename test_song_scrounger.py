import asyncio
import os
from song_scrounger import SongScrounger


async def test_create_playlist(song_scrounger):
    playlist = await song_scrounger.create_playlist("test_inputs/test_mini.txt")
    print("Got playlist: ", playlist)

async def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIFY_SECRET_KEY")
    bearer_token = os.environ.get("SPOTIFY_BEARER_TOKEN")
    if client_id is None or secret_key is None or bearer_token is None:
        raise Exception("Env vars 'SPOTIFY_CLIENT_ID', 'SPOTIFY_SECRET_KEY', 'SPOTIFY_BEARER_TOKEN' must be set.")

    song_scrounger = SongScrounger(client_id, secret_key, bearer_token)
    await test_create_playlist(song_scrounger)


if __name__ == "__main__":
    asyncio.run(main())