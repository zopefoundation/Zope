PathIndex by Zope Corporation + 
extensions by Plone Solutions (former ExtendedPathIndex)

    This is an index that supports depth limiting, and the ability to build a
    structure usable for navtrees and sitemaps. The actual navtree implementations
    are not (and should not) be in this Product, this is the index implementation
    only.

Features

    - Can construct a site map with a single catalog query

    - Can construct a navigation tree with a single catalog query

Usage:

    - catalog(path='some/path')  - search for all objects below some/path

    - catalog(path={'query' : 'some/path', 'depth' : 2 )  - search for all
      objects below some/path but only down to a depth of 2

    - catalog(path={'query' : 'some/path', 'navtree' : 1 )  - search for all
      objects below some/path for rendering a navigation tree. This includes
      all objects below some/path up to a depth of 1 and all parent objects.
 
Credits

    - Zope Corporation for the initial PathIndex code

    - Helge Tesdal from Plone Solutions for the ExtendedPathIndex implementation

License

    This software is released under the ZPL license.
