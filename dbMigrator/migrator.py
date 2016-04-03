import logging
import sys
from abc import ABCMeta, abstractmethod


class MigrationException(Exception):
    """Custom exception"""
    pass


class Migrator:
    """Facade (coordinator) - takes source files from the database_source,
and passes them as needed to the database_handler to execute against
the underlying database."""

    def __init__(self, database_source, database_handler):
        """database_source: a DatabaseSource
database_handler: database-platform-specific implementation of db manipulation routines"""

        logger = logging.getLogger('dbmigrator')
        logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(ch)

        self.database_source = database_source
        self.database_handler = database_handler
        self.is_debug_printing = False


    def delete_make_new(self, *db_nicknames):
        """DELETES THE SPECIFIED DATABASE, and creates a new one.  Note again,
this DELETES THE SPECIFIED DATABASE.  It does not perform any checks
of that database."""
        for db_nickname in db_nicknames:
            db_name = self.database_source.get_db_name_from_nickname(db_nickname)
            if (self.is_debug_printing):
                print "Dropping and recreating {0}".format(db_name)
            self.database_handler.delete_make_new(self.database_source.get_system_connection_hash(), db_name)


    def __build_script_list_and_execute(self, func, db_nicknames, track_scripts):
        """Passes the list of all scripts to be executed to a ScriptRunner,
which in turn executes the scripts."""
        s = ScriptRunner(self.database_source.get_connection_hashes(), self.database_handler)
        s.is_debug_printing = self.is_debug_printing
        for db_nickname in db_nicknames: 
            for tup in func(db_nickname):
                filename, sql = tup
                s.add_script(filename, db_nickname, sql)
        s.execute_scripts(track_scripts)


    def run_baseline_schema(self, *db_nicknames):
        """Runs baseline schema on empty database."""
        for db_nickname in db_nicknames: 
            conn = self.database_source.get_connection_hash(db_nickname)
            if self.database_handler.user_defined_tables_exist(conn):
                raise MigrationException("Can't run baseline script in non-empty database " + db_nickname)

        g = lambda x: self.database_source.get_baseline_schema_files(x)
        self.__build_script_list_and_execute(g, db_nicknames, False)


    def run_migrations(self, *db_nicknames):
        """Runs migrations, tracking them in tracking table."""
        g = lambda x: self.database_source.get_migrations_files(x)
        self.__build_script_list_and_execute(g, db_nicknames, True)

    def run_code_definitions(self, *db_nicknames):
        """Runs code definitions (functions, stored procs, views, etc).  Not tracked in tracking table."""
        g = lambda x: self.database_source.get_code_files(x)
        self.__build_script_list_and_execute(g, db_nicknames, False)

    def run_reference_data(self, *db_nicknames):
        """Runs idempotent reference data files.  Not tracked in tracking table."""
        g = lambda x: self.database_source.get_reference_data_files(x)
        self.__build_script_list_and_execute(g, db_nicknames, False)



class ScriptRunnerException(Exception):
    """Custom exception"""
    pass


class QueuedScriptCollection:
    """Keeps track of scripts to be executed, ensures that there are no duplicates."""

    """Scripts are recorded in a database table, and so their length can't exceed a maximum."""
    MAX_SCRIPT_NAME_LENGTH = 255

    def __init__(self):
        self.scripts = []

    def add_script(self, filename, dbname, sql):
        """Adds script name, db on which it is to be run, and the sql of the script."""
        if (filename.__len__() > QueuedScriptCollection.MAX_SCRIPT_NAME_LENGTH):
            raise ScriptRunnerException("Script name {0} has length {1}, exceeds max length".format(
                filename, filename.__len__(), QueuedScriptCollection.MAX_SCRIPT_NAME_LENGTH))

        matches = [x for x in self.scripts if (x[0] == filename and x[1] == dbname)]
        if len(matches) > 0:
            raise ScriptRunnerException("Already have file {0} for database {1}".format(filename, dbname))

        self.scripts.append( (filename, dbname, sql) )

    def get_sorted_scripts(self):
        """Returns scripts sorted by filename (necessary to ensure correct
execution order).  Additional sorting on dbname is done to
keep sorting deterministic for unit testing only."""
        ret = sorted(self.scripts, key=lambda tup: "{0}, {1}".format(tup[0], tup[1]))
        return ret


class ScriptRunner:
    """Collects and passes a set of scripts in correct order to a
DatabaseHandler, requesting logging if needed."""

    def __init__(self, connection_hashes, database_handler):
        """database_handler: the DatabaseHandler instance that will actually
execute out database-platform-specific scripts."""
        self.is_debug_printing = False
        self.queued_scripts_collection = QueuedScriptCollection()
        self.database_handler = database_handler
        self.tracking_table_created_for_connections = []
        self.connection_hashes = connection_hashes

    def add_script(self, filename, db_nickname, sql):
        """- filename: the name of the script to run.  Will be logged to tracking table if needed.
- db_nickname: database on which script will be run
- sql: the actual sql to run"""
        if not (db_nickname in self.connection_hashes):
            raise ScriptRunnerException("Missing connection hash for " + db_nickname)
        self.queued_scripts_collection.add_script(filename, db_nickname, sql)

    def clear_all_scripts(self):
        """Helper during testing only."""
        self.queued_scripts_collection = QueuedScriptCollection()

    def __get_conn_hash(self, db_nickname):
        """Gets connection hash, or throws nice message."""
        if not (db_nickname in self.connection_hashes):
            raise ScriptRunnerException("Missing connection hash for " + db_nickname)
        return self.connection_hashes[db_nickname]

    def __execute(self, db_nickname, script_name, sql):
        """Runs the sql on the database.  Errors are thrown back to the caller."""
        conn_hash = self.__get_conn_hash(db_nickname)
        if (self.is_debug_printing):
            print "Execute {0} on {1}".format(script_name, db_nickname)
        try:
            self.database_handler.execute(conn_hash, sql)
        except Exception as e:
            # From http://stackoverflow.com/questions/1350671/inner-exception-with-traceback-in-python
            raise ScriptRunnerException("Error executing " + script_name), None, sys.exc_info()[2]

    def __create_tracking_table_in_conn_if_required(self, conn_hash):
        """Creates a migration table in the connection if one hasn't been created before."""
        dbname = conn_hash["dbname"]
        if (dbname in self.tracking_table_created_for_connections):
            pass
        else:
            self.database_handler.create_tracking_table(conn_hash)
            self.tracking_table_created_for_connections.append(dbname)

    def execute_scripts(self, log_to_table = False):
        """Executes all scripts.  Creates a tracking table and logs script
names to this table if needed."""
        for tuple in self.queued_scripts_collection.get_sorted_scripts():
            script_name, db_nickname, sql = tuple
            if (log_to_table == False):
                self.__execute(db_nickname, script_name, sql)
            else:
                c = self.__get_conn_hash(db_nickname)
                self.__create_tracking_table_in_conn_if_required(c)
                if (not self.database_handler.is_in_tracking_table(c, script_name)):
                    self.__execute(db_nickname, script_name, sql)
                    self.database_handler.record_script_in_tracking_table(c, script_name)


class DatabaseSource(object):
    """Interface describing how clients using the Migrator must supply
their database scripts (deltas, etc). Given as an abstract class to
allow for different clients with different directory tree layouts.
Clients following a suggested layout can use the DefaultDatabaseSource
class.

The various *_files methods should return lists of (filename, content)
tuples [(scriptname, sql_contained_in_script), ...]  (eg, [(db.sql,
"create table SomeTable(id int); /* etc. */")]
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_db_name_from_nickname(self, nickname):
        """Databases can be referred to by a shorter alias, but scripts need
the actual database name."""
        pass

    @abstractmethod
    def get_system_connection_hash(self):
        """Returns connection components (db name, user, password, host, etc)
to create/destroy databases."""
        pass

    @abstractmethod
    def get_connection_hashes(self):
        """Returns hash of all connection string component hashes, keyed by db name."""
        # Connection string components are stored in a nested config
        # file structure:
        #
        # ["Databases"][db_name] { "host" => host, "user" => user, "password" => password }
        #
        # Note: exposing this data clears up logging, as this full
        # structure is passed to the ScriptRunner, which gets the
        # connection string at execution time from this hash.  This
        # means that the ScriptRunner can log the database name that
        # it's running the script on, as opposed to the connection
        # string, which is verbose.
        pass

    def get_connection_hash(self, db_name):
        """Convenience method, returns conn hash for a given db."""
        return self.get_connection_hashes()[db_name]

    @abstractmethod
    def get_baseline_schema_files(self, database_name):
        """Returns baseline schema for database."""
        pass

    @abstractmethod
    def get_reference_data_files(self, database_name):
        """Returns reference data for database."""
        pass

    @abstractmethod
    def get_code_files(self, database_name):
        """Returns code (views, functions, stored procs, etc) for database."""
        pass

    @abstractmethod
    def get_migrations_files(self, database_name):
        """Returns migrations for database."""
        pass


class DatabaseHandler(object):
    """Interface describing database operations required for the Migrator.
Subclassed for each different database platform (postgres, mysql, sql
server, etc)."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def delete_make_new(self, system_connection_hash, database_name):
        """DELETES DATABASES, and creates empty new databases."""
        pass

    @abstractmethod
    def create_tracking_table(self, connection_hash):
        """Creates tracking table if needed."""
        pass

    @abstractmethod
    def user_defined_tables_exist(self, connection_hash):
        """Returns true if user-defined tables exist.  Necessary to prevent accidental re-run of schema files."""
        pass

    @abstractmethod
    def is_in_tracking_table(self, connection_hash, script_name):
        """Returns true if script is in tracking table (assumes tbl is present)"""
        pass

    @abstractmethod
    def record_script_in_tracking_table(self, conn_hash, script_name):
        """Records a given migration script in the table created via a call to create_tracking_table."""
        pass

    @abstractmethod
    def execute(self, conn_hash, sql):
        """Executes sql on the database.  Should handle batch separators in
script (eg, ';' for postgres, 'GO' for mssql server)."""
        pass
        
