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

.. note::

    There is no version pin for `zc.buildout` as it has to be installed
    in the virtual environment but `checkversions` also prints its
    version number.

- Garden the change log.

- Run the tests::

  $ bin/tox

- Update version information in change log and ``setup.py``::

  $ bin/prerelease

- Pin the Zope version in ``versions-prod.cfg``.

- Run ``bin/buildout`` to update ``requirements-full.txt``.

- Commit the changes.

- Run all tests::

  $ bin/tox

- Check the future PyPI long description for ReST errors and for spelling
  issues::

  $ bin/longtest

- Upload the tagged release to PyPI::

    $ bin/release

    or

    $ git tag <TAG-NAME>
    $ bin/zopepy setup.py egg_info -RDb '' sdist bdist_wheel upload --sign

- Update version information::

  $ bin/postrelease
  $ vi versions-prod.cfg (remove Zope pin)
  $ bin/buildout

- Commit and push the changes.

- Check that the changes have been propagated to https://zope.readthedocs.io/en/latest/changes.html.
  (This should be done automatically via web hooks defined in GitHub and RTD.)

- Update https://zopefoundation.github.io/Zope/ (This is needed until https://github.com/zopefoundation/Zope/issues/244 is fixed.)::

  $ git checkout gh-pages
  $ ./build_index.sh

- Add the newly created files and commit and push the changes.

- Check on https://zopefoundation.github.io/Zope/ for the new release.

- Announce the release to the world via zope-announce@zope.org and https://community.plone.org/c/announcements.
