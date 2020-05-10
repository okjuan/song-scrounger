# Song Scrounger
A little tool for creating playlists out of songs mentioned in a text file. You can use it to create playlists out of songs mentioned on a web page.

### Repo Instructions
#### Prerequisites
* Python 3
* Pip 3

#### Setup
* clone the repo
* install the dependencies: `pip install -r requirements.txt` or (`dev-requirements.txt` if you want `ipdb` for debugging)

### Usage
#### Disclaimer
This is barely a prototype -- it is naive and crude. However, it works end-to-end for this particular scenario:
- Given a path to a text file, find all quoted songs
    - e.g. if the file contains `"Rolling in the Deep" was the craze of 2010`, then the tool will find `Rolling in the Deep`
- Search each song on Spotify and take the first hit
- Create a new playlist and populate it with all the songs that were found in the previous step

#### Prerequisites
* Spotify (Premium) account
* Spotify Developer app
  * sign up at [Spotify for Developers](https://developer.spotify.com/)
  * create a new app to get client ID and secret key
  * add the following redirect URI for your app: `https://localhost:5000`

#### Set Up Auth
* Set environment variables `SPOTIFY_CLIENT_ID` and `SPOTIFY_SECRET_KEY` with your credentials
  * `export SPOTIFY_SECRET_KEY="your-secret-key"`
* Get a bearer token:
  * Navigate to the following URL, with your client ID replaced: `https://accounts.spotify.com/en/authorize?client_id=<your-client-id>&redirect_uri=https:%2F%2Flocalhost:5000&scope=streaming,user-read-playback-state,user-read-email,user-read-private,playlist-modify-public&response_type=token&show_dialog=true`
  * Click **Agree**
  * You'll be redirected to a URL that looks like: `https://localhost:5000/#access_token=BQBjyGh4htNbiDcPrS9YpsIks9qfVQRr1cIJcWdeqVw4rVbU5XgcHVe74BJfU3jOuU-OyX7ssgQCLflbwoMpWt_uWE-Nu8VV5u4AcqBrRoZ1659H4Bb28GK-dgXKzMXZzEV07_UKAIH2Rhq5IS7m8AlehLbp_aoxtTTelUr-lwkZ6iWUNrHXeSK5Gc89nFxWYG4&token_type=Bearer&expires_in=3600`
  * Copy the value of `access_token`
 * Set environment variable `SPOTIFY_BEARER_TOKEN` with your new bearer token (should be good for 1 hour)

#### Get the Target Text
* Copy a webpage that mentions songs in quotes (e.g. "Rolling in the Deep") and save it to a text file on your computer

#### Run the Script!
* Run the tool: e.g. `python song_scrounger.py <path-to-input-file> <name-of-your-playlist>`
* You should now have a new playlist on your profile containing all the songs found in your input file
