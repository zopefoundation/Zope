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
"""Find support
"""
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permission import getPermissionIdentifier
from AccessControl.Permissions import view_management_screens
from AccessControl.tainted import TaintedString
from Acquisition import aq_base
from Acquisition import aq_parent
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from DocumentTemplate._DocumentTemplate import InstanceDict
from DocumentTemplate._DocumentTemplate import TemplateDict
from DocumentTemplate.DT_Util import Eval
from DocumentTemplate.security import RestrictedDTML
from ExtensionClass import Base
from OFS.interfaces import IFindSupport
from zope.interface import implementer
from ZPublisher.HTTPRequest import default_encoding


@implementer(IFindSupport)
class FindSupport(Base):
    """Find support for Zope Folders."""

    manage_options = ()
    security = ClassSecurityInfo()

    security.declareProtected(view_management_screens, 'manage_findForm')  # NOQA: D001,E501
    manage_findForm = DTMLFile(
        'dtml/findForm',
        globals(),
        management_view='Find',
    )

    manage_options = (
        {
            'label': 'Find',
            'action': 'manage_findForm',
        },
    )

    @security.protected(view_management_screens)
    def ZopeFind(self, obj, obj_ids=None, obj_metatypes=None,
                 obj_searchterm=None, obj_expr=None,
                 obj_mtime=None, obj_mspec=None,
                 obj_permission=None, obj_roles=None,
                 search_sub=0,
                 REQUEST=None, result=None, pre=''):
        """Zope Find interface."""
        return self.ZopeFindAndApply(
            obj, obj_ids=obj_ids,
            obj_metatypes=obj_metatypes, obj_searchterm=obj_searchterm,
            obj_expr=obj_expr, obj_mtime=obj_mtime, obj_mspec=obj_mspec,
            obj_permission=obj_permission, obj_roles=obj_roles,
            search_sub=search_sub, REQUEST=REQUEST, result=result,
            pre=pre, apply_func=None, apply_path=''
        )

    @security.protected(view_management_screens)
    def ZopeFindAndApply(self, obj, obj_ids=None, obj_metatypes=None,
                         obj_searchterm=None, obj_expr=None,
                         obj_mtime=None, obj_mspec=None,
                         obj_permission=None, obj_roles=None,
                         search_sub=0,
                         REQUEST=None, result=None, pre='',
                         apply_func=None, apply_path=''):
        """Zope Find interface and apply."""

        if result is None:
            result = []

            if obj_metatypes and 'all' in obj_metatypes:
                obj_metatypes = None

            if obj_mtime and isinstance(obj_mtime, str):
                obj_mtime = DateTime(obj_mtime).timeTime()

            if obj_permission:
                obj_permission = getPermissionIdentifier(obj_permission)

            if obj_roles and isinstance(obj_roles, str):
                obj_roles = [obj_roles]

            if obj_expr:
                # Setup expr machinations
                md = td()
                obj_expr = (Eval(obj_expr), md, md._push, md._pop)

        base = aq_base(obj)

        if not hasattr(base, 'objectItems'):
            return result
        try:
            items = obj.objectItems()
        except Exception:
            return result

        try:
            add_result = result.append
        except Exception:
            raise AttributeError(repr(result))

        for id, ob in items:
            if pre:
                p = f"{pre}/{id}"
            else:
                p = id

            dflag = 0
            if hasattr(ob, '_p_changed') and (ob._p_changed is None):
                dflag = 1

            bs = aq_base(ob)
            if obj_searchterm:
                if isinstance(obj_searchterm, TaintedString):
                    obj_searchterm = str(obj_searchterm)
                    if not isinstance(obj_searchterm, str):
                        obj_searchterm = obj_searchterm.decode(
                            default_encoding)
                if hasattr(ob, 'PrincipiaSearchSource'):
                    pss = ob.PrincipiaSearchSource()
                    if not isinstance(pss, str):
                        try:
                            pss = pss.decode(default_encoding)
                        except UnicodeDecodeError:
                            pss = ''
                if hasattr(ob, 'SearchableText'):
                    st = ob.SearchableText()
                    if not isinstance(st, str):
                        try:
                            st = st.decode(default_encoding)
                        except UnicodeDecodeError:
                            st = ''
            else:
                pss = st = ''

            if ((not obj_ids or absattr(bs.getId()) in obj_ids)
                and (not obj_metatypes
                     or (hasattr(bs, 'meta_type')
                         and bs.meta_type in obj_metatypes))
                and (not obj_searchterm
                     or (hasattr(ob, 'PrincipiaSearchSource')
                         and obj_searchterm in pss)
                     or (hasattr(ob, 'SearchableText')
                         and obj_searchterm in st))
                and (not obj_expr or expr_match(ob, obj_expr))
                and (not obj_mtime or mtime_match(ob, obj_mtime, obj_mspec))
                and ((not obj_permission or not obj_roles)
                     or role_match(ob, obj_permission, obj_roles))):

                if apply_func:
                    apply_func(ob, (apply_path + '/' + p))
                else:
                    add_result((p, ob))
                    dflag = 0

            if search_sub and hasattr(bs, 'objectItems'):
                self.ZopeFindAndApply(ob, obj_ids, obj_metatypes,
                                      obj_searchterm, obj_expr,
                                      obj_mtime, obj_mspec,
                                      obj_permission, obj_roles,
                                      search_sub,
                                      REQUEST, result, p,
                                      apply_func, apply_path)
            if dflag:
                ob._p_deactivate()

        return result


InitializeClass(FindSupport)


class td(RestrictedDTML, TemplateDict):
    pass


def expr_match(ob, ed, c=InstanceDict, r=0):
    e, md, push, pop = ed
    push(c(ob, md))
    try:
        r = e.eval(md)
    finally:
        pop()
        return r


def mtime_match(ob, t, q, fn=hasattr):
    if not fn(ob, '_p_mtime'):
        return 0
    return q == '<' and (ob._p_mtime < t) or (ob._p_mtime > t)


def role_match(ob, permission, roles, lt=type([]), tt=type(())):
    pr = []
    fn = pr.append

    while 1:
        if hasattr(ob, permission):
            p = getattr(ob, permission)
            if type(p) is lt:
                list(map(fn, p))
                if hasattr(ob, '__parent__'):
                    ob = aq_parent(ob)
                    continue
                break
            if type(p) is tt:
                list(map(fn, p))
                break
            if p is None:
                list(map(fn, ('Manager', 'Anonymous')))
                break

        if hasattr(ob, '__parent__'):
            ob = aq_parent(ob)
            continue
        break

    for role in roles:
        if not (role in pr):
            return 0
    return 1


def absattr(attr):
    if callable(attr):
        return attr()
    return attr
