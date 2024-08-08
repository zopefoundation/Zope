.. _zope4zodbmigration:

Migrating the ZODB
==================

This document describes the process of migrating a ZODB created with Zope 2
into a Zope 4 environment. The migration example steps have been tested on a
``FileStorage``-based ZODB with a ``Data.fs`` file.

.. warning::
   As soon as you open a ZODB from Zope 2 under Zope 4 you cannot use it under
   Zope 2 anymore, regardless of how the ZODB is opened (direct access to a
   ``Data.fs`` file or indirect access through a ``ZEO`` server). Always work
   on a copy of your ZODB so you retain a working copy for Zope 2 if you need
   to go back.


Pre-migration steps on Zope 2
-----------------------------

The following pre-migration steps can be done while still on Zope 2 and will
ease the final process.


Prepare ZODB-based code
~~~~~~~~~~~~~~~~~~~~~~~

Syntax changes that come with the move from Python 2 to Python 3 for filesystem
code apply to ZODB code as well, such as Python Scripts, DTML Methods, DTML
Documents, Z SQL Methods and Page Templates. Typical issues include:

- switching ``print`` statements to ``print`` function call syntax
- switching removed ``string`` module function calls to their string method
  equivalents
- safe handling of changed return value types for dictionary methods, such as
  ``keys``, ``values`` or ``items``
- fix indentation where a mix of spaces and tabs is used
- etc.

Many of these and others will be familiar from changing filesystem code to be
Python 3 compatible. 


Delete ZODB objects that no longer exist under Zope 4
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``Control_Panel`` has seen changes in Zope 4 that have a risk of
introducing spurious errors when verifying the ZODB contents in the steps
below. Visit the ZMI **while still running on Zope 2** and delete all objects
you see in the Products folder at ``/Control_Panel/Products/manage_main``. Pack
the ZODB after the cleanup.


Migrate to Zope 4 on Python 2
-----------------------------

There are no specific ZODB-related migration steps to take when moving to a
Python 2-based Zope 4 environment, except when you're proceeding with a Python
3 migration. See the section `Going from Zope 2 to Zope 4` below for
details.


Migrate to Zope 4 on Python 3
-----------------------------

.. highlight:: python

This part describes the process of migrating a ZODB created
with Python 2 (using Zope 2 or 4) to Python 3 (using Zope 4).
As there are significant changes between the two platforms,
there is no automated process to cover all edge cases, so it is
necessary to prepare and test your migration well in advance.


Migration example
~~~~~~~~~~~~~~~~~

- **Back up your ZODB before proceeding**

- Make all ZODB-persisted code Python 3 compatible (see above), while
  keeping Python 2 compatibility.

- Test that converted code works as expected


Going from Zope 2 to Zope 4
+++++++++++++++++++++++++++

If your ZODB was created under Zope 2 you have a few additional steps that will
ensure the latest ZODB code under Python 3 will work with your ZODB data. Make
sure your ZODB is packed before going on.

- prepare a Python 2 environment containing...

  - Zope 4 (latest)
  - all relevant applications and addons for your ZODB
  - `zodbverify <https://pypi.org/project/zodbverify/>`_

- prepare a Zope configuration

  - Create a new Zope instance using ``mkwsgiinstance`` or a
    ``plone.recipe.zope2instance`` buildout configuration

  - make sure the created configuration files (under ``etc/`` if you used
    ``mkwsgiinstance`` and under ``parts/<INSTANCE_NAME>/etc`` if you used
    ``plone.recipe.zope2instance``) reflect what was in your Zope 2
    configuration before the migration
    
  - start the Application using ``bin/runwsgi etc/zope.ini`` or
    ``bin/<INSTANCE_NAME>``, depending on the mechanism you used to create the
    instance configuration. Test it intensively for incompatibilities and errors.

- shut down the Zope instance(s) and ZEO server that serves your ZODB

- run ``bin/zodbverify -f path/to/Data.fs`` to uncover any errors in your ZODB.
  You may see cryptic errors pointing to the ``Products`` attribute of the
  ``Control_Panel``, this is not critical. All others need to be fixed.

Now you have a ZODB that is ready to be opened under Python 3 for the remaining
steps.
  

Going from Python 2 to Python 3
+++++++++++++++++++++++++++++++

- Prepare a Python 3 environment, containing:

  - Zope 4 (latest),
  - all relevant applications and addons for your ZODB, (make sure they are
    compatible with Python 3)
  - `zodbupdate <https://pypi.org/project/zodbupdate/>`_
  - `zodbverify <https://pypi.org/project/zodbverify/>`_

- Prepare a Zope configuration

  - Create a new Zope instance using ``mkwsgiinstance`` or a
    ``plone.recipe.zope2instance`` buildout configuration

  - make sure the created configuration files (under ``etc/`` if you used
    ``mkwsgiinstance`` and under ``parts/<INSTANCE_NAME>/etc`` if you used
    ``plone.recipe.zope2instance``) reflect what was in your Zope 2
    configuration before the migration

- make sure the Zope instance(s) and ZEO server that serves your ZODB are shut
  down

- to prevent any compatibility issues with the ZODB index files created under
  Python 2, remove ``Data.fs.index`` before proceeding.

- run the ZODB conversion. Please note that you cannot use ``-n`` to use the
  nondestructive ``--dry-run`` mode at this moment, but the actual conversion
  works:
  ``bin/zodbupdate --pack -f var/filestorage/Data.fs --convert-py3 --encoding utf-8 --encoding-fallback latin1``

- Verify the ZODB by iterative loading every pickle using
  ``bin/zodbverify -f path/to/Data.fs``

- Start the Application using ``bin/runwsgi etc/zope.ini`` or
  ``bin/<INSTANCE_NAME>``, depending on the mechanism you used to create the
  instance configuration.

- Verify that the Application works as expected.

- If your application uses the ZCatalog and there are problems with any of
  them, do a clear and rebuild.


Finding broken scripts and templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can find most scripts and templates that no longer compile under Python 3
by visiting the ZMI edit tabs, where you will see error messages for e.g.
syntax errors. Page Templates that have Python expressions embedded can only
be diagnosed at run time with manual site testing.

The ZMI edit tab method can be scripted as well by emulating what happens
behind the scenes. You can write a script that uses e.g. ``ZopeFind`` to find
objects of those script-like types and then calling the methods that attempt to
compile the script content, such as...

- ``pt_macros()`` for Page Templates, which will store errors in an attribute
  ``_v_errors`` that you can read out
- ``_compile()`` on Python Scripts that will store errors in an attribute
  ``errors`` that you can read out, or the call will directly raise a
  ``SyntaxError``
- ``template.cook()`` for Z SQL Methods, which will raise an exception of type
  ``DocumentTemplate.DT_Util.ParseError`` if there are problems
- ``cook()`` for DTML Methods and DTML Documents, which will raise an exception
  of type ``DocumentTemplate.DT_Util.ParseError`` if there are problems


If you encounter ``UnicodeDecodeError`` exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If ``zodbupdate`` or the Application raises a ``UnicodeDecodeError`` after
startup, there are several things to consider:

If the error happens on an object of a Product that is not migrated
yet, you can add an ``entry_point`` in ``setup.py`` for the package
containing the persistent Python classes. The entry point has to be
named ``"zodbupdate.decode"`` and needs to point to a dictionary
mapping paths to ``str`` attributes to a conversion (``binary`` resp.
a specific encoding).
For details, see
`zodbupdate documentation and <https://github.com/zopefoundation/zodbupdate/blob/master/README.rst>`__
or `a code example in PythonScripts <https://github.com/zopefoundation/Products.PythonScripts/pull/19/files>`__.



Under the hood: Changes in ZODB storage on Python 3
---------------------------------------------------

This section provides deeper technical detail about how the move to Python 3
affects the ZODB.

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


Further reading
~~~~~~~~~~~~~~~

The Plone project documentation contains a section `Migrate a ZODB from Python 2.7 to Python 3 <https://github.com/plone/documentation/blob/5.2/manage/upgrading/version_specific_migration/upgrade_zodb_to_python3.rst>`_
