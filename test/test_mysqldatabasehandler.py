import logging
import unittest
import sys
import os
import inspect
from configobj import ConfigObj
from warnings import filterwarnings
from warnings import resetwarnings
import MySQLdb

# sys.path.append(os.path.abspath(sys.path[0]) + '/../')
import dbMigrator
from dbMigrator.mysqldatabasehandler import MySqlDatabaseHandler


class MySqlDatabaseHandler_Tests(unittest.TestCase):

    longMessage = True

    def setUp(self):
        d = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        p = os.path.join(d, 'test_mysql_db.ini')
        if not os.path.exists(p):
            raise Exception("Missing ini file at " + p + ", create one using template " + p + ".template")
        self.config = ConfigObj(p)

        self.sys_conn_hash = self.config["Server"]
        self.db_1_conn_hash = self.config["Databases"]["t1"]
        self.db_2_conn_hash = self.config["Databases"]["t2"]

        # Convenience data for tests
        self.db_1_name = self.db_1_conn_hash["dbname"]
        self.db_2_name = self.db_2_conn_hash["dbname"]

        # Start each test with clean slate.
        self.exec_sys_sql("drop database if exists {0}".format(self.db_1_name))
        self.exec_sys_sql("drop database if exists {0}".format(self.db_2_name))

        self.handler = MySqlDatabaseHandler()

        # Don't pollute test output.
        logger = logging.getLogger('dbmigrator')
        logger.setLevel(logging.CRITICAL)


    def __get_open_connection(self, connection_hash):
        """Opens a connection to the database."""
        db = MySQLdb.connect(
            host=connection_hash["host"],
            user=connection_hash["user"],
            passwd=connection_hash["password"],
            db=connection_hash["dbname"]
        )
        return db


    def exec_sql_on_conn(self, conn, sql):
        cursor = conn.cursor()
        cursor.execute(sql)
        cursor.close()
        conn.close()
 
    def exec_sys_sql(self, sql):
        """Execute sql on the server (eg, to create or destroy test db)"""
        conn = self.__get_open_connection(self.sys_conn_hash)
        conn.autocommit(True)

        # MySQLdb prints warnings when using "drop database if exists",
        # these warnings add no value and can be ignored.
        # http://www.nomadjourney.com/2010/04/suppressing-mysqlmysqldb-warning-messages-from-python/
        filterwarnings('ignore', category = MySQLdb.Warning)
        return self.exec_sql_on_conn(conn, sql)
        resetwarnings()

    def exec_sql_get_records(self, conn, sql):
        cursor = conn.cursor()
        cursor.execute(sql)
        r = cursor.fetchall()
        cursor.close()
        conn.close()
        return r

    def exec_sql(self, conn_hash, sql):
        conn = self.__get_open_connection(conn_hash)
        return self.exec_sql_on_conn(conn, sql)

    def database_exists(self, db_name):
        """Returns True if exists, otherwise false"""
        conn = self.__get_open_connection(self.sys_conn_hash)
        conn.autocommit(True)
        sql = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{0}'".format(db_name)
        # print sql
        r = self.exec_sql_get_records(conn, sql)
        return (len(r) == 1)

    def get_recordcount(self, conn_hash, sql):
        conn = self.__get_open_connection(conn_hash)
        r = self.exec_sql_get_records(conn, sql)
        return len(r)

    def assert_recordcount_equals(self, expected, conn_hash, sql, msg):
        self.assertEqual(expected, self.get_recordcount(conn_hash, sql), msg)

    def assert_table_exists_equals(self, conn_hash, table_name, expected, msg):
        """expected should be True or False"""
        db_name = conn_hash["dbname"]
        sql = "select * from information_schema.tables where table_name = '{0}' and table_schema='{1}'".format(table_name, db_name)
        r = self.get_recordcount(conn_hash, sql)
        if (expected):
            self.assertEqual(1, r, "Should exist, " + msg)
        else:
            self.assertEqual(0, r, "Should not exist, " + msg)

    # Tests

    def test_delete_make_new_creates_empty_database(self):
        self.assertFalse(self.database_exists(self.db_1_name), "doesn't exist")
        self.handler.delete_make_new(self.sys_conn_hash, self.db_1_name)
        self.assertTrue(self.database_exists(self.db_1_name), "should exist")

    def test_delete_make_new_deletes_existing_database(self):
        self.assertFalse(self.database_exists(self.db_1_name), "doesn't exist")
        self.exec_sys_sql("create database {0}".format(self.db_1_name))
        self.assertTrue(self.database_exists(self.db_1_name), "should exist")

        sql = "create table dummy (i int)"
        conn = self.__get_open_connection(self.db_1_conn_hash)
        conn.autocommit(True)
        self.exec_sql_on_conn(conn, sql)
        sql = "select * from information_schema.tables where table_name = 'dummy'"
        self.assert_recordcount_equals(1, self.db_1_conn_hash, sql, "table exists")

        self.handler.delete_make_new(self.sys_conn_hash, self.db_1_name)
        self.assertTrue(self.database_exists(self.db_1_name), "still exists, created anew")
        self.assert_recordcount_equals(0, self.db_1_conn_hash, sql, "table doesn't exist, db was deleted")

    def test_can_check_if_database_contains_user_defined_tables(self):
        self.assertFalse(self.database_exists(self.db_1_name), "doesn't exist")
        self.exec_sys_sql("create database {0}".format(self.db_1_name))
        self.assertTrue(self.database_exists(self.db_1_name), "should exist")
        self.assertFalse(self.handler.user_defined_tables_exist(self.db_1_conn_hash), "Table doesn't exist yet")
        sql = "create table dummy (i int)"
        conn = self.__get_open_connection(self.db_1_conn_hash)
        conn.autocommit(True)
        self.exec_sql_on_conn(conn, sql)
        self.assertTrue(self.handler.user_defined_tables_exist(self.db_1_conn_hash), "Table exists")

    def test_can_create_tracking_table(self):
        self.handler.delete_make_new(self.sys_conn_hash, self.db_1_name)
        self.assert_table_exists_equals(self.db_1_conn_hash, "__schema_migrations", False, "not created yet")
        self.handler.create_tracking_table(self.db_1_conn_hash)
        self.assert_table_exists_equals(self.db_1_conn_hash, "__schema_migrations", True, "created")


    def test_can_track_scripts(self):
        self.handler.delete_make_new(self.sys_conn_hash, self.db_1_name)
        self.handler.create_tracking_table(self.db_1_conn_hash)
        self.assertFalse(self.handler.is_in_tracking_table(self.db_1_conn_hash, "a.txt"), "Not run yet")
        self.handler.record_script_in_tracking_table(self.db_1_conn_hash, "a.txt")
        self.assertTrue(self.handler.is_in_tracking_table(self.db_1_conn_hash, "a.txt"), "Has been run")

    def test_can_execute_script(self):
        self.handler.delete_make_new(self.sys_conn_hash, self.db_1_name)
        self.handler.execute(self.db_1_conn_hash, "create table dummy(i int)")
        self.assert_table_exists_equals(self.db_1_conn_hash, "dummy", True, "created")

    def test_can_execute_script_with_semicolons(self):
        self.handler.delete_make_new(self.sys_conn_hash, self.db_1_name)
        self.handler.execute(self.db_1_conn_hash, "create table dummy(i int); create table d2(i int)")
        self.assert_table_exists_equals(self.db_1_conn_hash, "dummy", True, "created")
        self.assert_table_exists_equals(self.db_1_conn_hash, "d2", True, "created d2")

    def test_bad_script_throws(self):
        self.handler.delete_make_new(self.sys_conn_hash, self.db_1_name)
        self.assertRaises(Exception, self.handler.execute, self.db_1_conn_hash, "blah blah")

    def test_bad_script_after_batch_marker_throws(self):
        self.handler.delete_make_new(self.sys_conn_hash, self.db_1_name)
        self.assertRaises(Exception, self.handler.execute, self.db_1_conn_hash, "create table dummy(i int); blah blah")


def main():
    unittest.main()

if __name__ == '__main__':
    main()
