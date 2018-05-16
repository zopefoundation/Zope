Installing Zope in a ``virtualenv``
===================================

.. highlight:: bash

This document describes how to install Zope into a ``virtualenv`` using ``pip``.


Create a Virtual Environment
----------------------------

.. code-block:: sh

   $ python3.6 -m venv zope
   $ cd zope

If you are still using Python 2.7 install `virtualenv` onto your system then call:

.. code-block:: sh

   $ virtualenv --python=python2.7 zope
   New python executable in zope/bin/python2.7
   Installing setuptools, pip, wheel...done.
   $ cd zope


Install the Zope Software Packages
----------------------------------

Look for the release you want to install on
https://zopefoundation.github.io/Zope/. Than use the specific
version of ``requirements-full.txt`` in the URL, replacing 4.0b4 in the example below:

.. code-block:: sh

   $ bin/pip install \
   -r https://zopefoundation.github.io/Zope/releases/4.0b4/requirements-full.txt
   Obtaining Zope
   ...
   Successfully installed ...


Creating a Zope instance
------------------------

.. attention::

  The following steps describe how to install a WSGI based Zope instance.
  If you want/have to use ZServer instead of WSGI (Python 2 only!) follow
  the documentation `Creating a Zope instance for Zope 2.13`_, as it has not
  changed since that version.

.. _`Creating a Zope instance for Zope 2.13` : http://zope.readthedocs.io/en/2.13/INSTALL-virtualenv.html#creating-a-zope-instance


Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkwsgiinstance`` script:

.. code-block:: sh

  $ bin/mkwsgiinstance -d .

You will be asked to provide a user name and password for an
administrator's account during ``mkwsgiinstance``.  To see the available
command-line options, run the script with the ``--help`` option:

.. code-block:: sh

   $ bin/mkwsgiinstance --help

The `-d .` specifies the directory to create the instance home in.
If you follow the example and choose the current directory, you'll
find the instances files in the subdirectories of the ``virtualenv``:

- ``etc/`` will hold the configuration files.
- ``var/`` will hold the database files.
