def find_quoted_tokens(text):
    """Retrieves all quoted strings in the order they occur in the given text.
    Params:
        text (str).

    Returns:
        tokens (list): strings found between quotes.

    Notes:
        - Assumes quotes are balanced
    """
    if len(text) == 0:
        return []

    tokens = []
    while len(text) > 0:
        quoted_text_start = text.find("\"")
        if quoted_text_start == len(text)-1:
            print("WARN: Found unbalanced opening delimiter '\"'")
            break
        elif quoted_text_start == -1:
            break

        quoted_text_end = text.find("\"", quoted_text_start+1)
        if quoted_text_end == -1:
            print("WARN: Found unbalanced opening delimiter '\"'")
            break

        # Don't include empty string
        if quoted_text_start < quoted_text_end:
            tokens.append(text[quoted_text_start+1:quoted_text_end])

        text = "" if quoted_text_end+1 == len(text) else text[quoted_text_end+1:]
    return tokens