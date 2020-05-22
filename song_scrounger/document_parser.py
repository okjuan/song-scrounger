from .spotify_client import SpotifyClient
from .models.song import Song


class DocumentParser():
    def __init__(self, spotify_client):
        self.spotify_client = spotify_client

    async def find_songs(self, text):
        """Parses given text for songs, matching with artists if mentioned.

        Each song is searched on Spotify. The artists in the search results
        are searched for in the text as well. Any matches are used for
        song disambiguation.

        Params:
            text (str): multi-paragraph page containing song names
                and perhaps some of their artists.

        Returns:
            (dict): key (str) is song name; val ([str]) is spotify URIs
                of matching songs, empty if no matching artist mentioned.
        """
        results = {}
        paragraphs = self._get_paragraphs(text)
        for paragraph in paragraphs:
            song_names = self.find_quoted_tokens(paragraph)
            for song_name in song_names:
                songs = await self.search_spotify(song_name)
                filtered_songs = self.filter_if_any_artists_mentioned(songs, text)
                # TODO: what if song_name in results?
                results[song_name] = [song.spotify_uri for song in filtered_songs]
        return results

    def filter_if_any_artists_mentioned(self, songs, text):
        songs_with_mentioned_artists = self.filter_by_mentioned_artist(songs, text)
        if len(songs_with_mentioned_artists) == 0:
            return set(songs)
        return songs_with_mentioned_artists

    def filter_by_mentioned_artist(self, songs, text):
        songs_whose_artists_are_mentioned = set()
        for song in songs:
            for artist in song.artists:
                if self.is_mentioned(artist, text):
                    songs_whose_artists_are_mentioned.add(song)
        return songs_whose_artists_are_mentioned

    async def search_spotify(self, song):
        """
        Params:
            song (str): e.g. "Sorry".

        Returns:
            songs ([Song]).
        """
        songs = []
        tracks = await self.spotify_client.find_track(song)
        for track in tracks:
            for artist in track.artists:
                songs.append(Song(
                    track.name,
                    track.uri,
                    [artist.name for artist in track.artists]
                ))
        return songs

    def is_mentioned(self, word, text):
        """True iff text contains word, ignoring case.

        Params:
            word (str): e.g. "Hello".
            text (str): e.g. "Hello dear".
        """
        word = word.lower()
        text = text.lower()
        return text.find(word) != -1

    def _get_paragraphs(self, text):
        "Returns non-empty paragraphs with one or more non-whitespace characters."
        paragraphs = text.split("\n")
        return [p for p in paragraphs if len(p.strip(" ")) > 0]

    def find_quoted_tokens(self, text):
        """Retrieves all quoted strings in the order they occur in the given text.
        Params:
            text (str).

        Returns:
            tokens (list): strings found between quotes.

        Notes:
            - Ignores trailing quote if quotes are unbalanced
            - Skips empty tokens
        """
        if len(text) == 0:
            return []

        tokens = []
        while len(text) > 0:
            quoted_token_indices = self._find_first_two_quotes(text)
            if quoted_token_indices is None:
                break

            opening_quote_index, closing_quote_index = quoted_token_indices
            if opening_quote_index < closing_quote_index:
                tokens.append(text[opening_quote_index+1:closing_quote_index])

            text = "" if closing_quote_index+1 == len(text) else text[closing_quote_index+1:]
        return tokens

    def _find_first_two_quotes(self, text):
        """Finds indices of first two quotation marks.

        e.g. 'A "quote"' => (2,8)
        e.g. 'No quote' => None
        e.g. 'Not "balanced' => None

        Params:
            text (str): e.g. 'A "quote"'.
        Returns:
            ((int,int)): indices of first two quotes in given text. None if absent or unbalanced.
        """
        if len(text) <= 1:
            return None

        opening_quote_index = text.find("\"")
        if opening_quote_index != -1:
            closing_quote_index = text.find("\"", opening_quote_index+1)
            if closing_quote_index != -1:
                return opening_quote_index, closing_quote_index
        return None