import util

def test_read_file_contents():
    contents = util.read_file_contents("test_inputs/test.txt")
    if len(contents) == 19973:
        print("Ok.")
    else:
        print(f"Expected to read 19973 chars but read {len(contents)} chars instead.")


if __name__ == "__main__":
    test_read_file_contents()
