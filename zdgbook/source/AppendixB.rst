############################
Appendix B: Zope Directories
############################

This is a list of some important directories in the Zope source code.

- 'Extensions' -- Code for External Methods go in this directory.

- 'ZServer' -- Python code for ZServer and Medusa.

- 'ZServer/medusa' -- Sam Rushing's Medusa package upon which ZServer
  is built.

- 'doc' -- Miscellaneous documentation.

- 'import' -- Place Zope export files here in order to import them
  into Zope.

- 'inst' -- Installation scripts.

- 'pcgi' -- C and Python code for PCGI.

- 'utilities' -- Miscellaneous utilities.

- 'var' -- Contains the ZODB data file (Data.fs) and various other
  files (logs, pids, etc.) This directory should be owned and
  writable by the userid that Zope is run as.

- 'lib/Components' -- Python extension modules written in C including
  BTree, ExtensionClass, cPickle, zlib, etc.

- 'lib/python' -- Most of the Zope Python code is in here.

- 'lib/python/AccessControl' -- Security classes.

- 'lib/python/App' -- Zope application classes. Stuff like product
  registration, and the control panel.

- 'lib/python/BTrees' -- Btrees package.

- 'lib/python/DateTime' -- DateTime package.

- 'lib/python/DocumentTemplate' -- DTML templating package. DTML
  Document and DTML Method use this.

- 'lib/python/HelpSys' -- Online help system.

- 'lib/python/Interface' -- Scarecrow interfaces package.

- 'lib/python/OFS' -- Object File System code. Includes basic Zope
  classes (Folder, DTML Document) and interfaces (ObjectManager,
  SimpleItem).

- 'lib/python/Products' -- Zope products are installed here.

- 'lib/python/Products/OFSP' -- The OFS product. Contains
  initialization code for basic Zope objects like Folder and DTML
  Document.

- 'lib/python/RestrictedPython' -- Python security used by DTML and
  Python Scripts.

- 'lib/python/SearchIndex' -- Indexes used by ZCatalog.

- 'lib/python/Shared' -- Shared code for use by multiple Products.

- 'lib/python/StructuredText' -- Structured Text package.

- 'lib/python/TreeDisplay' -- Tree tag package.

- 'lib/python/ZClasses' -- ZClasses package.

- 'lib/python/ZLogger' -- Logging package.

- 'lib/python/ZODB' -- ZODB package.

- 'lib/python/ZPublisher' -- The Zope ORB.

- 'lib/python/Zope' -- The Zope package published by ZPublisher.

- 'lib/python/webDAV' -- WebDAV support classes and interfaces.
