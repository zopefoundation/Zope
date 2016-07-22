Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
https://zope.readthedocs.io/en/2.13/CHANGES.html

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

- Make repoze.tm2 optional when using the WSGIPublisher.

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
    - ``Products.BTreeFolder2``
    - ``Products.ExternalMethod``
    - ``Products.MailHost``
    - ``Products.MIMETools``
    - ``Products.PythonScripts``
    - ``Products.SiteErrorLog``
    - ``Products.StandardCacheManagers``
    - ``Products.ZCatalog``
    - ``Products.ZCTextIndex``
    - ``Record``
