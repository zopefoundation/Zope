##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""Python Scripts Product

This product provides support for Script objects containing restricted
Python code.
"""

__version__='$Revision: 1.34 $'[11:-2]

import sys, os, traceback, re, marshal
from Globals import DTMLFile, MessageDialog, package_home
import AccessControl, OFS, RestrictedPython
from OFS.SimpleItem import SimpleItem
from DateTime.DateTime import DateTime
from urllib import quote
from webdav.Lockable import ResourceLockedError
from webdav.WriteLockInterface import WriteLockInterface
from Shared.DC.Scripts.Script import Script, BindingsUI, defaultBindings
from AccessControl import getSecurityManager
from OFS.History import Historical, html_diff
from OFS.Cache import Cacheable
from AccessControl import full_write_guard, safe_builtins
from AccessControl.ZopeGuards import guarded_getattr, guarded_getitem
from zLOG import LOG, ERROR, INFO, PROBLEM

# Track the Python bytecode version
import imp
Python_magic = imp.get_magic()
del imp

# This should only be incremented to force recompilation.
Script_magic = 2

manage_addPythonScriptForm = DTMLFile('www/pyScriptAdd', globals())
_default_file = os.path.join(package_home(globals()),
                             'www', 'default_py')

_marker = []  # Create a new marker object

def manage_addPythonScript(self, id, REQUEST=None, submit=None):
    """Add a Python script to a folder.
    """
    id = str(id)
    id = self._setObject(id, PythonScript(id))
    if REQUEST is not None:
        file = REQUEST.form.get('file', '')
        if type(file) is not type(''): file = file.read()
        if file:
            self._getOb(id).write(file)
        try: u = self.DestinationURL()
        except: u = REQUEST['URL1']
        if submit==" Add and Edit ": u="%s/%s" % (u,quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''


class PythonScript(Script, Historical, Cacheable):
    """Web-callable scripts written in a safe subset of Python.

    The function may include standard python code, so long as it does
    not attempt to use the "exec" statement or certain restricted builtins.
    """

    __implements__ = (WriteLockInterface,)
    meta_type='Script (Python)'
    _proxy_roles = ()

    _params = _body = ''
    errors = warnings = ()
    _v_change = 0

    manage_options = (
        {'label':'Edit',
         'action':'ZPythonScriptHTML_editForm',
         'help': ('PythonScripts', 'PythonScript_edit.stx')},
        ) + BindingsUI.manage_options + (
        {'label':'Test',
         'action':'ZScriptHTML_tryForm',
         'help': ('PythonScripts', 'PythonScript_test.stx')},
        {'label':'Proxy',
         'action':'manage_proxyForm',
         'help': ('OFSP','DTML-DocumentOrMethod_Proxy.stx')},
        ) + Historical.manage_options + SimpleItem.manage_options + \
        Cacheable.manage_options

    def __init__(self, id):
        self.id = id
        self.ZBindings_edit(defaultBindings)
        self._body = open(_default_file).read()

    security = AccessControl.ClassSecurityInfo()

    security.declareObjectProtected('View')
    security.declareProtected('View', '__call__')

    security.declareProtected('View management screens',
      'ZPythonScriptHTML_editForm', 'manage_main', 'read',
      'ZScriptHTML_tryForm', 'PrincipiaSearchSource',
      'document_src', 'params', 'body')

    ZPythonScriptHTML_editForm = DTMLFile('www/pyScriptEdit', globals())
    manage = manage_main = ZPythonScriptHTML_editForm
    ZPythonScriptHTML_editForm._setName('ZPythonScriptHTML_editForm')

    security.declareProtected('Change Python Scripts',
      'ZPythonScriptHTML_editAction',
      'ZPythonScript_setTitle', 'ZPythonScript_edit',
      'ZPythonScriptHTML_upload', 'ZPythonScriptHTML_changePrefs')
    def ZPythonScriptHTML_editAction(self, REQUEST, title, params, body):
        """Change the script's main parameters."""
        self.ZPythonScript_setTitle(title)
        self.ZPythonScript_edit(params, body)
        message = "Saved changes."
        return self.ZPythonScriptHTML_editForm(self, REQUEST,
                                               manage_tabs_message=message)

    def ZPythonScript_setTitle(self, title):
        title = str(title)
        if self.title != title:
            self.title = title
            self.ZCacheable_invalidate()

    def ZPythonScript_edit(self, params, body):
        self._validateProxy()
        if self.wl_isLocked():
            raise ResourceLockedError, "The script is locked via WebDAV."
        if type(body) is not type(''):
            body = body.read()
        if self._params <> params or self._body <> body or self._v_change:
            self._params = str(params)
            self.write(body)

    def ZPythonScriptHTML_upload(self, REQUEST, file=''):
        """Replace the body of the script with the text in file."""
        if self.wl_isLocked():
            raise ResourceLockedError, "The script is locked via WebDAV."
        if type(file) is not type(''): file = file.read()
        self.write(file)
        message = 'Saved changes.'
        return self.ZPythonScriptHTML_editForm(self, REQUEST,
                                               manage_tabs_message=message)

    def ZPythonScriptHTML_changePrefs(self, REQUEST, height=None, width=None,
                                      dtpref_cols='50', dtpref_rows='20'):
        """Change editing preferences."""
        szchh = {'Taller': 1, 'Shorter': -1, None: 0}
        szchw = {'Wider': 5, 'Narrower': -5, None: 0}
        try: rows = int(height)
        except: rows = max(1, int(dtpref_rows) + szchh.get(height, 0))
        try: cols = int(width)
        except: cols = max(40, int(dtpref_cols) + szchw.get(width, 0))
        e = (DateTime('GMT') + 365).rfc822()
        setc = REQUEST['RESPONSE'].setCookie
        setc('dtpref_rows', str(rows), path='/', expires=e)
        setc('dtpref_cols', str(cols), path='/', expires=e)
        REQUEST.form.update({'dtpref_cols': cols, 'dtpref_rows': rows})
        return apply(self.manage_main, (self, REQUEST), REQUEST.form)

    def ZScriptHTML_tryParams(self):
        """Parameters to test the script with."""
        param_names = []
        for name in self._params.split(','):
           
            name = name.strip()
            if name and name[0] != '*' and re.match('\w',name):
                param_names.append(name.split('=', 1)[0])
        return param_names

    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        return PythonScript.inheritedAttribute('manage_historyCompare')(
            self, rev1, rev2, REQUEST,
            historyComparisonResults=html_diff(rev1.read(), rev2.read()) )

    def __setstate__(self, state):
        Script.__setstate__(self, state)
        if (getattr(self, 'Python_magic', None) != Python_magic or
            getattr(self, 'Script_magic', None) != Script_magic):
            LOG(self.meta_type, PROBLEM,
                'Object "%s" needs to be recompiled.' % self.id)
            # Changes here won't get saved, unless this Script is edited.
            self._compile()
            self._v_change = 1
        elif self._code is None:
            self._v_f = None
        else:
            self._newfun(marshal.loads(self._code))

    def _compiler(self, *args):
        return RestrictedPython.compile_restricted_function(*args)
    def _compile(self):
        r = self._compiler(self._params, self._body or 'pass',
                           self.id, self.meta_type)
        code = r[0]
        errors = r[1]
        self.warnings = tuple(r[2])
        if errors:
            self._code = None
            self._v_f = None
            self._setFuncSignature((), (), 0)
            # Fix up syntax errors.
            filestring = '  File "<string>",'
            for i in range(len(errors)):
                line = errors[i]
                if line.startswith(filestring):
                    errors[i] = line.replace(filestring, '  Script', 1)
            self.errors = errors
            return

        self._code = marshal.dumps(code)
        self.errors = ()
        f = self._newfun(code)
        fc = f.func_code
        self._setFuncSignature(f.func_defaults, fc.co_varnames,
                               fc.co_argcount)
        self.Python_magic = Python_magic
        self.Script_magic = Script_magic
        self._v_change = 0

    def _newfun(self, code):
        g = {'__debug__': __debug__,
             '__builtins__': safe_builtins,
             '_getattr_': guarded_getattr,
             '_getitem_': guarded_getitem,
             '_write_': full_write_guard,
             '_print_': RestrictedPython.PrintCollector
             }
        l = {}
        exec code in g, l
        self._v_f = f = l.values()[0]
        return f

    def _makeFunction(self, dummy=0): # CMFCore.FSPythonScript uses dummy arg.
        self.ZCacheable_invalidate()
        self._compile()

    def _editedBindings(self):
        if getattr(self, '_v_f', None) is not None:
            self._makeFunction()

    def _exec(self, bound_names, args, kw):
        """Call a Python Script

        Calling a Python Script is an actual function invocation.
        """
        # Retrieve the value from the cache.
        keyset = None
        if self.ZCacheable_isCachingEnabled():
            # Prepare a cache key.
            keyset = kw.copy()
            asgns = self.getBindingAssignments()
            name_context = asgns.getAssignedName('name_context', None)
            if name_context:
                keyset[name_context] = self.aq_parent.getPhysicalPath()
            name_subpath = asgns.getAssignedName('name_subpath', None)
            if name_subpath:
                keyset[name_subpath] = self._getTraverseSubpath()
            # Note: perhaps we should cache based on name_ns also.
            keyset['*'] = args
            result = self.ZCacheable_get(keywords=keyset, default=_marker)
            if result is not _marker:
                # Got a cached value.
                return result

        __traceback_info__ = bound_names, args, kw, self.func_defaults

        f = self._v_f
        if f is None:
            raise RuntimeError, '%s %s has errors.' % (self.meta_type, self.id)
        if bound_names is not None:
            # Updating func_globals directly *should* be thread-safe.
            f.func_globals.update(bound_names)
    
        # Execute the function in a new security context.
        security=getSecurityManager()
        security.addContext(self)
        try:
            result = apply(f, args, kw)
            if keyset is not None:
                # Store the result in the cache.
                self.ZCacheable_set(result, keywords=keyset)
            return result
        finally:
            security.removeContext(self)

    def manage_haveProxy(self,r): return r in self._proxy_roles

    def _validateProxy(self, roles=None):
        if roles is None: roles=self._proxy_roles
        if not roles: return
        user=u=getSecurityManager().getUser()
        if user is not None:
            user=user.hasRole
            for r in roles:
                if r and not user(None, (r,)):
                    user=None
                    break
            if user is not None: return

        raise 'Forbidden', ('You are not authorized to change <em>%s</em> '
            'because you do not have proxy roles.\n<!--%s, %s-->' 
            % (self.id, u, roles))

    security.declareProtected('Change proxy roles',
      'manage_proxyForm', 'manage_proxy')

    manage_proxyForm = DTMLFile('www/pyScriptProxy', globals())
    def manage_proxy(self, roles=(), REQUEST=None):
        "Change Proxy Roles"
        self._validateProxy(roles)
        self._validateProxy()
        self.ZCacheable_invalidate()
        self._proxy_roles=tuple(roles)
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    security.declareProtected('Change Python Scripts',
      'PUT', 'manage_FTPput', 'write',
      'manage_historyCopy',
      'manage_beforeHistoryCopy', 'manage_afterHistoryCopy')

    def PUT(self, REQUEST, RESPONSE):
        """ Handle HTTP PUT requests """
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        self.write(REQUEST.get('BODY', ''))
        RESPONSE.setStatus(204)
        return RESPONSE        

    manage_FTPput = PUT

    def write(self, text):
        """ Change the Script by parsing a read()-style source text. """
        self._validateProxy()
        mdata = self._metadata_map()
        bindmap = self.getBindingAssignments().getAssignedNames()
        bup = 0

        st = 0
        try:
            while 1:
                # Find the next non-empty line
                m = _nonempty_line.search(text, st)
                if not m:
                    # There were no non-empty body lines
                    body = ''
                    break
                line = m.group(0).strip()
                if line[:2] != '##':
                    # We have found the first line of the body
                    body = text[m.start(0):]
                    break

                st = m.end(0)
                # Parse this header line
                if len(line) == 2 or line[2] == ' ' or '=' not in line:
                    # Null header line
                    continue
                k, v = line[2:].split('=', 1)
                k = k.strip().lower()
                v = v.strip()
                if not mdata.has_key(k):
                    SyntaxError, 'Unrecognized header line "%s"' % line
                if v == mdata[k]:
                    # Unchanged value
                    continue

                # Set metadata value
                if k == 'title':
                    self.title = v
                elif k == 'parameters':
                    self._params = v
                elif k[:5] == 'bind ':
                    bindmap[_nice_bind_names[k[5:]]] = v
                    bup = 1

            body = body.rstrip()
            if body:
                body = body + '\n'
            if body != self._body:
                self._body = body
            if bup:
                self._setupBindings(bindmap)

            if self._p_changed:
                self._makeFunction()
        except:
            LOG(self.meta_type, ERROR, 'write failed', error=sys.exc_info())
            raise

    def manage_FTPget(self):
        "Get source for FTP download"
        self.REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

    def _metadata_map(self):
        m = {
            'title': self.title,
            'parameters': self._params,
           }
        bindmap = self.getBindingAssignments().getAssignedNames()
        for k, v in _nice_bind_names.items():
            m['bind '+k] = bindmap.get(v, '')
        return m

    def read(self):
        """ Generate a text representation of the Script source.

        Includes specially formatted comment lines for parameters,
        bindings, and the title.
        """
        # Construct metadata header lines, indented the same as the body.
        m = _first_indent.search(self._body)
        if m: prefix = m.group(0) + '##'
        else: prefix = '##'

        hlines = ['%s %s "%s"' % (prefix, self.meta_type, self.id)]
        mm = self._metadata_map().items()
        mm.sort()
        for kv in mm: 
            hlines.append('%s=%s' % kv)
        if self.errors:
            hlines.append('')
            hlines.append(' Errors:')
            for line in self.errors:
                hlines.append('  ' + line)
        if self.warnings:
            hlines.append('')
            hlines.append(' Warnings:')
            for line in self.warnings:
                hlines.append('  ' + line)
        hlines.append('')
        return ('\n' + prefix).join(hlines) + '\n' + self._body

    def params(self): return self._params
    def body(self): return self._body
    def get_size(self): return len(self._body)
    getSize = get_size

    def PrincipiaSearchSource(self):
        "Support for searching - the document's contents are searched."
        return "%s\n%s" % (self._params, self._body)

    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return unprocessed document source."""

        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

_first_indent = re.compile('(?m)^ *(?! |$)')
_nonempty_line = re.compile('(?m)^(.*\S.*)$')

_nice_bind_names = {'context': 'name_context', 'container': 'name_container',
                    'script': 'name_m_self', 'namespace': 'name_ns',
                    'subpath': 'name_subpath'}
