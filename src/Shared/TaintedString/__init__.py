from zope.deferredimport import deprecated
deprecated('Shared.TaintedString will be removed in Zope 2.14. Please '
   'import from AccessControl.tainted instead.',
   TaintedString = 'AccessControl.tainted:TaintedString',
   createSimpleWrapper = 'AccessControl.tainted:createSimpleWrapper',
   createOneArgWrapper = 'AccessControl.tainted:createOneArgWrapper',
   createOneOptArgWrapper = 'AccessControl.tainted:createOneOptArgWrapper',
)
