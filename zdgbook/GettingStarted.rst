###############
Getting Started
###############

Introduction
============

This chapter cover installation and getting started with development
of a simple application.  This guide use a build system called
`Buildout <http://www.buildout.org>`_ to build the application.  And
the Python packages developed as part of the application can be
distributed as `Python eggs
<http://peak.telecommunity.com/DevCenter/setuptools>`_.


Directory Structure
===================

To begin the application development, create a directory structure to
place Python packages and build related files.

::

  $ mkdir poll
  $ mkdir poll/poll_build
  $ mkdir poll/poll.main

All build related files can be added inside `poll_build` directory.
The main Python package can be added inside `poll.main` directory.
We can make the ``poll``, a namespace package using the functionality
provided by `pkg_resources` module included in setuptools.

Bootstrapping the Build
=======================

You should have Python 2.6 or 2.7 installed in your system.  To start
the build process, download and run `bootstrap.py`.  The
`bootstrap.py` will download and install `setuptools` and
`zc.buildout` packages.  Also it will create the directory structure
and `buildout` script inside `bin` directory.

::

  $ cd poll/poll_build
  $ touch buildout.cfg
  $ wget -c http://svn.zope.org/repos/main/zc.buildout/trunk/bootstrap/bootstrap.py
  $ python2.6 bootstrap.py

Installing Zope 2
=================

Zope 2 is distributed in egg format.  To install Zope 2 egg
and create an instance, update buildout configuration file
(``buildout.cfg``) with appropriate parts and recipes.

::

  [buildout]
  parts = zope2
          instance
  extends = http://download.zope.org/Zope2/index/2.13.20/versions.cfg

  [zope2]
  recipe = zc.recipe.egg
  eggs = Zope2
  interpreter = zopepy

  [instance]
  recipe = plone.recipe.zope2instance
  user = admin:admin
  http-address = 8080
  eggs = ${zope2:eggs}

The ``[zope2]`` part use `zc.recipe.egg` which will download `Zope2`
egg and all its dependencies.  It will create few console scripts
inside `bin` directory.  Also it will create a custom Python
interpreter named ``zopepy``.

The ``[instance]`` part creates a Zope 2 application instance to
develop application.  It will create a script named ``instance``
inside `bin` directory.  We can use that script to run the
application instance.

After updating the buildout configuration, you can run the `buildout`
command to build the system.

::

  $ ./bin/buildout

The initial build will take some time to complete.

Running Instance
================

Once build is completed, you can run Zope 2 instance like this.

::

  $ ./bin/instance fg


You can see that Zope is running in 8080 port.  You can go to the
Zope Management Interface (ZMI).

::

  http://localhost:8080/manage

You can provide the user name & password provided in `[instance]`
part to access this page.

You can see a list of installable applications in the drop-down box.
Also you can see it in "Control_Panel" -> "Products".

::

  http://localhost:8080/Control_Panel/Products/manage_main

In the next section we will make the `poll.main` listed here.  And
later we will make it installable.


Developing the main package
===========================

Now we can move to `poll.main` packae to create the main package to
develop the application.  We can develop the entire application
inside `poll.main` package.  But it is reccomended to split packages
logically and maintain the dependencies between packages properly.

::

  $ cd ../poll.main

Again we need to create the basic directory structure and `setup.py`
to create egg distribution.  We are going to place python package
inside `src` directory.

::

  $ touch setup.py
  $ mkdir src
  $ mkdir src/poll
  $ mkdir src/poll/main
  $ touch src/poll/__init__.py
  $ touch src/poll/main/__init__.py
  $ touch src/poll/main/configure.zcml

The last file we created is a configuration file called Zope
Configuration Markup Language (ZCML). Soon we will add some boiler
plate code inside ZCML file.

To declare `poll` as a namespace package, we need to add this boiler
plate code to `src/poll/__init__.py`.

::

  __import__('pkg_resources').declare_namespace(__name__)

Next we need to add the minimum meta data required for the package in
`setup.py`.

::

  from setuptools import setup, find_packages

  setup(
      name="poll.main",
      version="0.1",
      packages=find_packages("src"),
      package_dir={"": "src"},
      namespace_packages=["poll"],
      install_requires=["setuptools",
                        "Zope2"],
      )

We need to add two more files to be recognized by Zope.  First,
define this call-back function in `src/poll/main/__init__.py`.

::

  def initialize(registrar):
      pass

And in the ZCML file add these few lines.

::

  <configure
      xmlns="http://namespaces.zope.org/five">

      <registerPackage package="." initialize=".initialize" />

  </configure>

Creating Installable Application
================================

We need three things to make an installable application.

- Form object created using ZPT (manage_addPollMain)
- A function to define form action (addPollMain)
- A class to define toplevel application object (PollMain).

And we need to register the class along with form and add function
using the `registrar` object passed to the `initialize` function.

We can define all these things in `app.py` and the form template as
`manage_addPollMain_form.zpt`.

::

  $ touch src/poll/main/app.py
  $ touch src/poll/main/manage_addPollMain_form.zpt

Here is the code for `app.py`.

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

And `manage_addPollMain_form.zpt`.

::

  <html xmlns="http://www.w3.org/1999/xhtml"
        xmlns:tal="http://xml.zope.org/namespaces/tal">
    <body>

      <h2>Add POLL</h2>
      <form action="addPollMain" method="post">
        Id: <input type="text" name="id" /><br />
        Title: <input type="text" name="title" /><br />
        <input type="submit" value="Add" />
      </form>
    </body>
  </html>

Finally we can register it like this (update `__init__.py`)::

  from poll.main.app import PollMain, manage_addPollMain, addPollMain

  def initialize(registrar):
      registrar.registerClass(PollMain,
                              constructors=(manage_addPollMain, addPollMain))

The application is now ready to install.  But we need to make some
changes in `poll_build` to recognize this package by Zope 2.

Adding poll.main to build
=========================

First in `[buildout]` part we need to mention that `poll.main` is
locally developed.  Otherwise buildout will try to get the package
from package index server, by default http://pypi.python.org/pypi .

::

  [buildout]
  develop = ../poll.main
  ...

Also we need to add `poll.main` egg to `eggs` option in `[zope2]`
part.

::

  ...
  eggs = Zope2
         poll.main
  ...

And finally we need to add a new option to include the ZCML file.  So
that the package will be recognized by Zope.

::

  ...
  zcml = poll.main

The final `buildout.cfg` will look like this.

::

  [buildout]
  develop = ../poll.main
  parts = zope2
          instance
  extends = http://download.zope.org/Zope2/index/2.13.20/versions.cfg

  [zope2]
  recipe = zc.recipe.egg
  eggs = Zope2
         poll.main
  interpreter = zopepy

  [instance]
  recipe = plone.recipe.zope2instance
  user = admin:admin
  http-address = 8080
  eggs = ${zope2:eggs}
  zcml = poll.main

Now to make these change effective, run the buildout again.

::

  $ ./bin/buildout

Now we can run application instance again.

::

  $ ./bin/instance fg

Adding application instance
===========================

Visit ZMI and select `POLL` from the drop-down box.  It will display
the add-form created earlier.  You can provide the ID as `poll` and
submit the form.  After submitting, it should display a message:
"POLL Installed: poll".

Adding the main page to POLL
============================

In this section we will try to add a main page to POLL application.
So that we can acces POLL application like this:
http://localhost:8080/poll .

First create a file named `index_html.zpt` inside `src/poll/main` with
content like this::

  <html>
  <head>
    <title>Welcome to POLL!</title>
  </head>
  <body>

  <h2>Welcome to POLL!</h2>

  </body>
  </html>

Now add an attribute named `index_html` inside PollMain class like
this::

  class PollMain(Folder):
      meta_type = "POLL"

      index_html = PageTemplateFile("index_html", globals())

Restart the Zope. Now you can see that it display the main page when
you access: http://localhost:8080/poll .

Summary
=======

This chapter covered installation and beginning a simple project in
Zope 2.
