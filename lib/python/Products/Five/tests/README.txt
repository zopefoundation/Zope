Five tests
==========

The tests need all products in the ``tests/products`` subdirectory
installed in your Zope instance's Products directory. On unixy
systems, this can be most simply done by a symlink::

  cd myinstance/Products
  ln -s Five/tests/products/FiveTest .

and so on for each product in tests/products. On other platforms, you
could manually copy these directories (though you'd need to do that
each time you change the tests).

The tests also require ZopeTestCase to be installed. ZopeTestCase can
be downloaded from here:

http://zope.org/Members/shh/ZopeTestCase

it needs to be installed in your Zope software's lib/python/Testing
directory.

Finally, if you have Zope 2.7.3 or better all you have to do is type::

  ./bin/zopectl test --dir Products/Five

to run the Five tests. For older versions of Zope you need to set the
following environment variables::

  export INSTANCE_HOME=/path/to/instance
  export SOFTWARE_HOME=/path/to/software/lib/python

Then you should be able to run the tests by typing::

  python2.3 runalltests.py

If you have troubles running the tests because zope.conf is looked for
in lib/Testing/etc/zope.conf, then you are running a Zope version
older than Zope 2.7.2. Please upgrade to Zope 2.7.2.
