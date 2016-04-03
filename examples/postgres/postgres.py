import sys
import os
import inspect

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import dbMigrator
from dbMigrator.driver import Driver
from dbMigrator.defaultdatabasesource import DefaultDatabaseSource
from dbMigrator.postgresdatabasehandler import PostgresDatabaseHandler


class PostgresExample:
    """An example wrapper that takes files in this directory and
applies them to a postgres database.  Parses command-line arguments to
determine which actions to take (call "python this_file.py -h" for
details):  You can create a new db, upgrade it, etc.

Configuration: See postgres_connections.ini.template (in this directory).

A sample run:

````
$ python postgres.py -nsu
Dropping and recreating postgres_test
Execute Db.sql on postgres_test
Execute 20130427_add_a_size.sql on postgres_test
Execute 20130428_create_Widget.sql on postgres_test
Execute 10_vX.sql on postgres_test
Execute bootstrap_data.sql on postgres_test
````
    """

    @staticmethod
    def build_driver():
        d = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        inifile = os.path.join(d, 'postgres_connections.ini')
        if not os.path.exists(inifile):
            inifile = inifile + '.template'
        if not os.path.exists(inifile):
            raise Exception("Missing ini file at " + inifile)

        dds = DefaultDatabaseSource(inifile, d)

        driver = Driver(dds, PostgresDatabaseHandler())
        driver.default_database = "postgres_test"
        driver.is_debug_printing = True

        return driver


def main():
    d = PostgresExample.build_driver()
    d.main(sys.argv)

if __name__ == '__main__':
    main()
