class Song():
    def __init__(self, name, spotify_uri, artists, popularity=None):
        """
        Params:
            name (str).
            spotify_uri (str): e.g. "spotify:track:2ZbTw8awL7EFat9Wz1DIHN".
            artists ([str]): e.g. ["Don McLean"].
            popularity (int): 0 <= popularity <= 100, as in Spotify's Web API.
                None if unspecified.
        """
        self.name = name
        self.spotify_uri = spotify_uri
        self.artists = artists
        if popularity is None or (
            isinstance(popularity, int) and popularity <= 100 and popularity >= 0):
            self.popularity = popularity
        else:
            raise ValueError(popularity, "Must be an int in [0,100] range.")
