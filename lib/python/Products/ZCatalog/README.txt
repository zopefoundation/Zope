Site Index

    A Site Index collects information about Zope objects. It allows
    indexes of Zope objects to be searched.

    To search a site index, use the same conventions as a Tabula. Use
    either 'DP_Search_Results' or '__call__' with REQUEST and/or kw
    arguments.
    
    Basic indexed meta data includes

        id -- The object's id

        url -- A url for the object, eg '/MyFolder/MyDoc'

        title -- The object's title

        meta_type -- The object's meta type

        last_modified -- The object's bobobase_lastmodification_time

        text_content -- Text of DTML Documents and Methods

    All indexes are FieldIndexes, except text_content which is a TextIndex.

How to Use the Catalog

    To use a Catalog, create a Catalog object and add items to the catalog.
    You can use a Find like interface to search for interesting objects
    to add. The catalog does not detect changes to indexed objects, so you
    should periodically update the catalog index.
    
    To search the catalog, first create a report form by selecting the 'Report'
    for the product add list. After you create your report you can test it by
    viewing it.
    
    Next create a search form by selecting 'Search Form' form the product add
    list. The wizard will allow you to tailor the search form in a number of 
    ways. You should indicate that the search form is to use the report that
    you previously created.

    Now you can search your Zope site by viewing the search page and filling
    out the search form.

Cataloging Interface

    Zope objects can define additional attributes to be cataloged. When
    an object is added to the catalog that specifies additional cataloging
    information, additional columns and indexes will be added to the catalog
    as needed.

    To define additinal cataloging data use the 'ZopeCatalogAttributes'
    method. The method should return a tuple or list of dictionaries which
    describe the cataloged attributes::

        {'name': name, 'attr': attr, 'type': type, 'index': indexType}

    Where
    
        'name' is the name of the index.

        'attr' is the name of a method or attribute to query.

        'type' is a type code ['s'|'t'|'i'|'f'|'d'|'b']

        'index' is the index type ['FieldIndex'|'TextIndex'|'KeywordIndex']

    Note that problems can occurr if an object tries to define an index that
    already exists, but is of a different type or index type. Be careful.

    Note: This interface is provisional and subject to change.










