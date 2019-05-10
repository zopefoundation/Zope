.. _zope4zodbmigration:

Migrating the ZODB
==================

This document describes the process of migrating a ZODB created with Zope 2
into a Zope 4 environment.

.. warning::
   As soon as you open a ZODB from Zope 2 under Zope 4 you cannot use it under
   Zope 2 anymore, regardless of how the ZODB is opened (direct access to a
   ``Data.fs`` file or indirect access through a ``ZEO`` server). Always work
   on a copy of your ZODB so you retain a working copy for Zope 2 if you need
   to go back.

.. contents::
   :local:


Python 2

    There are no specific ZODB-related migration steps to take when moving to a
    Python 2-based Zope 4 environment, but the warning shown above still applies.

Python 3

    Due to a string/bytes/unicode incompatibilities, additional steps are needed.


Migrating the ZODB from Python 2 to 3
-------------------------------------

.. highlight:: python

This part describes the process of migrating a ZODB created
with Python 2 (using Zope 2 or 4) to Python 3 (using Zope 4).
As there are significant changes between the two platforms,
there is no automated process to cover all edge cases, so it is
necessary to prepare and test your migration well in advance.


The string problem
~~~~~~~~~~~~~~~~~~

A ZODB ``Data.fs`` which was created under Python 2 cannot be
opened under Python 3. This is prevented by using a different
magic code in the first bytes of the file. This is done on
purpose because ``str`` has a different meaning for the two
Python versions: Under Python 2, a ``str`` is a container for
characters with an arbitrary encoding (aka ``bytes​``). Python 3
knows ``str`` as a text datatype which was called ``unicode``
in Python 2.

Trying to load a ``str`` object in Python 3
which actually contains binary data will fail. It has to be
bytes, but ``bytes`` is an alias for ``str`` in Python 2.
This means Python 2 replaces ``bytes`` with ``str``, making it
impossible to give Python 3 the class it expects for binary data.
A Python 2 ``str`` with any non-ascii characters will break, too.

For more details, read the `Saltlab-Sprint notes from Harald Frisnegger <https://github.com/frisi/coredev52multipy/blob/3e440d6bd918adba3e6f2557f7281ce448a9c3cc/README.rst>`_


The string solution
~~~~~~~~~~~~~~~~~~~

The ``Data.fs`` has to be migrated: each ``str`` which actually
contains ``bytes`` has to be converted into a ``zodbpickle.binary``
object which deserialises as ``bytes`` under Python 3. The ``str`` objects
actually containing text have to be decoded to ``str`` (known as ``unicode``
in Python 2).


The code problem
~~~~~~~~~~~~~~~~

Python 3 is not backwards-compatible to Python 2 in terms of its syntax,
which is a problem for ``Persistent`` objects in the ZODB containing
Python code. This is problem might arise with ``PythonScript`` objects,
and ``TAL`` or ``DTML`` templates that contain Python statements or
expressions.


The code solution
~~~~~~~~~~~~~~~~~

There are several tools that help with getting your code ready for Python 3,
especially in large code bases:

* `2to3 <https://docs.python.org/2/library/2to3.html>`__ comes with modern
  Python distributions preinstalled and can be used to convert either
  extracted code in files or directly on the ZODB through a custom script.
* `gocept.template_rewrite <https://github.com/gocept/gocept.template_rewrite>`__
  can extract and rewrite code parts of template files (DTML, ZPT).
* `zodbsync <https://github.com/perfact/zodbsync>`__ is a tool to serialize
  ZODB objects and store them in a file system tree and restore ZODB them
  from the same structure.

The migration path heavily depends on your specific use case and can
range from manually finding, inspecting and fixing code objects to
setting up a large, auditable and automated process. The tooling referenced
above even allows users to extract code to a file system, convert it and
restoring it back to the ZODB while keeping changes under version control.


Migration example
~~~~~~~~~~~~~~~~~

- Backup your `Data.fs` before proceeding.

- Make all ZODB-persisted code Python 3 compatible (see above), while
  keeping Python 2 compatibility.

- Test that converted code works as expected

- Prepare a Python 3 environment, containing:

  - Zope 4 (latest),
  - all relevant applications and addons for your ZODB,
  - `zodbupdate <https://pypi.org/project/zodbupdate/>`_,
  - `zodbverify <https://pypi.org/project/zodbverify/>`_,

- Prepare a Zope configuration

  - Create a new Zope instance using ``mkwsgiinstance``

  - Update configuration in ``zope.ini`` and ``zope.conf`` to match
    previous Zope2 instance configuration.

- Migrate the database:

  - Make sure no zope instance is running.

  - Dry-run the migration with
    ``zodbupdate --pack --convert-py3 --dry-run path/to/Data.fs``.
    This may take a while.

  - If no errors are shown, start the in-place migration of the ZODB
    ``zodbupdate --pack --convert-py3 path/to/Data.fs``.
    This may take a while.

- Check the migrated database:

  - Verify th ZODB by iterative loading every pickle using
    ``zodbverify --zodbfile path/to/Data.fs``.

  - Start the Application using ``runwsgi etc/zope.ini``.
    ``Data.fs.index`` will be discarded at the first start, you can ignore
    the error message telling that it cannot be read.

  - Verify that the Application works as expected.

  - If there are problems with one of the ZCatalogs in the ZODB, do a clear and rebuild.

In case of ``UnicodeDecodeError``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If ``zodbupdate`` or the Application raises a ``UnicodeDecodeError`` after
the start, there are several things to consider:

If the error happens on an object of a Product that is not migrated
yet, you can add an ``entry_point`` in ``setup.py`` for the package
containing the persistent Python classes. The entry point has to be
named ``"zodbupdate.decode"`` and needs to point to a dictionary
mapping paths to ``str`` attributes to a conversion (``binary`` resp.
a specific encoding).
For details, see
`zodbupdate documentation and <https://github.com/zopefoundation/zodbupdate/blob/master/README.rst>`__
or `a code example in PythonScripts <https://github.com/zopefoundation/Products.PythonScripts/pull/19/files>`__.


Further reading
~~~~~~~~~~~~~~~

The Plone project documentation contains a section `Migrate a ZODB from Python 2.7 to Python 3 <https://github.com/plone/documentation/blob/5.2/manage/upgrading/version_specific_migration/upgrade_zodb_to_python3.rst>`_
