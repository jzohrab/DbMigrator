import unittest
import sys
import os

sys.path.append(os.path.abspath(sys.path[0]) + '/../examples/postgres')

import postgres

class PostgresExample_Tests(unittest.TestCase):

    def test_sanity_check(self):
        d = postgres.PostgresExample.build_driver()
        d.is_debug_printing = False
        d.main(['example.py', '-nsu'])


def main():
    unittest.main()

if __name__ == '__main__':
    main()
