Change log
==========

This file contains change information for the current Zope release.
Change information for previous versions of Zope can be found at
https://github.com/zopefoundation/Zope/blob/4.x/CHANGES.rst


5.0a1 (unreleased)
------------------

Backwards incompatible changes
++++++++++++++++++++++++++++++

- Drop support for Python 2.7 aka Zope 5 cannot be run on Python 2 any more.
  If you are still running on Python 2.7 upgrade to the latest Zope 4 version
  first, migrate to Python 3 and than switch to Zope 5.


Features
++++++++

- Resurrect History ZMI tab and functionality

Other changes
+++++++++++++

- Update to current releases of the dependencies.

- Removed commented out configuration for tempstorage (and server side
  sessions) as that was known not working for ages. This was removed so we do
  not lead unsuspecting developers to think that this is the right way to do
  session data. See
  (`#679 <https://github.com/zopefoundation/Zope/issues/679>`_)
  (`tempstorage#8 <https://github.com/zopefoundation/tempstorage/issues/8>`_)
  (`tempstorage#12 <https://github.com/zopefoundation/tempstorage/issues/12>`_)
