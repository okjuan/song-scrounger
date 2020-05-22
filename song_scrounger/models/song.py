class Song():
    def __init__(self, name, spotify_uri, artists):
        self.name = name
        self.spotify_uri = spotify_uri
        self.artists = artists

    # TODO: implement __eq__
    # see: https://stackoverflow.com/questions/390250/elegant-ways-to-support-equivalence-equality-in-python-classes