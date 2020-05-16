import unittest

from song_scrounger.document_parser import find_quoted_tokens
from song_scrounger.util import read_file_contents

class TestDocumentParser(unittest.TestCase):
    def test_find_single_token(self):
        self.assertEqual(
            find_quoted_tokens("Should \"Find this\" at least"),
            ["Find this"],
            "Faild to find only token in text.",
        )

    def test_find_tokens(self):
        text = """
            When Don McClean recorded "American Pie" in 1972 he was remembering his own youth and the early innocence of rock 'n' roll fifteen years before; he may not have considered that he was also contributing the most sincere historical treatise ever fashioned on the vast social transition from the 1950s to the 1960s. For the record, "the day the music died" refers to Buddy Holly's February 1959 death in a plane crash in North Dakota that also took the lives of Richie ("La Bamba") Valens and The Big Bopper ("Chantilly Lace"). The rest of "American Pie" describes the major rock stars of the sixties and their publicity-saturated impact on the music scene: the Jester is Bob Dylan, the Sergeants are the Beatles, Satan is Mick Jagger. For 1950s teens who grew up with the phenomenon of primordial rock 'n' roll, the changes of the sixties might have seemed to turn the music into something very different: "We all got up to dance / Oh, but we never got the chance." There's no doubt that
        """
        self.assertEqual(
            set(find_quoted_tokens(text)),
            set(['American Pie', 'the day the music died', 'La Bamba', 'Chantilly Lace', 'American Pie', 'We all got up to dance / Oh, but we never got the chance.']),
            "Failed to find all tokens.",
        )

    def test_find_none(self):
        self.assertEqual(
            find_quoted_tokens("Nothing to see here."),
            [],
            "Should not have found any tokens.",
        )