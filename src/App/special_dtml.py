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
import sys
from logging import getLogger
from types import InstanceType
from zope import interface
from zope.location.interfaces import IContained

import DocumentTemplate
import MethodObject
import Persistence
from App import Common
from App.config import getConfiguration
from ExtensionClass import Base
from ZPublisher import getRequest

LOG = getLogger('special_dtml')

import Zope2
PREFIX = os.path.realpath(
    os.path.join(os.path.dirname(Zope2.__file__), os.path.pardir)
    )


class HTML(DocumentTemplate.HTML,Persistence.Persistent,):
    "Persistent HTML Document Templates"

class ClassicHTMLFile(DocumentTemplate.HTMLFile,MethodObject.Method,):
    "Persistent HTML Document Templates read from files"

    class func_code: pass
    func_code=func_code()
    func_code.co_varnames='trueself', 'self', 'REQUEST'
    func_code.co_argcount=3
    _need__name__=1
    _v_last_read=0

    def __init__(self, name, _prefix=None, **kw):
        if _prefix is None:
            _prefix = getattr(getConfiguration(), 'softwarehome', PREFIX)
        elif type(_prefix) is not type(''):
            _prefix = Common.package_home(_prefix)
        args=(self, os.path.join(_prefix, name + '.dtml'))
        if not kw.has_key('__name__'):
            kw['__name__'] = os.path.split(name)[-1]
        apply(ClassicHTMLFile.inheritedAttribute('__init__'), args, kw)

    def _cook_check(self):
        if getConfiguration().debug_mode:
            __traceback_info__=self.raw
            try:    mtime=os.stat(self.raw)[8]
            except: mtime=0
            if mtime != self._v_last_read:
                self.cook()
                self._v_last_read=mtime
        elif not hasattr(self,'_v_cooked'):
            try: changed=self.__changed__()
            except: changed=1
            self.cook()
            if not changed: self.__changed__(0)

    def _setName(self, name):
        self.__name__ = name
        self._need__name__ = 0

    def __call__(self, *args, **kw):
        self._cook_check()
        return apply(HTMLFile.inheritedAttribute('__call__'),
                     (self,)+args[1:],kw)

defaultBindings = {'name_context': 'context',
                   'name_container': 'container',
                   'name_m_self': 'self',
                   'name_ns': 'caller_namespace',
                   'name_subpath': 'traverse_subpath'}

from Shared.DC.Scripts.Bindings import Bindings
from Acquisition import Explicit, Implicit
from DocumentTemplate.DT_String import _marker, DTReturn, render_blocks
from DocumentTemplate.DT_Util import TemplateDict, InstanceDict
from AccessControl import getSecurityManager


_marker = object()

class AqWrapper(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __getitem__(self, name, default=None):
        if name == 'REQUEST':
            return self.request

        seen = set()

        ob = self.context
        while ob is not None or ob not in seen:
            try:
                attr = ob[name]
                if attr is not None:
                    return attr
            except:
                pass

            attr = getattr(ob, name, _marker)
            if attr is not _marker:
                return attr

            seen.add(ob)
            ob = getattr(ob, '__parent__', None)

        raise KeyError(name)

    def __len__(self):
        return 10


class DTMLFile(Base, Bindings, Explicit, ClassicHTMLFile):
    "HTMLFile with bindings and support for __render_with_namespace__"
    interface.implements(IContained)

    func_code = None
    func_defaults = None
    _need__name__=1

    _Bindings_ns_class = TemplateDict

    __parent__ = __name__ = None

    @property
    def __roles__(self):
        parent = getattr(self, '__parent__', None)
        if parent is not None:
            imp = getattr(parent, '%s__roles__' % self.__name__, None)
            return imp
        return None

    # By default, we want to look up names in our container.
    _Bindings_client = 'container'

    def __init__(self, name, _prefix=None, **kw):
        self.ZBindings_edit(defaultBindings)
        self._setFuncSignature()
        apply(DTMLFile.inheritedAttribute('__init__'),
              (self, name, _prefix), kw)

    def getOwner(self, info=0):
        '''
        This method is required of all objects that go into
        the security context stack.
        '''
        return None

    def _exec(self, bound_data, args, kw):
        # Cook if we haven't already
        self._cook_check()

        # Get our caller's namespace, and set up our own.
        cns = bound_data['caller_namespace']
        ns = self._Bindings_ns_class()
        push = ns._push
        ns.guarded_getattr = None
        ns.guarded_getitem = None

        req = getRequest()
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
            except: pass
        else:
            # We're first, so get the REQUEST.
            try:
                req = getRequest()
                if hasattr(req, 'taintWrapper'):
                    req = req.taintWrapper()
            except: pass
            bound_data['REQUEST'] = req
            ns.this = bound_data['context']
        # Bind 'keyword_args' to the complete set of keyword arguments.
        bound_data['keyword_args'] = kw_bind
        bound_data['REQUEST'] = getRequest()

        # Push globals, initialized variables, REQUEST (if any),
        # and keyword arguments onto the namespace stack

        for nsitem in (self.globals, self._vars, req, kw, 
                       AqWrapper(req.PARENTS[-1], req)):
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
        try:
            value = self.ZDocumentTemplate_beforeRender(ns, _marker)
            if value is _marker:
                try: result = render_blocks(self._v_blocks, ns)
                except DTReturn, v: result = v.v
                except AttributeError:
                    if type(sys.exc_value)==InstanceType and sys.exc_value.args[0]=="_v_blocks":
                        LOG.warn("DTML file '%s' could not be read" % self.raw)
                        raise ValueError, ("DTML file error: "
                                           "Check logfile for details")
                    else:
                        raise

                self.ZDocumentTemplate_afterRender(ns, result)
                return result
            else:
                return value
        finally:
            security.removeContext(self)
            # Clear the namespace, breaking circular references.
            while len(ns): ns._pop()
    from Shared.DC.Scripts.Signature import _setFuncSignature


HTMLFile = ClassicHTMLFile
