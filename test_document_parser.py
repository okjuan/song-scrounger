import document_parser
from util import read_file_contents

def test_find_quoted_tokens():
    test_cases = [
        {
            "input": "Should \"Find this\" and \"also this\"",
            "expected": ['Find this', 'also this'],
        },
        {
            "input": read_file_contents("test.txt"),
            "expected": ['American Pie', 'the day the music died', 'La Bamba', 'Chantilly Lace', 'American Pie', 'We all got up to dance / Oh, but we never got the chance.', 'Put Your Head on My Shoulder', "Everybody's Somebody's Fool", "I'm Sorry", 'Volare', "Travelin' Man", 'Moody River', 'Take Care of My Baby', 'Venus', 'Venus', 'At the Hop', 'oooh', 'girl groups', 'Wall of Sound,', 'To Know Him is to Love Him', 'Let me be Your Teddy Bear', 'Will You Love Me Tomorrow?', "Tonight's the Night", 'Be My Baby', "He's a Rebel", "My Boyfriend's Back", 'Leader of the Pack', 'He Hit Me (and it felt like a kiss),', "Thank goodness that's over with!", 'inevitable,', "Blowin' in the Wind,", "The Times They are a-Changin'", "yeah, 'the Order is rapidly fadin'!", "Blowin' in the Wind,", "A Hard Rain's A-Gonna Fall,", 'Masters of War,', '', ' Subterranean Homesick Blues,', 'Like a Rolling Stone,', 'Bob Dylan', "Blowin' in the Wind", 'folk', 'folk rock', 'protest', 'Will You Love Me Tomorrow', 'The Conscience of a Generation', 'Yuppies', 'born again', 'We Are The World', 'We Are The World'],
        }
    ]
    failures = 0
    for test in test_cases:
        tokens = document_parser.find_quoted_tokens(test['input'])
        if tokens != test['expected']:
            fail_test(test['input'], test['expected'], tokens)
            failures += 1
    return (len(test_cases), failures)

def fail_test(test_in, expected, result):
    print(f"FAIL:\n\texpected: '{expected}'\n\tresult: '{result}'\n\tinput: '{test_in if len(test_in) < 15 else str(test_in[:15]) + '...'}'")

def run_tests():
    total, failures = test_find_quoted_tokens()
    if failures > 0:
        print(f"FAILURES: {failures} total")
    else:
        print("Ok.")
    print(f"Ran {total} test(s).")


if __name__ == "__main__":
    run_tests()
