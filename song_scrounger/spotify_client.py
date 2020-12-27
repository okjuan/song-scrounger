import spotify
from spotify.http import HTTPUserClient
from spotify import Client
from spotify.errors import SpotifyException

from .models.song import Song
from .models.album import Album


class SpotifyClient:
    """
    Wrapper for Spotify library of choice.
    """
    def __init__(self, client_id, secret_key, bearer_token=None):
        self.client_id = client_id
        self.secret_key = secret_key
        self.bearer_token = bearer_token

    async def find_song(self, track_name):
        """Finds the given track, ignoring case.
        Params:
            track_name (str).

        Returns:
            (set(songscrounger.models.song.Song)): resulting Spotify tracks.
        """
        if len(track_name) == 0:
            raise ValueError("Track name cannot be empty.")

        try:
            # apparently only the async interface supports context management
            async with Client(self.client_id, self.secret_key) as cli:
                results = await cli.search(track_name, types=["track"])
        except SpotifyException as e:
            print("Error occurred when searching tracks on Spotify:", e)
            raise e

        return {
            Song(
                track.name,
                track.uri,
                [artist.name for artist in track.artists],
                track.popularity,
            )
            for track in results.tracks
            if track.name.lower() == track_name.lower() or
                self._strip_song_metadata(track.name).lower() == track_name.lower()
        }

    async def find_album(self, album_name):
        """Finds the given album, ignoring case.
        Params:
            album_name (str).

        Returns:
            [set(songscrounger.models.album.Album)]: matching Spotify albums.
        """
        if len(album_name) == 0:
            raise ValueError("Album name cannot be empty.")

        try:
            # apparently only the async interface supports context management
            async with Client(self.client_id, self.secret_key) as cli:
                results = await cli.search(album_name, types=["album"])
                albums = await cli.get_albums(*[album.uri for album in results.albums])
        except SpotifyException as e:
            print("Error occurred when searching albums on Spotify:", e)
            raise e

        return {
            Album(
                album.name,
                album.uri,
                [artist.name for artist in album.artists],
                album.popularity,
            )
            for album in albums
            if album.name.lower() == album_name.lower() or
                self._strip_album_metadata(album.name).lower() == album_name.lower()
        }

    def _strip_song_metadata(self, name):
        """
        Assumptions:
            - Everything after '-' is metadata
        """
        name = name.strip()
        if (tokens := name.split("-")) != [name]:
            name = tokens[0].strip()
        return name

    def _strip_album_metadata(self, name):
        """
        Assumptions:
            - Everything after '-' is metadata
            - Parentheses contain metadata depending on where they occur
                - If parentheses occur at the beginning of name, they don't contain metadata
                - Otherwise, they contain metadata
            - If at all, only 1 set of parentheses occurs
            - Parentheses are balanced
        """
        name = name.strip()

        if (tokens := name.split("-")) != [name]:
            name = tokens[0].strip()
        if "(" in name:
            open_paren_idx = name.index("(")
            if open_paren_idx > 0:
                tokens = name.split("(")
                name = tokens[0].strip()
        return name

    async def create_playlist(self, name, spotify_uris):
        """Creates Spotify playlist containing given tracks.

        Params:
            name (str).
            spotify_uris ([str]).
        """
        playlist = await self.create_empty_playlist(name)
        return await self.add_tracks(playlist, spotify_uris)

    async def create_empty_playlist(self, name):
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

    async def add_tracks(self, playlist, spotify_uris):
        """
        Params:
            playlist : spotify.Playlist, or str of Playlist URI.
            spotify_uris ([str]).

        Returns:
            (spotify.Playlist): the same one given as param.
        """
        http_cli = HTTPUserClient(self.client_id, self.secret_key, self.bearer_token, None)
        data = await http_cli.current_user()
        try:
            async with Client(self.client_id, self.secret_key) as spotify_client:
                user = spotify.User(spotify_client, data, http=http_cli)
                await user.add_tracks(playlist, *[uri for uri in spotify_uris])
        except SpotifyException as e:
            print("Could not add tracks to playlist with error:", e)
            raise e
        finally:
            await http_cli.close()
        return playlist