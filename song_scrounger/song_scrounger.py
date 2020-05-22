import asyncio
import sys

from .document_parser import DocumentParser
from .spotify_client import SpotifyClient
from .util import read_file_contents, get_spotify_creds, get_spotify_bearer_token


class SongScrounger:
    def __init__(self, spotify_client):
        self.spotify_client = spotify_client
        self.document_parser = DocumentParser(self.spotify_client)

    async def find_songs(self, input_file_path):
        """Finds spotify songs based on song names in given input file.

        Params:
            input_file_path (str): path to file containing text with song names.

        Returns:
            (dict): key (str) is song name; val (set(str)) is spotify URIs
                of matching songs, empty if no matching artist mentioned.
        """
        text = read_file_contents(input_file_path)
        return await self.document_parser.find_songs(text)