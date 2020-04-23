import util

def test_read_file_contents():
    contents = util.read_file_contents("test.txt")
    print(f"Read file:\n{contents}")


if __name__ == "__main__":
    test_read_file_contents()
