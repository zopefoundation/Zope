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

- [_] zope.app.publication 
      o ZPublisher.BaseRequest (for ``EndRequestEvent``)
      o Products.Five.component (for ``BeforeTraverseEvent``)

- [X] zope.app.publisher 
      * ZPublisher.BaseRequest
      * Products.Five.browser.adding (for ``getMenu``)
      * Products/Five/browser/configure.zcml (for ``IMenuItemType``,
        ``MenuAccessView``, and ``IMenuAccessView``)
      * Products.Five.viewlet.metaconfigure (for ``viewmeta``)
      * Products.Five.form.metaconfigure (for ``menuItemDirective``)
      * Products.Five.fivedirectives (for ``IBasicResourceInformation``)

- [_] zope.app.schema 
      o Products.Five (imports ``zope.app.schema.vocabulary`` for
        side-effects ?!).

- [_] zope.app.twisted
      o Zope2.Startup.datatypes (conditionally imports ``ServerFactory``)
      o Zope2.Startup.handlers (conditionally imports ``ServerType``,
      ``SSLServerType``, ``IServerType``;  worse, conditionally imports
      ``zope.app.twisted.main`` for side effects, which includes pulling
      back ``zope.app.appsetup`` as well as adding ``zope.app.wsgi``?!)

This shell script can be used to verify the direct dependencies::

  #! /bin/sh
  for f in $(find src/ -name "*.py" | xargs grep -l "zope\.app"); do
      echo ====================================================
      echo $f
      echo ====================================================
      grep "zope\.app" $f
   done

Zope2 has transitive dependencies on these packages:

- [_] zope.app.applicationcontrol 
      o zope.traversing
      o zope.app.publication

- [_] zope.app.basicskin 
      o zope.app.form

- [_] zope.app.debug 
      o zope.app.testing

- [_] zope.app.dependable 
      o zope.container
      o zope.app.testing

- [_] zope.app.exception 
      o zope.app.publication

- [_] zope.app.http 
      o zope.app.publication

- [_] zope.app.interface 
      o zope.app.component

- [_] zope.app.localpermission 
      o zope.app.security

- [_] zope.app.security 
      o zope.viewlet
      o zope.traversing
      o zope.testbrowser
      o zope.app.*

- [_] zope.app.testing 
      o zope.viewlet
      o zope.container
      o zope.copypastemve
      o zope.error
      o zope.dublincore
      o zope.formlib
      o zope.traversing
      o zope.testbrowser
      o zope.site
      o zope.app.*
