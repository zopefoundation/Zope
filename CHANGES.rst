Change log
==========

These are all changes for Zope 6.

The change log for Zope 4 is at
https://github.com/zopefoundation/Zope/blob/4.x/CHANGES.rst.
The change log for Zope 5 is at
https://github.com/zopefoundation/Zope/blob/5.x/CHANGES.rst.


6.1 (unreleased)
----------------


6.0 (2026-03-04)
----------------

- Fix bad calls to ``str`` in ZMI DTML templates to prevent name shadowing.
  (`#1285 <https://github.com/zopefoundation/Zope/issues/1285>`_)

- Update to newest compatible versions of dependencies.


6.0b2 (2026-01-15)
------------------

- Update to newest compatible versions of dependencies.

- Fix installation of console scripts.


6.0b1 (2025-11-22)
------------------

- Replace ``pkg_resources`` namespaces with PEP 420 native namespaces.
  This change requires using ``zc.buildout`` version 5.

- Drop support for Python 3.9.

- Switch from `z3c.checkversions` to `plone.versioncheck` to detect outdated
  dependency pins as `z3c.checkversions` no longer works and seems abandoned.
  See https://github.com/zopefoundation/z3c.checkversions/issues/32

- Update to newest compatible versions of dependencies.

- Enable multipart/form-data and application/x-www-form-urlencoded support
  for PATCH requests.
