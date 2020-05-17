import spotify
from spotify.http import HTTPUserClient
from spotify import Client
from spotify.errors import SpotifyException


# TODO: update return types to hide package-specific models
class SpotifyClient:
    """
    Wrapper for Spotify library of choice.
    """
    def __init__(self, client_id, secret_key, bearer_token=None):
        self.client_id = client_id
        self.secret_key = secret_key
        self.bearer_token = bearer_token

    async def find_track(self, track_name, verbatim=True):
        """
        Params:
            track_name (str).
            verbatim (bool), optional: whether to match track name exactly, ignoring case.

        Returns:
            [spotify.Track]: resulting Spotify tracks.
        """
        if len(track_name) == 0:
            raise ValueError("Track name cannot be empty.")

        try:
            # apparently only the async interface supports context management
            async with Client(self.client_id, self.secret_key) as cli:
                results = await cli.search(track_name, types=["track"])
        except SpotifyException as e:
            print("Could not add tracks to playlist with error:", e)
            raise e

        if verbatim:
            return [
                track for track in results.tracks if track.name.lower() == track_name.lower()
            ]
        return results.tracks

    async def create_playlist(self, name):
        """
        Params:
            name (str): name for new playlist.

        Returns:
            (spotify.Playlist).
        """
        if self.bearer_token is None:
            raise ValueError("Cannot create playlist without Bearer Token.")

        http_cli = HTTPUserClient(self.client_id, self.secret_key, self.bearer_token, None)
        data = await http_cli.current_user()
        try:
            async with Client(self.client_id, self.secret_key) as spotify_client:
                user = spotify.User(spotify_client, data, http=http_cli)
                return await user.create_playlist(name)
        except SpotifyException as e:
            print("Could not add tracks to playlist with error:", e)
            raise e
        finally:
            await http_cli.close()

    async def add_tracks(self, playlist, tracks):
        """
        Params:
            playlist : spotify.Playlist, or str of Playlist URI.
            tracks : [spotify.Track], or [str] containing Spotify track URIs.

        Returns:
            (spotify.Playlist): the same one given as param.
        """
        http_cli = HTTPUserClient(self.client_id, self.secret_key, self.bearer_token, None)
        data = await http_cli.current_user()
        try:
            async with Client(self.client_id, self.secret_key) as spotify_client:
                user = spotify.User(spotify_client, data, http=http_cli)
                for track in tracks:
                    await user.add_tracks(playlist, track)
        except SpotifyException as e:
            print("Could not add tracks to playlist with error:", e)
            raise e
        finally:
            await http_cli.close()
        return playlist