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

__version__='$Revision$'[11:-2]

import Globals
from Persistence import Persistent
from string import join, strip
import re

defaultBindings = {'name_context': 'context',
                   'name_container': 'container',
                   'name_m_self': 'script',
                   'name_ns': '',
                   'name_subpath': 'traverse_subpath'}

_marker = []  # Create a new marker

class NameAssignments:
    # Note that instances of this class are intended to be immutable
    # and persistent but not inherit from ExtensionClass.

    _exprs = (('name_context',   'self._getContext()'),
              ('name_container', 'self._getContainer()'),
              ('name_m_self',    'self'),
              ('name_ns',        'self._getNamespace(caller_namespace, kw)'),
              ('name_subpath',   'self._getTraverseSubpath()'),
              )

    _isLegalName = re.compile('_$|[a-zA-Z][a-zA-Z0-9_]*$').match
    _asgns = {}

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, mapping):
        # mapping is presumably the REQUEST or compatible equivalent.
        # Note that we take care not to store expression texts in the ZODB.
        asgns = {}
        _isLegalName = self._isLegalName
        for name, expr in self._exprs:
            if mapping.has_key(name):
                assigned_name = strip(mapping[name])
                if not assigned_name:
                    continue
                if not _isLegalName(assigned_name):
                    raise ValueError, ('"%s" is not a valid variable name.'
                                       % assigned_name)
                asgns[name] = assigned_name
        self._asgns = asgns

    def isAnyNameAssigned(self):
        if len(self._asgns) > 0:
            return 1
        return 0

    def isNameAssigned(self, name):
        return self._asgns.has_key(name)

    def getAssignedName(self, name, default=_marker):
        val = self._asgns.get(name, default)
        if val is _marker:
            raise KeyError, name
        return val

    def getAssignedNames(self):
        # Returns a copy of the assigned names mapping
        return self._asgns.copy()

    def getAssignedNamesInOrder(self):
        # Returns the assigned names in the same order as that of
        # self._exprs.
        rval = []
        asgns = self._asgns
        for name, expr in self._exprs:
            if asgns.has_key(name):
                assigned_name = asgns[name]
                rval.append(assigned_name)
        return rval

    def _generateCodeBlock(self, bindtext, assigned_names):
        # Returns a tuple: exec-able code that can compute the value of
        # the bindings and eliminate clashing keyword arguments,
        # and the number of names bound.
        text = ['bound_data.append(%s)\n' % bindtext]
        for assigned_name in assigned_names:
            text.append('if kw.has_key("%s"):\n' % assigned_name)
            text.append('    del kw["%s"]\n'     % assigned_name)
        codetext = join(text, '')
        return (compile(codetext, '<string>', 'exec'), len(assigned_names))

    def _createCodeBlockForMapping(self):
        # Generates a code block which generates the "bound_data"
        # variable and removes excessive arguments from the "kw"
        # variable.  bound_data will be a mapping, for use as a
        # global namespace.
        exprtext = []
        assigned_names = []
        asgns = self._asgns
        for name, expr in self._exprs:
            if asgns.has_key(name):
                assigned_name = asgns[name]
                assigned_names.append(assigned_name)
                exprtext.append('"%s":%s,' % (assigned_name, expr))
        text = '{%s}' % join(exprtext, '')
        return self._generateCodeBlock(text, assigned_names)

    def _createCodeBlockForTuple(self, argNames):
        # Generates a code block which generates the "bound_data"
        # variable and removes excessive arguments from the "kw"
        # variable.  bound_data will be a tuple, for use as
        # positional arguments.
        assigned_names = []
        exprtext = []
        asgns = self._asgns
        for argName in argNames:
            passedLastBoundArg = 1
            for name, expr in self._exprs:
                # Provide a value for the available exprs.
                if asgns.has_key(name):
                    assigned_name = asgns[name]
                    if assigned_name == argName:
                        # The value for this argument will be filled in.
                        exprtext.append('%s,' % expr)
                        assigned_names.append(assigned_name)
                        passedLastBoundArg = 0
                        break
            if passedLastBoundArg:
                # Found last of bound args.
                break
        text = '(%s)' % join(exprtext, '')
        return self._generateCodeBlock(text, assigned_names)


class Bindings:
    
    __ac_permissions__ = (
        ('View management screens', ('getBindingAssignments',)),
        ('Change bindings', ('ZBindings_edit', 'ZBindings_setClient')),
        )

    _Bindings_client = None

    def ZBindings_edit(self, mapping):
        names = self._setupBindings(mapping)
        self._prepareBindCode()
        self._editedBindings()

    def ZBindings_setClient(self, clientname):
        '''Name the binding to be used as the "client".

        This is used by classes such as DTMLFile that want to
        choose an object on which to operate by default.'''
        self._Bindings_client = str(clientname)

    def _editedBindings(self):
        # Override to receive notification when the bindings are edited.
        pass

    def _setupBindings(self, names={}):
        self._bind_names = names = NameAssignments(names)
        return names

    def getBindingAssignments(self):
        if not hasattr(self, '_bind_names'):
            self._setupBindings()
        return self._bind_names

    def __before_publishing_traverse__(self, self2, request):
        path = request['TraversalRequestNameStack']
        names = self.getBindingAssignments()
        if (not names.isNameAssigned('name_subpath') or
            (path and hasattr(self.aq_explicit, path[-1])) ):
            return
        subpath = path[:]
        path[:] = []
        subpath.reverse()
        request.set('traverse_subpath', subpath)

    def _createBindCode(self, names):
        return names._createCodeBlockForMapping()
        
    def _prepareBindCode(self):
        # Creates:
        # - a code block that quickly generates "bound_data" and
        #   modifies the "kw" variable.
        # - a count of the bound arguments.
        # Saves them in _v_bindcode and _v_bindcount.
        # Returns .
        names = self.getBindingAssignments()
        if names.isAnyNameAssigned():
            bindcode, bindcount = self._createBindCode(names)
        else:
            bindcode, bindcount = None, 0
        self._v_bindcode = bindcode
        self._v_bindcount = bindcount
        return bindcode

    def _getBindCount(self):
        bindcount = getattr(self, '_v_bindcount', _marker)
        if bindcount is _marker:
            self._prepareBindCode()
            bindcount = self._v_bindcount
        return bindcount            

    def _getContext(self):
        # Utility for bindcode.
        while 1:
            self = self.aq_parent
            if not getattr(self, '_is_wrapperish', None):
                return self

    def _getContainer(self):
        # Utility for bindcode.
        while 1:
            self = self.aq_inner.aq_parent
            if not getattr(self, '_is_wrapperish', None):
                return self

    def _getTraverseSubpath(self):
        # Utility for bindcode.
        if hasattr(self, 'REQUEST'):
            return self.REQUEST.other.get('traverse_subpath', [])
        else:
            return []

    def _getNamespace(self, caller_namespace, kw):
        # Utility for bindcode.
        if caller_namespace is None:
            # Try to get the caller's namespace by scanning
            # the keyword arguments for an argument with the
            # same name as the assigned name for name_ns.
            names = self.getBindingAssignments()
            assigned_name = names.getAssignedName('name_ns')
            caller_namespace = kw.get(assigned_name, None)
        if caller_namespace is None:
            # Create an empty namespace.
            return self._Bindings_ns_class()
        return caller_namespace

    def __call__(self, *args, **kw):
        '''Calls the script.
        '''
        return self._bindAndExec(args, kw, None)

    def __render_with_namespace__(self, namespace):
        '''Calls the script with the specified namespace.'''
        namevals = {}
        # Try to find unbound parameters in the namespace, if the
        # namespace is bound.
        if self.getBindingAssignments().isNameAssigned('name_ns'):
            for name in self.func_code.co_varnames:
                try:
                    namevals[name] = namespace[name]
                except KeyError:
                    pass
        return self._bindAndExec((), namevals, namespace)

    render = __call__

    def _bindAndExec(self, args, kw, caller_namespace):
        '''Prepares the bound information and calls _exec(), possibly
        with a namespace.
        '''
        bindcode = getattr(self, '_v_bindcode', _marker)
        if bindcode is _marker:
            bindcode = self._prepareBindCode()
        bound_data = None
        if bindcode is not None:
            bound_data = []
            exec bindcode
            bound_data = bound_data[0]
        return self._exec(bound_data, args, kw)



