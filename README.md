# Song Scrounger
A little tool for creating Spotify playlists based on song names mentioned in text, like [this webpage](http://www.dntownsend.com/Site/Rock/4unrest.htm).

```python
import asyncio

from song_scrounger.song_scrounger import SongScrounger
from song_scrounger.spotify_client import SpotifyClient
from song_scrounger.util import get_spotify_creds, get_spotify_bearer_token

async def main():
    spotify_client_id, spotify_secret_key = get_spotify_creds()
    spotify_bearer_token = get_spotify_bearer_token()
    spotify_client = SpotifyClient(spotify_client_id, spotify_secret_key, spotify_bearer_token)

    song_scrounger = SongScrounger(spotify_client)
    # assuming it is in the current working directory
    input_file_path = "input_file.txt"
    results = await song_scrounger.find_songs(input_file_path)

    # SongScrounger.find_songs() returns a list of hits for each song found in the input file
    # - e.g. assuming "American Pie" is mentioned in the input file results["American Pie"]
    #       will contain a list of 'Song' objects, each by a different artist
    all_spotify_uris = []
    for song_name, songs in results.items():
        all_spotify_uris.extend([song.spotify_uri for song in songs])

    playlist_name = "My New Playlist Created by Song Scrounger"
    await spotify_client.create_playlist(playlist_name, all_spotify_uris)


if __name__ == "__main__":
    asyncio.run(main())
```

![Spotify Playlist](https://github.com/okjuan/song-scrounger/raw/master/imgs/spotify_playlist_screenshot.png)

Assuming you have:
1. Created a file in the same directory called `input_file.txt` (see example below)
2. Created a Spotify Developer account and a Spotify Application to get a authentication credentials (client ID and a secret key).
3. Retrieved a Bearer Token with permissions to create playlists on your account.
4. Set the environment variables `SPOTIFY_CLIENT_ID`, `SPOTIFY_SECRET_KEY`, and `SPOTIFY_BEARER_TOKEN`.

## Example Input File
The contents of `input_file.txt` might look like:
> Does anybody remember Rock 'n' Roll? Rock music? You know, "be-bop-a-lula," and "my baby love," and "psycho killer, qu'est-ce que c'est"? Remember when it was rebellious to crank your bedroom stereo (or phonograph) to maximum on a Hendrix or Black Sabbath tune? How about standing around at a High School dance, making fun of the band as it tried to play a Stones or U2 song, while quietly dreading the moment when the inevitable slow dance number would begin? Was it "Loving You" by Elvis this time? Or was that another era, somebody else's life?

## Creating a Spotify Developer App
You'll need:
* Spotify (Premium) account
* Spotify Developer app
  * sign up at [Spotify for Developers](https://developer.spotify.com/)
  * create a new app to get client ID and secret key

Then you can take these steps to set up authentication for use by `song_scrounger`:
* Add the following **redirect URI** for your app: `https://localhost:5000`
* Set environment variables `SPOTIFY_CLIENT_ID` and `SPOTIFY_SECRET_KEY` with your credentials
  * e.g. `export SPOTIFY_SECRET_KEY="your-secret-key"`
* Get a bearer token:
  * Navigate to the following URL, with your client ID replaced: `https://accounts.spotify.com/en/authorize?client_id=<your-client-id>&redirect_uri=https:%2F%2Flocalhost:5000&scope=streaming,user-read-playback-state,user-read-email,user-read-private,playlist-modify-public&response_type=token&show_dialog=true`
  * Click **Agree**
  * You'll be redirected to a URL that looks like: `https://localhost:5000/#access_token=BQBjyGh4htNbiDcPrS9YpsIks9qfVQRr1cIJcWdeqVw4rVbU5XgcHVe74BJfU3jOuU-OyX7ssgQCLflbwoMpWt_uWE-Nu8VV5u4AcqBrRoZ1659H4Bb28GK-dgXKzMXZzEV07_UKAIH2Rhq5IS7m8AlehLbp_aoxtTTelUr-lwkZ6iWUNrHXeSK5Gc89nFxWYG4&token_type=Bearer&expires_in=3600`
  * Copy the value of `access_token`
 * Set environment variable `SPOTIFY_BEARER_TOKEN` with your new bearer token, which should be good for 1 hour