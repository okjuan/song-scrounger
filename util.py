import os


MAX_CHARS = 100000000

def read_file_contents(filename):
    with open(filename, "r") as f:
        file_contents = f.read(MAX_CHARS)
        file_too_large = f.read() != ''
    if file_too_large:
        raise Exception(f"File is too large. Exceeded character count: {MAX_CHARS}")
    return file_contents

def get_spotify_creds():
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    secret_key = os.environ.get("SPOTIFY_SECRET_KEY")
    if client_id is None or secret_key is None:
        raise Exception("Env vars 'SPOTIFY_CLIENT_ID' and 'SPOTIFY_SECRET_KEY' must be set.")
    return client_id, secret_key

def get_spotify_bearer_token():
    bearer_token = os.environ.get("SPOTIFY_BEARER_TOKEN")
    if bearer_token is None:
        raise Exception("Env var 'SPOTIFY_BEARER_TOKEN' must be set.")
    return bearer_token