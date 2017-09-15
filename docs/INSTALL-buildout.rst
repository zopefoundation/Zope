Installing Zope with ``zc.buildout``
====================================

.. highlight:: bash

This document describes how to get going with Zope using ``zc.buildout``.


About ``zc.buildout``
---------------------

`zc.buildout <https://pypi.python.org/pypi/zc.buildout>`_ is a powerful
tool for creating repeatable builds of a given software configuration
and environment.  The Zope developers use ``zc.buildout`` to develop
Zope itself, as well as the underlying packages it uses.

Prerequisites
-------------

In order to use Zope, you must have the following pre-requisites
available:

- A supported version of Python, including the development support if
  installed from system-level packages.  Supported versions include:

  * 2.7
  * 3.4
  * 3.5
  * 3.6

- Zope needs the Python ``zlib`` module to be importable.  If you are
  building your own Python from source, please be sure that you have the
  headers installed which correspond to your system's ``zlib``.

- A C compiler capable of building extension modules for your Python
  (gcc recommended).


Installing Zope using zc.buildout
---------------------------------

In this configuration, we use ``zc.buildout`` to install the Zope software,
and then generate a server "instance" inside the buildout environment.

Installing the Zope software
::::::::::::::::::::::::::::

Installing the Zope software using ``zc.buildout`` involves the following
steps:

- Download the Zope source distribution from `PyPI`__

  __ https://pypi.python.org/pypi/Zope

- Bootstrap the buildout

- Run the buildout

On Linux, this can be done as follows::

  $ wget https://pypi.python.org/packages/source/Z/Zope/Zope-<Zope version>.tar.gz
  $ tar xfvz Zope-<Zope version>.tar.gz
  $ cd Zope-<Zope version>
  $ /path/to/your/python bootstrap.py
  $ bin/buildout


Creating a Zope instance
::::::::::::::::::::::::

Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkwsgiinstance`` script::

  $ bin/mkwsgiinstance -d .

You will be asked to provide a user name and password for an
administrator's account during ``mkwsgiinstance``.  To see the available
command-line options, run the script with the ``--help`` option::

  $ bin/mkwsgiinstance --help

After installation, refer to :doc:`operation` for documentation on
configuring and running Zope.


Building the documentation with ``Sphinx``
------------------------------------------

To build the HTML documentation, run the :command:`make-docs` script (installed
by the buildout)::

   $ bin/make-docs
