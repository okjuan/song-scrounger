MAX_CHARS = 100000000

def read_file_contents(filename):
    with open(filename, "r") as f:
        file_contents = f.read(MAX_CHARS)
        file_too_large = f.read() != ''
    if file_too_large:
        raise Exception(f"File is too large. Exceeded character count: {MAX_CHARS}")
    return file_contents
