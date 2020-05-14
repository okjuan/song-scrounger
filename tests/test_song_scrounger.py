import asyncio
import os
import random
import util
from song_scrounger import SongScrounger


class TestSongScrounger:
    def __init__(self, client_id, secret_key, bearer_token=None):
        self.song_scrounger = SongScrounger(client_id, secret_key, bearer_token)

    async def test_create_playlist(self):
        name = f"Song Scrounger {random.randint(0,10000)}"
        playlist = await self.song_scrounger.create_playlist("test_inputs/test_mini.txt", name)
        print("Got playlist: ", playlist)

    async def test_get_tracks(self):
        tracks = await self.song_scrounger._get_tracks(["Redbone"])
        print("Tracks: ", tracks)

async def main():
    client_id, secret_key = util.get_spotify_creds()
    tests = TestSongScrounger(client_id, secret_key)
    await tests.test_get_tracks()

    bearer_token = util.get_spotify_bearer_token()
    tests = TestSongScrounger(client_id, secret_key, bearer_token)
    await tests.test_create_playlist()


if __name__ == "__main__":
    asyncio.run(main())