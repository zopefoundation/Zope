Change log
==========

These are all the changes for Zope 5, starting with the alpha releases,
since the branch point at Zope 4.1.2.

The change log for the previous version, Zope 4, is at
https://github.com/zopefoundation/Zope/blob/4.x/CHANGES.rst


5.3 (unreleased)
----------------

- Prevent ``DeprecationWarnings`` from moved imports in ``AccessControl``

- make sure "Manager" users can always modify proxy roles
  (`see Products.PythonScripts#50
    <https://github.com/zopefoundation/Products.PythonScripts/issues/50>`_)

- Deprecate usage of "unicode" converters. Also, the behavior of
  ``field2lines`` is now aligned to the other converters and returns a list of
  strings instead of a list of bytes.
  (`#962 <https://github.com/zopefoundation/Zope/issues/962>`_)

- Update to newest compatible versions of dependencies.


5.2.1 (2021-06-08)
------------------

- Prevent unauthorized traversal through authorized Python modules in
  TAL expressions

- Facelift the Zope logo.
  (`#973 <https://github.com/zopefoundation/Zope/issues/973>`_)

- Update to newest compatible versions of dependencies.


5.2 (2021-05-21)
----------------

- Prevent traversal to names starting with ``_`` in TAL expressions
  and fix path expressions for the ``chameleon.tales`` expression engine.

- Provide friendlier ZMI error message for the Transaction Undo form
  (`#964 <https://github.com/zopefoundation/Zope/issues/964>`_)

- Updated/fixed the poll application tutorial in the Zope Developers Guide
  (`#958 <https://github.com/zopefoundation/Zope/issues/958>`_)

- Update to newest versions of dependencies.

- Depend on ``zope.datetime`` for the functions ``iso8601_date``,
  ``rfc850_date``, and ``rfc1123_date`` which used to be in ``App.Common``
  keeping backwards-compatibility imports in place.

Backwards incompatible changes
++++++++++++++++++++++++++++++

- With the exception of ``field2bytes``, field converters do no longer try to
  read file like objects
  (`#558 <https://github.com/zopefoundation/Zope/issues/558>`_)


5.1.2 (2021-03-02)
------------------

- Enforce Zope permissions during recursive XML-RPC data dumps
  (`#954 <https://github.com/zopefoundation/Zope/issues/954>`_)

- The ``compute_size`` method properly returns None if the content does not
  have a ``get_size`` method but the parent has.
  (`#948 <https://github.com/zopefoundation/Zope/issues/948>`_)

- Fix control panel tab links on all control panel pages

- Update to newest versions of dependencies.


5.1.1 (2021-02-10)
------------------

- Replace (in ``OFS``) the deprecated direct ``id`` access by
  ``getId`` calls.
  (`#903 <https://github.com/zopefoundation/Zope/issues/903>`_)

- Update ZMI dependencies for Font Awesome, jQuery and bootstrap.

- Revise debug info GUI
  (`#937 <https://github.com/zopefoundation/Zope/pull/937>`_)

- Convert ``bytes`` ``HTTPResponse`` header value to ``str``
  via ``ISO-8859-1`` (the default encoding of ``HTTP/1.1``).

- Fix rendering of not found resources.
  (`#933 <https://github.com/zopefoundation/Zope/pull/933>`_)

- Update to newest versions of dependencies.


5.1 (2020-11-12)
----------------

Backwards incompatible changes
++++++++++++++++++++++++++++++

- Exclude characters special for ``chameleon``'s interpolation syntax
  (i.e. ``${}``) from use in TALES path expressions to reduce the failure risk
  for the ``chameleon`` interpolation heuristics
  (`#925 <https://github.com/zopefoundation/Zope/issues/925>`_)

Features
++++++++

- Restore the ZMI `Debug Information` control panel page
  (`#898 <https://github.com/zopefoundation/Zope/issues/898>`_)

Fixes
+++++

- Fix ZMI visibility of pre elements in error log
  (`Products.SiteErrorLog#26
  <https://github.com/zopefoundation/Products.SiteErrorLog/issues/26>`_)

- Fix ``length`` for page template repeat variables
  (`#913 <https://github.com/zopefoundation/Zope/issues/913>`_)

- Update `isort` to version 5.
  (`#892 <https://github.com/zopefoundation/Zope/pull/892>`_)

- Update to newest versions of dependencies.


5.0 (2020-10-08)
----------------

Backwards incompatible changes
++++++++++++++++++++++++++++++

- Drop support for Python 3.5 as it will run out of support soon.
  (`#841 <https://github.com/zopefoundation/Zope/issues/841>`_)


Features
++++++++

- HTTP header encoding support
  (`#905 <https://github.com/zopefoundation/Zope/pull/905>`_)

- Add support for Python 3.9.

- New interface ``Products.PageTemplates.interfaces.IZopeAwareEngine``.
  It can be used as the "provides" of an adapter registration
  to adapt a non ``Zope`` tales engine to an engine to be used
  by ``Zope`` page templates
  (`#864 <https://github.com/zopefoundation/Zope/issues/864>`_).
  Currently, the adaptation is used only when the
  template is rendered with ``chameleon``;
  with ``zope.pagetemplate``, the engine is used
  as is - this may change in the future.

- Allow (some) builtins as first element of a (TALES) path expression:
  in an untrusted context, the builtins from
  ``AccessControl.safe_builtins`` are allowed;
  in a trusted context, all Python builtins are allowed in addition
  (and take precedence)
  (`zope.tales#23 <https://github.com/zopefoundation/zope.tales/issues/23>`_).

- Support the ``attrs`` predefined template variable again (as
  far as ``chameleon`` allows it)
  (`#860 <https://github.com/zopefoundation/Zope/issues/860>`_).

- Use ``Chameleon`` (>= 3.7.2) configuration to get better
  information for errors detected during template execution
  (`#837 <https://github.com/zopefoundation/Zope/issues/837>`_).

Fixes
+++++

- Provide a more senseful ``OFS.SimpleItem.Item_w__name__.id``
  to avoid bugs by use of deprecated direct ``id`` access
  (as e.g. (`#903 <https://github.com/zopefoundation/Zope/issues/903>`_).

- Update to ``zope.interface > 5.1.0`` to fix a memory leak.

- Fix export of files with non-latin-1 compatible names
  (`#890 <https://github.com/zopefoundation/Zope/issues/890>`_)

- Avoid unsolicited translations
  (`#876 <https://github.com/zopefoundation/Zope/issues/876>`_)

- Make "chameleon-zope context wrapping" more faithful.
  (`#873 <https://github.com/zopefoundation/Zope/pull/873/files>`_)

- Let "unicode conflict resolution" work for all templates (not just
  ``ZopePageTemplate``).
  (`#872 <https://github.com/zopefoundation/Zope/pull/872/files>`_)

- Make "Unicode Conflict Resolution" available for templates
  rendered with ``chameleon``
  (`Products.CMFPlone#3145
  <https://github.com/plone/Products.CMFPlone/issues/3145>`_).

- Improve documentation of ``CONTEXTS`` in the "Zope Book".

- Decrease cookie size for copy/paste clipboard cookie
  (`#854 <https://github.com/zopefoundation/Zope/issues/854>`_)

- Fix ``default`` keyword handling in page templates
  (`#846 <https://github.com/zopefoundation/Zope/issues/846>`_)

- Fix parsing of package version and show correct major version in the ZMI

- Improve solidity of the ``debugError`` method.
  (`#829 <https://github.com/zopefoundation/Zope/issues/829>`_)

- Fix that ``ZTUtils.LazyFilter`` could not be imported inside a restricted
  Python script.
  (`#901 <https://github.com/zopefoundation/Zope/pull/901>`_)

Other changes
+++++++++++++

- Add ``pyupgrade`` via ``pre-commit``
  (`#859 <https://github.com/zopefoundation/Zope/issues/859>`_)

- Add ``tal:switch`` test


5.0a2 (2020-04-24)
------------------

Bug fixes
+++++++++

- Pin ``AccessControl`` 4.2 for the `Manage WebDAV Locks` permission

- Fix ``HEAD`` requests on registered views
  (`#816 <https://github.com/zopefoundation/Zope/issues/816>`_)

- Improve ``chameleon`` --> ``zope.tales`` context wrapper
  (support for template variable injection)
  (`#812 <https://github.com/zopefoundation/Zope/pull/812>`_).

- Require ``zope.tales>=5.0.2``

- Fix issue 717 by fully honoring the engine returned by
  ``PageTemplate.pt_getEngine``
  (`#717 <https://github.com/zopefoundation/Zope/issues/717>`_).
  The engine also decides about the use of ``zope.tales``
  (engine is an instance of ``zope.pagetemplate.engine.ZopeBaseEngine``)
  or ``chameleon.tales`` (otherwise) TALES expressions.

- Fixed encoding issue of `displayname` WebDAV property
  (`#797 <https://github.com/zopefoundation/Zope/issues/797>`_)

- Fixed fallback implementation of ``manage_DAVget``
  (`#799 <https://github.com/zopefoundation/Zope/issues/799>`_)

Other changes
+++++++++++++

- Update to newest versions of dependencies.


5.0a1 (2020-02-28)
------------------

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
