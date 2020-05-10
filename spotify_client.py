import spotify
from spotify.http import HTTPUserClient
from spotify import Client


class SpotifyClient:
    """
    Wrapper for Spotify library of choice.
    """
    def __init__(self, client_id, secret_key, bearer_token=None):
        self.client_id = client_id
        self.secret_key = secret_key
        self.bearer_token = bearer_token

    async def find_track(self, track_name, verbatim=True):
        if len(track_name) == 0:
            raise ValueError("Track name cannot be empty.")

        # apparently only the async interface supports context management
        async with Client(self.client_id, self.secret_key) as cli:
            results = await cli.search(track_name, types=["track"])

        if verbatim:
            return [
                track for track in results.tracks if track.name.lower() == track_name.lower()
            ]
        return results.tracks

    async def create_playlist(self, name, tracks=[]):
        if self.bearer_token is None:
            raise ValueError("Cannot create playlist without Bearer Token.")

        async with Client(self.client_id, self.secret_key) as spotify_client:
            http_cli = HTTPUserClient(self.client_id, self.secret_key, self.bearer_token, None)
            data = await http_cli.current_user()
            user = spotify.User(spotify_client, data, http=http_cli)
            playlist = await user.create_playlist(name)
            await http_cli.close()
        return playlist