import os


def get_path_to_test_input_file(name):
    # Relative from repo root
    return os.path.abspath(f"tests/test_inputs/{name}")