__doc__="""Principia Find support"""
__version__='$Revision: 1.2 $'[11:-2]


import sys, os, string, time, Globals
from DocumentTemplate.DT_Util import Eval, expr_globals
from AccessControl.Permission import name_trans
from cDocumentTemplate import *
from DateTime import DateTime
from string import find



class FindSupport:
    """Find support for Principia Folders"""
    def PrincipiaFind(self, obj, obj_ids=None, obj_metatypes=None,
                      obj_searchterm=None, obj_expr=None,
                      obj_mtime=None, obj_mspec=None,
                      obj_permission=None, obj_roles=None,
                      search_sub=0,
                      REQUEST=None, result=None, pre=''):
        """Principia Find interface"""

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
                if hasattr(REQUEST, 'AUTHENTICATED_USER'):
                    md.AUTHENTICATED_USER=REQUEST.AUTHENTICATED_USER
                obj_expr=(Eval(obj_expr, expr_globals), md, md._push, md._pop)

        base=obj
        if hasattr(obj, 'aq_base'):
            base=obj.aq_base

        if not hasattr(base, 'objectItems'):
            return result
        try:    items=base.objectItems()
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

            if hasattr(ob, 'aq_base'):
                bs=ob.aq_base

            if (
                (not obj_ids or absattr(bs.id) in obj_ids)
                and
                (not obj_metatypes or (hasattr(bs, 'meta_type') and
                 bs.meta_type in obj_metatypes))
                and
                (not obj_searchterm or
                 (hasattr(ob, 'PrincipiaSearchSource') and
                  find(ob.PrincipiaSearchSource(), obj_searchterm) >= 0
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
                add_result((p, ob))
                dflag=0
                    
            if search_sub and hasattr(bs, 'objectItems'):
                self.PrincipiaFind(ob, obj_ids, obj_metatypes,
                                   obj_searchterm, obj_expr,
                                   obj_mtime, obj_mspec,
                                   obj_permission, obj_roles,
                                   search_sub,
                                   REQUEST, result, p)
            if dflag: ob._p_deactivate()

        return result



class td(TemplateDict, cDocument):
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
    return '_' + string.translate(name, name_trans) + '_Permission'





############################################################################## 
#
# $Log: FindSupport.py,v $
# Revision 1.2  1998/08/13 13:48:16  brian
# Added find in all subfolders option
#
