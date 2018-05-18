Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
https://zope.readthedocs.io/en/2.13/CHANGES.html

For the change log of the alpha versions see
https://github.com/zopefoundation/Zope/blob/4.0a6/CHANGES.rst

4.0b5 (2018-05-18)
------------------

New features
++++++++++++

- The `ProductContext` handed to a product's `initialize()` method
  now has a `getApplication()` method which a product can use to,
  e.g., add an object to the Application during startup (as used
  by `Products.Sessions`).
  (`#277 <https://github.com/zopefoundation/Zope/pull/277>`_)

- Update dependencies to newest versions.

Bugfixes
++++++++

- Fix comparison against non-ints in ZCacheable_getModTime.

- Allow unicode in ids.
  (`#181 <https://github.com/zopefoundation/Zope/pull/181>`_)

- Use log.warning to avoid deprecation warning for log.warn

- Keep existing loggers
  (`#276 <https://github.com/zopefoundation/Zope/pull/276>`)

- Accept bytes and text as cookie value.
  (`#263 <https://github.com/zopefoundation/Zope/pull/263>`_)

- Always raise InternalError when using WSGI and let the WSGI server decide
  how to handle the request.
  (`#280 <https://github.com/zopefoundation/Zope/pull/280>`)

- ``__str__`` of an Image object now returns the image HTML tag in
  Python 3 as it already did on Python 2.
  (`#282 <https://github.com/zopefoundation/Zope/pull/282>`_)


4.0b4 (2018-04-23)
------------------

Supported versions
++++++++++++++++++

- Drop support for Python 3.4 because it was dropped by `AccessControl` on
  which `Zope` depends.

- Update dependencies to newest versions.

Breaking changes
++++++++++++++++

- The 'lines' property type now always stores bytes on all Python versions.
  (`#206 <https://github.com/zopefoundation/Zope/issues/206>`_)

Bugfixes
++++++++

- Fix an edge case where the data which was set using ``response.write()`` was
  not returned by ``publish_module``.
  (`#256 <https://github.com/zopefoundation/Zope/issues/256>`_)

- Fix renaming of images and files via ZMI.
  (`#247 <https://github.com/zopefoundation/Zope/issues/247>`_)

- Sort HTTP headers in doctests as in Zope 2.
  (`#259 <https://github.com/zopefoundation/Zope/pull/259>`_)

Changes
+++++++

- Add ``OFS.CopySupport.CopyContainer._pasteObjects()`` to be able to paste
  objects no matter how many objects where cut or copied.
  (`#217 <https://github.com/zopefoundation/Zope/issues/217>`_)


4.0b3 (2018-01-27)
------------------

Bugfixes
++++++++

- Test that ``str.format`` checks security for accessed keys and items.
  The real fix is in the AccessControl package, version 4.0b1.
  Part of PloneHotfix20171128.

- Made Redirect unavailable as url.  Part of PloneHotfix20171128.

- Fix ZMI navtree error by using DocumentTemplate version 3.0b2.
  (`#179 <https://github.com/zopefoundation/Zope/issues/179>`_)

- Re-add a link to refresh the ZMI menu tree on the left.

- Install a default page for the root view in new installations again.

- Re-raise app exceptions if x-wsgiorg.throw_errors is True in the request environ.

- Fix path expressions trying to call views that do not implement `__call__`.

- Move _html to HTTPBaseResponse since it is shared by HTTPResponse and WSGIResponse.

- Fix unpickling of instances created before 4.0b2 those classes changed from
  old-style classes to new-style classes.

- Prevent UnicodeDecodeError when publishing image (bytes) responses without content-type

Changes
+++++++

- Move `Products.SiteAccess` back here from ZServer distribution.

- Update dependencies to current versions.


4.0b2 (2017-10-13)
------------------

New features
++++++++++++

- Add support for IPv6 addresses for the trusted-proxy zope.conf setting.

Bugfixes
++++++++

- Fix special double under methods on `HTTPRequest.record` class.

- Add missing version pin for `Zope2` in `versions-prod.cfg`.

- Fix ``HTTPExceptionHandler`` to be usable as part of the WSGI pipeline in
  testbrowser tests.

Other changes
+++++++++++++

- Explicitly make all classes new-style classes.


4.0b1 (2017-09-15)
------------------

With this release the egg of the project is named `Zope` instead of `Zope2`.
There is a meta package named `Zope2` which depends on `Zope`.

See https://zope.readthedocs.io/en/latest/WHATSNEW.html for a higher level
description of the changes.

Supported versions
++++++++++++++++++

- Add support for Python 3.4, 3.5 and 3.6.

- Drop support for Python 2.6.

Breaking changes
++++++++++++++++

- Removed the old help system, in favor of the current Sphinx documentation
  hosted at https://zope.readthedocs.io/. For backwards compatibility the
  `registerHelp` and `registerHelpTitle` methods are still available on the
  ProductContext used during the `initialize` function.

- Remove ZMI re-ordering features.

- Retired icons from the `Zope Management Interface` and various smaller
  cleanups of ZMI screens.

- Remove xml-export.

- Remove `Globals` package, opened database are now found in
  `Zope2.opened` next to `Zope2.DB`.

- Remove proxy role support from DTML documents and methods.

- Remove `Products.ZReST` and the `reStructuredText` wrapper, you can use
  `docutils` directly to gain `reST` support.

- Stop setting ``CLIENT_HOME`` as a builtin, get it via
  ``App.config.getConfiguration().clienthome`` instead.

- Drop `OFS.History` functionality.

- Removed `OFS.DefaultObservable` - an early predecessor of `zope.event`.

- Removed `OFS.ZDOM`. `OFS.SimpleItem.Item` now implements `getParentNode()`.

- Removed special code to create user folders and page templates while creating
  new `OFS.Folder` instances.

- Removed the `App.version_txt.getZopeVersion` API, you can use
  ``pkg_resources.get_distribution('Zope').version`` instead.

- On the application object, removed `PrincipiaTime` in favor of `ZopeTime` and
  `PrincipiaRedirect` in favor of `Redirect` or `ZopeRedirect`.

- Removed `bobobase_modification_time` from `Persistence.Persistent`, you can
  use `DateTime(object._p_mtime)` instead.

- Removed the special handling of `Set-Cookie` headers in
  `HTTPResponse.setHeader`. Use the `setCookie`/`appendCookie`/`expireCookie`
  methods instead, or if low-level control is needed, use `addHeader` instead
  to get the exact same effect.

- Raise ``BadRequest`` instead of returning MessageDialog.

- Update available HTTP response code, 302 is now called ``Found``.

- Refactor ``browser:view`` and ``browser:page`` directives.
  This makes their implementation more similar to that in ``zope.browserpage``
  and adds allowed_interface support for the ``browser:view`` directive.
  By default the `aq_*` attributes are no longer available on those
  views/pages.

- Removed the last remaining code to support `SOFTWARE_HOME` and `ZOPE_HOME`.

- Simplified instance skeleton, removing old `Extensions`, `import`,
  `lib/python` and `Products` from the default. You can continue to manually
  add these back. (`Products` requires `ZServer` to be usable.)

- Remove the `zopectl` script.

WSGI
++++

- Document running Zope as a WSGI application.

- Remove `Connection` and `Transfer-Encoding` headers from WSGI responses.
  According to PEP 333 WSGI applications must not emit hop-by-hop headers.

- Ensure that the ``WSGIPublisher`` begins and ends an *interaction*
  at the request/response barrier. This is required for instance for
  the ``checkPermission`` call to function without an explicit
  ``interaction`` parameter.

- Make the WSGIPublisher normalize HTTP exception classes based on name
  (for example, any exception named NotFound will be converted
  into `zExceptions.NotFound`). This restores compatibility with
  similar behavior of the old publisher.

- Change the WSGIResponse exception methods to raise exceptions instead
  of returning responses. This includes ``notFoundError``, ``forbiddenError``,
  ``debugError``, ``badRequestError`` and ``unauthorized``.

- Add support for exception views to WSGIPublisher.

- Add support for ``ConflictError`` and ``TransientError`` retry logic directly
  into WSGIPublisher, thus `repoze.tm2` and `repoze.retry` are no longer
  needed and no longer supported.

- Change Testing to use the WSGI publisher for functional and testbrowser
  based tests incl. functional doctests. Alternatives are available
  in ``ZServer.Testing``.

- Split a WSGI part out of `Zope2.Startup.ZopeStarter`.

- Include ``waitress`` as a default WSGI app server.

- Add `egg:Zope#httpexceptions` WSGI middleware.

- Add a new `runwsgi` script to serve PasteDeploy files.


ZODB
++++

- Support ZODB 5.

- Removed persistent default content like `standard_error_message`,
  `error_log`, `temp_folder` and `index_html`.


Control panel
+++++++++++++

- Removed ZMI controls for restarting the process, these no longer apply when
  managed as a WSGI application.

- Remove `DebugInfo` and `DavLocks` from control panel.

- Move the undo management to Control Panel -> Databases -> Database -> Undo.

- Simplify ZMI control panel and globally available management screens.

- Remove `control panel` object from the ZODB, it is no longer persistent.


ZServer
+++++++

- Split out ``Lifetime``, ``webdav`` and ``ZServer`` packages into a `ZServer`
  project.

- Move ``EtagSupport``, ``Lockable`` and ``LockItem`` from ``webdav`` into
  `OFS`.

- Move ``ZPublisher.Publish`` module into `ZServer` distribution.

- Move ``Products.SiteAccess`` into `ZServer` distribution.

- Move ZServer related testing support into ``ZServer.Testing``.

zope.conf
+++++++++

- Always configure a `blob-dir` in the default skeleton.

- Removed `mime-types` option from `zope.conf`. You can use the `add_files`
  API from `zope.contenttype` instead.

- Removed various persistent product related code and options.

- Split a WSGI part out of `zopeschema.xml`. This reduces the supported
  `zope.conf` directives when run under WSGI. If a directive is now unkown
  it might have been moved to the `ZServer` package.
  See https://github.com/zopefoundation/ZServer/blob/master/src/ZServer/Zope2/Startup/zopeschema.xml
  for the directives which are supported via `ZServer`.

- Remove profiling support via `publisher-profile-file` directive.

- Changed the value for ``default-zpublisher-encoding`` to ``utf-8``.
  If you set a different value for ``management_page_charset`` consider
  changing ``default-zpublisher-encoding`` now.

- Removed the ``enable-ms-author-via`` directive which was only required for
  very old web folder implementations from before 2007.

- Changed `zope.conf` default settings for ``python-check-interval`` to ``1000``.

Dependencies
++++++++++++

- Integrate code from and drop dependency on `five.globalrequest`.

- Integrate `five.pt` code directly into `Products.PageTemplates`.

- Drop `ZopeUndo` dependency.

- Remove `Products.StandardCacheManagers` dependency.

- Remove dependency on `initgroups`. Use the standard libraries
  ``os.initgroups`` instead.

- Merge `Products.OFSP` project back in.

- `Products.SiteErrorLog` is now a separated package and Zope no longer depends
  on it.

- Split `Products.TemporaryFolder` and `Products.ZODBMountPoint` into
  one new project called `Products.TemporaryFolder`.

- Create new `Products.Sessions` distribution including ``Products.Sessions``
  and ``Products.Transience`` code.

- Dropped the direct dependencies on packages that have been factored out of
  the main Zope 2 tree. Make sure you declare a dependency in your own
  distribution if you still use one of these:

    - `Products.BTreeFolder2`
    - `Products.ExternalMethod`
    - `Products.MailHost`
    - `Products.MIMETools`
    - `Products.PythonScripts`
    - `Products.SiteErrorLog`
    - `Products.StandardCacheManagers`
    - `Products.ZCatalog`
    - `Record`

Deprecations
++++++++++++

- Five.browser: Marked `processInputs` and `setPageEncoding` as deprecated.
  `processInputs` was replaced by the `postProcessInputs` request method and
  the charset negotiation done by `setPageEncoding` was never fully supported.

New features
++++++++++++

- Add support to SameSite cookie in ``ZPublisher.HTTPBaseResponse``:
  https://tools.ietf.org/html/draft-west-first-party-cookies-07

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

- ZPublisher: If `IBrowserPage` is provided by a view, form input is decoded.
  This makes it easier to use ``zope.formlib`` and ``z3c.form`` in Zope 2.

Security fixes
++++++++++++++

- Fix reflective XSS in findResult.

- Patch zope.interface to remove docstrings and avoid publishing.

- Don't copy items the user is not allowed to view.

- Quote variable in manage_tabs to avoid XSS.

- Removed docstrings from some methods to avoid publishing them.

- Ensure that Request objects cannot be published / traversed
  directly via a URL.
  (`LP #789863 <https://bugs.launchpad.net/zope2/+bug/789863>`_)


- Port tests for ``str.format`` security fix from Zope 2.13.

Bugfixes
++++++++

- PropertyManagers and PropertySheets now correctly accept all forms of
  strings as property values.

- Allow handling of multipart requests in functional doctests using ``http``.

- Fix Content-Length header for non-ascii responses incl. a base tag.

- bobo_traverse of ProductDispatcher did not correctly invalidate cache
  when a product was not initializes after first access of the cache. Types
  that were added in test-profiles were not useable.

- Prevent leaked connections when broken ``EndRequestEvent``
  subscribers raise exceptions.
  (`#16 <https://github.com/zopefoundation/Zope/issues/16>`_)

- Made sure ``getConfiguration().default_zpublisher_encoding`` is set correctly.

- Fix publishing of ``IStreamIterator``. This interface does
  not have seek or tell.  Introduce ``IUnboundStreamIterator`` to support
  publishing iterators of unknown length.
  (`#28 <https://github.com/zopefoundation/Zope/pull/28>`_)

- Removed the (very obsolete) thread lock around the cookie parsing code
  in HTTPRequest.py; the python `re` module is thread-safe, unlike the
  ancient `regex` module that was once used here.
