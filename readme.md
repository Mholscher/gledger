# GLedger : General Ledger software #

## Installing GLedger ##

Install GLedger from Github. There is no way to instal it using pip.

## How GLedger is developed ##

GLedger is developed on openSuse Linux, using Python 3.4 and Firebird 2.5 to implement its database. To interface with the database I used SQLAlchemy, taking care to not use Firebird specific constructs. It should run with all database backends SQLAlchemy supports, but no guarantees :=)

## Details ##

### Files for testing ###

In the GLTests there are tests for the software. Some of these tests that address the posting API require files with Json interfaces. These are also supplied and need to be accessible when running the tests.

### Database for testing? ###

The tests are designed to be run on an empty database. Most tests don't mind 'stuff' being present in the database, however, one of the tests e.g. relies on an account with sequence number 1 **bold** not **bold** being present in the database. The tests do not create the database, it needs to be present before running tests.

### Crete a database ####

Go into a Python REPL and import glmodels. Than import db from gledger. You can then do do a db.dropall() and a db.create_all() to recreate the tables.

The only thing not recreated **bold** in Firebird **bold** is the sequences. These count on and on, recreate these by hand.
