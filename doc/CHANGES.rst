Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

Trunk (unreleased)
------------------

Restructuring
+++++++++++++

- Centralize interfaces defined in Products.ZCTextIndex, leaving BBB
  imports behind in old locations.

- Integrated zLOG package back into this package.

- Updated documentation to new version number.

Features Added
++++++++++++++

- Updated packages:

  - zope.app.appsetup = 3.12.0
  - zope.app.cache = 3.6.0
  - zope.app.publication = 3.8.1
  - zope.app.testing = 3.7.0
  - zope.app.wsgi = 3.6.0
  - zope.app.zcmlfiles = 3.6.0
  - zope.i18nmessageid = 3.5.0
  - zope.server = 3.6.0

Bugs Fixed
++++++++++

- LP #397861: exporting $PYTHON in generated 'zopectl' for fixing import issue
  with "bin/zopectl adduser"
