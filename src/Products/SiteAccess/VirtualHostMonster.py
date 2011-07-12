"""VirtualHostMonster module

Defines the VirtualHostMonster class
"""
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view as View
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.Dialogs import MessageDialog
from App.special_dtml import DTMLFile
from OFS.SimpleItem import Item
from Persistence import Persistent
from ZPublisher.BeforeTraverse import NameCaller
from ZPublisher.BeforeTraverse import queryBeforeTraverse
from ZPublisher.BeforeTraverse import registerBeforeTraverse
from ZPublisher.BeforeTraverse import unregisterBeforeTraverse
from ZPublisher.BaseRequest import quote
from zExceptions import BadRequest

class VirtualHostMonster(Persistent, Item, Implicit):
    """Provide a simple drop-in solution for virtual hosting.
    """

    meta_type='Virtual Host Monster'
    priority = 25

    id = 'VHM'
    title = ''
    lines = ()
    have_map = 0

    security = ClassSecurityInfo()

    manage_options=({'label':'About', 'action':'manage_main'},
                    {'label':'Mappings', 'action':'manage_edit'})

    security.declareProtected(View, 'manage_main')
    manage_main = DTMLFile('www/VirtualHostMonster', globals(),
                           __name__='manage_main')

    security.declareProtected('Add Site Roots', 'manage_edit')
    manage_edit = DTMLFile('www/manage_edit', globals())

    security.declareProtected('Add Site Roots', 'set_map')
    def set_map(self, map_text, RESPONSE=None):
        "Set domain to path mappings."
        lines = map_text.split('\n')
        self.fixed_map = fixed_map = {}
        self.sub_map = sub_map = {}
        new_lines = []
        for line in lines:
            line = line.split('#!')[0].strip()
            if not line:
                continue
            try:
                # Drop the protocol, if any
                line = line.split('://')[-1]
                try:
                    host, path = [x.strip() for x in  line.split('/', 1)]
                except:
                    raise ValueError(
                        'Line needs a slash between host and path: %s'
                            % line )
                pp = filter(None, path.split( '/'))
                if pp:
                    obpath = pp[:]
                    if obpath[0] == 'VirtualHostBase':
                        obpath = obpath[3:]
                    if 'VirtualHostRoot' in obpath:
                        i1 = obpath.index('VirtualHostRoot')
                        i2 = i1 + 1
                        while i2 < len(obpath) and obpath[i2][:4] == '_vh_':
                            i2 = i2 + 1
                        del obpath[i1:i2]
                    if obpath:
                        try:
                            ob = self.unrestrictedTraverse(obpath)
                        except:
                            raise ValueError, (
                                'Path not found: %s' % obpath )
                        if not getattr(ob.aq_base, 'isAnObjectManager', 0):
                            raise ValueError, (
                                'Path must lead to an Object Manager: %s'
                                    % obpath)
                    if 'VirtualHostRoot' not in pp:
                        pp.append('/')
                    pp.reverse()
                try:
                    int(host.replace('.',''))
                    raise ValueError,  (
                        'IP addresses are not mappable: %s' % host)
                except ValueError:
                    pass
                if host[:2] == '*.':
                    host_map = sub_map
                    host = host[2:]
                else:
                    host_map = fixed_map
                hostname, port = (host.split( ':', 1) + [None])[:2]
                if hostname not in host_map:
                    host_map[hostname] = {}
                host_map[hostname][port] = pp
            except 'LineError', msg:
                line = '%s #! %s' % (line, msg)
            new_lines.append(line)
        self.lines = tuple(new_lines)
        self.have_map = not not (fixed_map or sub_map) # booleanize
        if RESPONSE is not None:
            RESPONSE.redirect(
                'manage_edit?manage_tabs_message=Changes%20Saved.')

    def addToContainer(self, container):
        container._setObject(self.id, self)

    def manage_addToContainer(self, container, nextURL=''):
        self.addToContainer(container)
        if nextURL:
            return MessageDialog(title='Item Added',
              message='This object now has a %s' % self.meta_type,
              action=nextURL)

    def manage_beforeDelete(self, item, container):
        if item is self:
            unregisterBeforeTraverse(container, self.meta_type)

    def manage_afterAdd(self, item, container):
        if item is self:
            if queryBeforeTraverse(container,
                                                  self.meta_type):
                raise BadRequest, ('This container already has a %s' %
                                   self.meta_type)
            id = self.id
            if callable(id): id = id()

            # We want the original object, not stuff in between
            container = container.this()
            hook = NameCaller(id)
            registerBeforeTraverse(container, hook,
                                                  self.meta_type,
                                                  self.priority)

    def __call__(self, client, request, response=None):
        '''Traversing at home'''
        vh_used = 0
        stack = request['TraversalRequestNameStack']
        path = None
        while 1:
            if stack and stack[-1] == 'VirtualHostBase':
                vh_used = 1
                stack.pop()
                protocol = stack.pop()
                host = stack.pop()
                if ':' in host:
                    host, port = host.split(':')
                    request.setServerURL(protocol, host, port)
                else:
                    request.setServerURL(protocol, host)
                path = list(stack)

            # Find and convert VirtualHostRoot directive
            # If it is followed by one or more path elements that each
            # start with '_vh_', use them to construct the path to the
            # virtual root.
            vh = -1
            for ii in range(len(stack)):
                if stack[ii] == 'VirtualHostRoot':
                    vh_used = 1
                    pp = ['']
                    at_end = (ii == len(stack) - 1)
                    if vh >= 0:
                        for jj in range(vh, ii):
                            pp.insert(1, stack[jj][4:])
                        stack[vh:ii + 1] = ['/'.join(pp), self.id]
                        ii = vh + 1
                    elif ii > 0 and stack[ii - 1][:1] == '/':
                        pp = stack[ii - 1].split('/')
                        stack[ii] = self.id
                    else:
                        stack[ii] = self.id
                        stack.insert(ii, '/')
                        ii += 1
                    path = stack[:ii]
                    # If the directive is on top of the stack, go ahead
                    # and process it right away.
                    if at_end:
                        request.setVirtualRoot(pp)
                        del stack[-2:]
                    break
                elif vh < 0 and stack[ii][:4] == '_vh_':
                    vh = ii

            if vh_used or not self.have_map:
                if path is not None:
                    path.reverse()
                    vh_part = ''
                    if path and path[0].startswith('/'):
                        vh_part = path.pop(0)[1:]
                    if vh_part:
                        request['VIRTUAL_URL_PARTS'] = vup = (
                            request['SERVER_URL'],
                            vh_part, quote('/'.join(path)))
                    else:
                        request['VIRTUAL_URL_PARTS'] = vup = (
                            request['SERVER_URL'], quote('/'.join(path)))
                    request['VIRTUAL_URL'] = '/'.join(vup)

                    # new ACTUAL_URL
                    add = (path and
                           request['ACTUAL_URL'].endswith('/')) and '/' or ''
                    request['ACTUAL_URL'] = request['VIRTUAL_URL'] + add

                return
            vh_used = 1 # Only retry once.
            # Try to apply the host map if one exists, and if no
            # VirtualHost directives were found.
            host = request['SERVER_URL'].split('://')[1].lower()
            hostname, port = (host.split( ':', 1) + [None])[:2]
            ports = self.fixed_map.get(hostname, 0)
            if not ports and self.sub_map:
                get = self.sub_map.get
                while hostname:
                    ports = get(hostname, 0)
                    if ports:
                        break
                    if '.' not in hostname:
                        return
                    hostname = hostname.split('.', 1)[1]
            if ports:
                pp = ports.get(port, 0)
                if pp == 0 and port is not None:
                    # Try default port
                    pp = ports.get(None, 0)
                if not pp:
                    return
                # If there was no explicit VirtualHostRoot, add one at the end
                if pp[0] == '/':
                    pp = pp[:]
                    pp.insert(1, self.id)
                stack.extend(pp)

    def __bobo_traverse__(self, request, name):
        '''Traversing away'''
        if name[:1] != '/':
            return getattr(self, name)
        parents = request.PARENTS
        parents.pop() # I don't belong there

        if len(name) > 1:
            request.setVirtualRoot(name)
        else:
            request.setVirtualRoot([])
        return parents.pop() # He'll get put back on

InitializeClass(VirtualHostMonster)


def manage_addVirtualHostMonster(self, id=None, REQUEST=None, **ignored):
    """ """
    container = self.this()
    vhm = VirtualHostMonster()
    container._setObject(vhm.getId(), vhm)

    if REQUEST is not None:
        goto = '%s/manage_main' % self.absolute_url()
        qs = 'manage_tabs_message=Virtual+Host+Monster+added.'
        REQUEST['RESPONSE'].redirect('%s?%s' % (goto, qs))

constructors = (
  ('manage_addVirtualHostMonster', manage_addVirtualHostMonster),
)
