"""VirtualHostMonster module

Defines the VirtualHostMonster class
"""

from Globals import DTMLFile, MessageDialog, Persistent
from OFS.SimpleItem import Item
from Acquisition import Implicit, ImplicitAcquisitionWrapper
from ExtensionClass import Base
from string import split, strip, join
from ZPublisher import BeforeTraverse
import os

from AccessRule import _swallow

class VirtualHostMonster(Persistent, Item, Implicit):
    """Provide a simple drop-in solution for virtual hosting.
    """

    meta_type='Virtual Host Monster'
    priority = 25

    title = ''

    __ac_permissions__=(('View', ('manage_main',)),)

    manage_options=({'label':'View', 'action':'manage_main'},)

    manage_main = DTMLFile('www/VirtualHostMonster', globals())

    def addToContainer(self, container):
        container._setObject(self.id, self)
        self.manage_afterAdd(self, container)

    def manage_addToContainer(self, container, nextURL=''):
        self.addToContainer(container)
        if nextURL:    
            return MessageDialog(title='Item Added',
              message='This object now has a %s' % self.meta_type, 
              action=nextURL)

    def manage_beforeDelete(self, item, container):
        if item is self:
            BeforeTraverse.unregisterBeforeTraverse(container, self.meta_type)

    def manage_afterAdd(self, item, container):
        if item is self:
            id = self.id
            if callable(id): id = id()

            # We want the original object, not stuff in between
            container = container.this()
            hook = BeforeTraverse.NameCaller(id)
            BeforeTraverse.registerBeforeTraverse(container, hook,
                                                  self.meta_type,
                                                  self.priority)
    def _setId(self, id):
        id = str(id)
        if id != self.id:
            BeforeTraverse.unregisterBeforeTraverse(container,
            self.meta_type)
            hook = BeforeTraverse.NameCaller(id)
            BeforeTraverse.registerBeforeTraverse(container, hook,
                                                  self.meta_type,
                                                  self.priority)

    def __call__(self, client, request, response=None):
        '''Traversing at home'''
        stack = request['TraversalRequestNameStack']
        if stack and stack[-1] == 'VirtualHostBase':
            stack.pop()
            protocol = stack.pop()
            host = stack.pop()
            if ':' in host:
                host, port = split(host, ':')
                request.setServerURL(protocol, host, port)
            else:
                request.setServerURL(protocol, host)
        # Find and convert VirtualHostRoot directive
        # If it is followed by one or more path elements that each
        # start with '_vh_', use them to construct the path to the
        # virtual root.
        vh = -1
        for ii in range(len(stack)):
            if stack[ii] == 'VirtualHostRoot':
                if vh >= 0:
                    pp = ['']
                    for jj in range(vh, ii):
                        pp.insert(1, stack[jj][4:])
                    stack[vh:ii + 1] = [join(pp, '/'), self.id]
                elif ii > 0 and stack[ii - 1][:1] == '/':
                    stack[ii] = self.id
                else:
                    stack[ii] = self.id
                    stack.insert(ii, '/')
                break
            elif vh < 0 and stack[ii][:4] == '_vh_':
                vh = ii

    def __bobo_traverse__(self, request, name):
        '''Traversing away'''
        if name[:1] != '/':
            return getattr(self, name)
        parents = request.PARENTS
        parents.pop() # I don't belong there

        if len(name) > 1:
            request.setVirtualRoot(split(name[1:], '/'))
        else:
            request.setVirtualRoot([])
        return parents.pop() # He'll get put back on

def manage_addVirtualHostMonster(self, id, REQUEST=None, **ignored):
    """ """
    vhm = VirtualHostMonster()
    vhm.id = str(id)
    if REQUEST:
        return vhm.manage_addToContainer(self.this(),
                                        '%s/manage_main' % REQUEST['URL1'])
    else:
        vhm.addToContainer(self.this())

constructors = (
  ('manage_addVirtualHostMonsterForm', DTMLFile('www/VirtualHostMonsterAdd', globals())),
  ('manage_addVirtualHostMonster', manage_addVirtualHostMonster),
)
