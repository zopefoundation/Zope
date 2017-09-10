Zope2 Book
==========

Background
----------

The `Zope2 Book` has been the canonical source of information about Zope2 for
a long time.

During its lifetime it has seen many different places. The original location
has been: http://www.zope.org/Documentation/Books/ZopeBook/

Chris McDonough has done a great job of updating it for Zope 2.7 and
hosting the updated copy at http://www.plope.com/Books/2_7Edition

Various attempts to update the book and maintain it took place afterwards,
for example https://code.launchpad.net/zope2book and
http://wiki.zope.org/zope2/ZopeBook.

This is yet another attempt to bring the book back to live.

Technology
----------

This time we use `Sphinx`_ based on a conversion of the original content to
reStructured as the tool.

To install Sphinx you can simply do::

  easy_install Sphinx

You might want to use a `virtualenv`_ to protect your global Python from any
changes.

Sphinx can generate various different formats from the same source. If you
want to build a HTML version of the book, you can do::

  make html

To what extent this works on Windows is unknown.

Contact
-------

At this point the book is best discussed at:

http://mail.zope.org/mailman/listinfo/zope-dev


.. _Sphinx: http://sphinx.pocoo.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv/
