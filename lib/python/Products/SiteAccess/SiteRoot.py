"""SiteRoot module

Defines the Traverser base class and SiteRoot class
"""
from cgi import escape
import os

from Acquisition import Implicit
from Acquisition import ImplicitAcquisitionWrapper
from App.Dialogs import MessageDialog
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from OFS.SimpleItem import Item
from Persistence import Persistent
from ZPublisher.BeforeTraverse import NameCaller
from ZPublisher.BeforeTraverse import registerBeforeTraverse
from ZPublisher.BeforeTraverse import unregisterBeforeTraverse

from Products.SiteAccess.AccessRule import _swallow

SUPPRESS_SITEROOT = os.environ.has_key('SUPPRESS_SITEROOT')

class Traverser(Persistent, Item):
    """Class for overriding container's __before_traverse__

    Containers are expected to have at most one instance of any particular
    subclass, with Id equal to the meta_type of the subclass."""

    meta_type='Traverser'
    priority = 100

    __ac_permissions__=()

    def addToContainer(self, container):
        container._setObject(self.id, self)
        self.manage_afterAdd(self, container)

    def manage_addToContainer(self, container, nextURL=''):
        if nextURL:
            if hasattr(getattr(container, 'aq_base', container), self.id):
                return MessageDialog(title='Item Exists',
                  message='This object already contains a %s' % self.meta_type,
                  action=nextURL)
        self.addToContainer(container)
        if nextURL:
            return MessageDialog(title='Item Added',
              message='This object now has a %s' % escape(self.meta_type),
              action=nextURL)

    def manage_beforeDelete(self, item, container):
        if item is self:
            unregisterBeforeTraverse(container, self.meta_type)

    def manage_afterAdd(self, item, container):
        if item is self:
            id = self.id
            if callable(id): id = id()

            # We want the original object, not stuff in between
            container = container.this()
            hook = NameCaller(id)
            registerBeforeTraverse(container, hook,
                                                  self.meta_type,
                                                  self.priority)
    def _setId(self, id):
        if id != self.id:
            raise MessageDialog(
                title='Invalid Id',
                message='Cannot change the id of a %s' % escape(self.meta_type),
                action ='./manage_main',)

class SiteRoot(Traverser, Implicit):
    """SiteAccess.SiteRoot object

    A SiteRoot causes traversal of its container to replace the part
    of the Request path traversed so far with the request's SiteRootURL."""

    id = meta_type = 'SiteRoot'
    title = ''
    priority = 50

    manage_options=({'label':'Edit', 'action':'manage_main', 'help': ('SiteAccess', 'SiteRoot_Edit.stx')},)

    manage = manage_main = DTMLFile('www/SiteRootEdit', globals())
    manage_main._setName('manage_main')

    def __init__(self, title, base, path):
        '''Title'''
        self.title = title.strip()
        self.base = base = base.strip()
        self.path = path = path.strip()
        if base: self.SiteRootBASE = base
        else:
            try: del self.SiteRootBASE
            except: pass
        if path: self.SiteRootPATH = path
        else:
            try: del self.SiteRootPATH
            except: pass

    def manage_edit(self, title, base, path, REQUEST=None):
        '''Set the title, base, and path'''
        self.__init__(title, base, path)
        if REQUEST:
            return MessageDialog(title='SiteRoot changed.',
              message='SiteRoot changed.',
              action='%s/manage_main' % REQUEST['URL1'])

    def __call__(self, client, request, response=None):
        '''Traversing'''
        if SUPPRESS_SITEROOT: return
        if '_SUPPRESS_SITEROOT' in _swallow(request, '_SUPPRESS'):
            request.setVirtualRoot(request.steps)
            return
        srd = [None, None]
        for i in (0, 1):
            srp = ('SiteRootBASE', 'SiteRootPATH')[i]
            try:
                srd[i] = getattr(self, srp)
            except AttributeError:
                srd[i] = request.get(srp, None)
                if srd[i] is None:
                    srd[i] = request.environ.get(srp, None)
        if srd[0] is not None:
            request['ACTUAL_URL'] = request['ACTUAL_URL'].replace(request['SERVER_URL'], srd[0])
            request['SERVER_URL'] = srd[0]
            request._resetURLS()
        if srd[1] is not None:
            old = request['URL']
            request.setVirtualRoot(srd[1])
            request['ACTUAL_URL'] = request['ACTUAL_URL'].replace(old, request['URL'])

    def get_size(self):
        '''Make FTP happy'''
        return 0

def manage_addSiteRoot(self, title='', base='', path='', REQUEST=None,
                       **ignored):
    """ """
    sr=SiteRoot(title, base, path)
    if REQUEST:
        return sr.manage_addToContainer(self.this(),
                                        '%s/manage_main' % REQUEST['URL1'])
    else:
        sr.manage_addToContainer(self.this())

constructors = (
  ('manage_addSiteRootForm', DTMLFile('www/SiteRootAdd', globals())),
  ('manage_addSiteRoot', manage_addSiteRoot),
)
