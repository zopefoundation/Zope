Maintenance information
========================

.. note::

   This is internal documentation for Zope 2 developers having
   to create official Zope 2 releases

Zope 2.12+ release process
--------------------------

Maintainers 
+++++++++++

The following persons have access to the ``Zope2`` package on PyPI
(in order release new versions):

- Hanno Schlichting
- Tres Seaver
- Andreas Jung

Steps for creating a new Zope 2 release
+++++++++++++++++++++++++++++++++++++++

- update version information:

  - setup.py
  - inst/versions.py
  - inst/WinBuilders/mk/zope.mk

- update docs/CHANGES.rst

- tag the release

- upload the tagged release to PyPI 

- create the release specfic download index on download.zope.org
  (requires login credentials on download.zope.org. In case of
  problems contact Jens Vagelpohl)
  
  - login to download.zope.org

  - change to user ``zope``::
    
     sudo su - zope

  - create the download index::
     
    /var/zope/zope2index/bin/z2_kgs tags/2.12.2 /var/www/download.zope.org/Zope2/index/2.12.2

- update version information on zope2.zope.org

  - login on https://zope2.zope.org into the Plone site  



