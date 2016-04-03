import unittest

import dbMigrator
from dbMigrator.migrator import Migrator
from dbMigrator.migrator import MigrationException
from dbMigrator.migrator import ScriptRunner
from dbMigrator.migrator import QueuedScriptCollection
from dbMigrator.migrator import ScriptRunnerException
from dbMigrator.migrator import DatabaseSource
from fakedatabasehandler import FakeDatabaseHandler



class FakeDatabaseSource(DatabaseSource):
    """Fake script provider.  See DatabaseSource for notes on class function."""

    def __init__(self):
        self.connections = {}
        self.system_connection = "sys"

        # All of these are hashes, of db name to [(script_name, script_content), ...]
        self.baseline_schema = {}
        self.code = {}
        self.migrations = {}
        self.reference_data = {}

    def get_db_name_from_nickname(self, nickname):
        return self.connections[nickname]["dbname"]
    def get_connection_hashes(self):
        return self.connections
    def get_system_connection_hash(self):
        return self.system_connection
    def get_baseline_schema_files(self, database_name):
        return self.baseline_schema[database_name]
    def get_code_files(self, database_name):
        return self.code[database_name]
    def get_migrations_files(self, database_name):
        return self.migrations[database_name]
    def get_reference_data_files(self, database_name):
        return self.reference_data[database_name]


class MigratorTests(unittest.TestCase):
    """High-level functional tests."""

    longMessage = True

    def setUp(self):
        self.fake_db_handler = FakeDatabaseHandler()
        self.fake_db_source = FakeDatabaseSource()

        # In real life, these would be read from an .ini file,
        # or from the file system.
        self.fake_db_source.connections = {
            "1": { "dbname": "db_1", "conn": "db_1" },
            "2": { "dbname": "db_2", "conn": "db_2" }
        }
        self.fake_db_source.baseline_schema = {
            "1": [("a.txt", "a_sql"), ("b.txt", "b_sql")],
            "2": [("c.txt", "c_sql"), ("d.txt", "d_sql")]
        }
        self.fake_db_source.migrations = {
            "1": [("mig1.txt", "mig1_sql"), ("mig2.txt", "mig2_sql")],
            "2": [("mig3.txt", "mig3_sql"), ("mig4.txt", "mig4_sql")]
        }
        self.fake_db_source.code = {
            "1": [("code1.txt", "code1_sql"), ("code2.txt", "code2_sql")],
            "2": [("code3.txt", "code3_sql"), ("code4.txt", "code4_sql")]
        }
        self.fake_db_source.reference_data = {
            "1": [("ref1.txt", "ref1_sql"), ("ref2.txt", "ref2_sql")],
            "2": [("ref3.txt", "ref3_sql"), ("ref4.txt", "ref4_sql")]
        }
        self.migrator = Migrator(self.fake_db_source, self.fake_db_handler)


    def assert_db_history_contains(self, expected, msg):
        r = [x for x in self.fake_db_handler.call_history if x in expected]
        if (len(r) != len(expected)):
            self.assertFalse(True, "Missing expected matches {0}, got {1}".format(expected, r))

    def assert_db_history_does_not_contain(self, unexpected, msg):
        r = [x for x in self.fake_db_handler.call_history if x in unexpected]
        if (len(r) != 0):
            self.assertFalse(True, "Have excess matches {0} in {1}".format(unexpected, r))


    #####################################
    # Creating a new database.

    def test_delete_make_new_creates_empty_database_does_not_track_scripts(self):
        self.migrator.delete_make_new("1")
        expected = ["create db_1"]
        unexpected = ["create db_2", "execute c_sql in db_2", "execute d_sql in db_2", "execute a_sql in db_1", "execute b_sql in db_1"]
        self.assert_db_history_contains(expected, "db_1 run")
        self.assert_db_history_does_not_contain(unexpected, "db_2 not run")

    def test_can_create_multiple_databases(self):
        self.migrator.delete_make_new("1", "2")
        expected = ["create db_1", "create db_2"]
        unexpected = ["execute c_sql in db_2", "execute d_sql in db_2", "execute a_sql in db_1", "execute b_sql in db_1"]
        self.assert_db_history_contains(expected, "db_1 and db_2 run")
        self.assert_db_history_does_not_contain(unexpected, "not tracked")

    #####################################
    # Running baseline script.  More exhaustive testing is not
    # nessary, as that has already been handled by
    # test_scriptrunner.py

    def test_happy_path_can_run_baseline_schema(self):
        self.migrator.delete_make_new("1")
        self.migrator.run_baseline_schema("1")
        expected = ["create db_1", "execute a_sql in db_1", "execute b_sql in db_1"]
        unexpected = ["create db_2", "execute c_sql in db_2", "execute d_sql in db_2"]
        self.assert_db_history_contains(expected, "db_1 run")
        self.assert_db_history_does_not_contain(unexpected, "db_2 not run")

    def test_baseline_cannot_be_run_on_database_that_already_has_tables(self):
        self.fake_db_handler.contains_userdefined_tables = True
        self.assertRaises(MigrationException, self.migrator.run_baseline_schema, "1")


    def test_migrations_are_tracked(self):
        self.migrator.delete_make_new("1")
        self.migrator.run_migrations("1")
        expected = [
            'create db_1',
            'create_track_tbl in db_1',
            'check mig1.txt in db_1',
            'execute mig1_sql in db_1',
            'record mig1.txt in db_1',
            'check mig2.txt in db_1',
            'execute mig2_sql in db_1'
        ]
        self.assert_db_history_contains(expected, "db_1 run")
        unexpected = ["create db_2", "execute c_sql in db_2", "execute d_sql in db_2"]
        self.assert_db_history_does_not_contain(unexpected, "db_2 not run")


    def test_code_runs_are_not_tracked(self):
        self.migrator.delete_make_new("1")
        self.migrator.run_code_definitions("1")
        expected = ['create db_1', 'execute code1_sql in db_1', 'execute code2_sql in db_1']
        self.assert_db_history_contains(expected, "db_1 run")
        unexpected = ["create db_2", "execute c_sql in db_2", "execute d_sql in db_2"]
        self.assert_db_history_does_not_contain(unexpected, "db_2 not run")


    def test_ref_data_runs_are_not_tracked(self):
        self.migrator.delete_make_new("1")
        self.migrator.run_reference_data("1")
        expected = ['create db_1', 'execute ref1_sql in db_1', 'execute ref2_sql in db_1']
        self.assert_db_history_contains(expected, "db_1 run")
        unexpected = ["create db_2", "execute c_sql in db_2", "execute d_sql in db_2"]
        self.assert_db_history_does_not_contain(unexpected, "db_2 not run")


class QueuedScriptCollection_Tests(unittest.TestCase):

    longMessage = True

    def setUp(self):
        self.q = QueuedScriptCollection()
        pass

    def assert_sorted_data_equals(self, expected):
        d = self.q.get_sorted_scripts()
        self.assertEqual(expected, d, "data")

    def test_single_script(self):
        self.q.add_script("a.txt", "1", "content")
        self.assert_sorted_data_equals([("a.txt", "1", "content")])

    def test_no_scripts(self):
        self.assert_sorted_data_equals([])

    def test_multiple_scripts_sorted(self):
        self.q.add_script("a.txt", "1", "content_a")
        self.q.add_script("b.txt", "1", "content_b")
        self.assert_sorted_data_equals([("a.txt", "1", "content_a"), ("b.txt", "1", "content_b")])

    def test_two_scripts_with_same_name_are_further_sorted_by_db_name(self):
        self.q.add_script("a.txt", "2", "content_b")
        self.q.add_script("a.txt", "1", "content_a")
        self.assert_sorted_data_equals([("a.txt", "1", "content_a"), ("a.txt", "2", "content_b")])

    def test_cannot_add_the_same_script_for_the_same_db_twice(self):
        self.q.add_script("a.txt", "1", "content_b")
        self.assertRaises(ScriptRunnerException, self.q.add_script, "a.txt", "1", "content_b")

    def test_many_scripts_many_databases(self):
        self.q.add_script("a.txt", "2", "a_2")
        self.q.add_script("c.txt", "1", "c_1")
        self.q.add_script("a.txt", "1", "a_1")
        self.q.add_script("b.txt", "2", "b_2")
        self.q.add_script("b.txt", "1", "b_1")
        self.q.add_script("a.txt", "3", "a_3")

        self.assert_sorted_data_equals(
            [("a.txt", "1", "a_1"),
             ("a.txt", "2", "a_2"),
             ("a.txt", "3", "a_3"),
             ("b.txt", "1", "b_1"),
             ("b.txt", "2", "b_2"),
             ("c.txt", "1", "c_1")])

    def test_script_name_cannot_exceed_255_chars(self):
        self.q.add_script("x" * 255, "1", "255 ok")
        self.assertRaises(ScriptRunnerException, self.q.add_script, "x" * 256, "1", "256 bad")


class ScriptRunnerTests_Base(unittest.TestCase):

    longMessage = True

    def setUp(self):
        self.fake_db_handler = FakeDatabaseHandler()
        self.runner = self.create_script_runner()
        self.runner.is_debug_printing = False

    # Helper methods

    def create_script_runner(self):
        conn_hashes = { "1": { "dbname": "1", "conn": "1_c"}, "2": { "dbname": "2", "conn": "2_c" } }
        return ScriptRunner(conn_hashes, self.fake_db_handler)

    def assert_db_exec_equals(self, expected, msg):
        hist = self.fake_db_handler.get_history()
        if (hist != expected):
            print
            print expected
            print hist
        self.assertEqual("\n" + expected, "\n" + self.fake_db_handler.get_history(), msg)

    # Tests

    def test_runner_throws_if_missing_connection_hash(self):
        self.assertRaises(ScriptRunnerException, self.runner.add_script, "a", "missing", "sql")

    def test_migration_table_created_if_runner_is_tracking_scripts(self):
        self.runner.add_script("a", "1", "sql")
        self.runner.execute_scripts(True)
        self.assert_db_exec_equals("create_track_tbl in 1_c; check a in 1_c; execute sql in 1_c; record a in 1_c", "hist")

    def test_migration_table_not_created_if_runner_is_NOT_tracking_scripts(self):
        self.runner.add_script("a", "1", "sql")
        self.runner.execute_scripts(False)
        self.assert_db_exec_equals("execute sql in 1_c", "hist")

    def test_migration_table_is_only_created_once_on_connection_if_runner_is_tracking_scripts(self):
        self.runner.add_script("a", "1", "sql")
        self.runner.execute_scripts(True)
        self.runner.execute_scripts(True)
        self.assert_db_exec_equals("create_track_tbl in 1_c; check a in 1_c; execute sql in 1_c; record a in 1_c; check a in 1_c", "hist")

    def test_migration_table_is_created_in_every_referenced_database(self):
        self.runner.add_script("a", "1", "sql")
        self.runner.add_script("b", "2", "sql2")
        self.runner.execute_scripts(True)
        expected = "create_track_tbl in 1_c; check a in 1_c; execute sql in 1_c; record a in 1_c; " \
                   "create_track_tbl in 2_c; check b in 2_c; execute sql2 in 2_c; record b in 2_c"
        self.assert_db_exec_equals(expected, "hist")

    def test_tracked_script_is_logged_to_table_when_run(self):
        self.runner.add_script("a", "1", "sql")
        self.runner.execute_scripts(True)
        self.assertTrue("execute sql in 1_c" in self.fake_db_handler.call_history)

    def test_untracked_script_is_NOT_logged_to_table_when_run(self):
        self.runner.add_script("a", "1", "sql")
        self.runner.execute_scripts(False)
        self.assertTrue("record a in 1_c" not in self.fake_db_handler.call_history)

    def test_tracked_script_is_run_once_to_table_when_run_many_times(self):
        self.runner.add_script("a", "1", "sql")
        self.runner.execute_scripts(True)
        self.runner.execute_scripts(True)
        self.runner.execute_scripts(True)
        r = [x for x in self.fake_db_handler.call_history if x == "check a in 1_c"]
        self.assertEqual(3, len(r), "checked three times")
        r = [x for x in self.fake_db_handler.call_history if x == "record a in 1_c"]
        self.assertEqual(1, len(r), "only recorded once")

    def test_untracked_script_can_be_run_many_times(self):
        self.runner.add_script("a", "1", "sql")
        self.runner.execute_scripts(False)
        self.runner.execute_scripts(False)
        self.runner.execute_scripts(False)
        r = [x for x in self.fake_db_handler.call_history if x == "check a in 1_c"]
        self.assertEqual(0, len(r), "not checked")
        r = [x for x in self.fake_db_handler.call_history if x == "execute sql in 1_c"]
        self.assertEqual(3, len(r), "ran three times")

    def test_tracked_script_is_not_rerun_if_its_content_changed(self):
        self.runner.add_script("a", "1", "sql")
        self.runner.execute_scripts(True)
        self.runner.clear_all_scripts()
        self.runner.add_script("a", "1", "changed_sql")
        r = [x for x in self.fake_db_handler.call_history if x == "execute changed_sql in 1_c"]
        self.assertEqual(0, len(r), "script with same name not re-run")

    def test_can_run_scripts_in_several_databases(self):
        self.runner.add_script("a", "1", "aaa")
        self.runner.add_script("b", "2", "bbb")
        self.runner.execute_scripts(True)
        r = [x for x in self.fake_db_handler.call_history if x in ["execute aaa in 1_c", "execute bbb in 2_c"]]
        self.assertEqual(2, len(r), "both run")


    def test_can_have_many_scripts(self):
        self.runner.add_script("a", "1", "aaa")
        self.runner.add_script("b", "1", "bbb")
        self.runner.add_script("a2", "2", "aaa")
        self.runner.add_script("b2", "2", "bbb")
        self.runner.execute_scripts(True)

        expected = [
            "execute aaa in 1_c",
            "execute bbb in 1_c",
            "execute aaa in 2_c",
            "execute bbb in 2_c"
        ]
        r = [x for x in self.fake_db_handler.call_history if x in expected]
        self.assertEqual(4, len(r), "all run")


    def test_script_can_be_composed_of_several_batches(self):
        sql = "sql; sql"
        self.runner.add_script("a", "1", "sql; sql")
        self.runner.execute_scripts(True)
        r = [x for x in self.fake_db_handler.call_history if x == "execute sql; sql in 1_c"]
        self.assertEqual(1, len(r), "both run")

    def test_bad_migration_file_stops_all_subsequent_migrations(self):
        self.runner.add_script("a", "1", "aaa")
        self.runner.add_script("b", "1", "bbb")
        self.runner.add_script("bad_file", "2", "some_bad_sql")
        self.runner.add_script("b2", "2", "bbb")
        self.fake_db_handler.simulate_exception_on("some_bad_sql")
        self.assertRaises(Exception, self.runner.execute_scripts, True)
        expected = [
            "execute aaa in 1_c",
            "execute bbb in 1_c"
        ]
        r = [x for x in self.fake_db_handler.call_history if x in expected]
        self.assertEqual(len(expected), len(r), "all run")


def main():
    unittest.main()

if __name__ == '__main__':
    main()
