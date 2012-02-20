Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

2.12.23 (2012-02-20)
--------------------

- Note end-of-life timeline: Zope 2.12.x is now in security-fix-only mode and
  will continue to see security updates until October 2013, the same as Python
  2.6.x does.

- Ensure that ObjectManager's ``get`` and ``__getitem__`` methods return only
  "items" (no attributes / methods from the class or from acquisition).
  Thanks to Richard Mitchell at Netsight for the report.

- Updated distributions:

  - distribute = 0.6.24
  - Products.ZSQLMethods = 2.13.4
  - zope.catalog = 3.8.2
  - zope.componentvocabulary = 1.0.1
  - zope.datetime = 3.4.1
  - zope.deprecation = 3.4.1
  - zope.documenttemplate = 3.4.3
  - zope.index = 3.6.3
  - zope.keyreference = 3.6.4
  - zope.mkzeoinstance = 3.9.5
  - zope.session = 3.9.5
  - zope.testing = 3.9.7

2.12.22 (2012-01-18)
--------------------

- Prevent a cross-site-scripting attack against the default standard
  error message handling.  (CVE-2010-1104).

2.12.21 (2011-12-12)
--------------------

- Restrict the available functions in `DocumentTemplate.sequence` to public
  API's of `zope.sequencesort`.

- Turn `UndoSupport.get_request_var_or_attr` helper into a private API.

- Provide security declarations for `BTreeFolder2Base` class, instead of only
  for `BTreeFolder2` via the `OFS.Folder` mix-in.

- LP #902068: Fixed missing security declaration for `ObjectManager` class.

- Fixed serious authentication vulnerability in stock configuration.

2.12.20 (2011-10-04)
--------------------

- Fixed serious arbitrary code execution issue (CVE 2011-3587)
  http://zope2.zope.org/news/security-vulnerability-announcement-cve-2011-3587

2.12.19 (2011-06-28)
--------------------

Bugs Fixed
++++++++++

- Fixed a serious privilege escalation issue. For more information see:
  http://plone.org/products/plone/security/advisories/20110622

Features
++++++++

- Updated distributions:

  - Acquisition = 2.13.8


2.12.18 (2011-05-08)
--------------------

Features
++++++++

- Updated distributions:

  - zope.sendmail = 3.5.3

2.12.17 (2011-04-03)
--------------------

Bugs Fixed
++++++++++

- Corrected copyright information shown in the ZMI.

Features
++++++++

- Updated distributions:

  - Acquisition = 2.13.7
  - distribute = 0.6.15
  - docutils = 0.7
  - python-gettext = 1.1.1
  - pytz = 2011e
  - transaction = 1.0.1

2.12.16 (2011-02-23)
--------------------

Bugs Fixed
++++++++++

- LP #713820: Remove docstrings from various methods in ZCatalog, as they
  shouldn't be web-publishable.

Features
++++++++

- Updated distributions:

  - Acquisition = 2.13.6

2.12.15 (2011-02-06)
--------------------

Bugs Fixed
++++++++++

- LP #713253: Prevent publication of acquired attributes, where the acquired
  object does not have a docstring.

- Fix `LazyMap` to avoid unnecessary function calls.

2.12.14 (2010-12-07)
--------------------

Bugs Fixed
++++++++++

- Fixed argument parsing for entrypoint based zopectl commands.

- Fixed the usage of ``pstats.Stats()`` output stream. The
  `Control_Panel/DebugInfo/manage_profile` ZMI view was broken in Python 2.5+.

- Use cProfile where possible for the `Control_Panel/DebugInfo/manage_profile`
  ZMI view.

2.12.13 (2010-11-06)
--------------------

Bugs Fixed
++++++++++

- Fixed Chameleon compatibility in `ptEdit.zpt` of `Products.PageTemplates`.

Features Added
++++++++++++++

- LP #659968: Added support for level argument to the ``__import__`` function
  as introduced in Python 2.5. Currently only level=-1 is supported.

- Updated distributions:

  - DateTime = 2.12.6

2.12.12 (2010-10-02)
--------------------

Bugs Fixed
++++++++++

- Adjusted overflow logic in DateIndex and DateRangeIndex to work with latest
  ZODB 3.9.7.

- Fixed ``testZODBCompat`` tests in ZopeTestCase to match modern ZODB
  semantics.

- Fixed unit test that failed on fast Windows machines.

- Fixed OverflowError in Products.ZCatalog.Lazy on 64bit Python on Windows.

- LP #642728: Fixed TypeError on nested multi part messages in MailHost.

Features Added
++++++++++++++

- Add ability to define extra zopectl commands via setuptools entrypoints.

- Updated distributions:

  - Acquisition = 2.13.5
  - distribute = 0.6.14
  - lxml = 2.2.8
  - z3c.checkversions = 0.4.1
  - zc.buildout = 1.4.4
  - zc.recipe.testrunner = 1.2.1
  - ZODB3 = 3.9.7
  - zope.app.error = 3.5.3
  - zope.app.interface = 3.5.2
  - zope.app.locales = 3.6.2
  - zope.app.session = 3.6.2
  - zope.deferredimport = 3.5.3
  - zope.i18n = 3.7.4
  - zope.i18nmessageid = 3.5.3
  - zope.index = 3.6.1
  - zope.lifecycleevent = 3.6.2
  - zope.pagetemplate = 3.5.2
  - zope.principalregistry = 3.7.1
  - zope.proxy = 3.6.1
  - zope.security = 3.7.4
  - zope.sendmail = 3.5.2
  - zope.session = 3.9.3

2.12.11 (2010-09-09)
--------------------

Bugs Fixed
++++++++++

- BasicUserFolder and SiteErrorLog: Don't raise string exceptions.

Features Added
++++++++++++++

- LP #193122: New method getVirtualRoot added to the Request class.

- Added forward-compatibility shims for some frequently used modules moved in
  Zope 2.13.

- Updated packages:

  - Acquisition = 2.13.4
  - DateTime = 2.12.5
  - Products.ZSQLMethods = 2.13.3

2.12.10 (2010-07-20)
--------------------

Bugs Fixed
++++++++++

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

- LP #143273: Enable the dtml-var modifiers url_quote, url_unquote,
  url_quote_plus and url_unquote_plus to handle unicode strings.

Features Added
++++++++++++++

- Warn when App.ImageFile.ImageFile receives a relative path with no prefix,
  and then has to assume the path to be relative to "software home". This
  behaviour is deprecated as packages can be factored out to their own
  distribution, making the "software home" relative path meaningless.

2.12.9 (2010-07-13)
-------------------

Bugs Fixed
++++++++++

- Avoid problems in removing cache managers introduced in Zope 2.12.8.

- LP #143531: Fix broken object so they give access to their state.

- LP #578326: Add support for non-public permission attributes in the
  browser:view directive.

Features Added
++++++++++++++

- Factored out the `Products.ZSQLMethods` into its own distribution. The
  distribution also includes the `Shared.DC.ZRDB` code. The code is no longer
  included in Zope 2.13. If you rely on it, please specify a dependency on
  the new `Products.ZSQLMethods` distribution. This will only work for code
  that requires at least Zope 2.12.9.

- Made both `Shared` and `Shared.DC` namespace packages.

- Updated packages:

  - DateTime = 2.12.4

2.12.8 (2010-06-25)
-------------------

Bugs Fixed
++++++++++

- LP #597594: Performance optimization in OFS.subscriber.maybeWarnDeprecated.

- LP #143639: When the last cache manager in a container is deleted, we need to
  remove all traces of it from the container.

- LP #143619: Make sure to remove a RAMCache's contents when the ZODB object is
  removed.

- LP #143403: Prevent accidental acquisition of objectValues during recursive
  ownership changes when the changed object has no objectValues method.

- LP #374818: Use module-provided functions as opposed to the old
  "folder methods" when creating folders and user folders in ZopeTestCase.

- LP #143946: Provide a more informative error message when a WebDAV PUT fails.

Features Added
++++++++++++++

- Updated packages:

  - ExtensionClass = 2.13.2
  - Missing = 2.13.1
  - Persistence = 2.13.2
  - Sphinx = 0.6.7

- Added ``setSortKey()`` method to the ``Shared.DC.ZRDB.TM.TM`` class to allow
  database connections to specify the commit order without needing to override
  the ``sortKey()`` method.

2.12.7 (2010-06-13)
-------------------

Bugs Fixed
++++++++++

- LP #142535: Fix faulty docstring for manage_changeProperties which
  incorrectly suggested that passing a simple dictionary as REQUEST
  argument was supported.

- LP #583702: Fixed regression in mailhost queue processor code introduced
  in 2.12.6 in the LP #574286 changes.

- Handle Unauthorized exceptions in xmlrpc correctly.

- Five's processInputs() would stomp on :list or :tuple values that contained
  ints or other non-strings, would clear out :records entirely, and would not
  do anything for :record fields.

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
  AttributeError, or if the indexed attribute is empty.

- LP #142590: The ``DTMLMethod`` and ``DTMLDocument`` ``manage_edit``
  methods could not deal with ``TaintedString`` instances. Removed the
  entirely redundant ``DTMLDocument.manage_edit`` method at the same time.

- LP #142451: If non-recursive ownership changes are made using
  ``changeOwnership``, do not touch any children.

- LP #142750 and LP #142481: To prevent confusion when choosing an Id and
  to avoid issues when creating two VirtualHostMonsters in the same
  container the VirtualHostMoster now has a default Id. It can no longer
  be selected, and the intermediary Add view is gone.

Features Added
++++++++++++++

- Updated packages:

  - distribute = 0.6.13
  - five.formlib = 1.0.3
  - lxml = 2.2.6
  - Sphinx = 0.6.6
  - tempstorage = 2.11.3
  - zope.app.apidoc = 3.6.6
  - zope.app.applicationcontrol = 3.5.1
  - zope.app.authentication = 3.6.1
  - zope.app.i18n = 3.6.2
  - zope.app.intid = 3.7.1
  - zope.app.wsgi = 3.6.1
  - zope.contenttype = 3.4.3
  - zope.container = 3.8.3
  - zope.deferredimport = 3.5.2
  - zope.intid = 3.7.2
  - zope.principalannotation = 3.6.1

- Update Five's testbrowser to support both mechanize 0.1.x and 0.2.x.

- LP #142226: Added an extra keyword argument to the HTTPResponse
  setCookie method to suppress enclosing the cookie value field
  in double quotes.

2.12.6 (2010-05-17)
-------------------

Restructuring
+++++++++++++

- Removed Zope2's own mkzeoinstance script in favor of the version from the
  new zope.mkzeoinstance package.

Features Added
++++++++++++++

- Updated packages:

  - DateTime = 2.12.2
  - distribute = 0.6.12
  - ExtensionClass = 2.13.1
  - initgroups = 2.13.0
  - Missing = 2.13.0
  - MultiMapping = 2.13.0
  - Persistence = 2.13.1
  - pytz = 2010h
  - Record = 2.13.0
  - RestrictedPython = 3.5.2
  - ThreadLock = 2.13.0
  - ZODB3 = 3.9.5
  - zope.app.locales = 3.6.1
  - zope.authentication = 3.7.1
  - zope.browser = 1.3
  - zope.cachedescriptors = 3.5.1
  - zope.deferredimport = 3.5.1
  - zope.i18n = 3.7.3
  - zope.i18nmessageid = 3.5.2
  - zope.lifecycleevent = 3.6.1
  - zope.pagetemplate = 3.5.1
  - zope.proxy = 3.6.0
  - zope.security = 3.7.3

Bugs Fixed
++++++++++

- LP #142563:  Fix ``AccessControl.User.NullUnrestrictedUserTests.__str__``.

- Fix several template errors in SiteErrorLog (chameleon compatibility).

- LP #267820:  Fix bad except clause in the ``sequence_sort`` method of
  the ``<dtml-in>`` tag.

- LP #351006:  Don't nest block tags inside HTML ``<p>`` tags in
  ``zExceptions.ExceptionFormatter``.

- LP #411837:  Handle resource files with ``.htm`` extension properly,
  as page template resources.

- LP #435728:  Fix indentation of OFSP/help/sequence.py docstring.

- LP #574286:  Ensure that mailhosts which share a queue directory do not
  double-deliver mails, by sharing the thread which processes emails for
  that directory.

- BaseRequest: Fixed handling of errors in 'traverseName'.

2.12.5 (2010-04-24)
-------------------

Features Added
++++++++++++++

- Updated packages:

  - Acquisition = 2.13.3
  - distribute = 0.6.10
  - roman = 1.4.0
  - zope.annotation = 3.5.0
  - zope.app.cache = 3.6.0
  - zope.app.dav = 3.5.1
  - zope.app.i18n = 3.6.1
  - zope.app.localpermission = 3.7.2
  - zope.app.principalannotation = 3.7.0
  - zope.app.publication = 3.8.1
  - zope.app.publisher = 3.8.4
  - zope.app.renderer = 3.5.1
  - zope.app.security = 3.7.3
  - zope.app.session = 3.6.1
  - zope.app.testing = 3.7.3
  - zope.app.wsgi = 3.6.0
  - zope.app.zapi = 3.4.1
  - zope.broken = 3.6.0
  - zope.catalog = 3.8.1
  - zope.formlib = 3.7.0
  - zope.i18nmessageid = 3.5.1
  - zope.index = 3.6.0
  - zope.keyreference = 3.6.2
  - zope.lifecycleevent = 3.6.0
  - zope.location = 3.6.0
  - zope.minmax = 1.1.2
  - zope.securitypolicy = 3.6.1
  - zope.viewlet = 3.6.1

- Downgrade the ``manage_* is discouraged. You should use event subscribers
  instead`` warnings to debug level logging. This particular warning hasn't
  motivated anyone to actually change any code.

- Use the standard libraries doctest module in favor of the deprecated version
  in zope.testing.

- LP #143013: make the maximum number of retries on ConflictError a
  configuration option.

Bugs Fixed
++++++++++

- HTTPResponse: Fixed handling of exceptions with unicode values.

- zExceptions: Fixed some unicode issues in Unauthorized.

- LP #372632, comments #15ff.: Fixed regression in Unauthorized handling.

- LP #563229:  Process "evil" JSON cookies which contain double quotes in
  violation of RFC 2965 / 2616.

- Document ``Products.PluginIndexes.PathIndex.PathIndex.insertEntry`` as
  an API for use by subclasses.

- Fixed regression introduced in the resource directory fix in 2.12.4.

- LP #143655:  don't prevent sorting using a path index.

- LP #142478:  normalize terms passed to ``PLexicon.queryLexicon`` using
  the lexicon's pipeline (e.g., case flattening, stop word removal, etc.)

- Wrap exception views in the context of the published object.

2.12.4 (2010-04-05)
-------------------

Restructuring
+++++++++++++

- Removed unmaintained build scripts for full Windows installers and
  ``configure / make`` type builds.

- Updated copyright and license information to conform with repository policy.

- Factored out ZopeUndo package into a separate distribution.

Features Added
++++++++++++++

- Updated packages:

  - Acquisition = 2.13.2
  - ExtensionClass = 2.13.0
  - Persistence = 2.13.0
  - pytz = 2010b

- There is now an event ZPublisher.interfaces.IPubBeforeStreaming which will
  be fired just before the first chunk of data is written to the response
  stream when using the write() method on the response. This is the last
  possible point at which response headers may be set in this case.

Bugs Fixed
++++++++++

- LP #142430: Avoid using the contexts title_or_id method in the
  standard_error_message.

- LP #257675: request.form contained '-C':'' when no QUERY_STRING was in
  the environment.

- Zope 3-style resource directories would throw an Unauthorized error when
  trying to use restrictedTraverse() to reach a resource in a sub-directory
  of the resource directory.

- Restore ability to traverse to 'macros' on template-based browser views.

- Protect ZCTextIndex's clear method against storing Acquisition wrappers.

- LP #195761: fixed ZMI XML export / import and restored it to the UI.

- MailHost should fall back to HELO when EHLO fails.

2.12.3 (2010-01-12)
-------------------

Bugs Fixed
++++++++++

- LP #491224: proper escaping of rendered error message

- LP #246983: Enabled unicode conflict resolution on variables inside "string:"
  expressions in TALES.

- Fixed possible TypeError while sending multipart emails.

- Also look for ZEXP imports within the clienthome directory. This
  provides a place to put imports that won't be clobbered by buildout
  in a buildout-based Zope instance.

- Fixed a SyntaxError in utilities/load_site.py script.

Features Added
++++++++++++++

- Made OFS.Image.File and OFS.Image.Image send IObjectModifiedEvent when
  created through their factories and modified through the ZMI forms
  (manage_edit() and manage_upload()).

- Moved zope.formlib / zope.app.form integration into a separate package
  called five.formlib.

2.12.2 (2009-12-22)
-------------------

Features Added
++++++++++++++

- Updated packages:

  - ZODB3 = 3.9.4
  - docutils = 0.6
  - pytz = 2009r
  - zope.dottedname = 3.4.6
  - zope.i18n = 3.7.2
  - zope.interface = 3.5.3
  - zope.minmax = 1.1.1
  - zope.security = 3.7.2
  - zope.session = 3.9.2
  - zope.tal = 3.5.2

- Enhanced the internals of the DateRangeIndex based on an idea from
  experimental.daterangeindexoptimisations, thanks to Matt Hamilton.

- Updated the default value for ``management_page_charset`` from iso-8859-1
  to the nowadays more standard utf-8.

- Added IPubBeforeAbort event to mirror IPubBeforeCommit in failure scenarios.
  This event is fired just before IPubFailure, but, crucially, while the
  transaction is still open.

- Include bytes limited cache size in the cache parameters ZMI screen.

- Officially supporting Python 2.6 only (with inofficial support for
  Python 2.5) but dropping any support and responsibility for
  Python 2.4.

Bugs Fixed
++++++++++

- LP #143444: add labels to checkboxes / radio buttons on import /
  export form.

- LP #496941:  Remove all mention of ``standard_html_header`` and
  ``standard_html_footer`` from default DTML content.

- Fixed a regression in Products.PageTemplates that meant filesystem templates
  using Products.Five.browser.pagetemplatefile would treat TALES path
  expressions (but not python expressions) as protected code and so attempt
  to apply security. See original issue here:
  http://codespeak.net/pipermail/z3-five/2007q2/002185.html

- LP #491249:  fix tabindex on ZRDB connection test form.

- LP #490514:  preserve tainting when calling into DTML from ZPT.

- Avoid possible errors on test tear-down in Products.Five.fiveconfigure's
  cleanUp() function if Products.meta_types has not been set

2.12.1 (2009-11-02)
-------------------

Features Added
++++++++++++++

- Updated packages:

  - ZODB3 = 3.9.3  (fixes bug where blob conflict errors hung commits)
  - Acquisition = 2.12.4 (fixes problems with iteration support)
  - setuptools = 0.6c11

- LP #411732: Silence security declaration warnings for context and request
  on views protected by an interface.

- Assorted documentation cleanups, including a script to rebuild HTML
  documentation on Windows.

- Refactored Windows Service support to not need or use zopeservice.py
  in instances. This makes buildout-based instances work on Windows.

Bugs Fixed
++++++++++

- LP #440490: zopectl fg|adduser|run|debug now work on Windows.

- LP #443005: zopectl stop works once more on Windows.

- LP #453723: zopectl start works again on non-Windows platforms.

2.12.0 (2009-10-01)
-------------------

Features Added
++++++++++++++

- Updated packages:

  - ZODB3 = 3.9.0

- Backported clone of ``ZopeVocabularyRegistry`` from ``zope.app.schema``, and
  sane registration of it during initialization of Five product.

Bugs Fixed
++++++++++

- Backported removal of experimental support for configuring the Twisted HTTP
  server as an alternative to ``ZServer``.

- Backported fix for timezone issues in date index tests from trunk.

- LP #414757 (backported from Zope trunk): don't emit a IEndRequestEvent when
  clearing a cloned request.

2.12.0c1 (2009-09-04)
---------------------

Features Added
++++++++++++++

- Updated packages:

  - Acquisition = 2.12.3
  - pytz = 2009l
  - tempstorage = 2.11.2
  - transaction = 1.0.0
  - ZODB3 = 3.9.0c3
  - zope.app.basicskin = 3.4.1
  - zope.app.form = 3.8.1
  - zope.component = 3.7.1
  - zope.copypastemove = 3.5.2
  - zope.i18n = 3.7.1
  - zope.security = 3.7.1

Bugs Fixed
++++++++++

- Made the version information show up again, based on pkg_resources
  distribution information instead of the no longer existing version.txt.

2.12.0b4 (2008-08-06)
---------------------

Features Added
++++++++++++++

- The send method of MailHost now supports unicode messages and
  email.Message.Message objects.  It also now accepts charset and
  msg_type parameters to help with character, header and body
  encoding.

- Updated packages:

  - ZODB3 = 3.9.0b5
  - zope.testing = 3.7.7

- scripts: Added 'runzope' and 'zopectl' as entry points for instance scripts.

Bugs Fixed
++++++++++

- LP #418454: FTP server did not work with Python 2.6.X

- PythonScript: Fixed small Python 2.6 compatibility issue.

- mkzopeinstance: Made instance scripts more suitable for egg based installs.
  If you are using a customized skel, it has to be updated.

- Five: Fixed the permissions creation feature added in Zope 2.12.0a2.

- LP #399633: fixed interpreter paths

- MailHost manage form no longer interprets the value None as a string
  in user and password fields.

2.12.0b3 (2009-07-15)
---------------------

Features Added
++++++++++++++

- Updated packages:

  - ZConfig = 2.7.1
  - ZODB = 3.9.0b2
  - pytz = 2009j
  - zope.app.component = 3.8.3
  - zope.app.pagetemplate = 3.7.1
  - zope.app.publisher = 3.8.3
  - zope.app.zcmlfiles = 3.5.5
  - zope.contenttype = 3.4.2
  - zope.dublincore = 3.4.3
  - zope.index = 3.5.2
  - zope.interface = 3.5.2
  - zope.testing = 3.7.6
  - zope.traversing = 3.7.1

- Added support to indexing datetime values to the PluginIndexes
  DateRangeIndex. The DateIndex already had this feature.

Restructuring
+++++++++++++

- PluginIndexes: Removed deprecated TextIndex.

- HelpSys now uses ZCTextIndex instead of the deprecated TextIndex. Please
  update your Zope databases by deleting the Product registrations in the
  Control Panel and restarting Zope.

Bugs Fixed
++++++++++

- LP #397861: exporting $PYTHON in generated 'zopectl' for fixing import issue
  with "bin/zopectl adduser"

- PluginIndexes: Added 'indexSize' to IPluggableIndex.

- HelpSys: ProductHelp no longer depends on PluginIndexes initialization.

- App.Product: ProductHelp was broken since Zope 2.12.0a1.

- ObjectManagerNameChooser now also works with BTreeFolder2.

- Correctly handle exceptions in the ZPublisherExceptionHook.

2.12.0b2 (2009-05-27)
---------------------

Restructuring
+++++++++++++

- Removed all use of ``zope.app.pagetemplate`` by cloning / simplifying
  client code.

- Use ``zope.pagetemplate.engine`` instead of ``zope.app.pagetemplate.engine``.
  (update to versions 3.5.0 and 3.7.0, respectively, along with version 3.8.1
  of ``zope.app.publisher``).

- Use ``IBrowserView`` interface from ``zope.browser.interfaces``, rather than
  ``zope.publisher.interfaces.browser``.

- Use ``IAdding`` interface from ``zope.browser.interfaces``, rather than
  ``zope.app.container``.

- No longer depend on ``zope.app.appsetup``;  use the event implementations
  from ``zope.processlifetime`` instead.

Features Added
++++++++++++++

- zExceptions.convertExceptionType:  new API, breaking out conversion of
  exception names to exception types from 'upgradeException'.

- Launchpad #374719: introducing new ZPublisher events:
  PubStart, PubSuccess, PubFailure, PubAfterTraversal and PubBeforeCommit.

- Testing.ZopeTestCase: Include a copy of ZODB.tests.warnhook to silence
  a DeprecationWarning under Python 2.6.

- Updated packages:

  * python-gettext 1.0
  * pytz 2009g
  * zope.app.applicationcontrol = 3.5.0
  * zope.app.appsetup 3.11
  * zope.app.component 3.8.2
  * zope.app.container 3.8.0
  * zope.app.form 3.8.0
  * zope.app.http 3.6.0
  * zope.app.interface 3.5.0
  * zope.app.pagetemplate 3.6.0
  * zope.app.publication 3.7.0
  * zope.app.publisher 3.8.0
  * zope.browser 1.2
  * zope.component 3.7.0
  * zope.componentvocabulary 1.0
  * zope.container 3.8.2
  * zope.formlib 3.6.0
  * zope.lifecycleevent 3.5.2
  * zope.location 3.5.4
  * zope.processlifetime 1.0
  * zope.publisher 3.8.0
  * zope.security 3.7.0
  * zope.testing 3.7.4
  * zope.traversing 3.7.0

Bugs Fixed
++++++++++

- Launchpad #374729: Encoding cookie values to avoid issues with
  firewalls and security proxies.

- Launchpad #373583: ZODBMountPoint - fixed broken mount support and
  extended the test suite.

- Launchpad #373621: catching and logging exceptions that could cause
  leaking of worker threads.

- Launchpad #373577: setting up standard logging earlier within the startup
  phase for improving the analysis of startup errors.

- Launchpad #373601: abort transaction before connection close in order to
  prevent connection leaks in case of persistent changes after the main
  transaction is closed.

- Fix BBB regression which prevented setting browser ID cookies from
  browser ID managers created before the ``HTTPOnly`` feature landed.
  https://bugs.launchpad.net/bugs/374816

- RESPONSE.handle_errors was wrongly set (to debug, should have been
  ``not debug``). Also, the check for exception constructor arguments
  didn't account for exceptions that didn't override the ``__init__``
  (which are most of them). The combination of those two problems
  caused the ``standard_error_message`` not to be called. Fixes
  https://bugs.launchpad.net/zope2/+bug/372632 .

- DocumentTemplate.DT_Raise:  use new 'zExceptions.convertExceptionType'
  API to allow raising non-builtin exceptions.
  Fixes https://bugs.launchpad.net/zope2/+bug/372629 , which prevented
  viewing the "Try" tab of a script with no parameters.

2.12.0b1 (2009-05-06)
---------------------

Restructuring
+++++++++++++

- No longer depend on ``zope.app.locales``. Zope2 uses almost none of the
  translations provided in the package and is not required for most projects.
  The decision to include locales is left to the application developer now.

- Removed the dependency on ``zope.app.testing`` in favor of providing a more
  minimal placeless setup as part of ZopeTestCase for our own tests.

- updated to ZODB 3.9.0b1

Features Added
++++++++++++++
- zExceptions.convertExceptionType:  new API, breaking out conversion of
  exception names to exception types from ``upgradeException``.

- Extended BrowserIdManager to expose the ``HTTPOnly`` attribute for its
  cookie. Also via https://bugs.launchpad.net/zope2/+bug/367393 .

- Added support for an optional ``HTTPOnly`` attribute of cookies (see
  http://www.owasp.org/index.php/HTTPOnly).  Patch from Stephan Hofmockel,
  via https://bugs.launchpad.net/zope2/+bug/367393 .

Bugs Fixed
++++++++++

- ZPublisher response.setBody: don't append Accept-Encoding to Vary header if
  it is already present - this can make cache configuration difficult.

2.12.0a4 (2009-04-24)
---------------------

Bugs Fixed
++++++++++

- fixed versions.cfg in order to support zope.z2release for
  creating a proper index structure

2.12.0a3 (2009-04-19)
---------------------

The generated tarball for the 2.12.0a2 source release was incomplete, due to
a setuptools and Subversion 1.6 incompatibility.

Restructuring
+++++++++++++

- Added automatic inline migration for databases created with older Zope
  versions. The ``Versions`` screen from the ``Control_Panel`` is now
  automatically removed on Zope startup.

- Removed more unused code of the versions support feature including the
  Globals.VersionNameName constant.

2.12.0a2 (2009-04-19)
---------------------

Restructuring
+++++++++++++

- If the <permission /> ZCML directive is used to declare a permission that
  does not exist, the permission will now be created automatically, defaulting
  to being granted to the Manager role only. This means it is possible to
  create new permissions using ZCML only. The permission will Permissions that
  already exist will not be changed.

- Using <require set_schema="..." /> or <require set_attributes="..." /> in
  the <class /> directive now emits a warning rather than an error. The
  concept of protecting attribute 'set' does not exist in Zope 2, but it
  should be possible to re-use packages that do declare such protection.

- Updated to Acquisition 2.12.1.

- Updated to DateTime 2.12.0.

- Updated to ZODB 3.9.0a12.

- Removed the ``getPackages`` wrapper from setup.py which would force all
  versions to an exact requirement. This made it impossible to require
  newer versions of the dependencies. This kind of KGS information needs
  to be expressed in a different way.

- removed ``extras_require`` section from setup.py (this might possibly
  break legacy code).

Bugs Fixed
++++++++++

- Launchpad #348223: optimize catalog query by breaking out early from loop
  over indexes if the result set is already empty.

- Launchpad #344098: in ``skel/etc/zope.conf.ing``, replaced commented-out
  ``read-only-database`` option, which is deprecated, with pointers to the
  appropos sections of ZODB's ``component.xml``.  Updated the description
  of the ``zserver-read-only-mode`` directive to indicate its correct
  semantics (suppressing log / pid / lock files).  Added deprecation to the
  ``read-only-database`` option, which has had no effect since Zope 2.6.

- "Permission tab": correct wrong form parameter for
  the user-permission report

- PageTemplates: Made PreferredCharsetResolver work with new kinds of contexts
  that are not acquisition wrapped.

- Object managers should evaluate to True in a boolean test.

2.12.0a1 (2009-02-26)
---------------------

Restructuring
+++++++++++++

- Switched Products.PageTemplates to directly use zope.i18n.translate and
  removed the GlobalTranslationService hook.

- Removed bridging code from Product.Five for PlacelessTranslationService
  and Localizer. Neither of the two is actually using this anymore.

- Removed the specification of ``SOFTWARE_HOME`` and ``ZOPE_HOME`` from the
  standard instance scripts.
  [hannosch]

- Made the specification of ``SOFTWARE_HOME`` and ``ZOPE_HOME`` optional. In
  addition ``INSTANCE_HOME`` is no longer required to run the tests of a
  source checkout of Zope.

- Removed the ``test`` command from zopectl. The test.py script it was relying
  on does no longer exist.

- Updated to ZODB 3.9.0a11. ZODB-level version support has been
  removed and ZopeUndo now is part of Zope2.

- The Zope2 SVN trunk is now a buildout pulling in all dependencies as
  actual released packages and not SVN externals anymore.

- Make use of the new zope.container and zope.site packages.

- Updated to newer versions of zope packages. Removed long deprecated
  layer and skin ZCML directives.

- Disabled the XML export on the UI level - the export functionality
  however is still available on the Python level.

- No longer show the Help! links in the ZMI, if there is no help
  available. The help system depends on the product registry.

- Updated the quick start page and simplified the standard content.
  The default index_html is now a page template.

- Removed deprecated Draft and Version support from Products.OFSP.
  Also removed version handling from the control panel. Versions are
  no longer supported on the ZODB level.

- Removed left-overs of the deprecated persistent product distribution
  mechanism.

- The persistent product registry is not required for starting Zope
  anymore. ``enable-product-installation`` can be set to off if you don't
  rely on the functionality provided by the registry.

- ZClasses have been deprecated for two major releases. They have been
  removed in this version of Zope.

- Avoid deprecation warnings for the md5 and sha modules in Python 2.6
  by adding conditional imports for the hashlib module.

- Replaced imports from the 'Globals' module throughout the
  tree with imports from the actual modules;  the 'Globals' module
  was always intended to be an area for shared data, rather than
  a "facade" for imports.  Added zope.deferred.deprecation entries
  to 'Globals' for all symbols / modules previously imported directly.

- Protect against non-existing zope.conf path and products directories.
  This makes it possible to run a Zope instance without a Products or
  lib/python directory.

- Moved exception MountedStorageError from ZODB.POSExceptions
  to Products.TemporaryFolder.mount (now its only client).

- Moved Zope2-specific module, ZODB/Mount.py, to
  Products/TemporaryFolder/mount.py (its only client is
  Products/TemporaryFolder/TemporaryFolder.py).

- Removed spurious import-time dependencies from
  Products/ZODBMountPoint/MountedObject.py.

- Removed Examples.zexp from the skeleton. The TTW shopping cart isn't
  any good example of Zope usage anymore.

- Removed deprecated ZTUtil.Iterator module

- Removed deprecated StructuredText module

- Removed deprecated TAL module

- Removed deprecated modules from Products.PageTemplates.

- Removed deprecated ZCML directives from Five including the whole
  Five.site subpackage.

Features added
++++++++++++++

- OFS.ObjectManager now fully implements the zope.container.IContainer
  interface. For the last Zope2 releases it already claimed to implement the
  interface, but didn't actually full-fill the interface contract. This means
  you can start using more commonly used Python idioms to access objects
  inside object managers. Complete dictionary-like access and container
  methods including iteration are now supported. For each class derived from
  ObjectManager you can use for any instance om: ``om.keys()`` instead of
  ``om.objectIds()``, ``om.values()`` instead of ``om.objectValues()``, but
  also ``om.items()``, ``ob.get('id')``, ``ob['id']``, ``'id' in om``,
  ``iter(om)``, ``len(om)``, ``om['id'] = object()`` instead of
  ``om._setObject('id', object())`` and ``del ob['id']``. Should contained
  items of the object manager have ids equal to any of the new method names,
  the objects will override the method, as expected in Acquisition enabled
  types. Adding new objects into object managers by those new names will no
  longer work, though. The added methods call the already existing methods
  internally, so if a derived type overwrote those, the new interface will
  provide the same functionality.

- Acquisition has been made aware of ``__parent__`` pointers. This allows
  direct access to many Zope 3 classes without the need to mixin
  Acquisition base classes for the security to work.

- MailHost: now uses zope.sendmail for delivering the mail. With this
  change MailHost integrates with the Zope transaction system (avoids
  sending dupe emails in case of conflict errors). In addition
  MailHost now provides support for asynchronous mail delivery. The
  'Use queue' configuration option will create a mail queue on the
  filesystem (under 'Queue directory') and start a queue thread that
  checks the queue every three seconds. This decouples the sending of
  mail from its delivery.  In addition MailHosts now supports
  encrypted connections through TLS/SSL.

- SiteErrorLog now includes the entry id in the information copied to
  the event log. This allowes you to correlate a user error report with
  the event log after a restart, or let's you find the REQUEST
  information in the SiteErrorLog when looking at a traceback in the
  event log.

Bugs Fixed
++++++++++

- Launchpad #332168: Connection.py: do not expose DB connection strings
  through exceptions

- Specified height/width of icons in ZMI listings so the table doesn't
  jump around while loading.

- After the proper introduction of parent-pointers, it's now
  wrong to acquisition-wrap content providers. We will now use
  the "classic" content provider expression from Zope 3.

- Ported c69896 to Five. This fix makes it possible to provide a
  template using Python, and not have it being set to ``None`` by
  the viewlet manager directive.

- Made Five.testbrowser compatible with mechanize 0.1.7b.

- Launchpad #280334: Fixed problem with 'timeout'
  argument/attribute missing in testbrowser tests.

- Launchpad #267834: proper separation of HTTP header fields
  using CRLF as requested by RFC 2616.

- Launchpad #257276: fix for possible denial-of-service attack
  in PythonScript when passing an arbitrary module to the encode()
  or decode() of strings.

- Launchpad #257269: 'raise SystemExit' with a PythonScript could shutdown
  a complete Zope instance

- Switch to branch of 'zope.testbrowser' external which suppresses
  over-the-wire tests.

- Launchpad #143902: Fixed App.ImageFile to use a stream iterator to
  output the file. Avoid loading the file content when guessing the
  mimetype and only load the first 1024 bytes of the file when it cannot
  be guessed from the filename.

- Changed PageTemplateFile not to load the file contents on Zope startup
  anymore but on first access instead. This brings them inline with the
  zope.pagetemplate version and speeds up Zope startup.

- Collector #2278: form ':record' objects did not implement enough
  of the mapping protocol.

- "version.txt" file was being written to the wrong place by the
  Makefile, causing Zope to report "unreleased version" even for
  released versions.

- Five.browser.metaconfigure.page didn't protect names from interface
  superclasses (http://www.zope.org/Collectors/Zope/2333)

- DAV: litmus "notowner_modify" tests warn during a MOVE request
  because we returned "412 Precondition Failed" instead of "423
  Locked" when the resource attempting to be moved was itself
  locked.  Fixed by changing Resource.Resource.MOVE to raise the
  correct error.

- DAV: litmus props tests 19: propvalnspace and 20:
  propwformed were failing because Zope did not strip off the
  xmlns: attribute attached to XML property values.  We now strip
  off all attributes that look like xmlns declarations.

- DAV: When a client attempted to unlock a resource with a token
  that the resource hadn't been locked with, in the past we
  returned a 204 response.  This was incorrect.  The "correct"
  behavior is to do what mod_dav does, which is return a '400
  Bad Request' error.  This was caught by litmus
  locks.notowner_lock test #10.  See
  http://lists.w3.org/Archives/Public/w3c-dist-auth/2001JanMar/0099.html
  for further rationale.

- When Zope properties were set via DAV in the "null" namespace
  (xmlns="") a subsequent PROPFIND for the property would cause the
  XML representation for that property to show a namespace of
  xmlns="None".  Fixed within OFS.PropertySheets.dav__propstat.

- integrated theuni's additional test from 2.11 (see r73132)

- Relaxed requirements for context of
  Products.Five.browser.pagetemplatefile.ZopeTwoPageTemplateFile,
  to reduce barriers for testing renderability of views which
  use them.
  (http://www.zope.org/Collectors/Zope/2327)

- PluginIndexes: Fixed 'parseIndexRequest' for false values.

- Collector #2263: 'field2ulines' did not convert empty string
  correctly.

- Collector #2198: Zope 3.3 fix breaks Five 1.5 test_getNextUtility

- Prevent ZPublisher from insering incorrect <base/> tags into the
  headers of plain html files served from Zope3 resource directories.

- Changed the condition checking for setting status of
  HTTPResponse from to account for new-style classes.

- The Wrapper_compare function from tp_compare to tp_richcompare.
  Also another function Wrapper_richcompare is added.

- The doc test has been slightly changed in ZPublisher to get
  the error message extracted correctly.

- The changes made in Acquisition.c in Implicit Acquisition
  comparison made avail to Explicit Acquisition comparison also.

- zopedoctest no longer breaks if the URL contains more than one
  question mark. It broke even when the second question mark was
  correctly quoted.

Other Changes
+++++++++++++

- Added lib/python/webdav/litmus-results.txt explaining current
  test results from the litmus WebDAV torture test.

- DocumentTemplate.DT_Var.newline_to_br(): Simpler, faster
  implementation.

