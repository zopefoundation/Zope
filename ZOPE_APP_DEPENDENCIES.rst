Zope2 Dependencies on ``zope.app`` Packages
===========================================

Zope2 depends on the following zope.app packages directly:

- [X] zope.app.appsetup
      * Zope2.Startup
      * Zope.App.Startup

- [X] zope.app.component
      * Products.Five (meta.zcml)

- [X] zope.app.container
      * Products.Five.browser.adding (only indirect now)
      * Products.Five.browser.metaconfigure
      * Products/Five/browser/doc/products/ViewsTutorial/configure.zcml

- [_] zope.app.form
      o Products.Five.form.* (should be factored out into a separate
        package, maybe ``five.forms``)

- [X] zope.app.pagetemplate 
      * Products.PageTemplates.Expressions
      * Products.Five.browser.pagetemplatefile
      * Products.Five.browser.metaconfigure

- [X] zope.app.publication
      * ZPublisher.BaseRequest (imports ``EndRequestEvent``)
      * Products.Five.component (imports ``BeforeTraverseEvent``;
        ZCML registers subscribers for ``IBeforeTraverseEvent``
        and ``IEndRequestEvent``)

- [X] zope.app.publisher 
      * ZPublisher.BaseRequest
      * Products.Five.browser.adding (for ``getMenu``)
      * Products/Five/browser/configure.zcml (for ``IMenuItemType``,
        ``MenuAccessView``, and ``IMenuAccessView``)
      * Products.Five.viewlet.metaconfigure (for ``viewmeta``)
      * Products.Five.form.metaconfigure (for ``menuItemDirective``)
      * Products.Five.fivedirectives (for ``IBasicResourceInformation``)

- [X] zope.app.schema 
      * Products.Five (imports ``zope.app.schema.vocabulary`` for
        side-effects ?!).

- [X] zope.app.twisted
      * Zope2.Startup.datatypes (conditionally imports ``ServerFactory``)
      * Zope2.Startup.handlers (conditionally imports ``ServerType``,
      ``SSLServerType``, ``IServerType``;  worse, conditionally imports
      ``zope.app.twisted.main`` for side effects, which includes pulling
      back ``zope.app.appsetup`` as well as adding ``zope.app.wsgi``?!)

This shell script can be used to verify the direct dependencies::

  #! /bin/bash
  python=$(find src/ -name "*.py" | xargs grep -l "zope\.app")
  zcml=$(find src/ -name "*.zcml" | xargs grep -l "zope\.app")
  doctest=$(find src/ -name "*.txt" | grep -v "egg-info" |
            xargs grep -l "zope\.app")
  for f in $python $zcml $doctest; do
      echo ====================================================
      echo $f
      echo ====================================================
      grep "zope\.app" $f
   done

Zope2 has transitive dependencies on these packages:

- [X] zope.app.applicationcontrol 
      * zope.traversing
      * zope.app.publication
      * zope.app.twisted

- [X] zope.app.basicskin 
      * zope.app.form

- [X] zope.app.dependable 
      * zope.container
      * zope.app.testing

- [X] zope.app.exception 
      * zope.app.publication

- [X] zope.app.http 
      * zope.app.publication

- [X] zope.app.interface 
      * zope.app.component

- [_] zope.app.pagetemplate
      (this package has no zope.app dependencies of its own anymore and should
       be renamed to reflect this or its commonly used parts be extracted)
      o zope.viewlet

- [X] zope.app.security 
      * zope.viewlet
      * zope.traversing
      * zope.testbrowser
      * zope.app.*

- [_] zope.app.testing 
      * zope.viewlet
      * zope.copypastemve
      * zope.error
      * zope.dublincore
      o zope.formlib
      * zope.traversing
      * zope.testbrowser
      * zope.site
      * zope.app.*
