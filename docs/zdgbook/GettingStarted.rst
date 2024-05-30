###############
Getting Started
###############

Introduction
============

This chapter covers the installation of Zope and getting started with
the development of a simple application.  This guide uses a build
system called `Buildout <http://www.buildout.org>`_ to build the
application.

Prerequisites
=============

Make sure you have Python version 3.8 or higher installed.

Creating and activating a `VirtualEnv <https://pypi.org/project/virtualenv/>`_
is recommended.

In order to use buildout, you have to install the ``zc.buildout``
package.

::

  $ pip install zc.buildout

Directory structure
===================

To begin application development, create a directory structure for
the Python packages and build related files.

::

  $ mkdir poll
  $ mkdir poll/poll_build
  $ mkdir poll/poll.main

All build related files will be added inside the ``poll_build``
directory, whereas the main Python package goes into the
``poll.main`` directory.

Installing Zope using zc.buildout
=================================

Zope is distributed in egg format.  To install Zope
and create an instance, create a buildout configuration file
(``poll/poll_build/buildout.cfg``) with following content.

::

  [buildout]
  extends = https://zopefoundation.github.io/Zope/releases/master/versions-prod.cfg
  parts =
      zope4

  [zope4]
  recipe = zc.recipe.egg
  eggs =
      Zope
      Paste

The ``[zope4]`` part uses ``zc.recipe.egg`` which will download
``Zope`` and all its dependencies.  It will create few console
scripts inside the ``bin`` directory.

After updating the buildout configuration, you can run the `buildout`
command to build the system.

::

  $ cd poll/poll_build
  $ buildout

The initial build will take some time to complete.

Creating the instance
=====================

Once the build is complete, you can create an instance as follows.

::

  $ bin/mkwsgiinstance -d .


Running the instance
====================

Once you got a Zope instance, you can run it like this.

::

  $ bin/runwsgi etc/zope.ini

Now, Zope is running. You can convince yourself by visiting the
following URL.

::

  http://localhost:8080

You can also visit the administration area.

Use the user name and password you set earlier.

::

  http://localhost:8080/manage

When you have a look at the drop-down box in the top right corner,
you see a list of objects you may create.

In the next section we will create the poll application. Later, we
will make it installable, too.


Developing the main package
===========================

Now, we can move to the ``poll.main`` directory to create the main
package to develop the application.  We will develop the entire
application inside the ``poll.main`` package.  For bigger projects,
it is recommended to split packages logically and maintain the
dependencies between the packages properly.

::

  $ cd ../poll.main

In order to create an egg distribution, we need to create a
``setup.py`` and a basic directory structure. We are going to place
the Python package inside the ``src`` directory.

::

  $ touch setup.py
  $ mkdir src
  $ mkdir src/poll
  $ mkdir src/poll/main
  $ touch src/poll/__init__.py
  $ touch src/poll/main/__init__.py
  $ touch src/poll/main/configure.zcml

The last file is a configuration file. The ``.zcml`` file extension stands for
``Zope Configuration Markup Language``.

To declare ``poll`` as a namespace package, we need to add following
code to ``src/poll/__init__.py``.

::

  __import__('pkg_resources').declare_namespace(__name__)

Next, we need to add the minimum metadata required for the package
in ``setup.py``.

::

  from setuptools import setup, find_packages

  setup(
      name="poll.main",
      version="0.1",
      packages=find_packages("src"),
      package_dir={"": "src"},
      namespace_packages=["poll"],
      install_requires=["setuptools",
                        "Zope"],
      )

We need to edit two more files to be recognized by Zope.  First,
define the ``initialize`` callback function in ``src/poll/main/__init__.py``.

::

  def initialize(registrar):
      pass

And, in the ZCML file (``src/poll/main/configure.zcml``), add these
few lines.

::

  <configure xmlns="http://namespaces.zope.org/five">

    <registerPackage package="." initialize=".initialize" />

  </configure>

Creating an installable application
===================================

We need three things to make an installable application.

- A form object created as Zope Page Template (manage_addPollMain)
- A function to define the form action (addPollMain)
- A class to define the toplevel application object (PollMain).

Finally, we need to register the class along with the form and add
the function using the ``registrar`` object passed to the
``initialize`` function.

We can define all these things in ``app.py`` and the form template as
``manage_addPollMain_form.zpt``.

::

  $ touch src/poll/main/app.py
  $ touch src/poll/main/manage_addPollMain_form.zpt

Here is the code for ``app.py``...

::

  from OFS.Folder import Folder
  from Products.PageTemplates.PageTemplateFile import PageTemplateFile

  class PollMain(Folder):
      meta_type = "POLL"


  manage_addPollMain = PageTemplateFile("manage_addPollMain_form", globals())


  def addPollMain(context, id):
      """ """
      context._setObject(id, PollMain(id))
      return "POLL Installed: %s" % id

... and for ``manage_addPollMain_form.zpt``:

::

  <h1 tal:replace="structure context/manage_page_header">Header</h1>
  
  <main class="container-fluid">
  
    <h2 tal:define="form_title string:Add POLL"
        tal:replace="structure here/manage_form_title">Form Title</h2>
  
    <form action="addPollMain" method="post">
  
      <div class="form-group row">
        <label for="id" class="form-label col-sm-3 col-md-2">Id</label>
        <div class="col-sm-9 col-md-10">
          <input id="id" name="id" class="form-control" type="text" />
        </div>
      </div>
  
      <div class="form-group row form-optional">
        <label for="title" class="form-label col-sm-3 col-md-2">Title</label>
        <div class="col-sm-9 col-md-10">
          <input id="title" name="title" class="form-control" type="text" />
        </div>
      </div>
  
      <div class="zmi-controls">
        <input class="btn btn-primary" type="submit" name="submit" value="Add" />
      </div>
  
    </form>
  
  </main>
  
  <h1 tal:replace="structure context/manage_page_footer">Footer</h1>

Finally, we can register it within ``src/poll/main/__init__.py``::

  from poll.main.app import PollMain, manage_addPollMain, addPollMain

  def initialize(registrar):
      registrar.registerClass(
          PollMain,
          constructors=(manage_addPollMain, addPollMain)
      )

The application is now ready to install.  But we need to make some
changes in `poll_build`, so it gets installed along Zope.

Updating the build config
=========================

First, in the ``[buildout]`` section of ``buildout.cfg`` we need
to mention that ``poll.main`` is locally developed.  Otherwise,
buildout will try to get the package from package index server, by
default that is https://pypi.org/ .

::

  [buildout]
  develop = ../poll.main
  ...

Also, we need to add ``poll.main`` to the ``eggs`` option in the
``[zope4]`` section.

::

  ...
  eggs =
      Zope
      Paste
      poll.main
  ...

The final `buildout.cfg` will look like this.

::

  [buildout]
  develop = ../poll.main
  extends = https://zopefoundation.github.io/Zope/releases/master/versions-prod.cfg
  parts =
      zope4

  [zope4]
  recipe = zc.recipe.egg
  eggs =
      Zope
      Paste
      poll.main

To make these change effective, run the buildout again.

::

  $ buildout

Finally, we have to include our package within
``poll_build/etc/site.zcml``. Add the following towards the bottom
of that file:

::

  <include package="poll.main" />

Now, we can run application instance again.

::

  $ bin/runwsgi etc/zope.ini

Adding an application instance
==============================

Visit the ZMI ( http://localhost:8080/manage ) and select ``POLL``
from the drop-down box.  It will display the add-form created
earlier.  Enter ``poll`` in the ID field and submit the form. After
submitting, it should display a message:
"POLL Installed: poll".

Adding and index page for the POLL application
==============================================

In this section we will add a main page to the POLL application, so
that we can access the POLL application like this:
http://localhost:8080/poll .

First, create a file named ``index_html.zpt`` inside
``poll.main/src/poll/main``
with content like this::

  <html>
  <head>
    <title>Welcome to POLL!</title>
  </head>
  <body>

  <h2>Welcome to POLL!</h2>

  </body>
  </html>

Now add an attribute named ``index_html`` inside PollMain class like
this::

  class PollMain(Folder):
      meta_type = "POLL"

      index_html = PageTemplateFile("index_html", globals())

After restarting Zope, you can see that it displays the main page
when you access: http://localhost:8080/poll .

Summary
=======

This chapter covered the installation of Zope and the beginning of
the development of a simple project in Zope.
