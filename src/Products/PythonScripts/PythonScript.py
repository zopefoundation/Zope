##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Python Scripts Product

This product provides support for Script objects containing restricted
Python code.

$Id$
"""

from logging import getLogger
import marshal
import new
import os
import re
import sys
import traceback
from urllib import quote

from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import requestmethod
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.ZopeGuards import get_safe_globals, guarded_getattr
from AccessControl.ZopeGuards import get_safe_globals, guarded_getattr
from Acquisition import aq_parent
from App.Common import package_home
from App.Dialogs import MessageDialog
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from OFS.Cache import Cacheable
from OFS.History import Historical
from OFS.History import html_diff
from OFS.SimpleItem import SimpleItem
from RestrictedPython import compile_restricted_function
from Shared.DC.Scripts.Script import BindingsUI
from Shared.DC.Scripts.Script import defaultBindings
from Shared.DC.Scripts.Script import Script
from webdav.Lockable import ResourceLockedError
from zExceptions import Forbidden

LOG = getLogger('PythonScripts')

# Track the Python bytecode version
import imp
Python_magic = imp.get_magic()
del imp

# This should only be incremented to force recompilation.
Script_magic = 3
_log_complaint = (
    'Some of your Scripts have stale code cached.  Since Zope cannot'
    ' use this code, startup will be slightly slower until these Scripts'
    ' are edited. You can automatically recompile all Scripts that have'
    ' this problem by visiting /manage_addProduct/PythonScripts/recompile'
    ' of your server in a browser.')

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
        if not file:
            file = open(_default_file).read()
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
        self._makeFunction()

    security = ClassSecurityInfo()

    security.declareObjectProtected('View')
    security.declareProtected('View', '__call__')

    security.declareProtected('View management screens',
      'ZPythonScriptHTML_editForm', 'manage_main', 'read',
      'ZScriptHTML_tryForm', 'PrincipiaSearchSource',
      'document_src', 'params', 'body', 'get_filepath')

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

        if type(file) is not type(''):
            if not file: raise ValueError, 'File not specified'
            file = file.read()

        self.write(file)
        message = 'Saved changes.'
        return self.ZPythonScriptHTML_editForm(self, REQUEST,
                                               manage_tabs_message=message)

    def ZPythonScriptHTML_changePrefs(self, REQUEST, height=None, width=None,
                                      dtpref_cols="100%", dtpref_rows="20"):
        """Change editing preferences."""
        dr = {"Taller":5, "Shorter":-5}.get(height, 0)
        dc = {"Wider":5, "Narrower":-5}.get(width, 0)
        if isinstance(height, int): dtpref_rows = height
        if isinstance(width, int) or \
           isinstance(width, str) and width.endswith('%'):
            dtpref_cols = width
        rows = str(max(1, int(dtpref_rows) + dr))
        cols = str(dtpref_cols)
        if cols.endswith('%'):
           cols = str(min(100, max(25, int(cols[:-1]) + dc))) + '%'
        else:
           cols = str(max(35, int(cols) + dc))
        e = (DateTime("GMT") + 365).rfc822()
        setCookie = REQUEST["RESPONSE"].setCookie
        setCookie("dtpref_rows", rows, path='/', expires=e)
        setCookie("dtpref_cols", cols, path='/', expires=e)
        REQUEST.other.update({"dtpref_cols":cols, "dtpref_rows":rows})
        return self.manage_main(self, REQUEST)

    def ZScriptHTML_tryParams(self):
        """Parameters to test the script with."""
        param_names = []
        for name in self._params.split(','):

            name = name.strip()
            if name and name[0] != '*' and re.match('\w',name):
                param_names.append(name.split('=', 1)[0].strip())
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
            global _log_complaint
            if _log_complaint:
                LOG.info(_log_complaint)
                _log_complaint = 0
            # Changes here won't get saved, unless this Script is edited.
            body = self._body.rstrip()
            if body:
                self._body = body + '\n'
            self._compile()
            self._v_change = 1
        elif self._code is None:
            self._v_ft = None
        else:
            self._newfun(marshal.loads(self._code))

    def _compiler(self, *args, **kw):
        return compile_restricted_function(*args, **kw)

    def _compile(self):
        bind_names = self.getBindingAssignments().getAssignedNamesInOrder()
        r = self._compiler(self._params, self._body or 'pass',
                           self.id, self.meta_type,
                           globalize=bind_names)
        code = r[0]
        errors = r[1]
        self.warnings = tuple(r[2])
        if errors:
            self._code = None
            self._v_ft = None
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
        g = get_safe_globals()
        g['_getattr_'] = guarded_getattr
        g['__debug__'] = __debug__
        # it doesn't really matter what __name__ is, *but*
        # - we need a __name__
        #   (see testPythonScript.TestPythonScriptGlobals.test__name__)
        # - it should not contain a period, so we can't use the id
        #   (see https://bugs.launchpad.net/zope2/+bug/142731/comments/4)
        # - with Python 2.6 it should not be None
        #   (see testPythonScript.TestPythonScriptGlobals.test_filepath)
        g['__name__'] = 'script'

        l = {}
        exec code in g, l
        f = l.values()[0]
        self._v_ft = (f.func_code, g, f.func_defaults or ())
        return f

    def _makeFunction(self):
        self.ZCacheable_invalidate()
        self._compile()
        if not (aq_parent(self) is None or hasattr(self, '_filepath')):
            # It needs a _filepath, and has an acquisition wrapper.
            self._filepath = self.get_filepath()

    def _editedBindings(self):
        if getattr(self, '_v_ft', None) is not None:
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
                keyset[name_context] = aq_parent(self).getPhysicalPath()
            name_subpath = asgns.getAssignedName('name_subpath', None)
            if name_subpath:
                keyset[name_subpath] = self._getTraverseSubpath()
            # Note: perhaps we should cache based on name_ns also.
            keyset['*'] = args
            result = self.ZCacheable_get(keywords=keyset, default=_marker)
            if result is not _marker:
                # Got a cached value.
                return result

        #__traceback_info__ = bound_names, args, kw, self.func_defaults

        ft = self._v_ft
        if ft is None:
            __traceback_supplement__ = (
                PythonScriptTracebackSupplement, self)
            raise RuntimeError, '%s %s has errors.' % (self.meta_type, self.id)

        fcode, g, fadefs = ft
        g = g.copy()
        if bound_names is not None:
            g.update(bound_names)
        g['__traceback_supplement__'] = (
            PythonScriptTracebackSupplement, self, -1)
        g['__file__'] = getattr(self, '_filepath', None) or self.get_filepath()
        f = new.function(fcode, g, None, fadefs)

        try:
            result = f(*args, **kw)
        except SystemExit:
            raise ValueError('SystemExit cannot be raised within a PythonScript')

        if keyset is not None:
            # Store the result in the cache.
            self.ZCacheable_set(result, keywords=keyset)
        return result

    def manage_afterAdd(self, item, container):
        if item is self:
            self._filepath = self.get_filepath()

    def manage_beforeDelete(self, item, container):
        # shut up deprecation warnings
        pass

    def manage_afterClone(self, item):
        # shut up deprecation warnings
        pass

    def get_filepath(self):
        return self.meta_type + ':' + '/'.join(self.getPhysicalPath())

    def manage_haveProxy(self,r): return r in self._proxy_roles

    def _validateProxy(self, roles=None):
        if roles is None: roles = self._proxy_roles
        if not roles: return
        user = getSecurityManager().getUser()
        if user is not None and user.allowed(self, roles):
            return
        raise Forbidden, ('You are not authorized to change <em>%s</em> '
            'because you do not have proxy roles.\n<!--%s, %s-->'
            % (self.id, user, roles))

    security.declareProtected('Change proxy roles',
      'manage_proxyForm', 'manage_proxy')

    manage_proxyForm = DTMLFile('www/pyScriptProxy', globals())
    @requestmethod('POST')
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
                    raise SyntaxError, 'Unrecognized header line "%s"' % line
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
                self.ZBindings_edit(bindmap)
            else:
                self._makeFunction()
        except:
            LOG.error('write failed', exc_info=sys.exc_info())
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
    def get_size(self): return len(self.read())
    getSize = get_size

    def PrincipiaSearchSource(self):
        "Support for searching - the document's contents are searched."
        return "%s\n%s" % (self._params, self._body)

    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return unprocessed document source."""

        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()


InitializeClass(PythonScript)

class PythonScriptTracebackSupplement:
    """Implementation of ITracebackSupplement"""
    def __init__(self, script, line=0):
        self.object = script
        # If line is set to -1, it means to use tb_lineno.
        self.line = line


_first_indent = re.compile('(?m)^ *(?! |$)')
_nonempty_line = re.compile('(?m)^(.*\S.*)$')

_nice_bind_names = {'context': 'name_context', 'container': 'name_container',
                    'script': 'name_m_self', 'namespace': 'name_ns',
                    'subpath': 'name_subpath'}
