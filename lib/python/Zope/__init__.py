"""Initialize the Zope Package and provide a published module
"""

#######################################################################
# We need to get the right BTree extensions loaded
import sys, os, App.FindHomes
sys.path.insert(0, os.path.join(SOFTWARE_HOME, 'ZopeZODB3'))
#######################################################################

import ZODB, ZODB.FileStorage, ZODB.ZApplication
import Globals, OFS.Application, sys

Globals.BobobaseName = '%s/Data.fs' % Globals.data_dir

# Import products
OFS.Application.import_products()

# Open the database
DB=ZODB.FileStorage.FileStorage(
    Globals.BobobaseName,
    log=lambda x: sys.stderr.write(x))
DB=ZODB.DB(DB)
Globals.opened.append(DB)

# Set up the "application" object that automagically opens
# connections
app=bobo_application=ZODB.ZApplication.ZApplicationWrapper(
    DB, 'Application', OFS.Application.Application, (),
    Globals.VersionNameName)

# Initialize products:
c=app()
OFS.Application.initialize(c)
c._p_jar.close()
del c
