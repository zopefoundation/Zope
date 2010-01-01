Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

Trunk (unreleased)
------------------

Restructuring
+++++++++++++

- Marked the ``<five:implements />`` as officially deprecated. The standard
  ``<class />`` directive allows the same.

- Reuse IInclude from zope.configuration.xmlconfig.

- Reuse IMenuItemType from zope.browsermenu.

- Moved TaintedString from ZPublisher to Shared.
  This resolves a circular import issue.

- Moved zope.formlib / zope.app.form integration into a separate package
  called five.formlib.

- We no longer depend on the ``zope-functional-testing`` extra of
  zope.testbrowser.

- Removed the dependency on zope.app.publication in favor of new versions of
  zope.publisher and zope.traversing.

- Requiring Python 2.6 officially

- Changed startup server tests in Zope2 to use a randomized port number, to
  allow the nightly buildbot to run the tests at the same time for multiple
  configurations without the port being already in use.

- Cloned ``ZopeVocabularyRegistry`` from ``zope.app.schema``, and added
  sane registration of it during initialization of Five.

- Removed experimental support for configuring the Twisted HTTP server
  as an alternative to ``ZServer``.

- Moved ``Products/Five/security.py`` and security related ZCML configuration
  into the AccessControl package.

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

- Integrated zLOG package back into this distribution.

- Updated documentation to new version number.

Features Added
++++++++++++++

- The send method of MailHost now supports unicode messages and
  email.Message.Message objects.  It also now accepts charset and
  msg_type parameters to help with character, header and body
  encoding.

- Updated packages:

  - zope.annotation = 3.5.0
  - zope.app.form = 3.12.1
  - zope.browsermenu = 3.9.0
  - zope.browserpage = 3.11.0
  - zope.browserresource = 3.10.2
  - zope.component = 3.8.0
  - zope.configuration = 3.7.0
  - zope.container = 3.11.0
  - zope.contentprovider = 3.6.1
  - zope.contenttype = 3.5.0
  - zope.copypastemove = 3.6.0
  - zope.dublincore = 3.6.0
  - zope.filerepresentation = 3.6.0
  - zope.formlib = 3.10.0
  - zope.i18nmessageid = 3.5.0
  - zope.location = 3.9.0
  - zope.lifecycleevent = 3.6.0
  - zope.ptresource = 3.9.0
  - zope.publisher = 3.12.0
  - zope.schema = 3.6.0
  - zope.securitypolicy = 3.6.1
  - zope.sendmail = 3.6.1
  - zope.site = 3.9.0
  - zope.testbrowser = 3.7.0
  - zope.testing = 3.8.3
  - zope.traversing = 3.12.0
  - zope.viewlet = 3.7.0

Bugs Fixed
++++++++++

- LP #143444: add labels to checkboxes / radio buttons on import / export
  form.

- LP #496961:  Remove all mention of ``standard_html_header`` and
  ``standard_html_footer`` from default DTML content.

- LP #491249:  fix tabindex on ZRDB connection test form.

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
