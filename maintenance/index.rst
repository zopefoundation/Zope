Maintenance information
========================

.. note::

   This is internal documentation for Zope 2 developers having
   to create official Zope 2 releases

Zope 2.12+ release process
--------------------------

Maintainers
+++++++++++

The following persons have access to the ``Zope2`` package on PyPI
(in order to release new versions):

- Hanno Schlichting
- Tres Seaver
- Andreas Jung

Steps for creating a new Zope 2 release
+++++++++++++++++++++++++++++++++++++++

- check the versions.cfg file for outdated or updated
  packages and update version information where necessary

- update version information:

  - setup.py
  - versions.cfg

- update docs/CHANGES.rst

- run all tests::

   bin/alltests

- tag the release

- upload the tagged release to PyPI::

    python2.7 setup.py egg_info -RDb '' sdist --formats=zip register upload

- create the release specific download index on download.zope.org
  (requires login credentials on download.zope.org. In case of
  problems contact Jens Vagelpohl)

  - login to download.zope.org

  - change to user ``zope``::

     sudo su - zope

  - create the download index (e.g. for Zope 2.13.15)::

     /home/zope/zope2index/bin/z2_kgs tags/2.13.15 /var/www/download.zope.org/Zope2/index/2.13.15

- update the version tag for the auto-generated documentation of the release
  notes on docs.zope.org::

    svn propedit svn:externals svn+ssh://svn.zope.org/repos/main/zope2docs/trunk/releases

- update version information on zope2.zope.org

  - login on https://zope2.zope.org into the Plone site

- close the released milestone::

    https://launchpad.net/zope2/+milestone/2.13.15/+addrelease

- update the status of all bugs associated with the released milestone::

    https://launchpad.net/zope2/+milestone/2.13.15

- update launchpad. Create a new next milestone at::

    https://launchpad.net/zope2/2.13/+addmilestone


Pre-Zope 2.12 release process
-----------------------------

- update version information:

  - setup.py
  - inst/versions.py
  - inst/WinBuilders/mk/zope.mk

- run all tests::

      ./configure --with-python=/path/to/python2.4
      make
      bin/instance test

- create a source release::

      ./configure --with-python=/path/to/python2.4
      make sdist

- create a software release package under www.zope.org/Products/Zope and
  upload the source release as release file

- update the metadata of the release package (copy & paste from a former release)

- create a file CHANGES.txt with the related release notes

- send out a notification email
