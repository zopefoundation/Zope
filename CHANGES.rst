Change log
==========

These are all the changes in Zope 4, starting with the alpha releases.

The change log for the previous version, Zope 2.13, is at
https://zope.readthedocs.io/en/2.13/CHANGES.html


4.8.10 (2023-09-21)
-------------------

- Allow only some image types to be displayed inline. Force download for
  others, especially SVG images.  By default we use a list of allowed types.
  You can switch a to a list of denied types by setting OS environment variable
  ``OFS_IMAGE_USE_DENYLIST=1``.  You can override the allowed list with
  environment variable ``ALLOWED_INLINE_MIMETYPES`` and the disallowed list
  with ``DISALLOWED_INLINE_MIMETYPES``.  Separate multiple entries by either
  comma or space.  This change only affects direct URL access.
  ``<img src="image.svg" />`` works the same as before. (CVE-2023-42458)
  See `security advisory <https://github.com/zopefoundation/Zope/security/advisories/GHSA-wm8q-9975-xh5v>`_.

- Tighten down the ZMI frame source logic to only allow site-local sources.
  Problem reported by Miguel Segovia Gil.


4.8.9 (2023-09-05)
------------------

- Update ``RestrictedPython`` to version 5.4 to fix a potential a security
  issue. (CVE-2023-41039)

- Update ``AccessControl`` to version 4.4 to fix a potential a security
  issue. (CVE-2023-41050)


4.8.8 (2023-06-20)
------------------

- Sanitize tainting fixing
  `#1095 <https://github.com/zopefoundation/Zope/issues/1095>`_

- Restore filename on code objects of objects returned from
  ``App.Extensions.getObject()``. This got lost in 4.0a6.


4.8.7 (2023-01-10)
------------------

- Only set response header Content-Type as text/html on exception views when
  the response has content.
  (`#1089 <https://github.com/zopefoundation/Zope/issues/1089>`_)

- Update dependencies to the latest releases for each supported Python version.


4.8.6 (2022-12-19)
------------------

- Explicitly serve ``App.Dialogs.MessageDialog`` and exception views as HTML
  due to the changed default content type from `#1075
  <https://github.com/zopefoundation/Zope/pull/1075>`_.


4.8.5 (2022-12-17)
------------------

- Fix some broken ZMI pages due to the changed default content type
  from PR https://github.com/zopefoundation/Zope/pull/1075
  (`#1078 <https://github.com/zopefoundation/Zope/issues/1078>`_)

- Update dependencies to the latest releases for each supported Python version.


4.8.4 (2022-12-16)
------------------

- Set the published default ``Content-Type`` header to ``text/plain``
  if none has been set explicitly to prevent a cross-site scripting attack.
  Also remove the old behavior of constructing an HTML page for published
  methods returning a two-item tuple.

- Update dependencies to the latest releases for each supported Python version.

- Make ``Products.PageTemplates`` compatible with Chameleon 3.10.


4.8.3 (2022-10-31)
------------------

- Update dependencies to the latest releases for each supported Python version.

- Fix cookie path parameter handling:
  If the cookie path value contains ``%`` it is assumed to be
  fully quoted and used as is;
  if it contains only characters allowed (unquoted)
  in an URL path (with the exception of ``;``),
  it is used as is; otherwise, it is quoted using Python's
  ``urllib.parse.quote``
  (`#1052 <https://github.com/zopefoundation/Zope/issues/1052>`_).

- Change functional testing utilities to support percent encoded and unicode
  paths (`#1058 <https://github.com/zopefoundation/Zope/issues/1058>`_).

- Decode basic authentication header as utf-8, not latin1 anymore
  (`#1061 <https://github.com/zopefoundation/Zope/issues/1061>`_).

- Make ``ZPublisher.utils.basic_auth_encode`` support non-ascii strings on
  Python 2
  (`#1062 <https://github.com/zopefoundation/Zope/issues/1062>`_).


4.8.2 (2022-06-01)
------------------

- Update ``waitress`` to version 2.1.2.

- Fix version pin specifications for Python 3.6 compatibility.
  (`#1036 <https://github.com/zopefoundation/Zope/issues/1036>`_)

- Fix version pin specifications for Python 3.5 compatibility.

- Add more notices to the documentation urging users to migrate to Zope 5.

- Quote all components of a redirect URL (not only the path component)
  (`#1027 <https://github.com/zopefoundation/Zope/issues/1027>`_)

- Drop the convenience script generation from the buildout configuration
  in order to get rid of a lot of dependency version pins.
  These were only needed for maintainers who can install them manually.
  (`#1019 <https://github.com/zopefoundation/Zope/issues/1019>`_)

- Update dependencies to the latest releases that still support Python 2.

- Strip leading ``.`` in cookie domain names.
  (`#1041 <https://github.com/zopefoundation/Zope/pull/1041>`_)


4.8.1 (2022-04-05)
------------------

- The pip requirements files ``requirements-full.txt`` and ``constraints.txt``
  are now maintained manually.

- Update dependencies to the latest releases that still support Python 2.

- Update ``waitress`` to version 2.1.1 to mitigate a vulnerability in that
  package. As ``waitress`` no longer supports Python versions less than
  3.7 it is not advised to run Zope 4 on Python 2.7, 3.5 or 3.6 any longer,
  even though they are still supported by Zope 4 itself.

- To run ``bin/buildout`` inside the Zope project now ``zc.buildout >= 2.13.7``
  or ``zc.buildout >= 3.0.0b1`` is required.


4.8 (2022-03-10)
----------------

- Improve source documentation for methods ``_read_data`` and
  ``get_content_type`` of ``OFS.Image.File`` and
  fix its ``PUT``
  (`#1015 <https://github.com/zopefoundation/Zope/issues/1015>`_).

- Enhance cookie support. For details, see
  `#1010 <https://github.com/zopefoundation/Zope/issues/1010>`_

- Update dependencies to the latest releases that still support Python 2.


4.7 (2022-01-09)
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

- Reinstate simple sessioning with ``Products.TemporaryFolder``
  because the underlying issues with ``tempstorage`` have been fixed.
  (`#985 <https://github.com/zopefoundation/Zope/issues/985>`_)

- Update dependencies to the latest releases that still support Python 2.


4.6.3 (2021-07-31)
------------------

- Update the ``AccessControl`` version pin to fix a remote code execution issue
  (see `AccessControl security advisory GHSA-qcx9-j53g-ccgf
  <https://github.com/zopefoundation/AccessControl/security/advisories/GHSA-qcx9-j53g-ccgf>`_)

- Prevent ``DeprecationWarnings`` from moved imports in ``AccessControl``

- make sure "Manager" users can always modify proxy roles
  (`see Products.PythonScripts#50
  <https://github.com/zopefoundation/Products.PythonScripts/issues/50>`_)

- Update dependencies to the latest releases that still support Python 2.


4.6.2 (2021-06-27)
------------------

- Backport stricter traversal checks from Zope 5

- Update dependencies to the latest releases that still support Python 2.


4.6.1 (2021-06-08)
------------------

- Prevent unauthorized traversal through authorized Python modules in
  TAL expressions

- Facelift the Zope logo.
  (`#973 <https://github.com/zopefoundation/Zope/issues/973>`_)

- Update dependencies to the latest releases that still support Python 2.


4.6 (2021-05-21)
----------------

- Prevent traversal to names starting with ``_`` in TAL expressions
  and fix path expressions for the ``chameleon.tales`` expression engine.

- Provide friendlier ZMI error message for the Transaction Undo form
  (`#964 <https://github.com/zopefoundation/Zope/issues/964>`_)

- Updated/fixed the poll application tutorial in the Zope Developers Guide
  (`#958 <https://github.com/zopefoundation/Zope/issues/958>`_)

- Depend on ``zope.datetime`` for the functions ``iso8601_date``,
  ``rfc850_date``, and ``rfc1123_date`` which used to be in ``App.Common``
  keeping backwards-compatibility imports in place.

- Update dependencies to the latest releases that still support Python 2.


4.5.5 (2021-03-02)
------------------

- Enforce Zope permissions during recursive XML-RPC data dumps
  (`#954 <https://github.com/zopefoundation/Zope/issues/954>`_)

- The ``compute_size`` method properly returns None if the content does not
  have a ``get_size`` method but the parent has.
  (`#948 <https://github.com/zopefoundation/Zope/issues/948>`_)

- Fix control panel tab links on all control panel pages

- Update dependencies to the latest releases that still support Python 2.


4.5.4 (2021-02-10)
------------------

- Replace (in ``OFS``) the deprecated direct ``id`` access by
  ``getId`` calls.
  (`#903 <https://github.com/zopefoundation/Zope/issues/903>`_)

- Update ZMI dependencies for Font Awesome, jQuery and bootstrap.

- Revise debug info GUI
  (`#937 <https://github.com/zopefoundation/Zope/pull/937>`_)

- Fix rendering of not found resources.
  (`#933 <https://github.com/zopefoundation/Zope/pull/933>`_)


4.5.3 (2020-11-16)
------------------

- Update dependencies to the latest releases that still support Python 2.

Fixes
+++++

- Convert ``bytes`` (Python 3) and ``unicode`` (Python 2) values for
  HTTP response headers into native strings using the HTTP/1.1
  stipulated ``ISO-8859-1`` encoding. This makes ``waitress`` happy
  which insists on native strings for those values.
  (Fix for `#905 <https://github.com/zopefoundation/Zope/pull/905>`_)


4.5.2 (2020-11-12)
------------------

Backward incompatible changes
+++++++++++++++++++++++++++++

- Exclude characters special for ``chameleon``'s interpolation syntax
  (i.e. ``${}``) from use in TALES path expressions to reduce the failure risk
  for the ``chameleon`` interpolation heuristics
  (`#925 <https://github.com/zopefoundation/Zope/issues/925>`_)

Fixes
+++++

- Fix ``length`` for page template repeat variables
  (`#913 <https://github.com/zopefoundation/Zope/issues/913>`_)

- Restore the ZMI `Debug Information` control panel page
  (`#898 <https://github.com/zopefoundation/Zope/issues/898>`_)

- HTTP header encoding support
  (`#905 <https://github.com/zopefoundation/Zope/pull/905>`_)

- Provide a more senseful ``OFS.SimpleItem.Item_w__name__.id``
  to avoid bugs by use of deprecated direct ``id`` access
  (as e.g. `#903 <https://github.com/zopefoundation/Zope/issues/903>`_).

- Fix ZMI visibility of pre elements in error log

- Update dependencies to the latest releases that still support Python 2.

- Update to ``zope.interface > 5.1.0`` to fix a memory leak.

- Fix that ``ZTUtils.LazyFilter`` could not be imported inside a restricted
  Python script.
  (`#901 <https://github.com/zopefoundation/Zope/pull/901>`_)


4.5.1 (2020-08-13)
------------------

- Avoid unsolicited translations
  (`#876 <https://github.com/zopefoundation/Zope/issues/876>`_)

- Make "chameleon-zope context wrapping" more faithful.
  (`#873 <https://github.com/zopefoundation/Zope/pull/873/files>`_)

- Let "unicode conflict resolution" work for all templates (not just
  ``ZopePageTemplate``).
  (`#872 <https://github.com/zopefoundation/Zope/pull/872/files>`_)

- Update dependencies to the latest releases that still support Python 2.


4.5 (2020-07-09)
----------------

- Make "Unicode Conflict Resolution" available for templates
  rendered with ``chameleon``
  (`Products.CMFPlone#3145
  <https://github.com/plone/Products.CMFPlone/issues/3145>`_).

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

- Add ``tal:switch`` test

- Support the ``attrs`` predefined template variable again (as
  far as ``chameleon`` allows it)
  (`#860 <https://github.com/zopefoundation/Zope/issues/860>`_).

- Improve documentation of ``CONTEXTS`` in the "Zope Book".

- Update dependencies to the latest releases that still support Python 2.


4.4.4 (2020-06-26)
------------------

- Decrease cookie size for copy/paste clipboard cookie
  (`#854 <https://github.com/zopefoundation/Zope/issues/854>`_)

- Fix ``default`` keyword handling in page templates
  (`#846 <https://github.com/zopefoundation/Zope/issues/846>`_)

- Update dependencies to newest bugfix releases.


4.4.3 (2020-06-16)
------------------

- Fix parsing of package version and show correct major version in the ZMI.

- Improve solidity of the ``debugError`` method.
  (`#829 <https://github.com/zopefoundation/Zope/issues/829>`_)

- Use ``Chameleon`` (>= 3.7.2) configuration to get better
  information for errors detected during template execution.
  (`#837 <https://github.com/zopefoundation/Zope/issues/837>`_)

- Update dependencies to newest releases.


4.4.2 (2020-04-30)
------------------

- Fix faulty 4.4.1 release.


4.4.1 (2020-04-30)
------------------

- Fix ``HEAD`` requests on registered views.
  (`#816 <https://github.com/zopefoundation/Zope/issues/816>`_)

- Pin ``AccessControl`` to 4.2, it gained a missing WebDAV permission name.


4.4 (2020-03-31)
----------------

- Fix incompatiblities with ``Archetypes``

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


4.3 (2020-02-25)
----------------

- Enable WebDAV support independent of ``ZServer``
  (`#787 <https://github.com/zopefoundation/Zope/pull/787>`_)

- Only use ``wsgi.file_wrapper`` for response bodies with a ``read`` method
  (`#763 <https://github.com/zopefoundation/Zope/issues/763>`_)

- Improve detection of HTTPS requests
  (`#680 <https://github.com/zopefoundation/Zope/issues/680>`_)

- Fix several ZMI links so they respect virtual hosting
  (`#788 <https://github.com/zopefoundation/Zope/issues/788>`_)

- Deprecate unused ``postProcessInputs`` request method for removal in Zope 5
  (`#782 <https://github.com/zopefoundation/Zope/issues/782>`_)

- Clean up and sanitize permissions used for WebDAV-related methods


4.2.1 (2020-02-09)
------------------

- Repair Python 2.7 compatibility due to a Python 3-only import

- Add shim modules with deprecation warnings for some ``webdav`` consumers

- Prevent a UnicodeDecode error under Python 2 with non-ASCII properties


4.2 (2020-02-09)
----------------

- Restore WebDAV support in Zope
  (`#744 <https://github.com/zopefoundation/Zope/issues/744>`_)

- Fix sort link URLs on ``manage_main``
  (`#748 <https://github.com/zopefoundation/Zope/issues/748>`_)

- Fix longstanding test bug by forcing the page template engine.
  Many tests in ``Products.PageTemplates`` used the old Zope page template
  engine because the correct one was not registered during setup.

- Add deprecation warnings to the ``ZPublisher.maybe_lock`` module
  (`#758 <https://github.com/zopefoundation/Zope/issues/758>`_)

- Add deprecation warnings to Help System-related methods
  (`#756 <https://github.com/zopefoundation/Zope/issues/756>`_)

- Update to current releases of the dependencies


4.1.3 (2019-12-01)
------------------

- Close opened db during shutdown (as ZServer is already doing).
  (`#740 <https://github.com/zopefoundation/Zope/issues/740>`_)

- Add ``Paste`` as ``extras_require`` dependency to pull in ``Paste`` when
  installing with `pip` and `constraints.txt` to prevent startup errors.
  This requires adding the ``[wsgi]`` extra in the egg specification.
  (`#734 <https://github.com/zopefoundation/Zope/issues/734>`_)

- Fix broken deprecated import when ZServer is not installed
  (`#714 <https://github.com/zopefoundation/Zope/issues/714>`_)

- Improve ZMI Security Tab usability for high numbers of roles
  (`#730 <https://github.com/zopefoundation/Zope/issues/730>`_)

- Some small ZMI rendering fixes
  (`#729 <https://github.com/zopefoundation/Zope/issues/729>`_)

- Fix error when using database minimize in the ZMI
  (`#726 <https://github.com/zopefoundation/Zope/issues/726>`_)

- Fix ``__getattr__`` signature in ``UnauthorizedBinding``
  (`#703 <https://github.com/zopefoundation/Zope/issues/703>`_)

- Set ``REMOTE_USER`` in wsgi environ using Zope user authentication
  (`#713 <https://github.com/zopefoundation/Zope/pull/713>`_)

- Add ``wsgi.file_wrapper`` implementation
  https://www.python.org/dev/peps/pep-0333/#optional-platform-specific-file-handling
  (`#719 <https://github.com/zopefoundation/Zope/pull/719>`_)

- Fix VirtualHostMonster not being able to set mappings under Python 3.
  (`#708 <https://github.com/zopefoundation/Zope/issues/708>`_)

- Reduce the danger of acquiring built-in names on the ZMI Find tab
  (`#712 <https://github.com/zopefoundation/Zope/issues/712>`_)

- Restore the mistakenly removed Properties ZMI tab on Image objects
  (`#706 <https://github.com/zopefoundation/Zope/issues/706>`_)

- Fix ``OFS.Image.File.__str__`` for ``Pdata`` contents
  (`#711 <https://github.com/zopefoundation/Zope/issues/711>`_)

- Update to current releases of the dependencies.


4.1.2 (2019-09-04)
------------------

- Resurrect ZMI History tab and functionality.

- Remove commented out configuration for ``tempstorage`` (and server side
  sessions) as that was known not working for ages. This was removed so we do
  not lead unsuspecting developers to think that this is the right way to do
  session data. See
  (`#679 <https://github.com/zopefoundation/Zope/issues/679>`_)
  (`tempstorage#8 <https://github.com/zopefoundation/tempstorage/issues/8>`_)
  (`tempstorage#12 <https://github.com/zopefoundation/tempstorage/issues/12>`_)

- Reuse ``zope.publisher.http.splitport`` instead of defining our own
  (`#683 <https://github.com/zopefoundation/Zope/issues/683>`_)

- Update to current releases of the dependencies.


4.1.1 (2019-07-02)
------------------

- Document the Zope configuration options from the configuration schema itself
  (`#571 <https://github.com/zopefoundation/Zope/issues/571>`_)

- Update to current releases of the dependencies.

- Fix broken ZMI when using non-root deployments.
  (`#647 <https://github.com/zopefoundation/Zope/issues/647>`_)


4.1 (2019-06-19)
----------------

Features
++++++++

- Resurrect ZODB packing from the ZMI.
  (`#623 <https://github.com/zopefoundation/Zope/issues/623>`_)

- Optionally control the use of Zope's built-in XML-RPC support for
  POST requests with Content-Type ``text/xml`` via the
  registration of a ``ZPublisher.interfaces.IXmlrpcChecker`` utility.
  (`#620 <https://github.com/zopefoundation/Zope/issues/620>`_)

- Document request parameter handling.
  (`#636 <https://github.com/zopefoundation/Zope/issues/636>`_)


Fixes
+++++

- `allowed_attributes` and `allowed_interface` work again for BrowserViews.
  (`#397 <https://github.com/zopefoundation/Zope/issues/397>`_)

- Prevent encoding issues in existing DTML Method and DTML Document objects.

- Fixed logic error in exceptions handling during publishing. This error would
  prevent correct `Unauthorized` handling when exceptions debug mode was set.

- Do not cache (implicit) request access to form data and cookies in ``other``.
  (`#630 <https://github.com/zopefoundation/Zope/issues/630>`_)

- Bring request lookup order related documentation in line with the
  actual implementation.
  (`#629 <https://github.com/zopefoundation/Zope/issues/629>`_)
  Minor clean-up of ``HTTPRequest.get``.

- Fix missing ``Paste`` distribution on installation using ``pip``.
  (`#452 <https://github.com/zopefoundation/Zope/issues/452>`_)

Other changes
+++++++++++++

- Fixed usability on ZMI Security tab forms for sites with many roles.

- Update to current releases of most dependencies.


4.0 (2019-05-10)
----------------

Fixes
+++++

- Make sure new object IDs don't clash with the views lookup mechanism.
  (`#591 <https://github.com/zopefoundation/Zope/issues/591>`_)

- Be more careful when guessing at encoding for document template types.

- Ensure a redirect path does not get URL-encoded twice.

- Prevent inability to log into the ZMI due to failing exception views.

- Harden ``RESPONSE.redirect`` to deal with any unencoded or encoded input.
  (`#435 <https://github.com/zopefoundation/Zope/issues/435>`_)

- Fix broken ``title_and_id`` behaviour.
  (`#574 <https://github.com/zopefoundation/Zope/issues/574>`_)

- Fix broken ZMI DTML rendering for mixed unicode/bytes content.
  (`#271 <https://github.com/zopefoundation/Zope/issues/271>`_)

- Fix wrong `Content-Length` set by ``App.ImageFile`` on 304 responses.
  (`#513 <https://github.com/zopefoundation/Zope/issues/513>`_)

- Make the ZMI `Find` tab work for searching HTML tags
  by adding support for `Tainted` strings in ``ZopeFind``.

- Prevent ``mkwsgiinstance`` from blowing up parsing ``buildout.cfg``.

- Fix ``ZPublisher.HTTPResponse.HTTPBaseResponse.isHTML`` for binary data on
  Python 3.
  (`#577 <https://github.com/zopefoundation/Zope/pull/577>`_)

- Prevent ``FindSupport.ZopeFind`` from throwing ``UnicodeDecodeErrors``.
  (`#594 <https://github.com/zopefoundation/Zope/issues/594>`_)

Features
++++++++

- Add a configuration flag to show bookmarkable URLs in the ZMI.
  (`#580 <https://github.com/zopefoundation/Zope/issues/580>`_)

- Add a flag for suppressing object events during file import.
  (`#42 <https://github.com/zopefoundation/Zope/issues/42>`_)

- Add a Configuration details tab to the Control_Panel.

- Resurrect the Interfaces ZMI tab.
  (`#450 <https://github.com/zopefoundation/Zope/issues/450>`_)

- Better default logging configuration for simple waitress WSGI setups.
  (`#526 <https://github.com/zopefoundation/Zope/issues/526>`_)

- Replace usage of ``urllib.parse.splitport`` and ``urllib.parse.splittype``
  which are deprecated in Python 3.8.
  (`#476 <https://github.com/zopefoundation/Zope/pull/476>`_)

Other changes
+++++++++++++

- Update ZODB migration documentation.

- Expand the Zope 4 migration documentation.

- Change the WSGI configuration template so those annoying waitress queue
  messages only go into the event log, but not onto the console.

- Change naming for the generated WSGI configurations to ``zope.conf`` and
  ``zope.ini`` to match existing documentation for Zope configurations.
  (`#571 <https://github.com/zopefoundation/Zope/issues/571>`_)

- Make Zope write a PID file again under WSGI.
  This makes interaction with sysadmin tools easier.
  The PID file path can be set in the Zope configuration with ``pid-filename``,
  just like in ``ZServer``-based configurations.

- Exceptions during publishing are now re-raised in a new exceptions debug
  mode to allow WSGI middleware to handle/debug it. See the `debug
  documentation <https://zope.readthedocs.io/en/4.x/wsgi.html#werkzeug>`_
  for examples.
  (`#562 <https://github.com/zopefoundation/Zope/issues/562>`_)

- Remove hardcoded list of factories that don't want an add dialog.
  (`#540 <https://github.com/zopefoundation/Zope/issues/540>`_)

- Increase link visibility in old ZMI forms.
  (`#530 <https://github.com/zopefoundation/Zope/issues/530>`_)

- Always keep action buttons visible on the content list for large folders.
  (`#537 <https://github.com/zopefoundation/Zope/issues/537>`_)

- Make showing the ZMI modal add dialog configurable per product.
  (`#535 <https://github.com/zopefoundation/Zope/issues/535>`_)

- Added a few Zope 4 ZMI screenshots to the documentation.
  (`#378 <https://github.com/zopefoundation/Zope/issues/378>`_)

- Refresh Sphinx configuration and switched to the ReadTheDocs theme.

- Rename/move the `Zope 2 Book` to `Zope Book`.
  (`#443 <https://github.com/zopefoundation/Zope/issues/443>`_)

- Show item icons on ZMI `Find` tab results.
  (`#534 <https://github.com/zopefoundation/Zope/issues/534>`_)

- Full PEP-8 compliance.

- Fix ZMI font rendering on macOS.
  (`#531 <https://github.com/zopefoundation/Zope/issues/531>`_)

- Provide a method to get breadcrumb length to prevent ZMI errors.
  (`#533 <https://github.com/zopefoundation/Zope/issues/533>`_)

- Add ``zodbupdate_rename_dict`` to move ``webdav.LockItem`` to
  ``OFS.LockItem``.
  (`Products.CMFPlone#2800 <https://github.com/plone/Products.CMFPlone/issues/2800>`_)


4.0b10 (2019-03-08)
-------------------

Fixes
+++++

- Fix import file drop down on import export page.
  (`#524 <https://github.com/zopefoundation/Zope/issues/524>`_)

- Resurrect copyright and license page.
  (`#482 <https://github.com/zopefoundation/Zope/issues/482>`_)

- Fix FindSupport binary value handling.
  (`#406 <https://github.com/zopefoundation/Zope/issues/406>`_)

- Fix remove double quoting in ``ZPublisher.HTTPRequest.search_type``
  (`#511 <https://github.com/zopefoundation/Zope/issues/511>`_)

- Fix subscript access on Page Template ``macros`` attribute.
  (`#210 <https://github.com/zopefoundation/Zope/issues/210>`_)

- Fix ``OFS.interfaces`` attribute declarations to match reality.
  (`#498 <https://github.com/zopefoundation/Zope/issues/498>`_)

- Fix handling of DTML in Ace editor.
  (`#489 <https://github.com/zopefoundation/Zope/issues/489>`_)

- Fix error when not selecting a file for upload in Files and Images.
  (`#492 <https://github.com/zopefoundation/Zope/issues/492>`_)

- Fix ZMI add handling of ``len(filtered_meta_types()) == 1``.
  (`#505 <https://github.com/zopefoundation/Zope/issues/505>`_)

- Fix ZMI add handling of ``addItemSelect`` form.
  (`#506 <https://github.com/zopefoundation/Zope/issues/506>`_)

- Don't always flag ``PubBeforeAbort`` and ``PubBeforeAbort`` as retry.
  (`#502 <https://github.com/zopefoundation/Zope/pull/502>`_)

Features
++++++++

- Specify supported Python versions using ``python_requires`` in `setup.py`.
  (`#481 <https://github.com/zopefoundation/Zope/issues/481>`_)

- Provide additional links on PyPI with ``project_urls`` in ``setup.py``
  (`#434 <https://github.com/zopefoundation/Zope/issues/434>`_)

- Resurrect automatic support for ``standard_error_message`` DTML Method.
  (`#238 <https://github.com/zopefoundation/Zope/issues/238>`_)

Other changes
+++++++++++++

- Make sure the WSGI Response object respects lock semantics.
  (`#216 <https://github.com/zopefoundation/Zope/issues/216>`_)

- Remove references to separate ``Products.ZCTextIndex``.
  (`516 <https://github.com/zopefoundation/Zope/issues/516>`_)

- Update dependencies to newest versions.


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
  See the `document Running Zope
  <https://zope.readthedocs.io/en/4.x/operation.html#debugging-zope>`_.

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


4.0a6 (2017-06-01)
------------------

Features Added
++++++++++++++

- Updated distributions:

    - Products.BTreeFolder2 = 4.0.0
    - Products.ZCatalog = 4.0.0


Restructuring
+++++++++++++

- Claim support for Python 3 and update the documentation.


4.0a5 (2017-05-22)
------------------

Features Added
++++++++++++++

- Many changes to support Python 3.

- Updated distributions:

    - AccessControl = 4.0a7
    - DocumentTemplate = 3.0a3
    - Missing = 4.0
    - MultiMapping = 4.0
    - Record = 3.4
    - zExceptions = 3.6.1


4.0a4 (2017-05-12)
------------------

Bugs Fixed
++++++++++

- #116: Restore exception views for unauthorized.

- Restore a `_unauthorized` hook on the response object.

- Restore `HTTPResponse.redirect` behaviour of not raising an exception.

Features Added
++++++++++++++

- Updated distributions:

    - AccessControl = 4.0a6
    - Acquisition = 4.4.2
    - Record = 3.3
    - zope.dottedname = 4.2.0
    - zope.i18nmessageid = 4.1.0


4.0a3 (2017-05-03)
------------------

Bugs Fixed
++++++++++

- Fixed reflective XSS in findResult.
  This applies PloneHotfix20170117.  [maurits]

- Patch zope.interface to remove docstrings and avoid publishing.
  From Products.PloneHotfix20161129.   [maurits]

- Don't copy items the user is not allowed to view.
  From Products.PloneHotfix20161129.  [maurits]

- Make the WSGIPublisher normalize HTTP exception classes based on name
  (for example, any exception named NotFound will be converted
  into `zExceptions.NotFound`). This restores compatibility with
  similar behavior of the old publisher.
  [davisagli]

- Use unicode transaction-notes to support ZODB 5.
  [pbauer]

Features Added
++++++++++++++

- Add support to SameSite cookie in ``ZPublisher.HTTPBaseResponse``:
  https://tools.ietf.org/html/draft-west-first-party-cookies-07

- Updated distributions:

    - AccessControl = 4.0a4
    - Acquisition = 4.3.0
    - BTrees = 4.4.1
    - DateTime = 4.2
    - DocumentTemplate = 3.0a1
    - ExtensionClass = 4.3.0
    - Missing = 3.2
    - MultiMapping = 3.1
    - Persistence = 3.0a3
    - persistent = 4.2.2
    - Products.ZCatalog = 4.0a3
    - pytz = 2016.10
    - Record = 3.2
    - transaction = 2.1.1
    - waitress = 1.0.2
    - WebOb = 1.7.1
    - WebTest = 2.0.26
    - WSGIProxy2 = 0.4.3
    - zdaemon = 4.2.0
    - ZEO = 5.0.4
    - zExceptions = 3.6
    - ZODB = 5.2.0
    - zope.configuration = 4.1.0
    - zope.deprecation = 4.2.0
    - zope.interface = 4.3.3
    - zope.testbrowser = 5.2
    - zope.testing = 4.6.1
    - zope.testrunner = 4.6.0
    - zope.globalrequest = 1.3
    - zope.testing = 4.6.0
    - ZServer = 4.0a2

Restructuring
+++++++++++++

- Integrate code from and drop dependency on `five.globalrequest`.

- Remove special handling of redirect and unauthorized exceptions from
  the WSGI publisher. These are now always raised as exceptions, to
  match the behavior of all other HTTPExceptions.

- Removed xml-export.
  [maurits, pbauer]

- Add back ZCacheable support.

- Update to zope.testbrowser 5.0 and its WebTest based implementation.

- Use `@implementer` and `@adapter` class decorators.


4.0a2 (2016-09-09)
------------------

Bugs Fixed
++++++++++

- Quote variable in manage_tabs to avoid XSS.
  From Products.PloneHotfix20160830.  [maurits]

- Remove more HelpSys references.

Features Added
++++++++++++++

- Add support for exception views to WSGIPublisher.

- Add support for ConflictError and TransientError retry logic directly
  into WSGIPublisher.

- Add support for raising HTTPOK and HTTPRedirection exceptions and
  have them result in successful transactions.

- Add better blob support to HTTPRequest.ZopeFieldStorage.

- Updated distributions:

  - AccessControl = 4.0a3
  - AuthEncoding = 4.0.0
  - Products.ZCatalog = 4.0a2
  - zExceptions = 3.3
  - ZServer = 4.0a1

Restructuring
+++++++++++++

- Change the WSGIResponse exception methods to raise exceptions instead
  of returning responses. This includes notFoundError, forbiddenError,
  debugError, badRequestError, unauthorized and redirect.

- Split a common HTTPBaseResponse base class out of HTTPResponse and
  WSGIResponse. Move ZServer specific logic onto HTTPResponse.

- Simplified `ZPublisher.WSGIPublisher.get_module_info` contract.

- Add new `ZPublisher.utils.recordMetaData` function and use default
  `transaction.manager` as the transaction manager.

- Remove support for repoze.tm2.

- Change Testing to use the WSGI publisher for functional and testbrowser
  based tests incl. functional doctests. Alternatives are available
  in `ZServer.Testing`.

- Move `ZPublisher.Publish` module into ZServer distribution.

- Remove `Globals` package, opened database are now found in
  `Zope2.opened` next to `Zope2.DB`.

- Remove proxy role support from DTML documents and methods.

- Remove ZCacheable logic and StandardCacheManagers dependency.

- Stop mixing in `Five.bbb.AcquisitionBBB` into browser components.

- Integrate `five.pt` code directly into `Products.PageTemplates`.

- Move `Products.SiteAccess` into ZServer distribution.

- Simplify Page Template and Scripts ZMI screens.

- Change VHM id to `virtual_hosting` to match AppInitializer.

- Raise BadRequest instead of returning MessageDialog.

- Remove property management ZMI screens.

- Remove ZMI copy/cut/paste/rename and re-ordering features.

- Drop `OFS.History` functionality.

- Drop ZopeUndo dependency and move undo management to the control panel.

- Simplify ZMI control panel and globally available management screens.

- Move ZServer related testing support into ZServer.Testing.

- Split out Lifetime, webdav and ZServer packages into a ZServer project.

- Move webdav's EtagSupport, Lockable and LockItem into OFS.

- Split `Products.TemporaryFolder` and `Products.ZODBMountPoint` into
  one new project called `Products.TemporaryFolder`.

- Split a WSGI part out of `zopeschema.xml`. This reduces the supported
  `zope.conf` directives when run under WSGI.

- Remove temp_folder mount point from default configuration.

- Split a WSGI part out of `Zope2.Startup.ZopeStarter`.

- Add new `ZServer.Zope2.Startup.config` module to hold configuration.

- Remove `Control_Panel` `/DebugInfo` and `/DavLocks`.

- Remove profiling support via `publisher-profile-file` directive.

- Create new `Products.Sessions` distribution including Products.Sessions
  and Products.Transience code.

- Merge `Products.OFSP` project back in.

- No longer test compatibility with dependencies:

    ``Products.ExternalMethod``
    ``Products.PythonScripts``
    ``Products.Sessions``
    ``Products.SiteErrorLog``
    ``Products.TemporaryFolder``
    ``tempstorage``
    ``zLOG``
    ``ZopeUndo``

- Dropped dependency declarations for indirect dependencies:

    ``docutils``
    ``Missing``
    ``pytz``
    ``zLOG``
    ``zope.sendmail``
    ``zope.structuredtext``


4.0a1 (2016-07-22)
------------------

Bugs Fixed
++++++++++

- Remove `Connection` and `Transfer-Encoding` headers from WSGI responses.
  According to PEP 333 WSGI applications must not emit hop-by-hop headers.

- Removed docstrings from some methods to avoid publishing them.  From
  Products.PloneHotfix20160419.  [maurits]

- bobo_traverse of ProductDispatcher did not correctly invalidate cache
  when a product was not initializes after first access of the cache. Types
  that were added in test-profiles were not useable.
  [pbauer, jensens]

- Fix pt_editForm after the help-system was removed.
  [pbauer]

- Skipped ipv6 test on Travis, because Travis no longer supports this.

- LP #789863:  Ensure that Request objects cannot be published / traversed
  directly via a URL.

- Document running Zope as a WSGI application.

- Queue additional warning filters at the beginning of the queue in order to
  allow overrides.

- Issue #16: prevent leaked connections when broken ``EndRequestEvent``
  subscribers raise exceptions.

- Ensure that the ``WSGIPublisher`` begins and ends an *interaction*
  at the request/response barrier. This is required for instance for
  the ``checkPermission`` call to function without an explicit
  ``interaction`` parameter.

- Made sure getConfiguration().default_zpublisher_encoding is set correctly.

- Issue #28: Fix publishing of IStreamIterator. This interface does
  not have seek or tell.
  Introduce IUnboundStreamIterator to support publishing iterators
  of unknown length.


Features Added
++++++++++++++

- Include waitress as a default WSGI app server.

- Add `egg:Zope2#httpexceptions` WSGI middleware.

- Update available HTTP response code, 302 is now called Found.

- Add a new `runwsgi` script to serve PasteDeploy files.

- Depend on and automatically set up `five.globalrequest`.

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

- Always configure a `blob-dir` in the default skeleton.

- ZPublisher: If `IBrowserPage` is provided by a view, form input is decoded.
  This makes it easier to use ``zope.formlib`` and ``z3c.form`` in Zope 2.

- Remove `control panel` object from the ZODB.

- Updated to latest versions of Zope Toolkit libraries.

- Updated distributions:

  - AccessControl = 4.0a1
  - Acquisition = 4.2.2
  - BTrees = 4.0.8
  - DateTime = 4.1.1
  - ExtensionClass = 4.1.2
  - docutils = 0.9.1
  - five.globalrequest = 1.0
  - manuel = 1.6.0
  - Missing = 3.1
  - MultiMapping = 3.0
  - Persistence = 3.0a1
  - Products.BTreeFolder2 = 3.0
  - Products.ExternalMethod = 3.0
  - Products.MailHost = 3.0
  - Products.OFSP = 3.0
  - Products.PythonScripts = 3.0
  - Products.SiteErrorLog = 4.0
  - Products.StandardCacheManagers = 3.0
  - Products.ZCatalog = 4.0a1
  - Products.ZCTextIndex = 3.0
  - Record = 3.1
  - tempstorage = 3.0
  - zExceptions = 3.0
  - zLOG = 3.0
  - zope.globalrequest = 1.2
  - ZopeUndo = 4.1

Restructuring
+++++++++++++

- Remove dependency on initgroups. Use the standard libraries os.initgroups
  instead.

- Removed nt_svcutils support from zopectl.

- Python 2.6 is no longer supported. Use Python 2.7.

- Products.SiteErrorLog: Is now a separated package.

- OFS: Removed duplicate code in ZopeFind and ZopeFindAndApply

- Five: Removed obsolete metaclass.

- Five: Refactored ``browser:view`` and ``browser:page`` directives.
  This makes their implementation more similar to that in ``zope.browserpage``
  and adds allowed_interface support for the ``browser:view`` directive.
  By default the `aq_*` attributes are no longer available on those
  views/pages. If you still use them, you have to mix in Five's BrowserView.

- Removed the (very obsolete) thread lock around the cookie parsing code
  in HTTPRequest.py; the python `re` module is thread-safe, unlike the
  ancient `regex` module that was once used here.

- Removed the special handling of `Set-Cookie` headers in
  `HTTPResponse.setHeader`. Use the `setCookie`/`appendCookie`/`expireCookie`
  methods instead, or if low-level control is needed, use `addHeader` instead
  to get the exact same effect.

- Removed the `App.version_txt.getZopeVersion` API, you can use
  ``pkg_resources.get_distribution('Zope2').version`` instead.

- On the application object, removed `PrincipiaTime` in favor of `ZopeTime` and
  `PrincipiaRedirect` in favor of `Redirect` or `ZopeRedirect`.

- Removed `OFS.DefaultObservable` - an early predecessor of `zope.event`.

- Removed `mime-types` option from `zope.conf`. You can use the `add_files`
  API from `zope.contenttype` instead.

- Removed `OFS.ZDOM`. `OFS.SimpleItem.Item` now implements `getParentNode()`.

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
  hosted at https://zope.readthedocs.io/. For backwards compatibility the
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

- Five.browser: Marked `processInputs` and `setPageEncoding` as deprecated.
  `processInputs` was replaced by the `postProcessInputs` request method and
  the charset negotiation done by `setPageEncoding` was never fully supported.

- Dropped the direct dependencies on packages that have been factored out of
  the main Zope 2 tree. Make sure you declare a dependency in your own
  distribution if you still use one of these:

    ``Products.BTreeFolder2``
    ``Products.ExternalMethod``
    ``Products.MailHost``
    ``Products.MIMETools``
    ``Products.PythonScripts``
    ``Products.SiteErrorLog``
    ``Products.StandardCacheManagers``
    ``Products.ZCatalog``
    ``Record``
