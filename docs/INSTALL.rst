Installing Zope
===============
This document describes installing Zope with
`zc.buildout <https://pypi.org/project/zc.buildout/>`_
(the **recommended** method) or via ``pip``.


.. note::

    New installations should use Zope 5 instead of Zope 4. Users migrating
    applications from Zope 2 should upgrade to Zope 5 once their application
    supports Zope 4 on Python 3. The Zope developer community strives to make
    sure the next upgrade step to Zope 5 is and remains a quick and painless
    exercise.


.. contents::
   :local:


Prerequisites
-------------
In order to install Zope, you must have the following prerequisites
available:

- A supported version of Python, including the development support if
  installed from system-level packages.  Supported versions include:

  * 2.7
  * 3.5 - 3.8

  .. warning::

     The WSGI server Zope uses by default, waitress, was
     affected by `an important security issue
     <https://github.com/Pylons/waitress/security/advisories/GHSA-4f7p-27jc-3c36>`_.
     The fixed version 2.1.1 is only compatible with Python 3.7 and higher. We
     strongly advise you to either upgrade your Zope 4 installation to at least
     Python 3.7, move to Zope 5 on Python 3.7 or higher, or `switch to a
     different WSGI server
     <https://zope.readthedocs.io/en/latest/operation.html#recommended-wsgi-servers>`_.

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

- Install ``zc.buildout`` into the virtual environment or update it to the
  latest release before proceeding

- Run the buildout

The following examples are from Linux and use Zope version 4.5.1. Just replace
that version number with your desired version.

Built-in standard buildout configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

  $ wget https://pypi.org/packages/source/Z/Zope/Zope-4.5.1.tar.gz
  $ tar xfvz Zope-4.5.1.tar.gz
  $ cd Zope-4.5.1
  $ python3.7 -m venv .
  $ bin/pip install -U pip wheel zc.buildout
  $ bin/buildout

.. note::

  When using Python 2.7 instead of calling ``python3.7 -m venv .`` you have to
  install `virtualenv` and then call ``python2.7 -m virtualenv .``.


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
        https://zopefoundation.github.io/Zope/releases/4.5.1/versions-prod.cfg
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
        https://zopefoundation.github.io/Zope/releases/4.5.1/versions-prod.cfg
    parts =
        zopeinstance

    [zopeinstance]
    recipe = plone.recipe.zope2instance
    eggs =
        Products.TemporaryFolder
    user = admin:adminpassword
    http-address = 8080

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
        Products.TemporaryFolder
        gunicorn
    user = admin:adminpassword
    http-address = 8080
    wsgi = /path/to/zope.ini

On Python 2 you can also forego the use of WSGI and create an old-fashioned
ZServer-based installation by pulling in the ``ZServer`` egg and setting
``wsgi = off`` explicitly:

.. code-block:: ini

    [zopeinstance]
    recipe = plone.recipe.zope2instance
    eggs =
        Products.TemporaryFolder
        ZServer
    user = admin:adminpassword
    http-address = 8080
    wsgi = off


Installing Zope with ``pip``
----------------------------
Installing the Zope software using ``pip`` involves the following
steps:

- Create a virtual environment (There is no need to activate it.)

- Install Zope and its dependencies

Example steps on Linux. Replace the version number "4.5.1" with the latest
version you find on https://zopefoundation.github.io/Zope/:

.. code-block:: console

  $ python3.7 -m venv zope
  $ cd zope
  $ bin/pip install -U pip wheel
  $ bin/pip install Zope[wsgi]==4.5.1 \
    -c https://zopefoundation.github.io/Zope/releases/4.5.1/constraints.txt

.. note::

  When using Python 2.7 instead of calling ``python3.7 -m venv zope`` you have
  to install `virtualenv` and then call ``python2.7 -m virtualenv zope``.

You can also install Zope using a single requirements file. Note that this
installation method might install packages that are not actually needed (i. e.
more than are listed in the ``install_requires`` section of ``setup.py``):

.. code-block:: console

    $ bin/pip install \
    -r https://zopefoundation.github.io/Zope/releases/4.5.1/requirements-full.txt

If you are on Python 2 and want to use ZServer instead of WSGI , you'll have to
install that package seperately using the version spec in constraints.txt

.. code-block:: console

    $ bin/pip install \
    -c https://zopefoundation.github.io/Zope/releases/4.5.1/constraints.txt \
    ZServer

Building the documentation with ``Sphinx``
------------------------------------------
If you have used ``zc.buildout`` for installation, you can build the HTML
documentation locally:

.. code-block:: console

   $ bin/make-docs
