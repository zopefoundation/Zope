Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

2.13.13 (2012-02-20)
--------------------

- LP #933307: Fixed ++skin++ namespace handling.
  Ported the ``shiftNameToApplication`` implementation from zope.publisher to
  ZPublisher.HTTPRequest.HTTPRequest.

- Ensure that ObjectManager's ``get`` and ``__getitem__`` methods return only
  "items" (no attributes / methods from the class or from acquisition).
  Thanks to Richard Mitchell at Netsight for the report.

- Updated to Zope Toolkit 1.0.6.

- Removed HTML tags from exception text of ``Unauthorized`` exception
  because these tags get escaped since CVE-2010-1104 (see 2.13.12) got
  fixed.

2.13.12 (2012-01-18)
--------------------

- Prevent a cross-site-scripting attack against the default standard
  error message handling.  (CVE-2010-1104).

- Use ``in`` operator instead of deprecated ``has_key`` method (which
  is not implemented by ``OFS.ObjectManager``). This fixes an issue
  with WebDAV requests for skin objects.

- Updated distributions:

  - Products.ZCatalog = 2.13.22

2.13.11 (2011-12-12)
--------------------

- Turn `UndoSupport.get_request_var_or_attr` helper into a private API.

- LP #902068: Fixed missing security declaration for `ObjectManager` class.

- Avoid conflicting signal registrations when run under mod_wsgi.
  Allows the use of `WSGIRestrictSignal Off` (LP #681853).

- Make it possible to use WSGI without repoze.who.

- Fixed serious authentication vulnerability in stock configuration.

- Updated distributions:

  - AccessControl = 2.13.7
  - DocumentTemplate = 2.13.2
  - Products.BTreeFolder2 = 2.13.4
  - python-gettext = 1.2
  - repoze.who = 2.0
  - ZODB3 = 3.10.5
  - Zope Toolkit 1.0.5

2.13.10 (2011-10-04)
--------------------

- Fixed serious arbitrary code execution issue (CVE 2011-3587)
  http://zope2.zope.org/news/security-vulnerability-announcement-cve-2011-3587

- Fixed a regression of 2.13.9 in webdav support that broke external editor
  feature.

- `undoMultiple` was still broken as transactions were not undone in the proper
  order : tids were stored and retrieved as dictionary keys.

- Updated distributions:

  - Products.ZCatalog = 2.13.20

2.13.9 (2011-08-20)
-------------------

Bugs Fixed
++++++++++

- Restore ability to undo multiple transactions from the ZMI by using the
  `undoMultiple` API. Backported from trunk (r122087).

- Fixed Chameleon compatibility in templates.

- Updated distributions:

  - Products.ZCatalog = 2.13.19
  - Products.ZCTextIndex = 2.13.3
  - repoze.tm2 = 1.0b2
  - Zope Toolkit 1.0.4

2.13.8 (2011-06-28)
-------------------

Bugs Fixed
++++++++++

- Fixed a serious privilege escalation issue. For more information see:
  http://plone.org/products/plone/security/advisories/20110622

- Ensure __name__ is not None as well as __name__ existing. For example, object
  could be a widget within a z3c.form MultiWidget, which do not have __name__ set.

- Testing: Re-added 'extra' argument to Functional.publish.
  Removing it in Zope 2.13.0a1 did break backwards compatibility.

- LP #787541: Fix WSGIPublisher to close requests on abort unconditionally.
  Previously an addAfterCommitHook was used, but this is not run on transaction
  aborts.  Now a Synchronizer is used which unconditionally closes the request
  after a transaction is finished.

Features Added
++++++++++++++

- Updated distributions:

  - Acquisition = 2.13.8
  - Products.ZCatalog = 2.13.14
  - repoze.who = 2.0b1
  - ZODB3 = 3.10.3
  - Zope Toolkit 1.0.3

2.13.7 (2011-05-08)
-------------------

Features Added
++++++++++++++

- Added forward compatibility with DateTime 3.

- ZPublisher: HTTPResponse.appendHeader now keeps header values to a single
  line by default to avoid causing problems for proxy servers which do not
  correctly handle multi-line headers.

- Updated distributions:

  - Products.ZCatalog = 2.13.13
  - Products.ZCTextIndex = 2.13.2

2.13.6 (2011-04-03)
-------------------

Bugs Fixed
++++++++++

- Fix `WSGIResponse` and `publish_module` functions such that they
  support the `IStreamIterator` interface in addition to `file` (as
  supported by `ZServer.HTTPResponse`).

- Corrected copyright information shown in the ZMI.

- OFS: Fixed editing offset-naive 'date' properties in the ZMI.
  The "Properties" tab no longer shows the time zone of offset-naive dates.

Features Added
++++++++++++++

- Add preliminary IPv6 support to ZServer.

- Updated to Zope Toolkit 1.0.2.

- Updated distributions:

  - Acquisition = 2.13.7
  - mechanize = 0.2.5
  - Products.BTreeFolder2 = 2.13.3
  - Products.ZCatalog = 2.13.8
  - python-gettext = 1.1.1
  - pytz = 2011e
  - repoze.tm2 = 1.0b1
  - repoze.who = 2.0a4
  - ZConfig = 2.9.0
  - zope.testbrowser = 3.11.1

2.13.5 (2011-02-23)
-------------------

Bugs Fixed
++++++++++

- Five: Corrected a method name in the IReadInterface interface.

Features Added
++++++++++++++

- Updated distributions:

  - Acquisition = 2.13.6
  - Products.ZCatalog = 2.13.6
  - ZODB3 = 3.10.2

2.13.4 (2011-02-06)
-------------------

Bugs Fixed
++++++++++

- Applied missing bit of the code merge for LP #713253.

2.13.3 (2011-02-06)
-------------------

Features Added
++++++++++++++

- Updated distributions:

  - Products.ZCatalog = 2.13.5

Bugs Fixed
++++++++++

- LP #713253: Prevent publication of acquired attributes, where the acquired
  object does not have a docstring.


2.13.2 (2011-01-19)
-------------------

Bugs Fixed
++++++++++

- HelpSys: Fixed some permission checks.

- OFS: Fixed permission check in ObjectManager.

- webdav: Fixed permission check and error handling in DeleteCollection.

- LP 686664: WebDAV Lock Manager ZMI view wasn't accessible.

Features Added
++++++++++++++

- Report success or failure (when known) of creating a new user with the
  `addzope2user` script.

- Added `addzope2user` script, suitable for adding an admin user directly to
  the root acl_users folder.

- Updated distributions:

  - AccessControl = 2.13.4
  - Products.ZCatalog = 2.13.3

Restructuring
+++++++++++++

- Factored out the `Products.ZCatalog` and `Products.PluginIndexes` packages
  into a new `Products.ZCatalog` distribution.

2.13.1 (2010-12-07)
-------------------

Bugs Fixed
++++++++++

- Fixed argument parsing for entrypoint based zopectl commands.

- Fixed the usage of ``pstats.Stats()`` output stream. The
  `Control_Panel/DebugInfo/manage_profile` ZMI view was broken in Python 2.5+.

Features Added
++++++++++++++

- Report success or failure (when known) of creating a new user with
  the addzope2user script.

- Moved subset id calculation in `OFS.OrderSupport.moveObjectsByDelta` to a
  new helper method, patch by Tom Gross.

- Updated to Zope Toolkit 1.0.1.

- Use cProfile where possible for the `Control_Panel/DebugInfo/manage_profile`
  ZMI view.

Restructuring
+++++++++++++

- Stopped testing non-overridden ZTK eggs in ``bin/alltests``.

2.13.0 (2010-11-05)
-------------------

- No changes.

2.13.0c1 (2010-10-28)
---------------------

Bugs Fixed
++++++++++

- LP #628448:  Fix ``zopectl start`` on non-Windows platforms.

Features Added
++++++++++++++

- Updated to Zope Toolkit 1.0.

- Updated distributions:

  - DateTime = 2.12.6
  - mechanize = 0.2.3
  - ZODB3 = 3.10.1
  - zope.sendmail = 3.7.4
  - zope.testbrowser = 3.10.3

2.13.0b1 (2010-10-09)
---------------------

Bugs Fixed
++++++++++

- Avoid iterating over the list of packages to initialize while it is being
  mutated, which was skipping some packages.

- Fixed two unit tests that failed on fast Windows machines.

- Fixed OverflowError in Products.ZCatalog.Lazy on 64bit Python on Windows.

- Fixed ``testZODBCompat`` tests in ZopeTestCase to match modern ZODB
  semantics.

- LP #634942: Only require ``nt_svcutils`` on Windows.

Features Added
++++++++++++++

- Avoid conflict error hotspot in PluginIndexes' Unindex class by using
  IITreeSets instead of simple ints from the start. Idea taken from
  ``enfold.fixes``.

- Added date range index improvements from ``experimental.catalogqueryplan``.

- Changed policy on handling exceptions during ZCML parsing in ``Products``.
  We no longer catch any exceptions in non-debug mode.

- Added a new BooleanIndex to the standard PluginIndexes.

- Update to Zope Toolkit 1.0c3.

- Add ability to define extra zopectl commands via setuptools entrypoints.

- Updated distributions:

  - Acquisition = 2.13.5
  - Products.MailHost = 2.13.1
  - Products.ZCTextIndex = 2.13.1
  - repoze.retry = 1.0
  - tempstorage = 2.12.1
  - ZODB3 = 3.10.0
  - zope.testbrowser = 3.10.1

2.13.0a4 (2010-09-09)
---------------------

Restructuring
+++++++++++++

- Removed deprecated
  ``Products.Five.security.create_permission_from_permission_directive``
  event handler. Its code was moved into the Zope 2 version of the permission
  directive in ``AccessControl.security``.

Features Added
++++++++++++++

- LP #193122: New method getVirtualRoot added to the Request class.

- Updated test assertions to use unittest's ``assert*`` methods in favor of
  their deprecated `fail*` aliases.

- Update to Zope Toolkit 1.0a3.

- Updated distributions:

  - AccessControl = 2.13.3
  - Acquisition = 2.13.4
  - ZODB3 = 3.10.0b6

2.13.0a3 (2010-08-04)
---------------------

Bugs Fixed
++++++++++

- Adjusted overflow logic in DateIndex and DateRangeIndex to work with latest
  ZODB 3.10.0b4.

- Made sure to exclude a number of meta ZCML handlers from ``zope.*`` packages
  where Zope2 provides its own implementations.

- LP #599378: Fixed accumulated_headers not appending to headers correctly.

- Fix support for non-public permission attributes in the
  browser:view directive so that attributes which are not included in
  allowed_interface or allowed_attributes but which have declarations from a
  base class's security info don't get their security overwritten to be
  private.

- LP #143755: Also catch TypeError when trying to determine an
  indexable value for an object in PluginIndexes.common.UnIndex

- LP #143533: Instead of showing "0.0.0.0" as the SERVER_NAME
  request variable when no specific listening IP is configured for
  the HTTP server, do a socket lookup to show the current server's
  fully qualified name.

- LP #143722: Added missing permission to ObjectManager.manage_hasId,
  which prevented renaming files and folders via FTP.

- LP #143564: Request.resolve_url did not correctly re-raise
  exceptions encountered during path traversal.

Restructuring
+++++++++++++

- Removed catalog length migration code. You can no longer directly upgrade a
  Zope 2.7 or earlier database to Zope 2.13. Please upgrade to an earlier
  release first.

- Deprecated the ``Products.ZCatalog.CatalogAwareness`` and
  ``CatalogPathAwareness`` modules.

- Removed deprecated ``catalog-getObject-raises`` zope.conf option.

- Removed unmaintained HelpSys documents from ZCatalog and PluginIndexes.
  Useful explanations are given inside the form templates.

- Deprecate Products.ZCatalog's current behavior of returning the entire
  catalog content if no query restriction applied. In Zope 2.14 this will
  result in an empty LazyCat to be returned instead.

- Deprecate acquiring the request inside Products.ZCatalog's searchResults
  method if no explicit query argument is given.

- Cleaned up the Products.ZCatalog search API's. The deprecated support for
  using `<index id>_usage` arguments in the request has been removed. Support
  for overriding operators via the `<index id>_operator` syntax has been
  limited to the query value for each index and no longer works directly on
  the request. The query is now brought into a canonical form before being
  passed into the `_apply_index` method of each index.

- Factored out the `Products.MailHost` package into its own distributions. It
  will no longer be included by default in Zope 2.14 but live on as an
  independent add-on.

Features Added
++++++++++++++

- Merged the query plan support from both ``unimr.catalogqueryplan`` and
  ``experimental.catalogqueryplan`` into ZCatalog. On sites with large number of
  objects in a catalog (in the 100000+ range) this can significantly speed up
  catalog queries. A query plan monitors catalog queries and keeps detailed
  statistics about their execution. Currently the plan keeps track of execution
  time, result set length and support for the ILimitedResultIndex per index for
  each query. It uses this information to devise a better query execution plan
  the next time the same query is run. Statistics and the resulting plan are
  continuously updated. The plan is per running Zope process and not persisted.
  You can inspect the plan using the ``Query Plan`` ZMI tab on each catalog
  instance. The representation can be put into a Python module and the Zope
  process be instructed to load this query plan on startup. The location of the
  query plan is specified by providing the dotted name to the query plan
  dictionary in an environment variable called ``ZCATALOGQUERYPLAN``.

- Various optimizations to indexes _apply_index and the catalog's search
  method inspired by experimental.catalogqueryplan.

- Added a new ILimitedResultIndex to Products.PluginIndexes and made most
  built-in indexes compatible with it. This allows indexes to consider the
  already calculated result set inside their own calculations.

- Changed the internals of the DateRangeIndex to always use IITreeSet and do
  an inline migration from IISet. Some datum tend to have large number of
  documents, for example when using default floor or ceiling dates.

- Added a new reporting tab to `Products.ZCatalog` instances. You can use this
  to get an overview of slow catalog queries, as specified by a configurable
  threshold value.

- Warn when App.ImageFile.ImageFile receives a relative path with no prefix,
  and then has to assume the path to be relative to "software home". This
  behaviour is deprecated as packages can be factored out to their own
  distribution, making the "software home" relative path meaningless.

- Updated distributions:

  - AccessControl = 2.13.2
  - DateTime = 2.12.5
  - DocumentTemplate = 2.13.1
  - Products.BTreeFolder2 = 2.13.1
  - Products.OFSP = 2.13.2
  - ZODB3 = 3.10.0b4

2.13.0a2 (2010-07-13)
---------------------

Bugs Fixed
++++++++++

- Made ZPublisher tests compatible with Python 2.7.

- LP #143531: Fix broken object so they give access to their state.

- LP #578326: Add support for non-public permission attributes in the
  browser:view directive.

Restructuring
+++++++++++++

- No longer use HelpSys pages from ``Products.OFSP`` in core Zope 2.

- No longer create an `Extensions` folder in the standard instance skeleton.
  External methods will become entirely optional in Zope 2.14.

- Avoid using the ``Products.PythonScripts.standard`` module inside the
  database manager ZMI.

- Factored out the `Products.BTreeFolder2`, `Products.ExternalMethod`,
  `Products.MIMETools`, `Products.OFSP`, `Products.PythonScripts` and
  `Products.StandardCacheManagers` packages into their own distributions. They
  will no longer be included by default in Zope 2.14 but live on as independent
  add-ons.

- Factored out the `Products.ZSQLMethods` into its own distribution. The
  distribution also includes the `Shared.DC.ZRDB` code. The Zope2 distribution
  no longer includes the code automatically. Please depend on the new
  distribution yourself, if you use the functionality. To make the transition
  easier this change has been backported to Zope 2.12.9, so you can depend on
  the new distribution already in packages requiring at least that version of
  Zope 2.

- Made both `Shared` and `Shared.DC` namespace packages.

- Removed fallback code for old Python versions from
  `ZServer.FTPServer.zope_ftp_channel.push`.

- Removed fallback code for old `ZCatalog.catalog_object` function signatures
  from `Products.ZCatalog.ZCatalog.reindexIndex`.

Features Added
++++++++++++++

- Added official support for Python 2.7.

- Added a new API ``get_packages_to_initialize`` to ``OFS.metaconfigure``.
  This replaces any direct access to ``Products._packages_to_initialize``.
  The OFS.Application.install_package function takes care of removing entries
  from this list now.

- Added notification of ``IDatabaseOpenedWithRoot``.

- Added a new API's ``get_registered_packages, set_registered_packages`` to
  ``OFS.metaconfigure`` which replace any direct access to
  ``Products._registered_packages``.

- Changed product install so it won't write persistent changes only to abort
  them. Instead we don't make any database changes in the first place.

- Disabled persistent product installation in the default test configuration.

- Directly extend and use the Zope Toolkit KGS release 1.0a2 from
  http://download.zope.org/zopetoolkit/index/.

- Updated distributions:

  - DateTime = 2.12.4
  - nt_svcutils = 2.13.0

2.13.0a1 (2010-06-25)
---------------------

This release includes all bug fixes and features of the
`Zope 2.12.8 <http://pypi.python.org/pypi/Zope2/2.12.8>`_ release.

Distribution changes
++++++++++++++++++++

- Moved AccessControl, DocumentTemplate (incl. TreeDisplay) and
  Products.ZCTextIndex to their own distributions. This removes the last direct
  C extensions from the Zope2 distribution.

- Moved the ``zExceptions`` package into its own distribution.

- Drop the dependency on the ThreadLock distribution, by using Python's thread
  module instead.

- Integrated the Products.signalstack / z3c.deadlockdebugger packages. You can
  now send a SIGUSR1 signal to a Zope process and get a stack trace of all
  threads printed out on the console. This works even if all threads are stuck.

Instance skeleton
+++++++++++++++++

- Changed the default for ``enable-product-installation`` to off. This matches
  the default behavior of buildout installs via plone.recipe.zope2instance.
  Disabling the persistent product installation also disabled the ZMI help
  system.

- Removed Zope2's own mkzeoinstance script. If you want to set up ZEO instances
  please install the zope.mkzeoinstance and use its script.

- Removed deprecated ``read-only-database`` option from zope.conf.

- LP #143232: Added option to 'zope.conf' to specify an additional directory to
  be searched for 'App.Extensions' lookups. Thanks to Rodrigo Senra for the
  patch.

- LP #143604: Removed top-level database-quota-size from zope.conf, some
  storages support a quota option instead.

- LP #143089: Removed the top-level zeo-client-name option from zope.conf, as it
  had no effect since ZODB 3.2.

- Removed no longer maintained ``configure, make, make install`` related
  installation files. Zope2 can only be installed via its setup.py.

- Removed the unmaintained and no longer functioning ZopeTutorialExamples from
  the instance skeleton.

Deprecated and Removed
++++++++++++++++++++++

- Finished the move of five.formlib to an extra package and removed it from Zope
  2 itself. Upgrade notes have been added to the news section of the release
  notes.

- ZPublisher: Removed 'Main' and 'Zope' wrappers for Test.publish. If anybody
  really used them, he can easily use ZPublisher.test instead. In the long run
  ZPublisher.test and ZPublisher.Test might also be removed.

- ZPublisherExceptionHook: Removed ancient backwards compatibility code.
  Customized raise_standardErrorMessage methods have to implement the signature
  introduced in Zope 2.6.

- Removed ancient App.HotFixes module.

- Removed the deprecated ``hasRole`` method from user objects.

- Removed deprecated support for specifying ``__ac_permissions__``,
  ``meta_types`` and ``methods`` in a product's ``__init__``.

- Remove remaining support classes for defining permissions TTW.

- Removed the deprecated ``five:containerEvents`` directive, which had been a
  no-op for quite a while.

- Removed Products.Five.fivedirectives.IBridgeDirective - a leftover from the
  Interface to zope.interface bridging code.

- Marked the ``<five:implements />`` as officially deprecated. The standard
  ``<class />`` directive allows the same.

Refactoring
+++++++++++

- Completely refactored ``ZPublisher.WSGIResponse`` in order to provide
  non-broken support for running Zope under arbitrary WSGI servers. In this
  (alternate) scenario, transaction handling, request retry, error handling,
  etc. are removed from the publisher, and become the responsibility of
  middleware.

- Moved the code handling ZCML loading into the ``Zope2.App`` package. The
  component architecture is now setup before the application object is created
  or any database connections are opened. So far the CA was setup somewhat
  randomly in the startup process, when the ``Five`` product was initialized.

- Moved Products.Sessions APIs from ``SessionInterfaces`` to ``interfaces``,
  leaving behind the old module / names for backward compatibility.

- Centralize interfaces defined in Products.ZCTextIndex, leaving BBB imports
  behind in old locations.

- Moved ``cmf.*`` permissions into Products.CMFCore.

- Moved ``TaintedString`` into the new AccessControl.tainted module.

- Testing: Functional.publish now uses the real publish_module function instead
  of that from ZPublisher.Test. The 'extra' argument of the publish method is no
  longer supported.

- Moved ``testbrowser`` module into the Testing package.

- Moved general OFS related ZCML directives from Products.Five into the OFS
  package.

- Moved the ``absoluteurl`` views into the OFS package.

- Moved ``Products/Five/event.zcml`` into the OFS package.

- Moved ``Products/Five/security.py`` and security related ZCML configuration
  into the AccessControl package.

- Moved ``Products/Five/traversing.zcml`` directly into the configure.zcml.

- Moved ``Products/Five/i18n.zcml`` into the ZPublisher package.

- Moved ``Products/Five/publisher.zcml`` into the ZPublisher package.

- Ported the lazy expression into zope.tales and require a new version of it.

General
+++++++

- Updated copyright and license information to conform with repository policy.

- LP #143410: Removed unnecessary color definition in ZMI CSS.

- LP #374810: ``__bobo_traverse__`` implementation can raise
  ``ZPublisher.interfaces.UseTraversalDefault`` to indicate that there is no
  special casing for the given name and that standard traversal logic should
  be applied.

- LP #142464: Make undo log easier to read. Thanks to Toby Dickinson for the
  patch.

- LP #142401: Added a link in the ZMI tree pane to make the tree state
  persistent. Thanks to Lalo Martins for the patch.

- LP #142502: Added a knob to the Debug control panel for resetting profile
  data. Thanks to Vladimir Patukhov for the patch.

- ZCTextIndex query parser treats fullwidth space characters defined in Unicode
  as valid white space.

Updated distributions
+++++++++++++++++++++

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
- zope.schema = 3.6.4
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

- LP #143391: Protect against missing acl_users.hasUsers on quick start page.
