Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
https://zope.readthedocs.io/en/2.13/CHANGES.html

For the change log of the alpha versions see
https://github.com/zopefoundation/Zope/blob/4.0a6/CHANGES.rst

4.0b10 (unreleased)
-------------------

Fixes
+++++

- Fix import file drop down on import export page.
  (`#524 <https://github.com/zopefoundation/Zope/issues/524>`_)

- Resurrected copyright and license page
  (`#482 <https://github.com/zopefoundation/Zope/issues/482>`_)

- Fix FindSupport binary value handling
  (`#406 <https://github.com/zopefoundation/Zope/issues/406>`_)

- Fix remove double quoting in ``ZPublisher.HTTPRequest.search_type``
  (`#511 <https://github.com/zopefoundation/Zope/issues/511>`_)

- Fix subscript access on Page Template ``macros`` attribute
  (`#210 <https://github.com/zopefoundation/Zope/issues/210>`_)

- Fix ``OFS.interfaces`` attribute declarations to match reality
  (`#498 <https://github.com/zopefoundation/Zope/issues/498>`_)

- Fix handling of DTML in Ace editor
  (`#489 <https://github.com/zopefoundation/Zope/issues/489>`_)

- Fix error when not selecting a file for upload in Files and Images
  (`#492 <https://github.com/zopefoundation/Zope/issues/492>`_)

- Fix ZMI add handling of ``len(filtered_meta_types()) == 1``
  (`#505 <https://github.com/zopefoundation/Zope/issues/505>`_)

- Fix ZMI add handling of ``addItemSelect`` form
  (`#506 <https://github.com/zopefoundation/Zope/issues/506>`_)

- Don't always flag PubBeforeAbort and PubBeforeAbort as retry
  (`#502 <https://github.com/zopefoundation/Zope/pull/502>`_)

Other changes
+++++++++++++

- Make sure the WSGI Response object respects lock semantics
  (`#216 <https://github.com/zopefoundation/Zope/issues/216>`_)

- Specify supported Python versions using ``python_requires`` in setup.py
  (`#481 <https://github.com/zopefoundation/Zope/issues/481>`_)

- Removed references to separate ``Products.ZCTextIndex``
  (`516 <https://github.com/zopefoundation/Zope/issues/516>`_)

- Provide additional links on PyPI with ``project_urls`` in ``setup.py``
  (`#434 <https://github.com/zopefoundation/Zope/issues/434>`_)

- Resurrect automatic support for ``standard_error_message`` DTML Method
  (`#238 <https://github.com/zopefoundation/Zope/issues/238>`_)


4.0b9 (2019-02-09)
------------------

Breaking changes
++++++++++++++++

- Remove support for Bobo Call Interface
  (`#462 <https://github.com/zopefoundation/Zope/pull/462>`_)

- Remove support for ``management_page_charset``
  (`#313 <https://github.com/zopefoundation/Zope/issues/313>`_)

Features
++++++++

- Add preliminary support for Python 3.8. as of 3.8.0a1 is released.

- Recreate ``App.version_txt.getZopeVersion``
  (`#411 <https://github.com/zopefoundation/Zope/issues/411>`_)

Fixes
+++++

- Fix display of ZMI breadcrumbs with non-ASCII path elements
  (`#401 <https://github.com/zopefoundation/Zope/issues/401>`_)

- Make sure conflicts are always retried and not masked by exception views
  (`#413 <https://github.com/zopefoundation/Zope/issues/413>`_)

- Fix faulty ZMI links due to missing URL-quoting
  (`#391 <https://github.com/zopefoundation/Zope/issues/391>`_)

- Fix configuring the maximum number of conflict retries
  (`#413 <https://github.com/zopefoundation/Zope/issues/413>`_)

- Show the content add widget again on ZCatalogs
  (`ZCatalog#45 <https://github.com/zopefoundation/Products.ZCatalog/issues/45>`_)

- Improve showing/hiding of the left-hand tree pane
  (`#457 <https://github.com/zopefoundation/Zope/issues/457>`_)

- Restore the `View` ZMI tab on folders and their subclasses
  (`#449 <https://github.com/zopefoundation/Zope/issues/449>`_)

- Don't error out when showing permissions for a non-existent user
  (`#437 <https://github.com/zopefoundation/Zope/issues/437>`_)

- Fix ZMI listing view for narrow displays.
  (`#471 <https://github.com/zopefoundation/Zope/pull/471>`_)

Other changes
+++++++++++++

- Document filesystem caching for Chameleon page templates
  and activate it by default for new WSGI instances
  (`#291 <https://github.com/zopefoundation/Zope/issues/291>`_)

- Remove obsolete environment variable "Z_DEBUG_MODE"
  (`#445 <https://github.com/zopefoundation/Zope/issues/445>`_)

- Update dependencies to newest versions.


4.0b8 (2018-12-14)
------------------

New features
++++++++++++

- Add wildcard rewrite to sub host name in VirtualHostMonster.
  (`#317 <https://github.com/zopefoundation/Zope/issues/317>`_)

- Add support for IPv6 hosts in VirtualHostMonster.
  (`#314 <https://github.com/zopefoundation/Zope/pull/314>`_)

- Add TestBrowser ``login`` method to set basic auth header.
  (`#341 <https://github.com/zopefoundation/Zope/issues/341>`_)

Other changes
+++++++++++++

- Add security declarations to ``SimpleItem.manage_FTPlist()`` and
  ``Simplified.manage_FTPstat()`` instead of requiring classes extending
  ``SimpleItem`` to do so.
  (`#398 <https://github.com/zopefoundation/Zope/pull/398>`_)

- Clarify prerequisites for building Zope in documentation.
  (`#366 <https://github.com/zopefoundation/Zope/issues/366>`_)

- Update dependencies to newest versions.

Fixes
+++++

- Restore missing Properties tab for DTML Documents
  (`#409 <https://github.com/zopefoundation/Zope/issues/409>`_)

- Add some CSS fixes for ZMI.

- Sanitize file handling for uploading and adding DTML methods and documents.

- Add a note about the ``app`` toplevel object in the debugger.

- Show a message instead of an exception for empty file upload on PageTemplate.
  (`#357 <https://github.com/zopefoundation/Zope/issues/357>`_)

- Update cookie expiration method in a way Firefox 63+ understands.
  (`#405 <https://github.com/zopefoundation/Zope/pull/405>`_)

- Fix closing newly created request before processing it after a retryable
  error has occurred.
  (`#413 <https://github.com/zopefoundation/Zope/issues/413>`_)


4.0b7 (2018-10-30)
------------------

Security related fixes
++++++++++++++++++++++

- ``HTTPRequest.text()`` now obscures values of fields those name
  contain the string ``passw`` in the same way ``HTTPRequest.__str__`` already
  did.
  (`#375 <https://github.com/zopefoundation/Zope/issues/375>`_)

Bugfixes
++++++++

- Fix `bin/mkwsgiinstance` on Python 3 when Zope was installed via ``pip``.

- Fix a bug with scopes in scripts with zconsole, which made it impossible to
  reach global imports in the script within a function.

- Fix handling of non-ASCII characters in URLs on Python 2 introduced on 4.0b5.
  (`#380 <https://github.com/zopefoundation/Zope/pull/380>`_)

- Fix zodbupdate conversion of ``OFS.Image.Pdata`` objects.

- Install the `ipaddress` package only on Python 2.7 as it is part of the
  stdlib in Python 3.
  (`#368 <https://github.com/zopefoundation/Zope/issues/368>`_)

- Fix KeyError on releasing resources of a Connection when closing the DB.
  This requires at least version 2.4 of the `transaction` package.
  (See `ZODB#208 <https://github.com/zopefoundation/ZODB/issues/208>`_.)

- Fix rendering of ordered folder icon in ZMI.

Other changes
+++++++++++++

- Restore old ``__repr__`` via ``OFS.SimpleItem.PathReprProvider``. Use this
  as first base class for your custom classes, to restore the old behaviour.
  (`#379 <https://github.com/zopefoundation/Zope/issues/379>`_)

- Update dependencies to newest versions.


4.0b6 (2018-10-11)
------------------

Breaking changes
++++++++++++++++

- Remove the ``OFS.History`` module which contained only BBB code since 4.0a2.

- Remove `bootstrap.py`. To install Zope via `zc.buildout` install the
  `zc.buildout` package in a virtual environment at first.

New features
++++++++++++

- Style the ZMI using Bootstrap.
  (`#249 <https://github.com/zopefoundation/Zope/pull/249>`_ and
  `#307 <https://github.com/zopefoundation/Zope/pull/307>`_)

- Add zconsole module for running scripts and interactive mode.
  See `documentation <https://zope.readthedocs.io/en/latest/operation.html#debugging-zope>`_.

- Add support for Python 3.7.

- Restore support for XML-RPC when using the WSGI publisher - dropped in 4.0a2.

- Add a minimum ``buildout.cfg`` suggestion in the docs for creating ``wsgi``
  instances.

- Render an error message when trying to save DTML code containing a
  SyntaxError in ZMI of a DTMLMethod or DTMLDocument.

- Render an error message when trying to upload a file without choosing one
  in ZMI of a DTMLMethod or DTMLDocument.

- Update dependencies to newest versions.

Bugfixes
++++++++

- Restore controls for reordering items in an Ordered Folder and list them
  according to the internal order by default in ZMI.
  (`#344 <https://github.com/zopefoundation/Zope/pull/344>`_)

- Call exception view before triggering _unauthorized.
  (`#304 <https://github.com/zopefoundation/Zope/pull/304>`_)

- Fix XML Page template files in Python 3
  (`#319 <https://github.com/zopefoundation/Zope/issues/319>`_)

- Fix ZMI upload of `DTMLMethod` and `DTMLDocument` to store the DTML as a
  native ``str`` on both Python versions.
  (`#265 <https://github.com/zopefoundation/Zope/pull/265>`_)

- Fix upload and rendering of text files.
  (`#240 <https://github.com/zopefoundation/Zope/pull/240>`_)

- Work around Python bug (https://bugs.python.org/issue27777)
  when reading request bodies not encoded as application/x-www-form-urlencoded
  or multipart/form-data.

- Show navigation in ``manage_menu`` in case the databases cannot be retrieved.
  (`#309 <https://github.com/zopefoundation/Zope/issues/309>`_)

- Prevent breaking page rendering when setting `default-zpublisher-encoding`
  in `zope.conf` on Python 2.
  (`#308 <https://github.com/zopefoundation/Zope/issue/308>`_)

- Fix `HTTPResponse.setBody` when the published object returns a tuple.
  (`#340 <https://github.com/zopefoundation/Zope/pull/340>`_)

- Fix ``Products.Five.browser.ObjectManagerSiteView.makeSite``
  to interact well with plone.testing's patching of the global site manager.
  (`#361 <https://github.com/zopefoundation/Zope/pull/361>`_)

- Add a backwards compatible shim for ``AccessRule`` which was removed in 4.0a1
  but can exist in legacy databases.
  (`#321 <https://github.com/zopefoundation/Zope/issue/321>`_)


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
  (`#276 <https://github.com/zopefoundation/Zope/pull/276>`_)

- Accept bytes and text as cookie value.
  (`#263 <https://github.com/zopefoundation/Zope/pull/263>`_)

- Always raise InternalError when using WSGI and let the WSGI server decide
  how to handle the request.
  (`#280 <https://github.com/zopefoundation/Zope/pull/280>`)

- Make ZODB mount points in Python 2 compatible with `ZConfig >= 3.2`.
  (`#281 <https://github.com/zopefoundation/Zope/pull/281>`_)

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

- Removed `AccessRule` and `SiteRoot` from `Products.SiteAccess`.

- Remove `Products.ZReST` and the `reStructuredText` wrapper, you can use
  `docutils` directly to gain `reST` support.

- Stop setting ``CLIENT_HOME`` as a builtin, get it via
  ``App.config.getConfiguration().clienthome`` instead.

- Drop ``OFS.History`` functionality.

- Removed ``OFS.DefaultObservable`` - an early predecessor of `zope.event`.

- Removed ``OFS.ZDOM``. `OFS.SimpleItem.Item` now implements `getParentNode()`.

- Removed special code to create user folders and page templates while creating
  new ``OFS.Folder`` instances.

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
