import unittest
import sys
import os

sys.path.append(os.path.abspath(sys.path[0]) + '/example/mysql')

print sys.path

import mysql

class MySqlExample_Tests(unittest.TestCase):

    def test_schema_files(self):
        d = mysql.MySqlExample.build_driver()
        d.main(['example.py', '-nsu'])


def main():
    unittest.main()

if __name__ == '__main__':
    main()
