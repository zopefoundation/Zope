Zope2 depends on the following zope.app packages directly:

- [X] zope.app.appsetup
      * Zope2.Startup
      * Zope.App.Startup

- [_] zope.app.component
      o Products.Five (meta.zcml)

- [_] zope.app.container
      o Products.Five.browser.adding
      o Products.Five.browser.metaconfigure
      o Products.Five.browser.doc/products/ViewsTutoria (configure.zcml)

- [_] zope.app.form
      o Products.Five.form.*

- [_] zope.app.pagetemplate 
      o Products.PageTemplates.Expressions
      o Products.Five.browser.pagetemplatefile
      o Products.Five.browser.metaconfigure

- [_] zope.app.publication 
      o ZPublisher.BaseRequest
      o Products.Five.component

- [_] zope.app.publisher 
      o ZPublisher.BaseRequest
      o Products.Five.browser.*
      o Products.Five.viewlet.metaconfigure
      o Products.Five.form.metaconfigure
      o Products.Five.fivedirectives

- [_] zope.app.schema 
      o Products.Five


And has transitive dependencies on these packages:

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
