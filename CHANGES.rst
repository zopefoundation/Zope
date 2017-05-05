Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
https://zope.readthedocs.io/en/2.13/CHANGES.html

4.0a4 (unreleased)
------------------

Bugs Fixed
++++++++++

- Restore a `_unauthorized` hook on the response object.

- Restore `HTTPResponse.redirect` behaviour of not raising an exception.

Features Added
++++++++++++++

- Updated distributions:

    - Acquisition = 4.4.1

Restructuring
+++++++++++++


4.0a3 (2017-05-03)
------------------

Bugs Fixed
++++++++++

- Fixed reflective XSS in findResult.
  This applies PloneHotfix20170117.  [maurits]

- Patch zope.interface to remove docstrings and avoid publishing.
  From Products.PloneHotfix20161129.   [maurits]

- Don't copy items the user is not allowed to view.
  From Products.PloneHotfix20161129.  [maurits]

- Make the WSGIPublisher normalize HTTP exception classes based on name
  (for example, any exception named NotFound will be converted
  into `zExceptions.NotFound`). This restores compatibility with
  similar behavior of the old publisher.
  [davisagli]

- Use unicode transaction-notes to support ZODB 5.
  [pbauer]

Features Added
++++++++++++++

- Add support to SameSite cookie in ``ZPublisher.HTTPBaseResponse``:
  https://tools.ietf.org/html/draft-west-first-party-cookies-07

- Updated distributions:

    - AccessControl = 4.0a4
    - Acquisition = 4.3.0
    - BTrees = 4.4.1
    - DateTime = 4.2
    - DocumentTemplate = 3.0a1
    - ExtensionClass = 4.3.0
    - Missing = 3.2
    - MultiMapping = 3.1
    - Persistence = 3.0a3
    - persistent = 4.2.2
    - Products.ZCatalog = 4.0a3
    - pytz = 2016.10
    - Record = 3.2
    - transaction = 2.1.1
    - waitress = 1.0.2
    - WebOb = 1.7.1
    - WebTest = 2.0.26
    - WSGIProxy2 = 0.4.3
    - zdaemon = 4.2.0
    - ZEO = 5.0.4
    - zExceptions = 3.6
    - ZODB = 5.2.0
    - zope.configuration = 4.1.0
    - zope.deprecation = 4.2.0
    - zope.interface = 4.3.3
    - zope.testbrowser = 5.2
    - zope.testing = 4.6.1
    - zope.testrunner = 4.6.0
    - zope.globalrequest = 1.3
    - zope.testing = 4.6.0
    - ZServer = 4.0a2

Restructuring
+++++++++++++

- Integrate code from and drop dependency on `five.globalrequest`.

- Remove special handling of redirect and unauthorized exceptions from
  the WSGI publisher. These are now always raised as exceptions, to
  match the behavior of all other HTTPExceptions.

- Removed xml-export.
  [maurits, pbauer]

- Add back ZCacheable support.

- Update to zope.testbrowser 5.0 and its WebTest based implementation.

- Use `@implementer` and `@adapter` class decorators.


4.0a2 (2016-09-09)
------------------

Bugs Fixed
++++++++++

- Quote variable in manage_tabs to avoid XSS.
  From Products.PloneHotfix20160830.  [maurits]

- Remove more HelpSys references.

Features Added
++++++++++++++

- Add support for exception views to WSGIPublisher.

- Add support for ConflictError and TransientError retry logic directly
  into WSGIPublisher.

- Add support for raising HTTPOK and HTTPRedirection exceptions and
  have them result in successful transactions.

- Add better blob support to HTTPRequest.ZopeFieldStorage.

- Updated distributions:

  - AccessControl = 4.0a3
  - AuthEncoding = 4.0.0
  - Products.ZCatalog = 4.0a2
  - zExceptions = 3.3
  - ZServer = 4.0a1

Restructuring
+++++++++++++

- Change the WSGIResponse exception methods to raise exceptions instead
  of returning responses. This includes notFoundError, forbiddenError,
  debugError, badRequestError, unauthorized and redirect.

- Split a common HTTPBaseResponse base class out of HTTPResponse and
  WSGIResponse. Move ZServer specific logic onto HTTPResponse.

- Simplified `ZPublisher.WSGIPublisher.get_module_info` contract.

- Add new `ZPublisher.utils.recordMetaData` function and use default
  `transaction.manager` as the transaction manager.

- Remove support for repoze.tm2.

- Change Testing to use the WSGI publisher for functional and testbrowser
  based tests incl. functional doctests. Alternatives are available
  in `ZServer.Testing`.

- Move `ZPublisher.Publish` module into ZServer distribution.

- Remove `Globals` package, opened database are now found in
  `Zope2.opened` next to `Zope2.DB`.

- Remove proxy role support from DTML documents and methods.

- Remove ZCacheable logic and StandardCacheManagers dependency.

- Stop mixing in `Five.bbb.AcquisitionBBB` into browser components.

- Integrate `five.pt` code directly into `Products.PageTemplates`.

- Move `Products.SiteAccess` into ZServer distribution.

- Simplify Page Template and Scripts ZMI screens.

- Change VHM id to `virtual_hosting` to match AppInitializer.

- Raise BadRequest instead of returning MessageDialog.

- Remove property management ZMI screens.

- Remove ZMI copy/cut/paste/rename and re-ordering features.

- Drop `OFS.History` functionality.

- Drop ZopeUndo dependency and move undo management to the control panel.

- Simplify ZMI control panel and globally available management screens.

- Move ZServer related testing support into ZServer.Testing.

- Split out Lifetime, webdav and ZServer packages into a ZServer project.

- Move webdav's EtagSupport, Lockable and LockItem into OFS.

- Split `Products.TemporaryFolder` and `Products.ZODBMountPoint` into
  one new project called `Products.TemporaryFolder`.

- Split a WSGI part out of `zopeschema.xml`. This reduces the supported
  `zope.conf` directives when run under WSGI.

- Remove temp_folder mount point from default configuration.

- Split a WSGI part out of `Zope2.Startup.ZopeStarter`.

- Add new `ZServer.Zope2.Startup.config` module to hold configuration.

- Remove `Control_Panel` `/DebugInfo` and `/DavLocks`.

- Remove profiling support via `publisher-profile-file` directive.

- Create new `Products.Sessions` distribution including Products.Sessions
  and Products.Transience code.

- Merge `Products.OFSP` project back in.

- No longer test compatibility with dependencies:

    ``Products.ExternalMethod``
    ``Products.PythonScripts``
    ``Products.Sessions``
    ``Products.SiteErrorLog``
    ``Products.TemporaryFolder``
    ``tempstorage``
    ``zLOG``
    ``ZopeUndo``

- Dropped dependency declarations for indirect dependencies:

    ``docutils``
    ``Missing``
    ``pytz``
    ``zLOG``
    ``zope.sendmail``
    ``zope.structuredtext``


4.0a1 (2016-07-22)
------------------

Bugs Fixed
++++++++++

- Remove `Connection` and `Transfer-Encoding` headers from WSGI responses.
  According to PEP 333 WSGI applications must not emit hop-by-hop headers.

- Removed docstrings from some methods to avoid publishing them.  From
  Products.PloneHotfix20160419.  [maurits]

- bobo_traverse of ProductDispatcher did not correctly invalidate cache
  when a product was not initializes after first access of the cache. Types
  that were added in test-profiles were not useable.
  [pbauer, jensens]

- Fix pt_editForm after the help-system was removed.
  [pbauer]

- Skipped ipv6 test on Travis, because Travis no longer supports this.

- LP #789863:  Ensure that Request objects cannot be published / traversed
  directly via a URL.

- Document running Zope as a WSGI application.

- Queue additional warning filters at the beginning of the queue in order to
  allow overrides.

- Issue #16: prevent leaked connections when broken ``EndRequestEvent``
  subscribers raise exceptions.

- Ensure that the ``WSGIPublisher`` begins and ends an *interaction*
  at the request/response barrier. This is required for instance for
  the ``checkPermission`` call to function without an explicit
  ``interaction`` parameter.

- Made sure getConfiguration().default_zpublisher_encoding is set correctly.

- Issue #28: Fix publishing of IStreamIterator. This interface does
  not have seek or tell.
  Introduce IUnboundStreamIterator to support publishing iterators
  of unknown length.


Features Added
++++++++++++++

- Include waitress as a default WSGI app server.

- Add `egg:Zope2#httpexceptions` WSGI middleware.

- Update available HTTP response code, 302 is now called Found.

- Add a new `runwsgi` script to serve PasteDeploy files.

- Depend on and automatically set up `five.globalrequest`.

- Optimized the `OFS.ObjectManager.__contains__` method to do the
  least amount of work necessary.

- Optimized the `OFS.Traversable.getPhysicalPath` method to avoid excessive
  amounts of method calls.

- During startup open a connection to every configured database, to ensure all
  of them can indeed be accessed. This avoids surprises during runtime when
  traversal to some database mountpoint could fail as the underlying storage
  cannot be opened at all.

- Explicitly close all databases on shutdown, which ensures `Data.fs.index`
  gets written to the file system.

- Always configure a `blob-dir` in the default skeleton.

- ZPublisher: If `IBrowserPage` is provided by a view, form input is decoded.
  This makes it easier to use ``zope.formlib`` and ``z3c.form`` in Zope 2.

- Remove `control panel` object from the ZODB.

- Updated to latest versions of Zope Toolkit libraries.

- Updated distributions:

  - AccessControl = 4.0a1
  - Acquisition = 4.2.2
  - BTrees = 4.0.8
  - DateTime = 4.1.1
  - ExtensionClass = 4.1.2
  - docutils = 0.9.1
  - five.globalrequest = 1.0
  - manuel = 1.6.0
  - Missing = 3.1
  - MultiMapping = 3.0
  - Persistence = 3.0a1
  - Products.BTreeFolder2 = 3.0
  - Products.ExternalMethod = 3.0
  - Products.MailHost = 3.0
  - Products.OFSP = 3.0
  - Products.PythonScripts = 3.0
  - Products.SiteErrorLog = 4.0
  - Products.StandardCacheManagers = 3.0
  - Products.ZCatalog = 4.0a1
  - Products.ZCTextIndex = 3.0
  - Record = 3.1
  - tempstorage = 3.0
  - zExceptions = 3.0
  - zLOG = 3.0
  - zope.globalrequest = 1.2
  - ZopeUndo = 4.1

Restructuring
+++++++++++++

- Remove dependency on initgroups. Use the standard libraries os.initgroups
  instead.

- Removed nt_svcutils support from zopectl.

- Python 2.6 is no longer supported. Use Python 2.7.

- Products.SiteErrorLog: Is now a separated package.

- OFS: Removed duplicate code in ZopeFind and ZopeFindAndApply

- Five: Removed obsolete metaclass.

- Five: Refactored ``browser:view`` and ``browser:page`` directives.
  This makes their implementation more similar to that in ``zope.browserpage``
  and adds allowed_interface support for the ``browser:view`` directive.
  By default the `aq_*` attributes are no longer available on those
  views/pages. If you still use them, you have to mix in Five's BrowserView.

- Removed the (very obsolete) thread lock around the cookie parsing code
  in HTTPRequest.py; the python `re` module is thread-safe, unlike the
  ancient `regex` module that was once used here.

- Removed the special handling of `Set-Cookie` headers in
  `HTTPResponse.setHeader`. Use the `setCookie`/`appendCookie`/`expireCookie`
  methods instead, or if low-level control is needed, use `addHeader` instead
  to get the exact same effect.

- Removed the `App.version_txt.getZopeVersion` API, you can use
  ``pkg_resources.get_distribution('Zope2').version`` instead.

- On the application object, removed `PrincipiaTime` in favor of `ZopeTime` and
  `PrincipiaRedirect` in favor of `Redirect` or `ZopeRedirect`.

- Removed `OFS.DefaultObservable` - an early predecessor of `zope.event`.

- Removed `mime-types` option from `zope.conf`. You can use the `add_files`
  API from `zope.contenttype` instead.

- Removed `OFS.ZDOM`. `OFS.SimpleItem.Item` now implements `getParentNode()`.

- Removed the last remaining code to support `SOFTWARE_HOME` and `ZOPE_HOME`.

- Removed ZMI controls for restarting the process, these no longer apply when
  managed as a WSGI application.

- Removed `bobobase_modification_time` from `Persistence.Persistent`, you can
  use `DateTime(object._p_mtime)` instead.

- Removed `AccessRule` and `SiteRoot` from `Products.SiteAccess`.

- Removed `Products.ZReST` and the `reStructuredText` wrapper, you can use
  `docutils` directly to gain `reST` support.

- Removed special code to create user folders and page templates while creating
  new `OFS.Folder` instances.

- Removed persistent default code like the `error_log` and `temp_folder`.

- Removed persistent default content, including the `standard_error_message`
  template.

- Retired icons from the `Zope Management Interface` and various smaller
  cleanups of ZMI screens.

- Removed the old help system, in favor of the current Sphinx documentation
  hosted at https://zope.readthedocs.io/. For backwards compatibility the
  `registerHelp` and `registerHelpTitle` methods are still available on the
  ProductContext used during the `initialize` function.

- Removed various persistent product related code and options. The
  `enable-product-installation` `zope.conf` setting is now a no-op.

- Changed the value for `default-zpublisher-encoding` and
  `management_page_charset` to `utf-8`.

- Removed the `enable-ms-author-via` directive which was only required for
  very old web folder implementations from before 2007.

- Changed zope.conf default settings for `zserver-threads` to `2` and
  `python-check-interval` to `1000`.

- Simplified instance skeleton, removing old `Extensions`, `import`,
  `lib/python` and `Products` from the default. You can continue to manually
  add these back.

- Five.browser: Marked `processInputs` and `setPageEncoding` as deprecated.
  `processInputs` was replaced by the `postProcessInputs` request method and
  the charset negotiation done by `setPageEncoding` was never fully supported.

- Dropped the direct dependencies on packages that have been factored out of
  the main Zope 2 tree. Make sure you declare a dependency in your own
  distribution if you still use one of these:

    ``Products.BTreeFolder2``
    ``Products.ExternalMethod``
    ``Products.MailHost``
    ``Products.MIMETools``
    ``Products.PythonScripts``
    ``Products.SiteErrorLog``
    ``Products.StandardCacheManagers``
    ``Products.ZCatalog``
    ``Record``
