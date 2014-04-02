import sys
import argparse

from migrator import Migrator

class Driver:
    """A simple command-line driver to handle migrations per user-supplied
command line arguments (call it with "-h" for
details).  You can create a new db, upgrade it, etc.

The user can pass one or more database names to the command line; if
none are specified, the driver updates the default_database.  If that
too is blank, nothing happens.
    """

    def __init__(self, database_source, database_handler):
        self.database_source = database_source
        self.database_handler = database_handler
        self.default_database = ""
        self.is_debug_printing = False

    class ParsingException(Exception):
        pass

    def parse_args(self, sys_argv):
        """Parsing, public for unit testing.  sys_argv should be sys.argv.
The first entry is skipped, to account for sys.argv putting the
program name as the first element.
        """
        if (len(sys_argv) == 0):
            raise Driver.ParsingException("sys_argv must contain at least one element (name of the executing program, per sys.argv[0])")

        parser = argparse.ArgumentParser(description='Migrate one or more databases (or default database, if one is assigned).')
        parser.add_argument("-n", "--new", help="Create new (empty) database(s)", action="store_true")
        parser.add_argument("-s", "--schema", help="Run baseline schema(e)", action="store_true")
        parser.add_argument("-m", "--migrations", help="Run migrations", action="store_true")
        parser.add_argument("-c", "--code", help="Run code (for views, stored procs, etc)", action="store_true")
        parser.add_argument("-d", "--data", help="Load reference (bootstrap) data", action="store_true")
        parser.add_argument("-u", "--update", help="Updates database (runs migrations, code, and data)", action="store_true")
        parser.add_argument('databases', metavar='db', nargs='*', help='nickname of database to manipulate')

        # Skipping the first entry.  Note that internally,
        # argparse.ArgumentParser does this as well.
        args = parser.parse_args(sys_argv[1:])

        if (len(args.databases) == 0 and self.default_database != ""):
            args.databases.append(self.default_database)
        return args

    def main(self, command_line_args):
        """Main entry point.  Consumes command line args (clients can pass sys.argv)"""

        if (len(command_line_args) < 2):
            # Print help as the default, if no args given.
            command_line_args = [ "driver.py", "--help" ]

        args = self.parse_args(command_line_args)
        if (len(args.databases) == 0):
            return

        m = Migrator(self.database_source, self.database_handler)
        m.is_debug_printing = self.is_debug_printing
        
        if args.new:
            m.delete_make_new(*args.databases)
        if args.schema:
            m.run_baseline_schema(*args.databases)
        if args.migrations or args.update:
            m.run_migrations(*args.databases)
        if args.code or args.update:
            m.run_code_definitions(*args.databases)
        if args.data or args.update:
            m.run_reference_data(*args.databases)
