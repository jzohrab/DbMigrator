import unittest
import sys
import os

from .mysql import MySqlExample

class MySqlExample_Tests(unittest.TestCase):

    def test_sanity_check(self):
        d = MySqlExample.build_driver()
        d.is_debug_printing = False
        d.main(['example.py', '-nsu'])


def main():
    unittest.main()

if __name__ == '__main__':
    main()
