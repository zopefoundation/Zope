Zope Developer's Guide
======================

Background
----------

The "Zope Developer's Guide" was not maintained for a long time.

This is an attempt to bring the "Zope Developer's Guide" book back to
live.

Technology
----------

This time we use `Sphinx`_ based on a conversion of the original
content to reStructured as the tool.

To install Sphinx you can simply do::

  easy_install Sphinx

You might want to use a `virtualenv`_ to protect your global Python
from any changes.

Sphinx can generate various different formats from the same
source. If you want to build a HTML version of the book, you can do::

  make html

To what extent this works on Windows is unknown.

Contact
-------

At this point the book is best discussed at:

https://mail.zope.dev/mailman/listinfo/zope-dev


.. _Sphinx: http://sphinx.pocoo.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv/

TODO
----

- Split Testing and Debugging chapter
- Add getting started code inside examples
