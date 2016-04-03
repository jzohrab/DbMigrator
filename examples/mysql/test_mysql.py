import unittest
import sys
import os

# sys.path.append(os.path.abspath(sys.path[0]) + '/../examples/mysql')
# import examples
# import examples
# from examples.mysql import MySqlExample
# from mysql import MySqlExample
# import mysql

# import examples
# import examples.mysql
# from examples.mysql import mysql  # MySqlExample
# from .. import examples
# from examples import mysql
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
