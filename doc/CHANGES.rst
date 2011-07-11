Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

4.0.0a1 (unreleased)
--------------------

Bugs Fixed
++++++++++

- Restore ability to undo multiple transactions from the ZMI by using the
  `undoMultiple` API.

- Made sure getConfiguration().default_zpublisher_encoding is set correctly.

Features Added
++++++++++++++

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

- Updated to Zope Toolkit 1.2dev.

- Updated distributions:

  - DateTime = 3.0b1
  - manuel = 1.5.0

Restructuring
+++++++++++++

- On the application object, removed `PrincipiaTime` in favor of `ZopeTime` and
  `PrincipiaRedirect` in favor of `Redirect` or `ZopeRedirect`.

- Removed `OFS.DefaultObservable` - an early predecessor of `zope.event`.

- Removed `mime-types` option from `zope.conf`. You can use the `add_files`
  API from `zope.contenttype` instead.

- Removed `OFS.ZDOM`.

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
  hosted at http://docs.zope.org/zope2/. For backwards compatibility the
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

- Removed the rarely used support for the `++skin++` traverser. You can enable
  it in your own applications by defining::

    <adapter
      name="skin"
      for="* zope.publisher.interfaces.IRequest"
      provides="zope.traversing.interfaces.ITraversable"
      factory="zope.traversing.namespace.skin" />

- Five.browser: Marked `processInputs` and `setPageEncoding` as deprecated.
  `processInputs` was replaced by the `postProcessInputs` request method and
  the charset negotiation done by `setPageEncoding` was never fully supported.

- Dropped the direct dependencies on packages that have been factored out of
  the main Zope 2 tree. Make sure you declare a dependency in your own
  distribution if you still use one of these: ``Products.BTreeFolder2``,
  ``Products.ExternalMethod``, ``Products.MailHost``, ``Products.MIMETools``,
  ``Products.PythonScripts`` or ``Products.StandardCacheManagers``.
