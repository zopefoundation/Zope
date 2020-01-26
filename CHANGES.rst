Change log
==========

These are all the changes for Zope 5, starting with the alpha releases.

The change log for the previous version, Zope 4, is at
https://github.com/zopefoundation/Zope/blob/4.x/CHANGES.rst


5.0a1 (unreleased)
------------------

- Remove Help System methods from the product context
  (`756 <https://github.com/zopefoundation/Zope/issues/756>`_)

- Remove more deprecated code
  (`#757 <https://github.com/zopefoundation/Zope/issues/757>`_)

- Close opened db during shutdown (as ZServer is already doing).
  (`#740 <https://github.com/zopefoundation/Zope/issues/740>`_)

- Updated Zope documentation sources for Zope 5
  (`#659 <https://github.com/zopefoundation/Zope/issues/659>`_)

- The method ``unrestrictedTraverse`` raises an error when
  the argument ``path`` is not something it can work with
  (`#674 <https://github.com/zopefoundation/Zope/issues/674>`_)

- Improve ZMI Security Tab usability for high numbers of roles
  (`#730 <https://github.com/zopefoundation/Zope/issues/730>`_)

- Some small ZMI rendering fixes
  (`#729 <https://github.com/zopefoundation/Zope/issues/729>`_)

- Fix error when using database minimize in the ZMI
  (`#726 <https://github.com/zopefoundation/Zope/issues/726>`_)

- Fix ``__getattr__`` signature in ``UnauthorizedBinding``
  (`#703 <https://github.com/zopefoundation/Zope/issues/703>`_)

- Remove more Python 2 support code
  (`#692 <https://github.com/zopefoundation/Zope/issues/692>`_)

- Move retried request delay handling out of ``supports_retry``
  (`#474 <https://github.com/zopefoundation/Zope/issues/474>`_)

- Remove all backwards-compatibility code marked to go away in Zope 5
  (`#478 <https://github.com/zopefoundation/Zope/issues/478>`_)

- Fix VirtualHostMonster not being able to set mappings under Python 3.
  (`#708 <https://github.com/zopefoundation/Zope/issues/708>`_)

- Reduce the danger of acquiring built-in names on the ZMI Find tab
  (`#712 <https://github.com/zopefoundation/Zope/issues/712>`_)

- Restore the mistakenly removed Properties ZMI tab on Image objects
  (`#706 <https://github.com/zopefoundation/Zope/issues/706>`_)

- Fix ``OFS.Image.File.__str__`` for ``Pdata`` contents
  (`#711 <https://github.com/zopefoundation/Zope/issues/711>`_)

- Add ``wsgi.file_wrapper`` implementation
  https://www.python.org/dev/peps/pep-0333/#optional-platform-specific-file-handling
  (`#719 <https://github.com/zopefoundation/Zope/pull/719>`_)

- Set ``REMOTE_USER`` in wsgi environ using Zope user authentication
  (`#713 <https://github.com/zopefoundation/Zope/pull/713>`_)

- Improve documentation for Zope's error logging services.

- Add ``Paste`` as ``extras_require`` dependency to pull in ``Paste`` when 
  installing with `pip` and `constraints.txt` to prevent startup errors.
  This requires adding the ``[wsgi]`` extra in the egg specification.
  (`#734 <https://github.com/zopefoundation/Zope/issues/734>`_)


Backwards incompatible changes
++++++++++++++++++++++++++++++

- Drop support for Python 2.7 aka Zope 5 cannot be run on Python 2 any more.
  If you are still running on Python 2.7 upgrade to the latest Zope 4 version
  first, migrate to Python 3 and than switch to Zope 5.
  (`#692 <https://github.com/zopefoundation/Zope/issues/692>`_)

- Remove Python 2 support code and dependency on ``six``.
  (`#692 <https://github.com/zopefoundation/Zope/issues/692>`_)

- Drop support for running Zope with ZServer as it is Python 2 only.
  (`#592 <https://github.com/zopefoundation/Zope/issues/592>`_)
