Installing Zope
===============

.. highlight:: bash

This document descibes how to get going with Zope.


Prerequisites
-------------

In order to use Zope, you must have the following pre-requisites
available: 

- A supported version of Python, including the development support if
  installed from system-level packages.  Supported versions include:

  * 2.6.x
  * 2.7.x

- Zope needs the Python ``zlib`` module to be importable.  If you are
  building your own Python from source, please be sure that you have the
  headers installed which correspond to your system's ``zlib``.

- A C compiler capable of building extension modules for your Python
  (gcc recommended). This is not necessary for Windows as binary
  releases of the parts that would need compiling are always made
  available.

- If you wish to install Zope as a Service on Windows, you will need
  to have the `pywin32`__ package installed.

  __ https://sourceforge.net/projects/pywin32/


Installing Zope
---------------

The recommended way to install Zope is within a virtualized Python environment
using ``virtualenv`` as follows::

  $ virtualenv --no-site-packages my_zope
  $ cd my_zope
  $ bin/easy_install -i http://download.zope.org/Zope2/index/<Zope version> Zope2

If you don't already have ``virtualenv`` installed on your system, download
the latest release from the `virtualenv PyPI page
<http://pypi.python.org/pypi/virtualenv>`_, unpack it, and install it, e.g.::

  $ wget http://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.4.6.tar.gz
  $ tar xzf virtualenv-1.4.6.tar.gz
  $ cd virtuaenv-1.4.6
  $ /path/to/python2.7 setup.py install

If you wish to manage your Zope instance using
buildout, please see the :doc:`INSTALL-buildout`.


Creating a Zope Instance
------------------------

Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkzopeinstance`` script::

  $ bin/mkzopeinstance

You will be asked to provide a user name and password for an
administrator's account during ``mkzopeinstance``.  To see the available
command-line options, run the script with the ``--help`` option::

  $ bin/mkzopeinstance --help

.. note::
  The traditional "inplace" build is no longer supported.  Always use
  ``mkzopeinstance`` to create instances outside the virtualenv environment.

