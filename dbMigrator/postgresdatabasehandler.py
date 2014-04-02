import logging
import psycopg2
import psycopg2.extensions

from migrator import DatabaseHandler
logger = logging.getLogger('dbmigrator')

class PostgresDatabaseHandler(DatabaseHandler):
    """Postgres-specific implementation of the DatabaseHandler."""

    def __get_open_connection(self, connection_hash):
        """Opens a connection to the database."""
        template = "host='{0}' dbname='{1}' user='{2}' password='{3}'"
        hsh = connection_hash
        c = template.format(hsh["host"], hsh["dbname"], hsh["user"], hsh["password"])
        return psycopg2.connect(c)

    def delete_make_new(self, system_connection_hash, database_name):
        """Creates new database, deletes the old."""
        conn = self.__get_open_connection(system_connection_hash)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute("drop database if exists {0}".format(database_name))
        cursor.execute("create database {0}".format(database_name))
        cursor.close()
        conn.close()


    def __execute(self, conn_hash, sql):
        """Executes sql, Throws on error."""
        conn = self.__get_open_connection(conn_hash)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
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
        sql = """select table_name
        from information_schema.tables
        where (table_type = 'BASE TABLE' and table_schema not in ('pg_catalog', 'information_schema'))
        limit 1"""
        conn = self.__get_open_connection(connection_hash)
        cursor = conn.cursor()
        cursor.execute(sql)
        r = cursor.fetchall()
        cursor.close()
        conn.close()
        return (len(r) != 0)


    def create_tracking_table(self, connection_hash):
        """Creates table if needed."""
        # Using lowercase table name, as Postgres is case-sensitive.
        sql = """create table if not exists __schema_migrations
(
  migration_id serial primary key,
  script_name varchar(255),
  date_applied timestamp not null default CURRENT_TIMESTAMP
)"""
        self.__execute(connection_hash, sql)


    def is_in_tracking_table(self, connection_hash, script_name):
        """Returns true if script is in tracking table (assumes tbl is present)"""
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
        
