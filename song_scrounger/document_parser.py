class DocumentParser():
    def __init__(self):
        pass

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