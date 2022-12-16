Maintainer information
======================

.. note::

  This is internal documentation, mostly for Zope maintainers who manage
  software releases and the documentation

.. contents::

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

- Make sure you have the necessary tools around and install the manually if
  needed::

  $ bin/pip install -U wheel tox twine

- Create releases for the packages mentioned in `buildout.cfg` below
  ``auto-checkout`` and enter them into ``versions-prod.cfg``.

- Run ``bin/python util.py`` to update ``requirements-full.txt``. **Note:** The
  script will only run on Python 3.7 or higher!

- Garden the change log and check it for spelling issues.

- Check the future PyPI long description for ReST errors (example for macOS)::

  $ cat README.rst <(echo) CHANGES.rst | bin/rst2html.py >/tmp/test.html && open /tmp/test.html

- Check in the changes.

- Update version information in change log and ``setup.py`` and specify today's
  date as release date in the change log.

- Update the version information in the Sphinx documentation configuration::

    $ vim docs/conf.py

- Pin the Zope version in ``versions-prod.cfg``

- Run ``bin/python util.py`` to update ``requirements-full.txt``. **Note:** The
  script will only run on Python 3.7 or higher!

- Run all tests::

  $ bin/tox -pall

- If the tests succeed, commit the changes.

- Upload the tagged release to PyPI::

    $ git tag -as <TAG-NAME> -m "- tagging release <TAG-NAME>"
    $ git push --tags
    $ bin/zopepy setup.py egg_info -Db '' sdist bdist_wheel
    $ bin/twine upload -s dist/Zope-<TAG-NAME>*

- Update version information in the change log and ``setup.py`` and revert the
  version pin for Zope::

    $ vim CHANGES.rst setup.py
    $ vim versions-prod.cfg (set version pin of Zope back to ``< 5``)
    $ bin/python util.py
    $ bin/buildout

- Commit and push the changes.

- Check that the changes have been propagated to https://zope.readthedocs.io/en/4.x/changes.html.
  (This should be done automatically via web hooks defined in GitHub and RTD.)

- Update https://zopefoundation.github.io/Zope/::

  $ git checkout gh-pages
  $ python3 build_index.py

- Add the newly created files and commit and push the changes.

- Check on https://zopefoundation.github.io/Zope/ for the new release.

- Check the versions files for outdated or updated
  packages and update version information where necessary. The following
  commands only update to newer minor versions but not newer major versions
  expecting that removing Python 2 support is signalled by an increased major
  version::

  $ bin/checkversions --level=2 versions-prod.cfg
  $ bin/checkversions --level=2 versions.cfg
  $ bin/python util.py

  .. note::
  
      This step is done after the release to have time to fix problems which
      might get introduced by new versions of the dependencies.
  
      There is no version pin for `zc.buildout` as it has to be installed
      in the virtual environment but `checkversions` also prints its
      version number.
  
      There is no version pin for `zc.recipe.egg` in `versions-prod.cfg` as it is
      only needed for buildout install and not for pip, so we do not want to
      have it in `requirements.txt`.
  
      The script is called two times so the rendered version updates can be
      easily assigned to the correct file.

- Run the tests: ``bin/tox -pall``
- Build the documentation: ``bin/make-docs``
- Fix problems.
- Commit and push the changes.

- Update the Zope release schedule at https://www.zope.dev/releases.html

- Announce the release to the world via zope-announce@zope.dev and https://community.plone.org/c/announcements.


Maintaining the Zope documentation
----------------------------------

Contributing to the documentation
+++++++++++++++++++++++++++++++++
Any signed Zope contributor may contribute to the Sphinx-based documentation
in the ``docs`` subfolder, including `The Zope Book` and the `Zope Developer's
guide`.

Just like with code contributions, please follow best practice. Test your
changes locally before creating a pull request or pushing to the repository.
Use a reasonable line length (<80).

Building the documentation
++++++++++++++++++++++++++
After you have bootstrapped and run the buildout, you can build the
documentation using the script ``bin/make-docs`` to create the documentation
HTML output. The script will tell you where it saves the output.

The official documentation site on `Read the Docs`
++++++++++++++++++++++++++++++++++++++++++++++++++
Pushes to the Zope repository on GitHub will automatically trigger an automatic
documentation refresh on the official documentation site at
https://zope.readthedocs.io. This is true for the ``master`` branch, but also
for versions 2.12 and 2.13. The trigger is implemented as a GitHub Webhook, see
`Settings` | `Webhooks` in the GitHub repository.

The RTD configuration at https://readthedocs.org/projects/zope/ is currently
maintained by the following people:

- Hanno Schlichting
- Michael Howitz
- Tres Seaver
- Jens Vagelpohl
