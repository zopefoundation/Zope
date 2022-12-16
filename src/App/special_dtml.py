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

import os
from logging import getLogger

import DocumentTemplate
import MethodObject
import Persistence
import Zope2
from AccessControl import getSecurityManager
from Acquisition import Explicit
from Acquisition import aq_acquire
from Acquisition import aq_inner
from Acquisition import aq_parent
from App import Common
from App.config import getConfiguration
from ComputedAttribute import ComputedAttribute
from DocumentTemplate import OLD_DEFAULT_ENCODING
from DocumentTemplate._DocumentTemplate import InstanceDict
from DocumentTemplate._DocumentTemplate import TemplateDict
from DocumentTemplate._DocumentTemplate import render_blocks
from DocumentTemplate.DT_String import DTReturn
from DocumentTemplate.DT_String import _marker
from Shared.DC.Scripts.Bindings import Bindings


LOG = getLogger('special_dtml')

PREFIX = os.path.realpath(
    os.path.join(os.path.dirname(Zope2.__file__), os.path.pardir)
)


class Code:
    pass


class HTML(DocumentTemplate.HTML, Persistence.Persistent):
    "Persistent HTML Document Templates"


class ClassicHTMLFile(DocumentTemplate.HTMLFile, MethodObject.Method):
    "Persistent HTML Document Templates read from files"

    __code__ = Code()
    __code__.co_varnames = 'trueself', 'self', 'REQUEST'
    __code__.co_argcount = 3
    __defaults__ = None

    _need__name__ = 1
    _v_last_read = 0

    def __init__(self, name, _prefix=None, **kw):
        if _prefix is None:
            _prefix = PREFIX
        elif not isinstance(_prefix, str):
            _prefix = Common.package_home(_prefix)
        args = (self, os.path.join(_prefix, name + '.dtml'))
        if '__name__' not in kw:
            kw['__name__'] = os.path.split(name)[-1]
        ClassicHTMLFile.inheritedAttribute('__init__')(*args, **kw)

    def _cook_check(self):
        if getConfiguration().debug_mode:
            __traceback_info__ = self.raw
            try:
                mtime = os.stat(self.raw)[8]
            except Exception:
                mtime = 0
            if mtime != self._v_last_read:
                self.cook()
                self._v_last_read = mtime
        elif not hasattr(self, '_v_cooked'):
            try:
                changed = self.__changed__()
            except Exception:
                changed = 1
            self.cook()
            if not changed:
                self.__changed__(0)

    def _setName(self, name):
        self.__name__ = name
        self._need__name__ = 0

    def __call__(self, *args, **kw):
        self._cook_check()
        return HTMLFile.inheritedAttribute('__call__')(
            *(self,) + args[1:], **kw)


defaultBindings = {'name_context': 'context',
                   'name_container': 'container',
                   'name_m_self': 'self',
                   'name_ns': 'caller_namespace',
                   'name_subpath': 'traverse_subpath'}


class DTMLFile(Bindings, Explicit, ClassicHTMLFile):
    "HTMLFile with bindings and support for __render_with_namespace__"

    __code__ = None
    __defaults__ = None
    _need__name__ = 1

    _Bindings_ns_class = TemplateDict

    def _get__roles__(self):
        imp = getattr(aq_parent(aq_inner(self)),
                      '%s__roles__' % self.__name__)
        if hasattr(imp, '__of__'):
            return imp.__of__(self)
        return imp

    __roles__ = ComputedAttribute(_get__roles__, 1)

    # By default, we want to look up names in our container.
    _Bindings_client = 'container'

    def __init__(self, name, _prefix=None, **kw):
        self.ZBindings_edit(defaultBindings)
        self._setFuncSignature()
        DTMLFile.inheritedAttribute('__init__')(self, name, _prefix, **kw)

    def getOwner(self, info=0):
        '''
        This method is required of all objects that go into
        the security context stack.
        '''
        return None

    def _exec(self, bound_data, args, kw):
        # Cook if we haven't already
        self._cook_check()

        # If this object has no encoding set, we use the old default
        encoding = getattr(self, 'encoding', OLD_DEFAULT_ENCODING)

        # Get our caller's namespace, and set up our own.
        cns = bound_data['caller_namespace']
        ns = self._Bindings_ns_class()
        push = ns._push
        ns.guarded_getattr = None
        ns.guarded_getitem = None

        req = None
        kw_bind = kw
        if cns:
            # Someone called us.
            push(cns)
            ns.level = cns.level + 1
            ns.this = getattr(cns, 'this', None)
            # Get their bindings.  Copy the request reference
            # forward, and include older keyword arguments in the
            # current 'keyword_args' binding.
            try:
                last_bound = ns[('current bindings',)]
                last_req = last_bound.get('REQUEST', None)
                if last_req:
                    bound_data['REQUEST'] = last_req
                old_kw = last_bound['keyword_args']
                if old_kw:
                    kw_bind = old_kw.copy()
                    kw_bind.update(kw)
            except Exception:
                pass
        else:
            # We're first, so get the REQUEST.
            try:
                req = aq_acquire(self, 'REQUEST')
                if hasattr(req, 'taintWrapper'):
                    req = req.taintWrapper()
            except Exception:
                pass
            bound_data['REQUEST'] = req
            ns.this = bound_data['context']
        # Bind 'keyword_args' to the complete set of keyword arguments.
        bound_data['keyword_args'] = kw_bind

        # Push globals, initialized variables, REQUEST (if any),
        # and keyword arguments onto the namespace stack

        for nsitem in (self.globals, self._vars, req, kw):
            if nsitem:
                push(nsitem)

        # Push the 'container' (default), 'context', or nothing.
        bind_to = self._Bindings_client
        if bind_to in ('container', 'client'):
            push(InstanceDict(bound_data[bind_to], ns))

        # Push the name bindings, and a reference to grab later.
        push(bound_data)
        push({('current bindings',): bound_data})

        security = getSecurityManager()
        security.addContext(self)

        # Set a content type to override the publisher default "text/plain"
        # This class is only used in the Zope ZMI so it's safe to assume
        # that it is rendering HTML.
        if 'REQUEST' in bound_data:
            response = bound_data['REQUEST'].RESPONSE
            if not response.getHeader('Content-Type'):
                response.setHeader('Content-Type', 'text/html')

        try:
            value = self.ZDocumentTemplate_beforeRender(ns, _marker)
            if value is _marker:
                try:
                    result = render_blocks(self._v_blocks, ns,
                                           encoding=encoding)
                except DTReturn as v:
                    result = v.v

                self.ZDocumentTemplate_afterRender(ns, result)
                return result
            else:
                return value
        finally:
            security.removeContext(self)
            # Clear the namespace, breaking circular references.
            while len(ns):
                ns._pop()
    from Shared.DC.Scripts.Signature import _setFuncSignature


HTMLFile = ClassicHTMLFile
