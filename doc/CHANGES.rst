Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

Trunk (unreleased)
------------------

Restructuring
+++++++++++++

- Requiring Python 2.6 officially

- Changed startup server tests in Zope2 to use a randomized port number, to
  allow the nightly buildbot to run the tests at the same time for multiple
  configurations without the port being already in use.

- Cloned ``ZopeVocabularyRegistry`` from ``zope.app.schema``, and added
  sane registration of it during initialization of Five.

- Removed experimental support for configuring the Twisted HTTP server
  as an alternative to ``ZServer``.

- Moved ``Products/Five/security.py`` into the AccessControl package.

- Moved ``Products/Five/traversing.zcml`` directly into the configure.zcml.

- Moved zope.security-style permission registrations from Products.Five into
  the AccessControl package.

- Moved ``Products/Five/i18n.zcml`` into the ZPublisher package.

- Moved ``Products/Five/publisher.zcml`` into the ZPublisher package.

- Moved ``Products/Five/event.zcml`` into the OFS package.

- Removed no longer maintained ``configure, make, make install`` related
  installation files. Zope2 can only be installed via its setup.py.

- Centralize interfaces defined in Products.ZCTextIndex, leaving BBB
  imports behind in old locations.

- Integrated zLOG package back into this package.

- Updated documentation to new version number.

Features Added
++++++++++++++

- The send method of MailHost now supports unicode messages and
  email.Message.Message objects.  It also now accepts charset and
  msg_type parameters to help with character, header and body
  encoding.

- We know depend on the official Zope Toolkit and its known-good-set of
  packages.

Bugs Fixed
++++++++++

- LP #490514:  preserve tainting when calling into DTML from ZPT.

- LP #414757: Don't send a request closed event from a cloned request.

- LP #418454: FTP server did not work with Python 2.6.X

- Fixed issue with sending text containing ':' from MailHost.

- MailHost will now ensure the headers it sets are 7bit.

- MailHost no longer generates garbage when given unicode input.

- MailHost manage form no longer interprets the value None as a string
  in user and password fields.

- Made C extensions work for 64-bit Python 2.5.x / 2.6.x.

- Unfutzed test failures due to use of naive timezones with ``datetime``
  instances.

- LP #397861: exporting $PYTHON in generated 'zopectl' for fixing import issue
  with "bin/zopectl adduser"

- LP #399633: fixed interpreter paths
