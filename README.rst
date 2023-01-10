.. image:: https://github.com/zopefoundation/Zope/actions/workflows/tests.yml/badge.svg?branch=4.x
        :target: https://github.com/zopefoundation/Zope/actions/workflows/tests.yml

.. image:: https://coveralls.io/repos/github/zopefoundation/Zope/badge.svg?branch=4.x
        :target: https://coveralls.io/github/zopefoundation/Zope?branch=master

.. image:: https://readthedocs.org/projects/zope/badge/?version=4.x
        :target: https://zope.readthedocs.org/en/4.x/
        :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/Zope.svg
        :target: https://pypi.org/project/Zope/
        :alt: Current version on PyPI

.. image:: https://img.shields.io/pypi/pyversions/Zope/4.5.5
        :target: https://pypi.org/project/Zope/
        :alt: Supported Python versions

.. image:: https://requires.io/github/zopefoundation/Zope/requirements.svg?branch=4.x
        :target: https://requires.io/github/zopefoundation/Zope/requirements/?branch=4.x
        :alt: Requirements Status

.. |nbsp| unicode:: 0xA0 
        :trim:

|nbsp|

.. image:: https://zopefoundation.github.io/Zope/artwork/Zope.svg
        :alt: Zope logo
        :width: 300px

**Zope is an open-source web application server.**

This document provides some general information about Zope and provides
links to other documents. The full documentation can be found at
https://zope.readthedocs.io.


.. contents::
    :local:
    :depth: 1


Zope 4 - the bridge between Zope 2 and Zope 5
=============================================

**Zope 4 has reached End Of Life status on 12/31/2022. All support has ended.
Please upgrade to Zope 5 as soon as possible.** The `Zope release
schedule <https://www.zope.dev/releases.html>`_ has details about support
policies and timeframes.

Zope 4 supports Python 2 and Python 3. It is meant to act as a bridge for those
upgrading applications from Zope 2. Once you are on Zope 4 and Python 3 the
next step to Zope 5 is painless and we recommend upgrading to Zope 5
immediately.


Installation
============

**Security warning:** The WSGI server Zope uses by default, waitress, was
affected by `an important security issue
<https://github.com/Pylons/waitress/security/advisories/GHSA-4f7p-27jc-3c36>`_.
Fixes were only released for Python 3.7 and higher. Therefore we strongly urge
you to either upgrade your Zope 4 installation to Python
3.7 or 3.8 or `switch to a different
WSGI server
<https://zope.readthedocs.io/en/latest/operation.html#recommended-wsgi-servers>`_.
**If you are running Zope 4 on Python 3 we recommend you upgrade to Zope 5.**

Please visit the installation documentation at
https://zope.readthedocs.io/en/4.x/INSTALL.html for detailed installation
guidance.


License
=======

Zope is licensed under the OSI-approved `Zope Public License` (ZPL), version
2.1. The full license text is included in ``LICENSE.txt``.

Bug tracker
===========

Bugs reports should be made through the Zope bugtracker at
https://github.com/zopefoundation/Zope/issues.  A bug report should
contain detailed information about how to reproduce the bug.
