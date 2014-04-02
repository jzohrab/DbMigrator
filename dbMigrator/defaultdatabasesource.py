import sys
import os
from configobj import ConfigObj
from os import listdir
from os.path import isfile, join
import glob

from migrator import DatabaseSource

class DefaultDatabaseSource(DatabaseSource):
    """Default source for database scripts and connections that can be
used by people following the suggested directory layout.

Database file directories must be as follows:
- <root directory>
  - db_1_name
    - baseline_schema
    - migrations
    - code
    - reference_data
  - db_2_name
    - etc.

The database folder names (db_1_name, etc) must match the database
names used as "Database" subsection names in the .ini file.
    """

    def __init__(self, ini_file, root_directory):
        """ctor.  Arguments:

ini_file: path to an .ini file.  See database_connections.ini.template
for the required layout; this file should be copied and renamed x.ini
for your particular database.

root_directory: root directory of your databases."""

        if not os.path.exists(ini_file):
            raise Exception("Missing ini file at " + ini_file)
        self.config = ConfigObj(ini_file)
        self.root_dir = root_directory

    def get_db_name_from_nickname(self, nickname):
        return self.config["Databases"][nickname]["dbname"]

    def get_system_connection_hash(self):
        return self.config["Server"]

    def get_connection_hashes(self):
        return self.config["Databases"]

    def __get_files(self, database_name, subfolder_name):
        mypath = os.path.join(self.root_dir, database_name, subfolder_name, "*.sql")
        ret = []
        for f in glob.glob(mypath):
            bn = os.path.basename(f)
            with open (f, "r") as myfile:
                data=myfile.read()
            ret.append( (bn, data) )
        return ret

    def get_baseline_schema_files(self, database_name):
        return self.__get_files(database_name, "baseline_schema")

    def get_reference_data_files(self, database_name):
        return self.__get_files(database_name, "reference_data")

    def get_code_files(self, database_name):
        return self.__get_files(database_name, "code")

    def get_migrations_files(self, database_name):
        return self.__get_files(database_name, "migrations")
