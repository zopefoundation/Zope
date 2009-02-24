What's new in Zope 2.12
=======================

The article explains the new high-level features and changes found in this
version of Zope2.

You can have a look at the `detailed change log <CHANGES.rst>`_ to learn
about all minor new features and bugs being solved in this release.


Support for newer Python versions
---------------------------------

Zope2 has supported and required Python 2.4 since its 2.9 release in
summer 2006. Later versions of Python have so far been incompatible with
Zope2.

This version of Zope2 adds support for both Python 2.5 and 2.6 at the same
time. As Python 2.4 is no longer maintained itself, it is no longer officially
supported by this Zope2 version. There is however no code in Zope2 yet which
requires Python 2.5, so applications built on top of Zope2 should still
continue to run with Python 2.4.

Python 3 is a backwards incompatible release of Python and not supported. At
this point there is no concrete roadmap for adoption of Python 3. It is
expected to be a question of multiple major Zope2 releases or years, though.


Fully eggified
--------------

Zope2 itself is now fully eggified and compatible with `setuptools
<http://pypi.python.org/pypi/setuptools>`_. You can use popular tools like
`easy_install <http://peak.telecommunity.com/DevCenter/EasyInstall>`_ or
`zc.buildout <http://pypi.python.org/pypi/zc.buildout>`_ to install Zope2.

Releases of Zope2 can be found at and will be installable from the Python
package index at http://pypi.python.org/pypi/Zope2.

The repackaging of Zope2 into an eggified form and accompanying changes to the
file system layout have caused a number of changes. The environment variables
`SOFTWARE_HOME` and `ZOPE_HOME` are no longer available nor set in the control
scripts. If you need to access data files inside the Zope2 package, you can for
example use `import os, OFS; os.path.dirname(OFS.__file__)` to locate the files
inside the OFS package.

In general it is discouraged to rely on the `lib/python` and `Products`
directories to make code available to the running Zope process. While these
mechanisms continue to work, you are encouraged to use normal distutils or
setuptools managed packages and add these to your `sys.path` using any of the
standard Python mechanisms. To create isolated Python environments both
`zc.buildout <http://pypi.python.org/pypi/zc.buildout>`_ and `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_ are in wide-spread use.


Latest version of Zope Components
---------------------------------

This version of Zope2 is compatible with and is based on Zope 3.5.

A major focus of the new version of the Zope component libraries was to
refactor package dependencies to generate more maintainable and better
structured code. Based on this effort the number of packages included by
Zope2 could be dramatically reduced from about 120 additional packages to
just over 60. The total code size of Zope2 and its dependencies has decreased
by over 200,000 lines of code as a result.

You can find more information about the changes in Zope 3.5 at
http://download.zope.org/zope3.5/. Upgrade information from Zope 3.4 to 3.5
can be found at http://docs.zope.org/zope3docs/migration/34to35.html.


ZODB 3.9
--------

This version of Zope2 includes the latest version of the `ZODB (3.9)
<http://pypi.python.org/pypi/ZODB3>`_. It has a multitude of new configuration
options and bug fixes. File storages have gotten native support for blob
storages and demo storages have been expanded extensively. There is a large
number of options to tune ZEO servers and clients in large scale environments
and control cache invalidation and packaging to a much wider degree.

You can read more about the detailed changes in the `ZODB3 change log
<http://pypi.python.org/pypi/ZODB3>`_ for version 3.9.


Module cleanup
--------------

As with every release of Zope2 this version has removed various modules
which have been deprecated in prior versions.

Most notably ZClasses and supporting modules have been removed entirely from
Zope2. As a result the persistent product registry has been optional, but is
still enabled by default. If your application does not rely on the registry you
can now disable the registry by specifying::

  enable-product-installation off

inside your `zope.conf` file. As a result Zope will no longer write any new
transactions to your database during startup.

With the upgrade to ZODB 3.9 database-level version support is no longer
available. Many of the modules in Products.OFSP have been removed as a result.
The low level API to load objects from the database has lost its version
argument as a result of this.


Documentation updates
---------------------

Zope2 now uses `Sphinx <http://sphinx.pocoo.org/>`_ to create pleasant HTML
representations of its documentation. An effort is underway to update the
publicly available documentation using Sphinx at http://docs.zope.org/.

So far the Zope2 Book, the Zope Developers Guide and many smaller articles
have been converted to reStructuredText and their content updated.


