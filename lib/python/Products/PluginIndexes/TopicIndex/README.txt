TopicIndex

  Reference: http://dev.zope.org/Wikis/DevSite/Proposals/TopicIndexes

  A TopicIndex is a container for so-called FilteredSet. A FilteredSet
  consists of an expression and a set of internal ZCatalog document 
  identifiers that represent a pre-calculated result list for performance
  reasons. Instead of executing the same query on a ZCatalog multiple times
  it is much faster to use a TopicIndex instead.
 
  Building up FilteredSets happens on the fly when objects are cataloged
  and uncatalogued. Every indexed object is evaluated against the expressions
  of every FilteredSet. An object is added to a FilteredSet if the expression
  with the object evaluates to 1. Uncatalogued objects are removed from the
  FilteredSet.


  Types of FilteredSet

    PythonFilteredSet
     
      A PythonFilteredSet evaluates using the eval() function inside the
      context of the FilteredSet class. The object to be indexes must
      be referenced inside the expression using "o.".

      Examples::

             "o.meta_type=='DTML Method'"
    
    

  Queries on TopicIndexes
 
    A TopicIndex is queried in the same way as other ZCatalog Indexes and supports
    usage of the 'operator' parameter to specify how to combine search results.



  API

    The TopicIndex implements the API for pluggable Indexes.
    Additionally it provides the following functions to manage FilteredSets

      -- addFilteredSet(Id, filterType, expression): 

        -- Id:  unique Id for the FilteredSet
 
        -- filterType:     'PythonFilteredSet'
    
        -- expression:  Python expression


      -- delFilteredSet(Id):

      -- clearFilteredSet(Id):
     
  
