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

__version__='$Revision: 1.3 $'[11:-2]

import sys, os, traceback, re
from Globals import MessageDialog, HTMLFile, package_home
import AccessControl, OFS, Guarded
from OFS.SimpleItem import SimpleItem
from DateTime.DateTime import DateTime
from string import join, strip, rstrip, split, replace, lower
from urllib import quote
from Bindings import Bindings, defaultBindings
from Script import Script
from AccessControl import getSecurityManager
from OFS.History import Historical, html_diff
from zLOG import LOG, ERROR, INFO

_www = os.path.join(package_home(globals()), 'www')
manage_addPythonScriptForm=HTMLFile('pyScriptAdd', _www)

def manage_addPythonScript(self, id, REQUEST=None):
    """Add a Python script to a folder.
    """
    id = str(id)
    id = self._setObject(id, PythonScript(id))
    if REQUEST is not None:
        file = REQUEST.form.get('file', None)
        if file:
            if type(file) is not type(''): file = file.read()
            getattr(self, id).write(file)
        try: u = self.DestinationURL()
        except: u = REQUEST['URL1']
        REQUEST.RESPONSE.redirect('%s/%s/manage_main' % (u, quote(id)))
    return ''


class PythonScript(Script, Historical):
    """Web-callable scripts written in a safe subset of Python.

    The function may include standard python code, so long as it does
    not attempt to use the "exec" statement or certain restricted builtins.
    """

    meta_type='Python Script'
    _proxy_roles = ()

    _params = _body = ''

    manage_options = (
        {'label':'Edit', 'action':'ZPythonScriptHTML_editForm'},
        {'label':'Upload', 'action':'ZPythonScriptHTML_uploadForm'},
        ) + Bindings.manage_options + (
        {'label':'Try It', 'action':'ZScriptHTML_tryForm'},
        {'label':'Proxy', 'action':'manage_proxyForm'},
        ) + Historical.manage_options + SimpleItem.manage_options 

    __ac_permissions__ = (
        ('View management screens',
          ('ZPythonScriptHTML_editForm', 'ZPythonScript_changePrefs',
           'manage_main', 'ZScriptHTML_tryForm', 'read')),
        ('Change Python Scripts',
          ('ZPythonScript_edit', 'PUT', 'manage_FTPput', 'write',
           'ZPythonScript_setTitle', 'ZPythonScriptHTML_upload',
           'ZPythonScriptHTML_uploadForm', 'manage_historyCopy',
           'manage_beforeHistoryCopy', 'manage_afterHistoryCopy')),
        ('Change proxy roles', ('manage_proxyForm', 'manage_proxy')),
        ('View', ('__call__','','ZPythonScriptHTML_tryAction')),
        )

    def __init__(self, id):
        self.id = id
        self.ZBindings_edit(defaultBindings)
        self._makeFunction(1)

    ZPythonScriptHTML_editForm = HTMLFile('pyScriptEdit', _www)
    manage = manage_main = ZPythonScriptHTML_editForm
    manage_proxyForm = HTMLFile('pyScriptProxy', _www)
    ZScriptHTML_tryForm = HTMLFile('scriptTry', _www)
    ZPythonScriptHTML_uploadForm = HTMLFile('pyScriptUpload', _www)

    def ZPythonScriptHTML_editAction(self, REQUEST, title, params, body):
        """Change the script's main parameters."""
        self.ZPythonScript_setTitle(title)
        self.ZPythonScript_edit(params, body)
        message = "Content changed."
        if getattr(self, '_v_warnings', None):
            message = ("<strong>Warning:</strong> <i>%s</i>" 
                       % join(self._v_warnings, '<br>'))
        return self.ZPythonScriptHTML_editForm(self, REQUEST,
                                               manage_tabs_message=message)

    def ZPythonScript_setTitle(self, title):
        self.title = str(title)

    def ZPythonScript_edit(self, params, body):
        self._validateProxy()
        if type(body) is not type(''):
            body = body.read()
        if self._params <> params or self._body <> body:
            self._params = str(params)
            self._body = rstrip(body)
            self._makeFunction(1)

    def ZPythonScriptHTML_upload(self, REQUEST, file=''):
        """Replace the body of the script with the text in file."""
        if type(file) is not type(''): file = file.read()
        self.write(file)
        message = 'Content changed.'
        return self.ZPythonScriptHTML_editForm(self, REQUEST,
                                               manage_tabs_message=message)

    def ZScriptHTML_tryParams(self):
        """Parameters to test the script with."""
        param_names = []
        for name in split(self._params, ','):
            name = strip(name)
            if name and name[0] != '*':
                param_names.append(name)
        return param_names

    def ZPythonScriptHTML_changePrefs(self, REQUEST, height=None, width=None,
                                      dtpref_cols='50', dtpref_rows='20'):
        """Change editing preferences."""
        LOG('PythonScript', INFO, 'Change prefs h: %s, w: %s, '
            'cols: %s, rows: %s' % (height, width, dtpref_cols, dtpref_rows)) 
        szchh = {'Taller': 1, 'Shorter': -1, None: 0}
        szchw = {'Wider': 5, 'Narrower': -5, None: 0}
        try: rows = int(height)
        except: rows = max(1, int(dtpref_rows) + szchh.get(height, 0))
        try: cols = int(width)
        except: cols = max(40, int(dtpref_cols) + szchw.get(width, 0))
        LOG('PythonScript', INFO, 'to cols: %s, rows: %s' % (cols, rows))
        e = (DateTime('GMT') + 365).rfc822()
        setc = REQUEST['RESPONSE'].setCookie
        setc('dtpref_rows', str(rows), path='/', expires=e)
        setc('dtpref_cols', str(cols), path='/', expires=e)
        REQUEST.form.update({'dtpref_cols': cols, 'dtpref_rows': rows})
        return apply(self.manage_main, (self, REQUEST), REQUEST.form)

    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        return PythonScript.inheritedAttribute('manage_historyCompare')(
            self, rev1, rev2, REQUEST,
            historyComparisonResults=html_diff(rev1.read(), rev2.read()) )

    def _checkCBlock(self, MakeBlock):
        params = self._params
        body = self._body or ' pass'
        # If the body isn't indented, indent it one space.
        nbc = re.search('\S', body).start()
        if nbc and body[nbc - 1] in ' \t':
            defblk = 'def f(%s):\n%s\n' % (params, body)
        else:
            # Waaa: triple-quoted strings will get indented too.
            defblk = 'def f(%s):\n %s\n' % (params, replace(body, '\n', '\n '))

        blk = MakeBlock(defblk, self.id, self.meta_type)
        self._v_errors, self._v_warnings = blk.errors, blk.warnings
        if blk.errors:
            if hasattr(self, '_v_f'): del self._v_f
            self._setFuncSignature((), (), 0)
        else:
            self._t = blk.t

    def _newfun(self, allowSideEffect, g, **kws):
        from Guarded import UntupleFunction
        self._v_f = f = apply(UntupleFunction, (self._t, g), kws)
        if allowSideEffect:
            fc = f.func_code
            self._setFuncSignature(f.func_defaults, fc.co_varnames,
                                   fc.co_argcount)
        return f

    def _makeFunction(self, allowSideEffect=0):
        from Guarded import GuardedBlock, theGuard, safebin
        from Guarded import WriteGuard, ReadGuard
        if allowSideEffect:
            self._checkCBlock(GuardedBlock)
        if getattr(self, '_v_errors', None):
            raise "Python Script Error", ('<pre>%s</pre>' %
                                          join(self._v_errors, '\n') )
        return self._newfun(allowSideEffect, {'$guard': theGuard,
                                              '$write_guard': WriteGuard,
                                              '$read_guard': ReadGuard},
                            __builtins__=safebin)

    def _editedBindings(self):
        f = getattr(self, '_v_f', None)
        if f is None:
            return
        self._makeFunction(1)

    def _exec(self, globals, args, kw):
        """Call a Python Script

        Calling a Python Script is an actual function invocation.
        """
        f = getattr(self, '_v_f', None)
        if f is None:
            f = self._makeFunction()

        __traceback_info__ = globals, args, kw, self.func_defaults

        if globals is not None:
            # Updating func_globals directly *should* be thread-safe.
            f.func_globals.update(globals)
    
        security=getSecurityManager()
        security.addContext(self)
        try:
            return apply(f, args, kw)
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

    def manage_proxy(self, roles=(), REQUEST=None):
        "Change Proxy Roles"
        self._validateProxy(roles)
        self._validateProxy()
        self._proxy_roles=tuple(roles)
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def PUT(self, REQUEST, RESPONSE):
        """ Handle HTTP PUT requests """
        self.dav__init(REQUEST, RESPONSE)
        self.write(REQUEST.get('BODY', ''))
        RESPONSE.setStatus(204)
        return RESPONSE        

    manage_FTPput = PUT

    def write(self, text):
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
                line = strip(m.group(0))
                if line[:2] != '##':
                    # We have found the first line of the body
                    body = text[m.start(0):]
                    break

                st = m.end(0)
                # Parse this header line
                if len(line) == 2 or line[2] == ' ' or '=' not in line:
                    # Null header line
                    continue
                k, v = split(line[2:], '=', 1)
                k = lower(strip(k))
                v = strip(v)
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

            self._body = rstrip(body)
            if bup:
                self._setupBindings(bindmap)
            self._makeFunction(1)
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
        # Construct metadata header lines, indented the same as the body.
        m = _first_indent.search(self._body)
        if m: prefix = m.group(0) + '##'
        else: prefix = '##'

        hlines = ['%s %s "%s"' % (prefix, self.meta_type, self.id)]
        mm = self._metadata_map().items()
        mm.sort()
        for kv in mm: 
            hlines.append('%s=%s' % kv)
        hlines.append('')
        return join(hlines, '\n' + prefix) + '\n' + self._body

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
