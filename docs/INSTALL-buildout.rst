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
  * 3.5
  * 3.6
  * 3.7

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

  __ https://pypi.org/project/Zope/

- Bootstrap the buildout

- Run the buildout

You may need to replace the used Zope version used in the examples (4.0b6) with
 he one you actually want to install.

On Linux, this can be done as follows::

  $ wget https://pypi.python.org/packages/source/Z/Zope/Zope-4.0b6.tar.gz
  $ tar xfvz Zope-<Zope version>.tar.gz
  $ cd Zope-<Zope version>
  $ python3.7 -m venv .
  $ bin/pip install -U pip zc.buildout
  $ bin/buildout

.. note::

  When using Python 2.7 instead of calling ``python3.7 -m venv .`` you have to
  install `virtualenv` and then call ``virtualenv-2.7 .``.

Instead of using the buildout configuration shipping with Zope itself, you
can also start with a minimum configuration like this::

    [buildout]
    extends =
        https://zopefoundation.github.io/Zope/releases/4.0b6/versions-prod.cfg
    parts =
        zopescripts
    
    [zopescripts]
    recipe = zc.recipe.egg
    interpreter = zopepy
    eggs =
        Zope

Creating a Zope instance
::::::::::::::::::::::::

.. attention::

  The following steps describe how to install a WSGI based Zope instance.
  If you want/have to use ZServer instead of WSGI (Python 2 only!) follow
  the documentation `Creating a Zope instance for Zope 2.13`_, as it has not
  changed since that version.

.. _`Creating a Zope instance for Zope 2.13` : http://zope.readthedocs.io/en/2.13/INSTALL-buildout.html#creating-a-zope-instance

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
