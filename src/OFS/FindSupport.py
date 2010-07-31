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

from string import translate

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permission import name_trans
from AccessControl.Permissions import view_management_screens
from Acquisition import aq_base
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from DocumentTemplate.DT_Util import Eval
from DocumentTemplate.DT_Util import InstanceDict
from DocumentTemplate.DT_Util import TemplateDict
from DocumentTemplate.security import RestrictedDTML
from ExtensionClass import Base
from zope.interface import implements

from OFS.interfaces import IFindSupport


class FindSupport(Base):

    """Find support for Zope Folders"""

    implements(IFindSupport)

    security = ClassSecurityInfo()

    #findframe is deprecated
    security.declareProtected(view_management_screens, 'manage_findFrame')
    manage_findFrame=DTMLFile('dtml/findFrame', globals())

    security.declareProtected(view_management_screens, 'manage_findForm')
    manage_findForm=DTMLFile('dtml/findForm', globals(),
                             management_view='Find')

    security.declareProtected(view_management_screens, 'manage_findAdv')
    manage_findAdv=DTMLFile('dtml/findAdv', globals(),
                            management_view='Find')

    security.declareProtected(view_management_screens, 'manage_findResult')
    manage_findResult=DTMLFile('dtml/findResult', globals(),
                               management_view='Find')

    manage_options=(
        {'label':'Find', 'action':'manage_findForm'},
        )

    security.declareProtected(view_management_screens, 'ZopeFind')
    def ZopeFind(self, obj, obj_ids=None, obj_metatypes=None,
                 obj_searchterm=None, obj_expr=None,
                 obj_mtime=None, obj_mspec=None,
                 obj_permission=None, obj_roles=None,
                 search_sub=0,
                 REQUEST=None, result=None, pre=''):
        """Zope Find interface"""

        if result is None:
            result=[]

            if obj_metatypes and 'all' in obj_metatypes:
                obj_metatypes=None

            if obj_mtime and type(obj_mtime)==type('s'):
                obj_mtime=DateTime(obj_mtime).timeTime()

            if obj_permission:
                obj_permission=p_name(obj_permission)

            if obj_roles and type(obj_roles) is type('s'):
                obj_roles=[obj_roles]

            if obj_expr:
                # Setup expr machinations
                md=td()
                obj_expr=(Eval(obj_expr), md, md._push, md._pop)

        base = aq_base(obj)

        if hasattr(base, 'objectItems'):
            try:    items=obj.objectItems()
            except: return result
        else:
            return result

        try: add_result=result.append
        except:
            raise AttributeError, `result`

        for id, ob in items:
            if pre: p="%s/%s" % (pre, id)
            else:   p=id

            dflag=0
            if hasattr(ob, '_p_changed') and (ob._p_changed == None):
                dflag=1

            bs = aq_base(ob)
            if (
                (not obj_ids or absattr(bs.getId()) in obj_ids)
                and
                (not obj_metatypes or (hasattr(bs, 'meta_type') and
                 bs.meta_type in obj_metatypes))
                and
                (not obj_searchterm or
                 (hasattr(ob, 'PrincipiaSearchSource') and
                  ob.PrincipiaSearchSource().find(str(obj_searchterm)) >= 0
                  )
                 or
                 (hasattr(ob, 'SearchableText') and
                  ob.SearchableText().find(str(obj_searchterm)) >= 0)
                 )
                and
                (not obj_expr or expr_match(ob, obj_expr))
                and
                (not obj_mtime or mtime_match(ob, obj_mtime, obj_mspec))
                and
                ( (not obj_permission or not obj_roles) or \
                   role_match(ob, obj_permission, obj_roles)
                )
                ):
                add_result((p, ob))
                dflag=0

            if search_sub and (hasattr(bs, 'objectItems')):
                subob = ob
                sub_p = p
                self.ZopeFind(subob, obj_ids, obj_metatypes,
                                   obj_searchterm, obj_expr,
                                   obj_mtime, obj_mspec,
                                   obj_permission, obj_roles,
                                   search_sub,
                                   REQUEST, result, sub_p)
            if dflag: ob._p_deactivate()

        return result



    security.declareProtected(view_management_screens, 'PrincipiaFind')
    PrincipiaFind=ZopeFind

    security.declareProtected(view_management_screens, 'ZopeFindAndApply')
    def ZopeFindAndApply(self, obj, obj_ids=None, obj_metatypes=None,
                         obj_searchterm=None, obj_expr=None,
                         obj_mtime=None, obj_mspec=None,
                         obj_permission=None, obj_roles=None,
                         search_sub=0,
                         REQUEST=None, result=None, pre='',
                         apply_func=None, apply_path=''):
        """Zope Find interface and apply"""

        if result is None:
            result=[]

            if obj_metatypes and 'all' in obj_metatypes:
                obj_metatypes=None

            if obj_mtime and type(obj_mtime)==type('s'):
                obj_mtime=DateTime(obj_mtime).timeTime()

            if obj_permission:
                obj_permission=p_name(obj_permission)

            if obj_roles and type(obj_roles) is type('s'):
                obj_roles=[obj_roles]

            if obj_expr:
                # Setup expr machinations
                md=td()
                obj_expr=(Eval(obj_expr), md, md._push, md._pop)

        base = aq_base(obj)

        if not hasattr(base, 'objectItems'):
            return result
        try:    items=obj.objectItems()
        except: return result

        try: add_result=result.append
        except:
            raise AttributeError, `result`

        for id, ob in items:
            if pre: p="%s/%s" % (pre, id)
            else:   p=id

            dflag=0
            if hasattr(ob, '_p_changed') and (ob._p_changed == None):
                dflag=1

            bs = aq_base(ob)
            if (
                (not obj_ids or absattr(bs.getId()) in obj_ids)
                and
                (not obj_metatypes or (hasattr(bs, 'meta_type') and
                 bs.meta_type in obj_metatypes))
                and
                (not obj_searchterm or
                 (hasattr(ob, 'PrincipiaSearchSource') and
                  ob.PrincipiaSearchSource().find(obj_searchterm) >= 0
                  ))
                and
                (not obj_expr or expr_match(ob, obj_expr))
                and
                (not obj_mtime or mtime_match(ob, obj_mtime, obj_mspec))
                and
                ( (not obj_permission or not obj_roles) or \
                   role_match(ob, obj_permission, obj_roles)
                )
                ):
                if apply_func:
                    apply_func(ob, (apply_path+'/'+p))
                else:
                    add_result((p, ob))
                    dflag=0

            if search_sub and hasattr(bs, 'objectItems'):
                self.ZopeFindAndApply(ob, obj_ids, obj_metatypes,
                                      obj_searchterm, obj_expr,
                                      obj_mtime, obj_mspec,
                                      obj_permission, obj_roles,
                                      search_sub,
                                      REQUEST, result, p,
                                      apply_func, apply_path)
            if dflag: ob._p_deactivate()

        return result

InitializeClass(FindSupport)


class td(RestrictedDTML, TemplateDict):
    pass


def expr_match(ob, ed, c=InstanceDict, r=0):
    e, md, push, pop=ed
    push(c(ob, md))
    try: r=e.eval(md)
    finally:
        pop()
        return r



def mtime_match(ob, t, q, fn=hasattr):
    if not fn(ob, '_p_mtime'):
        return 0
    return q=='<' and (ob._p_mtime < t) or (ob._p_mtime > t)


def role_match(ob, permission, roles, lt=type([]), tt=type(())):
    pr=[]
    fn=pr.append

    while 1:
        if hasattr(ob, permission):
            p=getattr(ob, permission)
            if type(p) is lt:
                map(fn, p)
                if hasattr(ob, 'aq_parent'):
                    ob=ob.aq_parent
                    continue
                break
            if type(p) is tt:
                map(fn, p)
                break
            if p is None:
                map(fn, ('Manager', 'Anonymous'))
                break

        if hasattr(ob, 'aq_parent'):
            ob=ob.aq_parent
            continue
        break

    for role in roles:
        if not (role in pr):
            return 0
    return 1


# Helper functions

def absattr(attr):
    if callable(attr): return attr()
    return attr


def p_name(name):
    return '_' + translate(name, name_trans) + '_Permission'
