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
            await self._to_song(track)
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
            await self._to_album(
                album,
                await self._get_album_songs(
                    album.name,
                    [x.name for x in album.artists], album.uri
                )
            )
            for album in albums
            if album.name.lower() == album_name.lower() or
                self._strip_album_metadata(album.name).lower() == album_name.lower()
        }

    async def _get_album_songs(self, album_name, artists, album_uri):
        """Finds the songs belonging to a given album.

        Params:
            album_name (str).
            artists ([str]).
            album_uri (str).

        Returns:
            [set(songscrounger.models.album.Album)]: matching Spotify albums.
        """
        try:
            # apparently only the async interface supports context management
            async with Client(self.client_id, self.secret_key) as cli:
                results = await cli.search(
                    self._get_query_str(album=album_name, artists=artists), types=["track"])
        except SpotifyException as e:
            print("Error occurred when searching albums on Spotify:", e)
            raise e

        unordered_songs = [
            (await self._to_song(track), track.track_number)
            for track in results.tracks
            if track.album.uri == album_uri
        ]
        return self._order_album_songs(unordered_songs)

    def _order_album_songs(self, songs_w_number):
        """
        Params:
            songs_w_number ([2-tuple]): 0th position is song name (songscrounger.models.song.Song),
                1st position is its track number (starting with 1) (int).

        Returns:
            ordered_songs ([songscrounger.models.song.Song]): names of songs ordered by their specified position.
        """
        get_tracklist_pos = lambda song_w_number: song_w_number[1]
        return [song for song, pos in sorted(songs_w_number, key=get_tracklist_pos)]

    def _get_query_str(self, album=None, track=None, artists=[]):
        url_encode_spaces = lambda str: str.replace(' ', '%20')
        join_w_AND_condition = lambda strs: url_encode_spaces(' AND ').join(strs)
        return " ".join([
            f"album:{url_encode_spaces(album)}" if album is not None else "",
            f"artist:{join_w_AND_condition([url_encode_spaces(a) for a in artists])}" if artists != [] else "",
            f"track:{url_encode_spaces(track)}" if track is not None else "" if track is not None else "",
        ]).strip()

    async def _to_song(self, track):
        """
        Params:
            track (spotify.models.track.Track).

        Returns:
            (Song).
        """
        return Song(
            track.name,
            track.uri,
            [artist.name for artist in track.artists],
            track.popularity,
            await self._to_album(track.album) if track.album is not None else None
        )

    async def _to_album(self, album, songs=[]):
        """
        Params:
            album (spotify.models.album.Album).
            songs (songscrounger.models.song.Song): optional.

        Returns:
            (Song).
        """
        return Album(
            album.name,
            album.uri,
            [artist.name for artist in album.artists],
            songs,
            album.popularity,
        )

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