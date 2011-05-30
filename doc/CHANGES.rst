Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

2.14.0a1 (unreleased)
---------------------

Bugs Fixed
++++++++++

- LP #787541: Fix WSGIPublisher to close requests on abort unconditionally.
  Previously an addAfterCommitHook was used, but this is not run on transaction
  aborts.  Now a Synchronizer is used which unconditionally closes the request
  after a transaction is finished.

- Fix `WSGIResponse` and `publish_module` functions such that they
  support the `IStreamIterator` interface in addition to `file` (as
  supported by `ZServer.HTTPResponse`).

- Made sure getConfiguration().default_zpublisher_encoding is set correctly.

- LP #713253: Prevent publication of acquired attributes, where the acquired
  object does not have a docstring.

- Fix `LazyMap` to avoid unnecessary function calls.

- LP 686664: WebDAV Lock Manager ZMI view wasn't accessible.

- Fixed argument parsing for entrypoint based zopectl commands.

- Fixed the usage of ``pstats.Stats()`` output stream. The
  `Control_Panel/DebugInfo/manage_profile` ZMI view was broken in Python 2.5+.

Features Added
++++++++++++++

- ZPublisher: HTTPResponse.appendHeader now keeps header values to a single
  line by default to avoid causing problems for proxy servers which do not
  correctly handle multi-line headers. (Merged from 2.13 branch.)

- Add preliminary IPv6 support to ZServer.

- ZPublisher: If `IBrowserPage` is provided by a view, form input is decoded.
  This makes it easier to use ``zope.formlib`` and ``z3c.form`` in Zope 2.

- Report success or failure (when known) of creating a new user with
  the addzope2user script.

- Moved subset id calculation in `OFS.OrderSupport.moveObjectsByDelta` to a
  new helper method, patch by Tom Gross.

- Use cProfile where possible for the `Control_Panel/DebugInfo/manage_profile`
  ZMI view.

- Updated to Zope Toolkit 1.2dev.

- Added `addzope2user` script, suitable for adding an admin user directly to
  the root acl_users folder.

- Remove "Control panel" object from zodb.

- Updated distributions:

  - AccessControl = 2.13.4
  - Acquisition = 2.13.7
  - DateTime = 3.0b1
  - manuel = 1.5.0
  - Products.BTreeFolder2 = 2.13.3
  - Products.ZCatalog = 2.13.14
  - Products.ZCTextIndex = 2.13.2
  - python-gettext = 1.1.1
  - pytz = 2011e
  - repoze.tm2 = 1.0b1
  - repoze.who = 2.0a4
  - zope.testbrowser = 3.11.1

Restructuring
+++++++++++++

- Five.browser: Marked `processInputs` and `setPageEncoding` as deprecated.
  `processInputs` was replaced by the `postProcessInputs` request method and
  the charset negotiation done by `setPageEncoding` was never fully supported.

- Factored out the `Products.ZCatalog` and `Products.PluginIndexes` packages
  into a new `Products.ZCatalog` distribution.

- Stopped testing non-overridden ZTK eggs in ``bin/alltests``.

- Dropped the direct dependencies on packages that have been factored out of
  the main Zope 2 tree. Make sure you declare a dependency in your own
  distribution if you still use one of these: ``Products.BTreeFolder2``,
  ``Products.ExternalMethod``, ``Products.MailHost``, ``Products.MIMETools``,
  ``Products.PythonScripts`` or ``Products.StandardCacheManagers``.
