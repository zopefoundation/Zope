Maintenance information
========================

.. note::

   This is internal documentation for Zope developers having
   to create official Zope releases.

Release process
---------------

Maintainers
+++++++++++

The following persons have access to the ``Zope2`` package on PyPI
(in order to release new versions):

- Hanno Schlichting
- Tres Seaver

Steps for creating a new Zope release
+++++++++++++++++++++++++++++++++++++

- check the versions.cfg file for outdated or updated
  packages and update version information where necessary

- update version information:

  - setup.py (remove dev postfix)
  - versions.cfg (pin Zope2)

- update docs/CHANGES.rst

- run all tests::

   bin/alltests

- tag the release

- upload the tagged release to PyPI::

    python2.7 setup.py egg_info -RDb '' sdist --formats=zip register upload

- update version information:

  - setup.py (bump version number, add dev postfix)
  - versions.cfg (remove Zope2 pin)

- check the visible releases on readthedocs.org at (should default to
  showing the active branches)::

    https://readthedocs.org/dashboard/zope/versions/

- update the status of all bugs associated with the released milestone::

    https://launchpad.net/zope2/+milestone/2.13.x
