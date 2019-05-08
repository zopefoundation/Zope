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


Migrating to Zope 4 under Python 2
----------------------------------
There are no specific ZODB-related migration steps to take when moving to a
Python 2-based Zope 4 environment, but the warning shown above still applies.


Migrating to Zope 4 under Python 3
----------------------------------

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
in Python 2. Trying to load a ``str`` object in Python 3
which actually contains binary data will fail. It has to be
bytes, but ``bytes`` is an alias for ``str`` in Python 2.
This means Python 2 replaces ``bytes`` with ``str``, making it
impossible to give Python 3 the class it expects for binary data.
A Python 2 ``str`` with any non-ascii characters will break, too.


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

- Prepare a Python 2 environment containing Zope 4 (latest), all relevant
  applications for your ZODB as well as ``zodbupdate`` and ``zodb.py3migrate``

  - Create a new Zope instance using ``mkwsgiinstance``

  - Update configuration in ``zopewsgi.ini`` and ``zope.conf`` to match
    previous Zope2 instance configuration.

  - Run ``zodb-py3migrate-analyze Data.fs`` to determine if third party
    products have serialized objects into the ZODB that would cause decoding
    errors in Python 3.
    Note: This functionality might be rolled into zodbupdate, see https://github.com/zopefoundation/zodbupdate/issues/10.

  - Run ``zodbupdate --pack --convert-py3 --file Data.fs`` to migrate the ZODB.

- Prepare a Python 3 environment with Zope 4 (latest) and all relevant
  applications.

  - Start the Application using ``runwsgi etc/zopewsgi.ini``.
  
  - ``Data.fs.index`` will be discarded at the first start, you can ignore
    the error message telling that it cannot be read.

  - Delete and recreate all ZCatalog/Index objects.

  - Verify that the Application works as expected.

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

This guide is adapted from several sources that contain further information
and examples.

* https://blog.gocept.com/2018/06/07/migrate-a-zope-zodb-data-fs-to-python-3/
* https://github.com/frisi/coredev52multipy/tree/zodbupdate
* https://github.com/plone/Products.CMFPlone/issues/2525
* https://github.com/plone/documentation/pull/1022
* https://github.com/zopefoundation/Zope/pull/285
