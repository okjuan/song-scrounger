import unittest

from song_scrounger.document_parser import find_quoted_tokens
from song_scrounger.util import read_file_contents

class TestDocumentParser(unittest.TestCase):
    def test_find_single_token(self):
        text = "Should \"Find this\" at least"

        tokens = find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            ["Find this"],
            "Faild to find only token in text.",
        )

    def test_find_tokens(self):
        text = """
            When Don McClean recorded "American Pie" in 1972 he was remembering his own youth and the early innocence of rock 'n' roll fifteen years before; he may not have considered that he was also contributing the most sincere historical treatise ever fashioned on the vast social transition from the 1950s to the 1960s. For the record, "the day the music died" refers to Buddy Holly's February 1959 death in a plane crash in North Dakota that also took the lives of Richie ("La Bamba") Valens and The Big Bopper ("Chantilly Lace"). The rest of "American Pie" describes the major rock stars of the sixties and their publicity-saturated impact on the music scene: the Jester is Bob Dylan, the Sergeants are the Beatles, Satan is Mick Jagger. For 1950s teens who grew up with the phenomenon of primordial rock 'n' roll, the changes of the sixties might have seemed to turn the music into something very different: "We all got up to dance / Oh, but we never got the chance." There's no doubt that
        """

        tokens = find_quoted_tokens(text)

        self.assertEqual(
            set(tokens),
            set(['American Pie', 'the day the music died', 'La Bamba', 'Chantilly Lace', 'American Pie', 'We all got up to dance / Oh, but we never got the chance.']),
            "Failed to find all tokens.",
        )

    def test_find_none(self):
        text = "Nothing to see here."

        tokens = find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            [],
            "Should not have found any tokens.",
        )

    def test_find_quoted_tokens__ignores_unbalanced(self):
        text = "For \" there is no closing quote"

        tokens = find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            [],
            "Should not have found any tokens."
        )

    def test_find_quoted_tokens__ignores_final_unbalanced_quote(self):
        text = "Here's \"a token\" but for \" there is no closing quote"

        tokens = find_quoted_tokens(text)

        self.assertEqual(
            tokens,
            ["a token"],
            "Should not have found any tokens."
        )

    def test_find_quoted_tokens__preserves_order(self):
        text = "\"first token\" and \"second token\""

        tokens = find_quoted_tokens(text)

        self.assertEqual(
            tokens[0],
            "first token",
            "Did not find first token in expected position."
        )
        self.assertEqual(
            tokens[1],
            "second token",
            "Did not find second token in expected position."
        )

    def test_find_quoted_tokens__preserves_dups(self):
        text = "\"repeat token\" again \"repeat token\" again \"repeat token\""

        tokens = find_quoted_tokens(text)

        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0], "repeat token")
        self.assertEqual(tokens[1], "repeat token")
        self.assertEqual(tokens[2], "repeat token")