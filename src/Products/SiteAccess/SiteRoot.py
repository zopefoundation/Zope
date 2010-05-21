"""SiteRoot module

Defines the Traverser base class and SiteRoot class
"""
from cgi import escape
import os

from Acquisition import Implicit
from App.Dialogs import MessageDialog
from App.special_dtml import DTMLFile
from OFS.SimpleItem import Item
from Persistence import Persistent
from ZPublisher.BeforeTraverse import NameCaller
from ZPublisher.BeforeTraverse import registerBeforeTraverse
from ZPublisher.BeforeTraverse import unregisterBeforeTraverse

SUPPRESS_SITEROOT = os.environ.has_key('SUPPRESS_SITEROOT')

class Traverser(Persistent, Item):
    """ Class for overriding container's __before_traverse__

    Containers are expected to have at most one instance of any particular
    subclass, with Id equal to the meta_type of the subclass.
    """
    meta_type = 'Traverser'
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
            raise ValueError('Cannot change the id of a %s'
                                % escape(self.meta_type))

class SiteRoot(Traverser, Implicit):
    """ SiteAccess.SiteRoot object

    A SiteRoot causes traversal of its container to replace the part
    of the Request path traversed so far with the request's SiteRootURL.
    """
    id = meta_type = 'SiteRoot'
    title = ''
    priority = 50

    manage_options=({'label':'Edit',
                     'action':'manage_main',
                     'help': ('SiteAccess', 'SiteRoot_Edit.stx'),
                    },)

    manage = manage_main = DTMLFile('www/SiteRootEdit', globals())
    manage_main._setName('manage_main')

    def __init__(self, title, base, path):
        self.title = title.strip()
        self.base = base = base.strip()
        self.path = path = path.strip()

    def manage_edit(self, title, base, path, REQUEST=None):
        """ Set the title, base, and path.
        """
        self.__init__(title, base, path)
        if REQUEST:
            return MessageDialog(title='SiteRoot changed.',
              message='SiteRoot changed.',
              action='%s/manage_main' % REQUEST['URL1'])

    def __call__(self, client, request, response=None):
        """ Traversing.
        """
        rq = request
        if SUPPRESS_SITEROOT:
            return
        base = (self.base or
                rq.get('SiteRootBASE') or
                rq.environ.get('SiteRootBASE'))
        path = (self.path or
                rq.get('SiteRootPATH') or
                rq.environ.get('SiteRootPATH'))
        if base is not None:
            rq['ACTUAL_URL'] = rq['ACTUAL_URL'].replace(rq['SERVER_URL'], base)
            rq['SERVER_URL'] = base
            rq._resetURLS()
        if path is not None:
            old = rq['URL']
            rq.setVirtualRoot(path)
            rq['ACTUAL_URL'] = rq['ACTUAL_URL'].replace(old, rq['URL'])

    def get_size(self):
        """ Make FTP happy
        """
        return 0

def manage_addSiteRoot(self, title='', base='', path='', REQUEST=None,
                       **ignored):
    """ Add a SiteRoot to a container.
    """
    sr = SiteRoot(title, base, path)
    if REQUEST:
        return sr.manage_addToContainer(self.this(),
                                        '%s/manage_main' % REQUEST['URL1'])
    else:
        sr.manage_addToContainer(self.this())

constructors = (
  ('manage_addSiteRootForm', DTMLFile('www/SiteRootAdd', globals())),
  ('manage_addSiteRoot', manage_addSiteRoot),
)
