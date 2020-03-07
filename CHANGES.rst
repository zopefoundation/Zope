Change log
==========

These are all the changes for Zope 5, starting with the alpha releases.

The change log for the previous version, Zope 4, is at
https://github.com/zopefoundation/Zope/blob/4.x/CHANGES.rst

5.0a2 (unreleased)
------------------

(These are the changes since Zope 4.3 Besides the backwards incompatible
changes all changes have been merged back to Zope 4.x.)

Backwards incompatible changes
++++++++++++++++++++++++++++++

- None, yet.

New features
++++++++++++

- Add preliminary support for Python 3.9: the latest pre-release is tested.

Bug fixes
+++++++++

- Fixed encoding issue of `displayname` WebDAV property
  (`#797 <https://github.com/zopefoundation/Zope/issues/797>`_)

- Fixed fallback implementation of ``manage_DAVget``
  (`#799 <https://github.com/zopefoundation/Zope/issues/799>`_)


Other changes
+++++++++++++

- Update to newest versions of dependencies.


5.0a1 (2020-02-28)
------------------

These are the changes since Zope 4.1.2 where the Zope 5 branch was created
from. Besides the backwards incompatible changes all changes have been merged
back to Zope 4.x.

Backwards incompatible changes
++++++++++++++++++++++++++++++

- Drop support for Python 2.7 aka Zope 5 cannot be run on Python 2 any more.
  If you are still running on Python 2.7 upgrade to the latest Zope 4 version
  first, migrate to Python 3 and than switch to Zope 5.
  (`#692 <https://github.com/zopefoundation/Zope/issues/692>`_)

- Remove all backwards-compatibility code marked to go away in Zope 5
  (`#478 <https://github.com/zopefoundation/Zope/issues/478>`_)

- Drop support for running Zope with ZServer as it is Python 2 only.
  (`#592 <https://github.com/zopefoundation/Zope/issues/592>`_)

- Remove deprecated ``postProcessInputs`` request method.
  (`#782 <https://github.com/zopefoundation/Zope/issues/782>`_)

- Remove deprecated module ``ZPublisher.maybe_lock``.
  (`#758 <https://github.com/zopefoundation/Zope/issues/758>`_)

- Remove Help System methods from the product context.
  (`#756 <https://github.com/zopefoundation/Zope/issues/756>`_)

- Remove more deprecated code.
  (`#757 <https://github.com/zopefoundation/Zope/issues/757>`_)

- Updated Zope documentation sources for Zope 5.
  (`#659 <https://github.com/zopefoundation/Zope/issues/659>`_)

New features
++++++++++++

- Restore WebDAV support in Zope.
  (`#744 <https://github.com/zopefoundation/Zope/issues/744>`_)

- Enable WebDAV support independent of ``ZServer``.
  (`#787 <https://github.com/zopefoundation/Zope/pull/787>`_)

- Clean up and sanitize permissions used for WebDAV-related methods.

- Add ``wsgi.file_wrapper`` implementation
  https://www.python.org/dev/peps/pep-0333/#optional-platform-specific-file-handling
  (`#719 <https://github.com/zopefoundation/Zope/pull/719>`_)

Bug fixes
+++++++++

- Only use ``wsgi.file_wrapper`` for response bodies with a ``read`` method.
  (`#763 <https://github.com/zopefoundation/Zope/issues/763>`_)

- Improve detection of HTTPS requests.
  (`#680 <https://github.com/zopefoundation/Zope/issues/680>`_)

- Fix several ZMI links so they respect virtual hosting.
  (`#788 <https://github.com/zopefoundation/Zope/issues/788>`_)

- Fix sort link URLs on ``manage_main``
  (`#748 <https://github.com/zopefoundation/Zope/issues/748>`_)

- More tests to make sure all ``__str__`` implementations return native
  strings.
  (`#692 <https://github.com/zopefoundation/Zope/issues/692>`_)

- Fix longstanding test bug by forcing the page template engine.
  Many tests in ``Products.PageTemplates`` used the old Zope page template
  engine because the correct one was not registered during setup.

- Close opened db during shutdown (as ZServer is already doing).
  (`#740 <https://github.com/zopefoundation/Zope/issues/740>`_)

- The method ``unrestrictedTraverse`` raises an error when
  the argument ``path`` is not something it can work with.
  (`#674 <https://github.com/zopefoundation/Zope/issues/674>`_)

- Improve ZMI Security Tab usability for high numbers of roles.
  (`#730 <https://github.com/zopefoundation/Zope/issues/730>`_)

- Some small ZMI rendering fixes.
  (`#729 <https://github.com/zopefoundation/Zope/issues/729>`_)

- Fix error when using database minimize in the ZMI.
  (`#726 <https://github.com/zopefoundation/Zope/issues/726>`_)

- Fix ``__getattr__`` signature in ``UnauthorizedBinding``.
  (`#703 <https://github.com/zopefoundation/Zope/issues/703>`_)

- Fix VirtualHostMonster not being able to set mappings under Python 3.
  (`#708 <https://github.com/zopefoundation/Zope/issues/708>`_)

- Reduce the danger of acquiring built-in names on the ZMI Find tab.
  (`#712 <https://github.com/zopefoundation/Zope/issues/712>`_)

- Restore the mistakenly removed Properties ZMI tab on Image objects
  (`#706 <https://github.com/zopefoundation/Zope/issues/706>`_)

- Fix ``OFS.Image.File.__str__`` for ``Pdata`` contents
  (`#711 <https://github.com/zopefoundation/Zope/issues/711>`_)

- Set ``REMOTE_USER`` in wsgi environ using Zope user authentication
  (`#713 <https://github.com/zopefoundation/Zope/pull/713>`_)

- Add ``Paste`` as ``extras_require`` dependency to pull in ``Paste`` when
  installing with `pip` and `constraints.txt` to prevent startup errors.
  This requires adding the ``[wsgi]`` extra in the egg specification.
  (`#734 <https://github.com/zopefoundation/Zope/issues/734>`_)

Other changes
+++++++++++++

- Move retried request delay handling out of ``supports_retry``
  (`#474 <https://github.com/zopefoundation/Zope/issues/474>`_)

- Improve documentation for Zope's error logging services.
