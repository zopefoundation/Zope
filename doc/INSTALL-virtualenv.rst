Installing Zope with ``virtualenv``
===================================

.. highlight:: bash

This document describes how to install Zope into a ``virtualenv``.


Create a Virtual Environment
----------------------------

.. code-block:: sh

   $ /opt/Python-2.7.14/bin/virtualenv z213
   New python executable in z213/bin/python
   Installing setuptools, pip, wheel...done.
   $ cd z213


Install the Zope2 2.13.27 Software Packages
-------------------------------------------

.. code-block:: sh

   $ bin/pip install \
    --no-binary zc.recipe.egg \
    -r https://zopefoundation.github.io/Zope/releases/2.13.27/requirements.txt
   Collecting Zope2
   ...
   Successfully installed ...

Creating a Zope instance
------------------------

Once you've installed Zope, you will need to create an "instance
home". This is a directory that contains configuration and data for a
Zope server process.  The instance home is created using the
``mkzopeinstance`` script:

.. code-block:: sh

  $ bin/mkzopeinstance

You can specify the Python interpreter to use for the instance
explicitly:

.. code-block:: sh

  $ bin/mkzopeinstance --python=bin/python

You will be asked to provide a user name and password for an
administrator's account during ``mkzopeinstance``.  To see the available
command-line options, run the script with the ``--help`` option:

.. code-block:: sh

   $ bin/mkzopeinstance --help

Using the ``virtualenv`` as the Zope Instance
---------------------------------------------

You can choose to use the ``virtualenv`` as your Zope instance:

.. code-block:: sh

   $ bin/mkzopeinstance -d .

In this case, the instance files will be located in the
subdirectories of the ``virtualenv``:

- ``etc/`` will hold the configuration files.
- ``log/`` will hold the log files.
- ``var/`` will hold the database files.
