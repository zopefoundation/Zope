Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

Trunk (unreleased)
------------------

Restructuring
+++++++++++++

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

- Updated packages:

  - roman = 1.4.0
  - zc.buildout = 1.4.1
  - zope.app.applicationcontrol = 3.5.1
  - zope.app.appsetup = 3.12.0
  - zope.app.cache = 3.6.0
  - zope.app.form = 3.8.1
  - zope.app.i18n = 3.6.1
  - zope.app.publication = 3.8.1
  - zope.app.publisher = 3.9.0
  - zope.app.renderer = 3.5.1
  - zope.app.security = 3.7.1
  - zope.app.testing = 3.7.1
  - zope.app.wsgi = 3.6.0
  - zope.app.zcmlfiles = 3.6.0
  - zope.browsermenu = 3.9.0
  - zope.browserresource = 3.9.0
  - zope.component = 3.7.1
  - zope.container = 3.9.0
  - zope.i18nmessageid = 3.5.0
  - zope.index = 3.6.0
  - zope.location = 3.6.0
  - zope.ptresource = 3.9.0
  - zope.publisher = 3.9.0
  - zope.securitypolicy = 3.6.1
  - zope.server = 3.6.0
  - zope.site = 3.6.2
  - zope.testbrowser = 3.7.0a1
  - zope.testing = 3.8.1
  - zope.traversing = 3.7.2
  - zope.viewlet = 3.6.1

Bugs Fixed
++++++++++

- Fixed issue with sending text containing ':' from MailHost.

- MailHost will now ensure the headers it sets are 7bit.

- MailHost no longer generates garbage when given unicode input.

- Made C extensions work for 64-bit Python 2.5.x / 2.6.x.

- Unfutzed test failures due to use of naive timezones with ``datetime``
  instances.

- LP #397861: exporting $PYTHON in generated 'zopectl' for fixing import issue
  with "bin/zopectl adduser"

- LP #399633: fixed interpreter paths
