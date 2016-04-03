import unittest

import dbMigrator
from dbMigrator.driver import Driver
from dbMigrator.migrator import DatabaseSource, DatabaseHandler

class FakeDatabaseSource(DatabaseSource):
    """Fake script provider.  See DatabaseSource for notes on class function."""
    def get_db_name_from_nickname(self, nickname):
        return nickname
    def get_connection_hashes(self):
        return { "db1" : { "dbname": "db1", "conn": "1_c" }, "db2" : { "dbname": "db2", "conn": "2_c" } }
    def get_system_connection_hash(self):
        return { "conn": "sys" }
    def get_baseline_schema_files(self, database_name):
        return [('schema.sql', 'schema')]
    def get_code_files(self, database_name):
        return [('code.sql', 'code')]
    def get_migrations_files(self, database_name):
        return [('migration.sql', 'migration')]
    def get_reference_data_files(self, database_name):
        return [('data.sql', 'data')]

class FakeDatabaseHandler(DatabaseHandler):
    """Fake/mock handler.  See DatabaseHandler for notes."""
    def __init__(self):
        # Stores history for checking in test.
        self.hist = []
    def delete_make_new(self, system_connection_hash, database_name):
        self.hist.append("create " + database_name)
    def create_tracking_table(self, connection_hash):
        self.hist.append("create tracking in " + connection_hash["conn"])
    def user_defined_tables_exist(self, connection_hash):
        return False
    def is_in_tracking_table(self, connection_hash, script_name):
        return False
    def record_script_in_tracking_table(self, conn_hash, script_name):
        self.hist.append("recording " + script_name + " in " + conn_hash["conn"])
    def execute(self, conn_hash, sql):
        self.hist.append("executing " + sql + " in " + conn_hash["conn"])

    
class DriverTests(unittest.TestCase):
    """Test driver"""

    longMessage = True

    def setUp(self):
        self.fake_db_handler = FakeDatabaseHandler()
        self.fake_db_source = FakeDatabaseSource()
        self.driver = Driver(self.fake_db_source, self.fake_db_handler)

    def test_throws_if_args_doesnt_contain_a_single_element(self):
        self.assertRaises(Driver.ParsingException, self.driver.parse_args, [])

    def assert_databases_equals(self, expected, additional_args, msg):
        full_args = ["program.py"]  # sys.argv[0] is the program name
        full_args.extend(additional_args)
        self.assertEqual(expected, self.driver.parse_args(full_args).databases, msg)

    def test_uses_default_database_if_one_is_supplied_and_no_db_specified_in_args(self):
        self.driver.default_database = "default"
        self.assert_databases_equals(["default"], [], "default is used if no databases indicated")
        self.assert_databases_equals(["other"], ["other"], "default not used if other db indicated")
        self.assert_databases_equals(["default"], ["default"], "not double default")
        self.assert_databases_equals(["default"], ["-n"], "default used since -n is a parser flag")
        self.assert_databases_equals(["default"], ["-nsmcdu"], "default used since all are parser flags")
        self.assert_databases_equals(["db1", "db2"], ["-nsmcdu", "db1", "db2"], "more dbs")

    def test_no_default_supplied(self):
        self.driver.default_database = ""
        self.assert_databases_equals([], [], "no databases indicated")
        self.assert_databases_equals(["other"], ["other"], "db indicated")
        self.assert_databases_equals([], ["-n"], "-n is a parser flag")
        self.assert_databases_equals([], ["-nsmcdu"], "all are parser flags")
        self.assert_databases_equals(["db1", "db2"], ["-nsmcdu", "db1", "db2"], "more dbs")

    def call_driver_with_args(self, additional_args):
        full_args = ["program.py"]  # sys.argv[0] is the program name
        full_args.extend(additional_args)
        self.driver.main(full_args)

    def assert_db_history_equals(self, expected):
        self.assertEqual(expected, self.fake_db_handler.hist)

    def test_does_nothing_if_no_action_specified(self):
        self.driver.default_database = "db1"
        self.call_driver_with_args(["db1", "db2"])
        self.assert_db_history_equals([])
    
    def test_does_nothing_if_no_default_and_no_databases_specified(self):
        self.driver.default_database = ""
        self.call_driver_with_args(["-n"])
        self.assert_db_history_equals([])

    def test_all_databases_called_if_several_supplied(self):
        self.driver.default_database = ""
        self.call_driver_with_args(["-n", "db1", "db2"])
        self.assert_db_history_equals(['create db1', 'create db2'])

    def test_default_database_called_if_action_supplied(self):
        self.driver.default_database = "default_db"
        self.call_driver_with_args(["-n"])
        self.assert_db_history_equals(['create default_db'])

    def test_many_actions(self):
        self.driver.default_database = ""
        self.call_driver_with_args(["-nmsd", "db1"])
        expected = ['create db1',
                    'executing schema in 1_c',
                    'create tracking in 1_c',
                    'executing migration in 1_c',
                    'recording migration.sql in 1_c',
                    'executing data in 1_c']
        self.assert_db_history_equals(expected)

    def test_upgrade(self):
        self.driver.default_database = ""
        self.call_driver_with_args(["-u", "db1"])
        expected = ['create tracking in 1_c',
                    'executing migration in 1_c',
                    'recording migration.sql in 1_c',
                    'executing code in 1_c',
                    'executing data in 1_c']
        self.assert_db_history_equals(expected)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
