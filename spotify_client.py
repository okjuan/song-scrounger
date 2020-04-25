import spotify

class SpotifyClient:
    """
    Wrapper for Spotify library of choice.
    """
    def __init__(self, client_id, secret_key):
        self.client_id = client_id
        self.secret_key = secret_key

    async def _get_client(self):
        return spotify.Client(self.client_id, self.secret_key)

    async def find_track(self, track_name: str, verbatim=True):
        if len(track_name) == 0:
            raise ValueError("Track name cannot be empty.")

        # apparently only the async interface supports context management
        async with spotify.Client(self.client_id, self.secret_key) as cli:
            results = await cli.search(track_name, types=["track"])

        if verbatim:
            return [
                track for track in results.tracks if track.name.lower() == track_name.lower()
            ]
        return results.tracks