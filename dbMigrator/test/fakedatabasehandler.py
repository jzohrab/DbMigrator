import unittest
import sys
import os
import re
import inspect
import ConfigParser

sys.path.append(os.path.abspath(sys.path[0]) + '/../')
from migrator import DatabaseHandler


class FakeDatabaseHandler(DatabaseHandler):
    """Mock database to record interactions.  Records all calls to string"""

    def __init__(self):
        super(self.__class__, self).__init__()
        self.call_history = []
        self.fail_on = []
        self.contains_userdefined_tables = False

    def delete_make_new(self, system_connection_hash, database_name):
        self.call_history.append("create " + database_name)

    def user_defined_tables_exist(self, connection_hash):
        return self.contains_userdefined_tables

    def simulate_exception_on(self, sql):
        self.fail_on.append(sql)

    def create_tracking_table(self, connection_hash):
        self.call_history.append("create_track_tbl in " + connection_hash["conn"])

    def is_in_tracking_table(self, connection_hash, script_name):
        msg = "check " + script_name + " in " + connection_hash["conn"]
        ret = (msg in self.call_history)
        self.call_history.append(msg)
        return ret

    def record_script_in_tracking_table(self, conn_hash, script_name):
        self.call_history.append("record " + script_name + " in " + conn_hash["conn"])

    def execute(self, conn_hash, sql):
        if (sql in self.fail_on):
            raise Exception("bad sql")
        msg = "execute " + sql + " in " + conn_hash["conn"]
        self.call_history.append(msg)

    def get_history(self):
        return "; ".join(self.call_history)

