Zope 2.4 introduces a new way to register customized indexes
(see PluggableIndex interface). 

Changes to Indexes:

 New package structure

  -  The indexes (TextIndex, FieldIndex, KeywordIndex, PathIndex) shipped 
     with the Zope 2.4 distribution now live in 'lib/python/Products/PluginIndexes'. 
     Every index type has now its own package containing all dependent
     modules, DTML management files...

  - modules used by all index types reside in the 'common' directory

  - all dependencies from the 'lib/python/SearchIndex' directory were removed

  - 'lib/python/SearchIndex' is deprecated and should no longer be used.
    It is kept for backward compatibility. 



 Changes to all indexes:

  - every index type implements the PluggableIndex interface

  - 'common/util.py' provides functionality for handling the 'request'
    parameter of the _apply_index() function.  _apply_index() 
    now handles old-style ZCatalog parameters, passing of Record
    instances and dictionary-like parameters. See common/util.py
    for details.


 Changes to KeywordIndex:

  - default search operator 'or' may be overridden by specifying a new one as
    'operator' (see below)

  - internal changes


 Changes to FieldIndex:

  - internal changes

 Changes for PathIndex:
 
  - new index type


Changes to ZCatalog

  - added ZCatalogIndexes.py to provide access to indexes with pluggable
    index interface

  
  Parameter passing to the ZCatalog

    Parameter passing to the ZCatalog/Catalog has been enhanced and unified
    and is now much more logical.

    - Method 1: The old way to pass a query including parameters to an index XXX
      was to specify the query as value in the request dictionary. Additional 
      parameters were passed XXX_parameter : <value> in the request dictionary.
      (This method is deprecated).

    - Method 2: The query and all parameters to be passed to an index XXX are
      passed as dictionary inside the request dictionary. Example:
      
        old: <dtml-in myCatalog(myindex='xx yy',myindex_usage':'blabla')
        new: <dtml-in myCatalog(myindex={'query':'xx yy','XXXXX':'blabla')

        Please check the indexes documentation for informations about additional 
        parameters.

    - Method 3: Inside a formular you can use Record as types for parameter passing.
      Example:

            <form action=...>
            <input type=text name="person.query:record" value="">
            <input type=hidden name="person.operator:record" value="and">
            ..</form>

            and in the DTML method:

             <dtml-in myCatalog(person=person)>

            This example will pass both parameters as a Record instance to the index
            'person'. 

   All index types of Zope support all three methods. On the DTML level only
   method 3 type parameter should be used. 



Backward compatibility:
  
  - any existing pre-2.4 ZCatalog should work under 2.4

  - pre-2.4 indexes of a ZCatalog are marked as 'pre-2.4 Index' in the Index view of the
    ZCatalog

  - '# objects' is set to 'not available' for pre-2.4 indexes


