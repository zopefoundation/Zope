Change log
==========

These are all the changes for Zope 5, starting with the alpha releases,
since the branch point at Zope 4.1.2.

The change log for the previous version, Zope 4, is at
https://github.com/zopefoundation/Zope/blob/4.x/CHANGES.rst

5.7.2 (unreleased)
------------------

- Fix some broken ZMI pages due to the changed default content type
  from PR https://github.com/zopefoundation/Zope/pull/1075
  (`#1078 <https://github.com/zopefoundation/Zope/issues/1078>`_)

- Update to newest compatible versions of dependencies.


5.7.1 (2022-12-16)
------------------

- Set the published default ``Content-Type`` header to ``text/plain``
  if none has been set explicitly to prevent a cross-site scripting attack.
  Also remove the old behavior of constructing an HTML page for published
  methods returning a two-item tuple.

- Update to newest compatible versions of dependencies.


5.7 (2022-11-17)
----------------

- Script `addzopeuser` accepts now parameter '-c' or '--configuration'.
  This allows passing in a custom location for the `zope.conf` file to use.
  If not specified, behavior is not altered.

- Update to newest compatible versions of dependencies.

- Change functional testing utilities to support percent encoded and unicode
  paths (`#1058 <https://github.com/zopefoundation/Zope/issues/1058>`_).

- Decode basic authentication header as utf-8, not latin1 anymore
  (`#1061 <https://github.com/zopefoundation/Zope/issues/1061>`_).

- Use UTF-8 charset for WWW-Authenticate headers in challenge responses,
  as described in `RFC7617 <https://datatracker.ietf.org/doc/html/draft-ietf-httpauth-basicauth-update-07#section-2.1>`_
  ( `#1065 <https://github.com/zopefoundation/Zope/pull/1065>`_).

- Added `:json` converter in `ZPublisher.Converters`.
  (`#957 <https://github.com/zopefoundation/Zope/issues/957>`_)

- Support Python 3.11.


5.6 (2022-09-09)
----------------

- Make Products.PageTemplate engine compatible with Chameleon 3.10.

- Update to newest compatible versions of dependencies.

- Start work on Python 3.11 support, which will arrive in a later release.

- Fix cookie path parameter handling:
  If the cookie path value contains ``%`` it is assumed to be
  fully quoted and used as is;
  if it contains only characters allowed (unquoted)
  in an URL path (with the exception of ``;``),
  it is used as is; otherwise, it is quoted using Python's
  ``urllib.parse.quote``
  (`#1052 <https://github.com/zopefoundation/Zope/issues/1052>`_).


5.5.2 (2022-06-28)
------------------

- Update ``waitress`` to version 2.1.2.

- Improvements on find_bad_templates(): check Filesystem Page
  Templates too and show html tags in web report
  (`#1042 <https://github.com/zopefoundation/Zope/issues/1042>`_)

- Fix version pin specifications for Python 3.6 compatibility.
  (`#1036 <https://github.com/zopefoundation/Zope/issues/1036>`_)

- Quote all components of a redirect URL (not only the path component)
  (`#1027 <https://github.com/zopefoundation/Zope/issues/1027>`_)

- Drop the convenience script generation from the buildout configuration
  in order to get rid of a lot of dependency version pins.
  These were only needed for maintainers who can install them manually.
  (`#1019 <https://github.com/zopefoundation/Zope/issues/1019>`_)

- Update to newest compatible versions of dependencies.

- Modify "manage_access" to allow users to switch from the compact view
  to the complete matrix view when more than 30 roles are defined.
  (`#1039 <https://github.com/zopefoundation/Zope/pull/1039>`_)

- Strip leading ``.`` in cookie domain names.
  (`#1041 <https://github.com/zopefoundation/Zope/pull/1041>`_)


5.5.1 (2022-04-05)
------------------

- Update to newest compatible versions of dependencies.

- Update ``waitress`` to version 2.1.1 to mitigate a vulnerability in that
  package. As ``waitress`` no longer supports Python 3.6 it is not advised
  to run Zope on Python 3.6 any longer even though it still supports Python
  3.6. **Due to this security issue support for Python 3.6 is now officially
  deprecated. It will be removed with Zope version 5.7.**

- To run ``bin/buildout`` inside the Zope project now ``zc.buildout >= 2.13.7``
  or ``zc.buildout >= 3.0.0b1`` is required.


5.5 (2022-03-10)
----------------

- Fix several exceptions when calling ``ZPublisher.utils.fix_properties``.

- Update to newest compatible versions of dependencies.

- Enhance cookie support. For details, see
  `#1010 <https://github.com/zopefoundation/Zope/issues/1010>`_

- Use intermediate ``str`` representation for non-bytelike response data unless
  indicated differently by the content type.
  (`#1006 <https://github.com/zopefoundation/Zope/issues/1006>`_)

- Use ``zc.buildout 3.0rc2`` to install Zope to run its tests.


5.4 (2022-01-09)
----------------

- Audit and fix all hyperlinks in code and documentation

  - Change zope.org references to zope.dev due to ongoing domain ownership
    issues. zope.dev is owned by the Plone Foundation and thus safe from
    interference. XML/ZCML namespace URLs remain unchanged.
  - Remove all links that are completely dead, such as the old zope.org
    Collectors issue trackers.
  - Update all other miscellaneous links to make them work again or remove if
    the information is gone.

- Improve type guessing for the default WebDAV PUT factory
  (`#997 <https://github.com/zopefoundation/Zope/issues/997>`_)

- Enable WebDAV PUT factories to change a newly created object's ID
  (`#997 <https://github.com/zopefoundation/Zope/issues/997>`_)

- Fix potential race condition in ``App.version_txt.getZopeVersion``
  (`#999 <https://github.com/zopefoundation/Zope/issues/999>`_)

- Don't coerce file upload fields for adding DTML Documents/Methods to string.
  This makes the Add forms work again with the ZPublisher converter code
  changes.

- Remove deprecated ulines, utext, utokens, ustring from more code.
  In the properties form, show a deprecation warning.

- Add function ``ZPublisher.utils.fix_properties``.
  You can call this to fix lines properties to only contain strings, not bytes.
  It also replaces the deprecated property types ulines, utext, utoken, and
  ustring with their non-unicode variants.
  (`#987 <https://github.com/zopefoundation/Zope/issues/987>`_)

- Add support for Python 3.10.

- Update to newest compatible versions of dependencies.


5.3 (2021-07-31)
----------------

- Reinstate simple sessioning with ``Products.TemporaryFolder``
  because the underlying issues with ``tempstorage`` have been fixed.
  (`#985 <https://github.com/zopefoundation/Zope/issues/985>`_)

- Update the ``AccessControl`` version pin to fix a remote code execution issue
  (see `AccessControl security advisory GHSA-qcx9-j53g-ccgf
  <https://github.com/zopefoundation/AccessControl/security/advisories/GHSA-qcx9-j53g-ccgf>`_)

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
