##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
# 
##############################################################################
"""
$Id: IZCatalog.py,v 1.1 2002/07/29 14:10:48 jim Exp $
"""

from Interface import Interface

class IZCatalog(Interface):
    """ZCatalog object

    A ZCatalog contains arbitrary index like references to Zope
    objects.  ZCatalog's can index object attribute using a variety
    of "plug-in" index types.

    Several index types are included, and others may be added.

      Text -- Text indexes index textual content.  The index can be
      used to search for objects containing certain words.

      Field -- Field indexes index atomic values.  The index can be
      used to search for objects that have certain properties.

      Keyword -- Keyword indexes index sequences of values.  The index
      can be used to search for objects that match one or more of the
      search terms.
      
      Path -- Path indexes index URI paths. They allow you to find objects
      based on their placement in a hierarchy.
      
      Date -- Date indexes index date and type data. They are a type of field
      index specifically optimized for indexing dates.

      Date Range -- Date range indexes index time intervals. They are designed
      for efficient searching of dates falling between two boundaries
      (such as effective / expiration dates).
      
      Topic -- Topic indexes store prefiltered sets of documents. They are used
      to optimize complex queries into a single fast query by prefiltering 
      documents by an expression 

    The ZCatalog can maintain a table of extra data about cataloged
    objects.  This information can be used on search result pages to
    show information about a search result.

    The meta-data table schema is used to build the schema for
    ZCatalog Result objects.  The objects have the same attributes
    as the column of the meta-data table.

    ZCatalog does not store references to the objects themselves, but
    rather to a unique identifier that defines how to get to the
    object.  In Zope, this unique identifier is the object's relative
    path to the ZCatalog (since two Zope objects cannot have the same 
    URL, this is an excellent unique qualifier in Zope).

    """

    def catalog_object(obj, uid):
        """Catalogs the object 'obj' with the unique identifier 'uid'.

        The uid must be a physical path!
        """

    def uncatalog_object(uid):
        """Uncatalogs the object with the unique identifier 'uid'.

        The uid must be a physical path!
        """

    def uniqueValuesFor(name):
        """returns the unique values for a given FieldIndex named 'name'.
        """

    def getpath(rid):
        """Return the path to a cataloged object given a 'data_record_id_'
        """

    def getrid(rid):
        """Return the 'data_record_id_' to a cataloged object given a path
        """

    def getobject(rid, REQUEST=None):
        """Return a cataloged object given a 'data_record_id_'
        """

    def schema():
        """Get the meta-data schema

        Returns a sequence of names that correspond to columns in the
        meta-data table.

        """

    def indexes():
        """Returns a sequence of names that correspond to indexes.
        """

    def index_objects():
        """Returns a sequence of actual index objects.
        """

    def searchResults(REQUEST=None, **kw):
        """Search the catalog.

        Search terms can be passed in the REQUEST or as keyword
        arguments.

        Search queries consist of a mapping of index names to search
        parameters.  You can either pass a mapping to searchResults as
        the variable 'REQUEST' or you can use index names and search
        parameters as keyword arguments to the method, in other words::

          searchResults(title='Elvis Exposed',
                        author='The Great Elvonso')

        is the same as::

          searchResults({'title' : 'Elvis Exposed',
                         'author : 'The Great Elvonso'})

        In these examples, 'title' and 'author' are indexes.  This
        query will return any objects that have the title *Elvis
        Exposed* AND also are authored by *The Great Elvonso*.  Terms
        that are passed as keys and values in a searchResults() call
        are implicitly ANDed together. To OR two search results, call
        searchResults() twice and add concatenate the results like this::

          results = ( searchResults(title='Elvis Exposed') +
                      searchResults(author='The Great Elvonso') )

        This will return all objects that have the specified title OR
        the specified author.

        There are some special index names you can pass to change the
        behavior of the search query:

          sort_on -- This parameters specifies which index to sort the
          results on.

          sort_order -- You can specify 'reverse' or 'descending'.
          Default behavior is to sort ascending.

        There are some rules to consider when querying this method:

            - an empty query mapping (or a bogus REQUEST) returns all
              items in the
            catalog.

            - results from a query involving only field/keyword
              indexes, e.g.  {'id':'foo'} and no 'sort_on' will be
              returned unsorted.

            - results from a complex query involving a field/keyword
              index *and* a text index,
              e.g. {'id':'foo','PrincipiaSearchSource':'bar'} and no
              'sort_on' will be returned unsorted.

            - results from a simple text index query
              e.g.{'PrincipiaSearchSource':'foo'} will be returned
              sorted in descending order by 'score'.  A text index
              cannot beused as a 'sort_on' parameter, and attempting
              to do so will raise an error.

        Depending on the type of index you are querying, you may be
        able to provide more advanced search parameters that can
        specify range searches or wildcards.  These features are
        documented in The Zope Book.

        """
    
    def __call__(REQUEST=None, **kw):
        """Search the catalog, the same way as 'searchResults'.
        """

__doc__ = IZCatalog.__doc__ + __doc__
