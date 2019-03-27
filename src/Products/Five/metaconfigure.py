# BBB Zope 5.0

from zope.deferredimport import deprecated


deprecated(
    'Please import from AccessControl.metaconfigure',
    ClassDirective='AccessControl.metaconfigure:ClassDirective',
)
