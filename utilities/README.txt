This directory contains utility scripts and modules that augment Zope.

To get detailed usage information, run any of these scripts without arguments:

  load_site.py -- Load a Zope site from files and directories

    This script illustrates used of the Zope RPC mechanism, 
    ZPublisher.Client.  It provides some examples of pitfalls
    and their work-arounds.

  testrunner.py -- A Zope test suite utility.

    The testrunner utility is used to execute PyUnit test suites. You can
    find more information on PyUnit at http://pyunit.sourceforge.net. This
    utility should be run from the root of your Zope installation.

The following scripts are for use with the old BoboPOS 2 fileformat.

  fixbbbts.py -- Fix database time stamps

    Sometimes, problems with system clocks can cause invalid time stamps
    to be written to databases.  The fixbbbts script can be used to 
    shift invalid times in the database to make them valid.

  bbb.py -- Read and summarize a Zope database.
 
    This script illustrates how to read a database file outside of
    Zope and provides a number of options for finding bad data and 
    generating reports of data.

