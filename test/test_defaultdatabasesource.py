import unittest
import sys
import os
import inspect

import dbMigrator
from dbMigrator.defaultdatabasesource import DefaultDatabaseSource

class DefaultDatabaseSource_Tests(unittest.TestCase):

    longMessage = True

    def setUp(self):
        d = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        inifile = os.path.join(d, 'test_postgres_db.ini')
        rootdir = os.path.join(d, 'test_defaultdatabasesource_scripts')
        if not os.path.exists(inifile):
            raise Exception("Missing ini file at " + inifile)
        self.dds = DefaultDatabaseSource(inifile, rootdir)

    def assertReturnsFiles(self, expected_files, ret, msg):
        expected_files = sorted(expected_files)
        files = sorted([x[0] for x in ret])
        self.assertEqual(expected_files, files, msg)

    def test_schema_files(self):
        self.assertReturnsFiles(["Db.sql"], self.dds.get_baseline_schema_files("db_files"), "baseline")
        self.assertReturnsFiles(["10_vX.sql"], self.dds.get_code_files("db_files"), "code")
        self.assertReturnsFiles(["20130427_add_a_size.sql", "20130428_create_Widget.sql"], self.dds.get_migrations_files("db_files"), "migrations")
        self.assertReturnsFiles(["bootstrap_data.sql"], self.dds.get_reference_data_files("db_files"), "data")

    def test_connections(self):
        c = self.dds.get_system_connection_hash()
        self.assertTrue(c is not None, "have system connection")
        c = self.dds.get_connection_hash("t1")
        self.assertTrue(c is not None, "have db connection")
        self.assertTrue(len(c.keys()) > 0, "have db connection hash components")

def main():
    unittest.main()

if __name__ == '__main__':
    main()
