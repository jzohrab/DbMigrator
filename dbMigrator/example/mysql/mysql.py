import sys
import os
import inspect
import ConfigParser
import argparse

sys.path.append(os.path.abspath(sys.path[0]) + '/../../')
from driver import Driver
from defaultdatabasesource import DefaultDatabaseSource
from mysqldatabasehandler import MySqlDatabaseHandler


class MySqlExample:
    """An example wrapper that takes files in this directory and
applies them to a mysql database.  Parses command-line arguments to
determine which actions to take (call "python this_file.py -h" for
details):  You can create a new db, upgrade it, etc.

Configuration: To use this example, copy mysql_connections.ini.template (in
this directory) to mysql_connections.ini, and fix the connection component
entries.  Leave the [Databases] key as mysql_test and the dbname as
mysql_test, as the DefaultDatabaseSource assumes that the database
root directory contains a folder by that name.

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
    
    def main(self):
        d = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        inifile = os.path.join(d, 'mysql_connections.ini')
        if not os.path.exists(inifile):
            raise Exception("Missing ini file at " + inifile)

        dds = DefaultDatabaseSource(inifile, d)

        driver = Driver(dds, MySqlDatabaseHandler())
        driver.default_database = "mysql_test"
        driver.is_debug_printing = True

        driver.main(sys.argv)


def main():
    p = MySqlExample()
    p.main()

if __name__ == '__main__':
    main()
