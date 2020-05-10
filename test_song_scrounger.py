import asyncio
import os
import random
from song_scrounger import SongScrounger


class TestSongScrounger:
    def __init__(self, client_id, secret_key, bearer_token):
        self.song_scrounger = SongScrounger(client_id, secret_key, bearer_token)

    async def test_create_playlist(self):
        name = f"Song Scrounger {random.randint(0,10000)}"
        playlist = await self.song_scrounger.create_playlist("test_inputs/test_mini.txt", name)
        print("Got playlist: ", playlist)

    async def test_get_tracks(self):
        tracks = await self.song_scrounger._get_tracks(["Redbone"])
        print("Tracks: ", tracks)

async def main():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIFY_SECRET_KEY")
    bearer_token = os.environ.get("SPOTIFY_BEARER_TOKEN")
    if client_id is None or secret_key is None or bearer_token is None:
        raise Exception("Env vars 'SPOTIFY_CLIENT_ID', 'SPOTIFY_SECRET_KEY', 'SPOTIFY_BEARER_TOKEN' must be set.")

    tests = TestSongScrounger(client_id, secret_key, bearer_token)
    await tests.test_create_playlist()
    await tests.test_get_tracks()


if __name__ == "__main__":
    asyncio.run(main())