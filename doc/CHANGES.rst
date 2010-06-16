Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

Trunk (unreleased)
------------------

Restructuring
+++++++++++++

- Testing: Functional.publish now uses the real publish_module function
  instead of that from ZPublisher.Test. The 'extra' argument of the publish
  method is no longer supported.

- Removed the deprecated ``hasRole`` method from user objects.

- Removed deprecated support for specifying ``__ac_permissions__``,
  ``meta_types`` and ``methods`` in a product's ``__init__``.

- Remove remaining support classes for defining permissions TTW.

- Moved ``TaintedString`` into the new AccessControl.tainted module.

- Moved the ``zExceptions`` package into its own distribution.

- Completely refactored ``ZPublisher.WSGIResponse`` in order to provide
  non-broken support for running Zope under arbitrary WSGI servers. In this
  (alternate) scenario, transaction handling, request retry, error handling,
  etc. are removed from the publisher, and become the responsibility of
  middleware.

- Drop the dependency on the ThreadLock distribution, by using Python's thread
  module instead.

- Removed Zope2's own mkzeoinstance script. If you want to set up ZEO instances
  please install the zope.mkzeoinstance and use its script.

- Removed deprecated ``read-only-database`` option from zope.conf.

- Updated copyright and license information to conform with repository policy.

- Moved the ``absoluteurl`` views into the OFS package.

- Moved ``testbrowser`` module into the Testing package.

- Moved the code handling ZCML loading into the ``Zope2.App`` package. The
  component architecture is now setup before the application object is created
  or any database connections are opened. So far the CA was setup somewhat
  randomly in the startup process, when the ``Five`` product was initialized.

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

- LP #142226: Added an extra keyword argument to the HTTPResponse 
  setCookie method to suppress enclosing the cookie value field 
  in double quotes.

- LP #142464:  Make undo log easier to read.  Thanks to Toby Dickinson
  for the patch.

- LP #142401:  Added a link in the ZMI tree pane to make the tree state
  persistent.  Thanks to Lalo Martins for the patch.

- LP #142502:  Added a knob to the Debug control panel for resetting
  profile data.  Thanks to Vladimir Patukhov for the patch.

- LP #143232: Added option to 'zope.conf' to specify an additional directory
  to be searched for 'App.Extensions' lookups.  Thanks to Rodrigo Senra for
  the patch.

- Integrated the Products.signalstack / z3c.deadlockdebugger packages. You can
  now send a SIGUSR1 signal to a Zope process and get a stack trace of all
  threads printed out on the console. This works even if all threads are stuck.

- ZCTextIndex query parser treats fullwidth space characters defined
  in Unicode as valid white space.

- Updated packages:

  - Jinja2 = 2.5.0
  - RestrictedPython = 3.6.0a1
  - Sphinx = 1.0b2
  - transaction = 1.1.0
  - ZConfig = 2.8.0
  - ZODB3 = 3.10.0b1
  - zope.annotation = 3.5.0
  - zope.broken = 3.6.0
  - zope.browsermenu = 3.9.0
  - zope.browserpage = 3.12.2
  - zope.browserresource = 3.10.3
  - zope.component = 3.9.4
  - zope.configuration = 3.7.2
  - zope.container = 3.11.1
  - zope.contentprovider = 3.7.2
  - zope.contenttype = 3.5.1
  - zope.event = 3.5.0-1
  - zope.exceptions = 3.6.0
  - zope.filerepresentation = 3.6.0
  - zope.i18nmessageid = 3.5.0
  - zope.interface = 3.6.1
  - zope.location = 3.9.0
  - zope.lifecycleevent = 3.6.0
  - zope.ptresource = 3.9.0
  - zope.publisher = 3.12.3
  - zope.schema = 3.6.3
  - zope.sendmail = 3.7.2
  - zope.site = 3.9.1
  - zope.structuredtext = 3.5.0
  - zope.tales = 3.5.1
  - zope.testbrowser = 3.9.0
  - zope.testing = 3.9.3
  - zope.traversing = 3.12.1
  - zope.viewlet = 3.7.2

Bugs Fixed
++++++++++

- LP #143403: Prevent accidental acquisition of objectValues during
  recursive ownership changes when the changed object has no
  objectValues method.

- LP #142535: Fix faulty docstring for manage_changeProperties which
  incorrectly suggested that passing a simple dictionary as REQUEST
  argument was supported.

- LP #374818: Use module-provided functions as opposed to the old
  "folder methods" when creating folders and user folders in
  ZopeTestCase.

- LP #143946: Provide a more informative error message when a
  WebDAV PUT fails.

- LP #143261: The (very old-fashioned) Zope2.debug interactive request
  debugger still referred to the toplevel module ``Zope``, which was
  renamed to ``Zope2`` a long time ago.

- LP #142874: Naming objects ``URL`` or ``URL1`` broke several ZMI
  views.

- LP #142878: Remove URL-based suppression of access rules and site root
  objects.   Suppression using ``os.environ`` still works.

- LP #143144: Fix documentation for the zope.conf ``mount-point``
  directive.

- LP #142410: Do not index documents in a KeywordIndex if the document 
  is missing the indexed attribute, if determining the value raises 
  AttributeError, or of the indexed attribute is empty.

- LP #142590: The ``DTMLMethod`` and ``DTMLDocument`` ``manage_edit`` 
  methods could not deal with ``TaintedString`` instances. Removed the 
  entirely redundant ``DTMLDocument.manage_edit`` method at the same time.

- LP #142750 and LP #142481: To prevent confusion when choosing an Id and 
  to avoid issues when creating two VirtualHostMonsters in the same 
  container the VirtualHostMoster now has a default Id. It can no longer 
  be selected, and the intermediary Add view is gone.

- LP #142451: If non-recursive ownership changes are made using 
  ``changeOwnership``, do not touch any children.

- LP #142563:  Fix ``AccessControl.User.NullUnrestrictedUserTests.__str__``.

- LP #267820:  Fix bad except clause in the ``sequence_sort`` method of
  the ``<dtml-in>`` tag.

- LP #351006:  Don't nest block tags inside HTML ``<p>`` tags in
  ``zExceptions.ExceptionFormatter``.

- LP #411837:  Handle resource files with ``.htm`` extention properly,
  as page template resources.

- LP #435729:  Fix indentation of OFSP/help/sequence.py docstring.

- LP #574286:  Ensure that mailhosts which share a queue directory do not
  double-deliver mails, by sharing the thread which processes emails for
  that directory.

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
