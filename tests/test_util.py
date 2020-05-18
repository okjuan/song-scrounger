import os
import unittest

from tests import helper

from song_scrounger import util

class TestUtil(unittest.TestCase):
    def test_read_file_contents(self):
        input_file = helper.get_path_to_test_input_file("test.txt")
        contents = util.read_file_contents(input_file)
        num_chars_read = len(contents)
        self.assertEqual(
            num_chars_read,
            19973,
            f"Expected to read 19973 chars but read {num_chars_read} chars instead.",
        )