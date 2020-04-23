def find_quoted_tokens(text):
    """Retrieves all quoted strings.
    Params:
        text (str).

    Returns:
        tokens (list): strings found between quotes.

    Notes:
        - Assumes quotes are balanced
    """
    tokens = []
    while len(text) > 0:
        quoted_text_start = text.find("\"")
        quoted_text_end = text.find("\"", quoted_text_start+1)
        token = text[quoted_text_start+1:quoted_text_end]
        text = text[quoted_text_end+1:]
        tokens.append(token)
    return tokens

