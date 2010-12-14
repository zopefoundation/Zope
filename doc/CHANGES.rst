Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

2.14.0a1 (unreleased)
---------------------

Bugs Fixed
++++++++++

- Fix `LazyMap` to avoid unnecessary function calls.

- LP 686664: WebDAV Lock Manager ZMI view wasn't accessible.

- Fixed argument parsing for entrypoint based zopectl commands.

- Fixed the usage of ``pstats.Stats()`` output stream. The
  `Control_Panel/DebugInfo/manage_profile` ZMI view was broken in Python 2.5+.

Features Added
++++++++++++++

- Moved subset id calculation in `OFS.OrderSupport.moveObjectsByDelta` to a
  new helper method, patch by Tom Gross.

- Updated to Zope Toolkit 1.0.1.

- Use cProfile where possible for the `Control_Panel/DebugInfo/manage_profile`
  ZMI view.

Restructuring
+++++++++++++

- Stopped testing non-overridden ZTK eggs in ``bin/alltests``.

- Dropped the direct dependencies on packages that have been factored out of
  the main Zope 2 tree. Make sure you declare a dependency in your own
  distribution if you still use one of these: ``Products.BTreeFolder2``,
  ``Products.ExternalMethod``, ``Products.MailHost``, ``Products.MIMETools``,
  ``Products.PythonScripts`` or ``Products.StandardCacheManagers``.
