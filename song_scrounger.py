from document_parser import find_quoted_tokens
from util import read_file_contents

def scrounge_songs(filename):
    tokens = find_quoted_tokens(read_file_contents(filename))

    song_data = [dict(spotify_uri=token) for token in tokens]


    return song_data

def create_playlist(name, spotify_uris):
    # TODO
    print(f"TODO: implement create_playlist for spotify_uris: {spotify_uris}")

def main():
    #spotify_client = SpotifyClient()
    create_playlist(
        "Created by Song Scrounger",
        [song_data.get('spotify_uri') for song_data in scrounge_songs("tests/test.txt")]
    )

if __name__ == "__main__":
    main()