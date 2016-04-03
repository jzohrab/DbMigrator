import sys
import os
import inspect
import ConfigParser
import argparse

import dbMigrator
from dbMigrator.driver import Driver
from dbMigrator.defaultdatabasesource import DefaultDatabaseSource
from dbMigrator.mysqldatabasehandler import MySqlDatabaseHandler


class MySqlExample:
    """An example wrapper that takes files in this directory and
applies them to a mysql database.  Parses command-line arguments to
determine which actions to take (call "python this_file.py -h" for
details):  You can create a new db, upgrade it, etc.

Configuration: See mysql_connections.ini.template (in this directory).

A sample run:

````
$ python mysql.py -nsu
Dropping and recreating mysql_test
Execute Db.sql on mysql_test
Execute 20130427_add_a_size.sql on mysql_test
Execute 20130428_create_Widget.sql on mysql_test
Execute 10_vX.sql on mysql_test
Execute bootstrap_data.sql on mysql_test
````
    """

    @staticmethod
    def build_driver():
        """Factory method."""

        d = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        inifile = os.path.join(d, 'mysql_connections.ini')
        if not os.path.exists(inifile):
            inifile = inifile + '.template'
        if not os.path.exists(inifile):
            raise Exception("Missing ini file at " + inifile)

        dds = DefaultDatabaseSource(inifile, d)

        driver = Driver(dds, MySqlDatabaseHandler())
        driver.default_database = "mysql_test"
        driver.is_debug_printing = True

        return driver

def main():
    d = MySqlExample.build_driver()
    d.main(sys.argv)

if __name__ == '__main__':
    main()
