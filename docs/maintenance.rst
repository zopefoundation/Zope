Maintainer information
======================

.. note::

  This is internal documentation, mostly for Zope maintainers who manage
  software releases and the documentation


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

- Make sure you have the necessary tools around and install them manually if
  needed::

  $ bin/pip install -U wheel tox twine

- Create releases for the packages mentioned in `buildout.cfg` below
  ``auto-checkout`` enter them into ``versions-prod.cfg`` and run
  ``bin/buildout`` to update ``requirements-full.txt``.

- Garden the change log and check it for spelling issues. Look at the changes
  for this new release and decide on the version number. Features should
  trigger a feature release.

- Check the future PyPI long description for ReST errors::

    $ cat README.rst <(echo) CHANGES.rst | bin/rst2html >/tmp/test.html && open /tmp/test.html

- Update version information in change log and ``setup.py`` and specify today’s
  date as release date in the change log::

    $ bin/prerelease  # if you use zest.releaser

    or

    $ vi CHANGES.rst setup.py

- Update the version information in the Sphinx documentation configuration::

    $ vim docs/conf.py

- Pin the Zope version in ``versions-prod.cfg``.

- Run ``bin/buildout`` to update ``requirements-full.txt``.

- Run all tests::

    $ bin/tox -pall

- If the tests succeed, commit the changes.

- Upload the tagged release to PyPI::

    $ bin/release  # if you use zest.releaser

    or

    $ git tag -as <TAG-NAME> -m "- tagging release <TAG-NAME>"
    $ git push --tags
    $ bin/zopepy setup.py egg_info -Db '' sdist bdist_wheel
    $ bin/twine upload dist/Zope-<TAG-NAME>*

- Update version information in the change log and setup.py::

    $ bin/postrelease  # if you use zest.releaser

    or 

    $ vi CHANGES.rst setup.py

- Remove the version pin for Zope::

    $ vi versions-prod.cfg (remove Zope pin)
    $ bin/buildout

- Commit and push the changes.

- Check that the changes have been propagated to https://zope.readthedocs.io/en/latest/changes.html.
  (This should be done automatically via web hooks defined in GitHub and RTD.)

- Update https://zopefoundation.github.io/Zope/::

    $ git checkout gh-pages
    $ python3 build_index.py

- Add the newly created files and commit and push the changes.

- Check on https://zopefoundation.github.io/Zope/ for the new release.

- Check the versions.cfg file for outdated or updated
  packages and update version information where necessary.::

    $ bin/checkversions versions-prod.cfg
    $ bin/checkversions versions.cfg
    $ bin/buildout

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
- Build the documentation: ``bin/tox -edocs``
- Fix problems.
- Commit and push the changes.

- Update the Zope release schedule at https://github.com/zopefoundation/www.zope.org/blob/master/docs/releases.rst

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
documentation using the script ``bin/tox -edocs`` to create the documentation
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

Maintaining Zope documentation translations
-------------------------------------------
The Sphinx documentation has some translations now. Adding new translations or
maintaining existing ones is done in several steps. The following is mostly
taken from https://www.sphinx-doc.org/en/master/usage/advanced/intl.html.

Adding a new document translation
+++++++++++++++++++++++++++++++++
If you are just working on an existing ``.po`` file you can skip these steps.

- Create the ``.pot`` files that form the basis for all translations::

    $ cd docs
    $ make gettext

- Copy the ``.pot`` file for the new document to the correct language folder,
  the following example uses ``ja`` for the Japanese translation. If the folder
  does not exist yet, just create it::

    $ mkdir -p locale/ja/LC_MESSAGES
    $ cp _build/gettext/maintenance.pot locale/ja/LC_MESSAGES/maintenance.po

Now continue with the steps in the next section.


Maintaining existing translations
+++++++++++++++++++++++++++++++++
Start here if the translation ``.po`` file already exists. This example uses a
file ``maintenance.po`` from the Japanese translation:

- At the top of the ``.po`` file, enter your name and optionally email address
  into the field `Last-Translator`::

    $ cd docs
    $ vim locale/ja/LC_MESSAGES/maintenance.po

- Enter translated strings into the various `msgstr` fields

- Build the translated HTML pages from the ``docs`` folder::

    $ make -e SPHINXOPTS="-D language='ja'" html

- When you are happy with the result, commit the changes to the repository::

    $ git commit locale/ja/LC_MESSAGES/maintenance.po

  .. note::

    Please do not add any ``.po`` files to the repository that have no
    translations. Those will not do anything but increase the size of the
    released package.



