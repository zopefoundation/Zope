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

- Create releases for the packages mentioned in `buildout.cfg` below
  ``auto-checkout``.

- Check the versions.cfg file for outdated or updated
  packages and update version information where necessary::

  $ bin/checkversions buildout.cfg

- Run the tests::

  $ bin/tox

- Update version information in change log and ``setup.py``::

  $ bin/prerelease

- Pin the Zope version in ``versions-prod.cfg``.

- Run ``bin/buildout`` to update ``requirements-full.txt``

- Commit the changes.

- Run all tests::

  $ bin/tox

- Upload the tagged release to PyPI::

    $ git tag <TAG-NAME>
    $ bin/zopepy setup.py egg_info -RDb '' sdist bdist_wheel upload --sign

    or

    $ bin/release

- Update version information::

  $ bin/postrelease
  $ vi versions-prod.cfg (remove Zope pin)
  $ bin/buildout

- Commit and push the changes.

- Check the visible releases on readthedocs.org at (should default to
  showing the active branches)::

    https://readthedocs.org/projects/zope/versions/

- Update https://zopefoundation.github.io/Zope/ (This is needed until https://github.com/zopefoundation/Zope/issues/244 is fixed.)::

  $ git checkout gh-pages
  $ ./build_index.sh

- Add the newly created files and commit and push the changes.

- Check on https://zopefoundation.github.io/Zope/ for the new release.

- Announce the release to the world via zope-announce@zope.org and https://community.plone.org/c/announcements.
