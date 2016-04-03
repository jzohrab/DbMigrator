import unittest

from .postgres import PostgresExample

class PostgresExample_Tests(unittest.TestCase):

    def test_sanity_check(self):
        d = PostgresExample.build_driver()
        d.is_debug_printing = False
        d.main(['example.py', '-nsu'])


def main():
    unittest.main()

if __name__ == '__main__':
    main()
