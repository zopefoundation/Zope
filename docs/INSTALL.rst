Installing Zope
===============
This document describes installing Zope with
`zc.buildout <https://pypi.org/project/zc.buildout/>`_
(the **recommended** method) or via ``pip``.

.. contents::
   :local:


Prerequisites
-------------
In order to install Zope, you must have the following prerequisites
available:

- A supported version of Python, including the development support if
  installed from system-level packages.  Supported versions include
  **3.7** up to **3.11**.

- Zope needs the Python ``zlib`` module to be importable.  If you are
  building your own Python from source, please be sure that you have the
  headers installed which correspond to your system's ``zlib``.

- A C compiler capable of building extension modules for your Python
  (gcc recommended).

- If you are using a Python interpreter shipping with your Linux distribution,
  you need to install the matching Python development package. As example, for
  Python 3 on Ubuntu 18.04, you have to type the following:

  .. code-block:: console

    $ sudo apt-get install python3-dev


Installing Zope with ``zc.buildout``
------------------------------------
`zc.buildout <https://pypi.org/project/zc.buildout/>`_ is a powerful
tool for creating repeatable builds of a given software configuration
and environment.  The Zope developers use ``zc.buildout`` to develop
Zope itself, as well as the underlying packages it uses. **This is the
recommended way of installing Zope**.

Installing the Zope software using ``zc.buildout`` involves the following
steps:

- Download and uncompress the Zope source distribution from `PyPI`__ if you
  are using the built-in standard buildout configuration

  __ https://pypi.org/project/Zope/

- Create a virtual environment

- Install ``zc.buildout`` into the virtual environment

- Run the buildout

The following examples are from Linux and use Zope version 5.0. Just replace
that version number with your desired version.

Built-in standard buildout configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    The standard buildout configuration is designed to create scripts needed
    for developing and testing Zope, it is not for production use. Please use
    a custom buildout configuration, a minimal example is shown below.

.. code-block:: console

  $ wget https://pypi.org/packages/source/Z/Zope/Zope-5.0.tar.gz
  $ tar xfvz Zope-5.0.tar.gz
  $ cd Zope-5.0
  $ python3.7 -m venv .
  $ bin/pip install -U pip wheel zc.buildout
  $ bin/buildout


Custom buildout configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Instead of using the buildout configuration shipping with Zope itself, you
can also start with your own buildout configuration file.

The installation with a custom buildout configuration does not require you
to download Zope first:

.. code-block:: console

   $ python3.7 -m venv zope
   $ cd zope
   <create buildout.cfg in this folder>
   $ bin/pip install -U pip wheel zc.buildout
   $ bin/buildout


Minimum configuration
+++++++++++++++++++++
Here's a minimum ``buildout.cfg`` configuration  example:

.. code-block:: ini

    [buildout]
    extends =
        https://zopefoundation.github.io/Zope/releases/5.0/versions-prod.cfg
    parts =
        zopescripts

    [zopescripts]
    recipe = zc.recipe.egg
    interpreter = zopepy
    eggs =
        Zope
        Paste

Using ``plone.recipe.zope2instance``
++++++++++++++++++++++++++++++++++++
To make your life a lot easier, you can use ``plone.recipe.zope2instance``
to automate a lot of the configuration tasks from the following document,
:doc:`operation`. ``plone.recipe.zope2instance`` has a myriad configuration
options, please see the
`PyPI page <https://pypi.org/project/plone.recipe.zope2instance/>`_.

.. code-block:: ini

    [buildout]
    extends =
        https://zopefoundation.github.io/Zope/releases/5.0/versions-prod.cfg
    parts =
        zopeinstance

    [zopeinstance]
    recipe = plone.recipe.zope2instance
    eggs =
    user = admin:adminpassword
    http-address = 8080
    zodb-temporary-storage = off

One feature this kind of installation offers is the easy integration of WSGI
servers other than the built-in ``waitress``. You can specify a file path to a
WSGI configuration file to use when starting the Zope instance. This works for
WSGI servers that offer a PasteDeply-compatible entry point, like ``gunicorn``.
You will need to create the ``.ini`` file yourself, and don't forget to
include the WSGI server software egg in the ``eggs`` specification:

.. code-block:: ini

    [zopeinstance]
    recipe = plone.recipe.zope2instance
    eggs =
        gunicorn
    user = admin:adminpassword
    http-address = 8080
    zodb-temporary-storage = off
    wsgi = /path/to/zope.ini

Installing Zope with ``pip``
----------------------------
Installing the Zope software using ``pip`` involves the following
steps:

- Create a virtual environment (There is no need to activate it.)

- Install Zope and its dependencies

Example steps on Linux. Replace the version number "5.0" with the latest
version you find on https://zopefoundation.github.io/Zope/:

.. code-block:: console

  $ python3.7 -m venv zope
  $ cd zope
  $ bin/pip install -U pip wheel
  $ bin/pip install Zope[wsgi]==5.0 \
    -c https://zopefoundation.github.io/Zope/releases/5.0/constraints.txt

You can also install Zope using a single requirements file. **Note that this
installation method might install packages that are not actually needed** (i. e.
more than are listed in the ``install_requires`` section of ``setup.py``):

.. code-block:: console

    $ bin/pip install \
    -r https://zopefoundation.github.io/Zope/releases/5.0/requirements-full.txt


Building the documentation with ``Sphinx``
------------------------------------------
If you have used ``zc.buildout`` for installation, you can build the HTML
documentation locally:

.. code-block:: console

   $ bin/make-docs
