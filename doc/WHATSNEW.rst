What's new in Zope 2.13
=======================

The article explains the new high-level features and changes found in this
version of Zope 2.

You can have a look at the `detailed change log <CHANGES.html>`_ to learn
about all minor new features and bugs being solved in this release.


ZODB 3.10
---------

...


WSGI
----

...


Zope Toolkit
------------

...


Optional Formlib support
------------------------

Zope 2 made a number of frameworks available through its integration layer
Products.Five. Among these has been direct support for an automated form
generation framework called zope.formlib with its accompanying widget library
zope.app.form.

This form generation framework has seen only minor adoption throughout the Zope
community and more popular alternatives like z3c.form exist. To reflect this
status Zope 2 no longer directly contains formlib support.

If you rely on formlib, you need to add a dependency to the new five.formlib
distribution and change all related imports pointing to Products.Five.form or
Products.Five.formlib to point to the new package instead.

In order to ease the transition, five.formlib has been backported to the 2.12
release series. Starting in 2.12.3 you can already use the new five.formlib
package, but backwards compatibility imports are left in place in Products.Five.
This allows you to easily adopt your packages to work with both 2.12 and 2.13.
