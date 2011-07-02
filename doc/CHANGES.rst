Changelog
=========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
http://docs.zope.org/zope2/releases/.

2.14.0a1 (unreleased)
---------------------

Bugs Fixed
++++++++++

- Made sure getConfiguration().default_zpublisher_encoding is set correctly.

Features Added
++++++++++++++

- ZPublisher: If `IBrowserPage` is provided by a view, form input is decoded.
  This makes it easier to use ``zope.formlib`` and ``z3c.form`` in Zope 2.

- Remove `control panel` object from the ZODB.

- Updated to Zope Toolkit 1.2dev.

- Updated distributions:

  - DateTime = 3.0b1
  - manuel = 1.5.0

Restructuring
+++++++++++++

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
