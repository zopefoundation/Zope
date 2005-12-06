"""AccessRule module

Provide a simple method to set up Access Rules
"""

from Globals import DTMLFile, MessageDialog
from ZPublisher.BeforeTraverse import \
 registerBeforeTraverse, unregisterBeforeTraverse, queryBeforeTraverse, \
 NameCaller
import os
from cgi import escape

SUPPRESS_ACCESSRULE = os.environ.has_key('SUPPRESS_ACCESSRULE')

class AccessRule(NameCaller):
    meta_type = 'Set Access Rule'

    def __call__(self, container, request):
        if SUPPRESS_ACCESSRULE: return
        if '_SUPPRESS_ACCESSRULE' in _swallow(request, '_SUPPRESS'):
            request.setVirtualRoot(request.steps)
            return
        NameCaller.__call__(self, container, request)

def _swallow(request, prefix):
    path = request['TraversalRequestNameStack']
    steps = request.steps
    i = len(steps)
    while i > 0 and steps[i - 1][:1] == '_':
        i = i - 1
    while path and path[-1][:len(prefix)] == prefix:
        steps.append(path.pop())
    return steps[i:]

def manage_addAccessRule(self, method_id=None, REQUEST=None, **ignored):
    """Point a __before_traverse__ entry at the specified method"""
    # We want the original object, not stuff in between, and no acquisition
    self = self.this()
    self = getattr(self, 'aq_base', self)
    priority = (1, 'AccessRule')

    if method_id is None or (REQUEST and REQUEST.form.has_key('none')):
        rules = unregisterBeforeTraverse(self, 'AccessRule')
        if rules:
            try: del getattr(self, rules[0].name).icon
            except: pass
        if REQUEST:
            return MessageDialog(title='No Access Rule',
              message='This object now has no Access Rule',
              action='%s/manage_main' % REQUEST['URL1'])
    elif method_id and hasattr(self, method_id):
        rules = unregisterBeforeTraverse(self, 'AccessRule')
        if rules:
            try: del getattr(self, rules[0].name).icon
            except: pass
        hook = AccessRule(method_id)
        registerBeforeTraverse(self, hook, 'AccessRule', 1)
        try:
            getattr(self, method_id).icon = 'misc_/SiteAccess/AccessRule.gif'
        except: pass
        if REQUEST:
            return MessageDialog(title='Access Rule Set',
              message='"%s" is now the Access Rule for this object'
                      % escape(method_id),
              action='%s/manage_main' % REQUEST['URL1'])
    else:
        if REQUEST:
            return MessageDialog(title='Invalid Method Id',
              message='"%s" is not the Id of a method of this object'
                      % escape(method_id),
              action='%s/manage_main' % REQUEST['URL1'])

def getAccessRule(self, REQUEST=None):
    "Return the name of the current AccessRule, if any"
    self = self.this()
    rules = queryBeforeTraverse(self, 'AccessRule')
    if rules:
        try:
            return rules[0][1].name
        except:
            return 'Invalid BeforeTraverse data: ' + `rules`
    return ''

constructors = (
  ('manage_addAccessRuleForm', DTMLFile('www/AccessRuleAdd', globals())),
  ('manage_addAccessRule', manage_addAccessRule),
  ('manage_getAccessRule', getAccessRule),
)
