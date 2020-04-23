import document_parser

def test_find_quoted_tokens():
    test_cases = [
        {
            "input": "Should \"Find this\" and \"also this\"",
            "expected": ['Find this', 'also this'],
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
    print(f"FAIL:\n\texpected: '{expected}'\n\tresult: '{result}'\n\tinput: '{test_in}'")

def run_tests():
    total, failures = test_find_quoted_tokens()
    if failures > 0:
        print(f"FAILURES: {failures} total")
    else:
        print("Ok.")
    print(f"Ran {total} test(s).")


if __name__ == "__main__":
    run_tests()
