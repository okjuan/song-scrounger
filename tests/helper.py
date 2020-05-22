import os

from unittest.mock import Mock


def get_path_to_test_input_file(name):
    # Relative from repo root
    return os.path.abspath(f"tests/test_inputs/{name}")

def get_num_times_called(mock):
    if isinstance(mock, Mock):
        return len(mock.call_args_list)
    return NotImplemented