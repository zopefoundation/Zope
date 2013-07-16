Maintenance information
========================

.. note::

   This is internal documentation for Zope 2 developers having
   to create official Zope 2 releases

Release process
---------------

Maintainers
+++++++++++

The following persons have access to the ``Zope2`` package on PyPI
(in order to release new versions):

- Hanno Schlichting

Steps for creating a new Zope release
+++++++++++++++++++++++++++++++++++++

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

- check the visible releases on readthedocs.org at (should default to
  showing the active branches)::

    https://readthedocs.org/dashboard/zope/versions/

- update version information on zope2.zope.org

  - login on https://zope2.zope.org into the Plone site

- close the released milestone::

    https://launchpad.net/zope2/+milestone/2.13.15/+addrelease

- update the status of all bugs associated with the released milestone::

    https://launchpad.net/zope2/+milestone/2.13.15

- update launchpad. Create a new next milestone at::

    https://launchpad.net/zope2/2.13/+addmilestone
