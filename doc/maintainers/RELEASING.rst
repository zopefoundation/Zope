Makeing a 2.13.x Release
========================

Make a branch for release prepration.
-------------------------------------

We need to make a number of changes for the release which we do *not* want
checked in on the ``2.13`` branch.  Therefore, create a release-preparation
branch, based on the ``2.13`` branch, as the locus for those changes:

.. code-block:: bash

   $ git checkout -b 2.13.23-prep 2.13

Update the release version in ``setup.py``
------------------------------------------

Set the new release version, and commit:

.. code-block:: bash

   $ vim setup.py
   $ git commit -m "Update version for 2.13.23 release" setup.py

Pin versions in ``buildout.cfg``
--------------------------------

For a release, we want to switch away from the range-based version constraints
we use for the development branch, and pin the specific versions.

First, re-run the buildout, which will dump the currently-selected versions
on standard output.  E.g.:

.. code-block:: bash

   $ bin/buildout
   ...
   [versions]
   AccessControl = 2.13.13
   Acquisition = 2.13.9
   ...
   setuptools = 18.0.1

Next, update the ``buildout.cfg`` settings as follows:

- Copy the ``[versions]`` section from the buildout run and paste it
  at the bottom of the ``buildout`` file.
- In the ``[buildout]`` section, remove ``show-picked-verions = true``,
  add ``allow-picked-versions = false``, and remove the ``version_ranges``
  from the ``extends``.

.. code-block:: bash

   $ vim buildout.cfg

Re-run the buildout and test:

.. code-block:: bash

   $ rm -rf bin/ develop-eggs/ eggs/ include/ lib/
   $ tox -r

Pin versions in a ``pip`` requirements file
-------------------------------------------

Copy the version pins from the ``[versions]`` section of ``buildout.cfg``
into a ``requirements.txt`` file, to enable ``pip`` users to install
without buildout (be sure to add the new ``Zope2`` release version to
``requirements.txt`` and the ``[versions]`` section).

.. note::

   Update the single equal signs used in ``buildout.cfg`` to pip-compatible
   double-equal signs.

.. code-block:: bash

   $ vim requirements.txt
   $ git add requirements.txt
   $ git commit -m "Pin versions for 2.13.23 release" buildout.cfg requirements.txt

Review / update the changelog
-----------------------------

Add today's date to the current release.

.. code-block:: bash

   $ vim doc/CHANGES.rst
   $ git commit -m "Finalize changelog 2.13.23 release" doc/CHANGES.rst

.. note::

   Keep track of the hash for this commit:  you will want to cherry-pick
   it to the ``2.13`` branch later.

Tag the release
---------------

.. code-block:: bash

   $ git tag -sm "Tag 2.13.23 release" 2.13.23

.. note::

   The ``-s`` signs the tag using PGP.

Register and upload the release to PyPI
---------------------------------------

.. code-block:: bash

   $ bin/python setup.py sdist upload --sign

.. note::

   The ``upload --sign`` signs the sdist using PGP and uploads the signature
   to PyPI along with the distribution file.

Push the git release artefacts
------------------------------

.. code-block:: bash

   $ git push origin 2.13.23-prep && git push --tags

Update the ``2.13`` branch for the next release
-----------------------------------------------

.. code-block:: bash

   $ git checkout 2.13

Cherry-pick the changelog update from above:

.. code-block:: bash

   $ git cherry-pick -x <hash from commit above>^..<hash from commit above>

Add the next release to the changelog, with "(unreleased)" as its release
date and a "TBD" bullet, and update the next development release in
``setup.py``.

.. code-block:: bash

   $ vim doc/CHANGES.rst
   $ vim setup.py
   $ git commit -m svb doc/CHANGES.rst setup.py
   $ git push origin 2.13


Update versions on GitHub pages
-------------------------------

.. code-block:: bash

   $ git checkout gh-pages

Add the new version number below "Select 2.13 version" at the beginning of the
versions list and create the pages:

.. code-block:: bash

   $ vi build_index.sh
   $ ./build_index.sh

Commit the changes and newly created files and push the changes. (Assure there
are no releases deleted by calling ``./build_index.sh``.)

Check the result on https://zopefoundation.github.io/Zope/.


Create index on download.zope.org
---------------------------------

.. code-block:: bash

   $ ssh download.zope.org
   $ sudo -iu zope
   $ cd ~/zope2index

In the next line replace the two version numbers with the current release:

.. code-block:: bash

   $ bin/z2_kgs 2.13.23 /var/www/download.zope.org/Zope2/index/2.13.23/

Visit ``http://download.zope.org/Zope2/index/2.13.23/`` and make sure
a ``Zope2`` folder with an ``index.html`` was created.

If this is missing, you forgot to add ``Zope2`` to the ``[versions]``
section in the buildout file. Also double check ``requirements.txt``
for the same mistake.
