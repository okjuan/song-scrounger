import os
import unittest

from song_scrounger import util

class TestUtil(unittest.TestCase):
    @classmethod
    def _get_path_to_test_input_file(cls, name):
        # Relative from repo root
        return os.path.abspath(f"tests/test_inputs/{name}")

    def test_read_file_contents(self):
        input_file = TestUtil._get_path_to_test_input_file("test.txt")
        contents = util.read_file_contents(input_file)
        num_chars_read = len(contents)
        self.assertEqual(
            num_chars_read,
            19973,
            f"Expected to read 19973 chars but read {num_chars_read} chars instead.",
        )