import logging
import MySQLdb
from warnings import filterwarnings
from warnings import resetwarnings

from migrator import DatabaseHandler
logger = logging.getLogger('dbmigrator')

class MySqlDatabaseHandler(DatabaseHandler):
    """MySql-specific implementation of the DatabaseHandler."""

    def __get_open_connection(self, connection_hash):
        """Opens a connection to the database."""
        db = MySQLdb.connect(
            host=connection_hash["host"],
            user=connection_hash["user"],
            passwd=connection_hash["password"],
            db=connection_hash["dbname"]
        )
        return db

    def delete_make_new(self, system_connection_hash, database_name):
        """Creates new database, deletes the old."""
        # MySQLdb prints warnings when using "drop database if exists",
        # these warnings add no value and can be ignored.
        # http://www.nomadjourney.com/2010/04/suppressing-mysqlmysqldb-warning-messages-from-python/
        filterwarnings('ignore', category = MySQLdb.Warning)
        conn = self.__get_open_connection(system_connection_hash)
        conn.autocommit(True)
        cursor = conn.cursor()
        cursor.execute("drop database if exists {0}".format(database_name))
        cursor.execute("create database {0}".format(database_name))
        resetwarnings()
        cursor.close()
        conn.close()


    def __execute(self, conn_hash, sql):
        """Executes sql, Throws on error."""
        conn = self.__get_open_connection(conn_hash)
        conn.autocommit(True)
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
        except Exception as e:
            logger.error("Executing sql: %s"  % e)
            raise
        finally:
            cursor.close()
            conn.close()

    def user_defined_tables_exist(self, connection_hash):
        sql = """select table_name from information_schema.tables
        where (table_type = 'BASE TABLE' and table_schema = '{0}')
        limit 1""".format(connection_hash["dbname"])
        conn = self.__get_open_connection(connection_hash)
        cursor = conn.cursor()
        cursor.execute(sql)
        r = cursor.fetchall()
        cursor.close()
        conn.close()
        return (len(r) != 0)


    def create_tracking_table(self, connection_hash):
        """Creates table if needed."""
        # Mysql raising a 'table already exists' warning,
        # regardless of the use of 'create table if not exists'.
        # This can be ignored.
        filterwarnings('ignore', category = MySQLdb.Warning)
        # Using lowercase table name, as MySql is case-sensitive.
        sql = """create table if not exists __schema_migrations
(
  migration_id serial primary key,
  script_name varchar(255),
  date_applied timestamp not null default CURRENT_TIMESTAMP
)"""
        self.__execute(connection_hash, sql)
        resetwarnings()


    def is_in_tracking_table(self, connection_hash, script_name):
        """Returns True if script is in tracking table (assumes tbl is present)"""
        sql = "select script_name from __schema_migrations where script_name = '{0}'".format(script_name)
        conn = self.__get_open_connection(connection_hash)
        cursor = conn.cursor()
        cursor.execute(sql)
        r = cursor.fetchall()
        cursor.close()
        conn.close()
        return (len(r) > 0)


    def record_script_in_tracking_table(self, conn_hash, script_name):
        sql = "insert into __schema_migrations(script_name) values ('{0}')"
        self.__execute(conn_hash, sql.format(script_name))

    def execute(self, conn_hash, sql):
        self.__execute(conn_hash, sql.format(sql))
        
