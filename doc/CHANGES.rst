Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

Trunk (unreleased)
------------------

Restructuring
+++++++++++++

- Removed deprecated ``read-only-database`` option from zope.conf.

- Updated copyright and license information to conform with repository policy.

- Moved the ``absoluteurl`` views into the OFS package.

- Moved ``testbrowser`` module into the Testing package.

- Moved the code handling ZCML loading into the ``Zope2.App`` package. The
  component architecture is now setup before the application object is created
  or any database connections are opened. So far the CA was setup somewhat
  randomly in the startup process, when the ``Five`` product was initialized.

- Downgrade the ``manage_* is discouraged. You should use event subscribers
  instead`` warnings to debug level logging. This particular warning hasn't
  motivated anyone to actually change any code.

- Use the standard libraries doctest module in favor of the deprecated version
  in zope.testing.

- Finished the move of five.formlib to an extra package and removed it from
  Zope 2 itself. Upgrade notes have been added to the news section of the
  release notes.

- Moved Products.Sessions APIs from ``SessionInterfaces`` to ``interfaces``,
  leaving behind the old module / names for backward compatibility.

- Moved ``cmf.*`` permissions into Products.CMFCore.

- Moved general OFS related ZCML directives from Products.Five into the OFS
  package itself.

- Ported the lazy expression into zope.tales and require a new version of it.

- Updated Five documentation to clarify its role in regard to Zope packages.

- Removed the deprecated ``five:containerEvents`` directive, which had been
  a no-op for quite a while.

- Removed Products.Five.fivedirectives.IBridgeDirective - a leftover from the
  Interface to zope.interface bridging code.

- Marked the ``<five:implements />`` as officially deprecated. The standard
  ``<class />`` directive allows the same.

- Reuse IInclude from zope.configuration.xmlconfig.

- Reuse IMenuItemType from zope.browsermenu.

- Moved TaintedString from ZPublisher to Shared.
  This resolves a circular import issue.

- We no longer depend on the ``zope-functional-testing`` extra of
  zope.testbrowser.

- Removed the dependency on zope.app.publication in favor of new versions of
  zope.publisher and zope.traversing.

- Changed startup server tests in Zope2 to use a randomized port number, to
  allow the nightly buildbot to run the tests at the same time for multiple
  configurations without the port being already in use.

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

- Integrated the Products.signalstack / z3c.deadlockdebugger packages. You can
  now send a SIGUSR1 signal to a Zope process and get a stack trace of all
  threads printed out on the console. This works even if all threads are stuck.

- ZCTextIndex query parser treats fullwidth space characters defined
  in Unicode as valid white space.

- Updated packages:

  - Acquisition = 2.13.2
  - initgroups = 2.13.0
  - Missing = 2.13.0
  - MultiMapping = 2.13.0
  - Record = 2.13.0
  - ThreadLock = 2.13.0
  - zope.annotation = 3.5.0
  - zope.app.form = 3.12.1
  - zope.broken = 3.6.0
  - zope.browsermenu = 3.9.0
  - zope.browserpage = 3.11.0
  - zope.browserresource = 3.10.2
  - zope.component = 3.9.3
  - zope.configuration = 3.7.1
  - zope.container = 3.11.0
  - zope.contentprovider = 3.6.1
  - zope.contenttype = 3.5.1
  - zope.copypastemove = 3.6.0
  - zope.dublincore = 3.6.0
  - zope.filerepresentation = 3.6.0
  - zope.formlib = 3.10.0
  - zope.i18nmessageid = 3.5.0
  - zope.location = 3.9.0
  - zope.lifecycleevent = 3.6.0
  - zope.ptresource = 3.9.0
  - zope.publisher = 3.12.1
  - zope.schema = 3.6.1
  - zope.securitypolicy = 3.6.1
  - zope.sendmail = 3.7.1
  - zope.site = 3.9.0
  - zope.testbrowser = 3.7.0
  - zope.testing = 3.9.3
  - zope.traversing = 3.12.0
  - zope.viewlet = 3.7.0

Bugs Fixed
++++++++++

- LP #143604: Removed top-level database-quota-size from zope.conf, some
  storages support a quota option instead.

- LP #143089: Removed the top-level zeo-client-name option from zope.conf, as
  it had no effect since ZODB 3.2.

- LP #143410: Removed unnecessary color definition in ZMI CSS.

- LP #143391: Protect against missing acl_users.hasUsers on quick start page.

- Fixed issue with sending text containing ':' from MailHost.

- MailHost will now ensure the headers it sets are 7bit.

- MailHost no longer generates garbage when given unicode input.

- Unfutzed test failures due to use of naive timezones with ``datetime``
  instances.
