Maintenance information
=======================

.. note::

   This is internal documentation for Zope developers having
   to create official Zope releases.

Release process
---------------

Maintainers
+++++++++++

The following persons have access to the ``Zope`` package on PyPI
(in order to release new versions):

- Hanno Schlichting
- Michael Howitz
- Tres Seaver
- Jens Vagelpohl

Steps for creating a new Zope release
+++++++++++++++++++++++++++++++++++++

- Check the versions.cfg file for outdated or updated
  packages and update version information where necessary.

- Update version information:

  - setup.py (remove dev postfix)
  - versions-prod.cfg (pin Zope)

- Run ``bin/buildout`` to update ``requirements-full.txt``

- Update docs/CHANGES.rst with a release date.

- Commit the changes.

- Run all tests::

   bin/tox

- Tag the release.

- Upload the tagged release to PyPI::

    python2.7 setup.py egg_info -RDb '' sdist bdist_wheel upload --sign
    
    or
    
    release (of zest.releaser)

- Update version information:

  - setup.py (bump version number, add dev postfix)
  - versions-prod.cfg (remove Zope pin)
  - run ``bin/buildout`` to update ``requirements-full.txt``
  - commit and push the changes

- Check the visible releases on readthedocs.org at (should default to
  showing the active branches)::

    https://readthedocs.org/dashboard/zope/versions/

- Switch to the ``gh-pages`` branch of ``Zope`` and run ``./build_index.sh``. Commit and push the changes.
