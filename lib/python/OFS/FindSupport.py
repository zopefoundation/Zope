__doc__="""Principia Find support"""
__version__='$Revision: 1.1 $'[11:-2]


import sys, os, string, time, Globals
from DocumentTemplate.DT_Util import Eval, expr_globals
from AccessControl.Permission import name_trans
from cDocumentTemplate import *
from DateTime import DateTime
from string import find









class FindSupport:

    def PrincipiaFind(self, obj, obj_ids=None, obj_metatypes=None,
                      obj_searchterm=None, obj_expr=None,
                      obj_mtime=None, obj_mspec=None,
                      obj_permission=None, obj_roles=None,
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
#                 (obj_modspec=='<' and hasattr(ob, '_p_mtime') and \
#                  ob._p_mtime < obj_modtime) or
#                 (obj_modspec=='>' and hasattr(ob, '_p_mtime') and \
#                  ob._p_mtime > obj_modtime)
#                 )
                and
                ( (not obj_permission or not obj_roles) or \
                   role_match(ob, obj_permission, obj_roles)
                )
                ):
                add_result((p, ob))
                dflag=0
                    
            if hasattr(bs, 'objectItems'):
                self.PrincipiaFind(ob, obj_ids, obj_metatypes,
                                   obj_searchterm, obj_expr,
                                   obj_mtime, obj_mspec,
                                   obj_permission, obj_roles,
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
#    ob=obj
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









## def oldpermission_match(obj, permission, roles):
## #    if not hasattr(obj, '__ac_permissions__'):
## #        return 0
##     r=proles(obj, permission)
##     for role in roles:
##         if not (role in r):
##             return 0
##     return 1


## def pldproles(obj, permission):
##     for p in obj.__ac_permissions__:
##         name, value = p[:2]
##         if name==permission:
##             p=Permission(name,value,obj)
##             r=p.getRoles()

##             if r is None: r=['Anonymous']
##             if type(r) is type(()):
##                 r=list(r)

##             if hasattr(obj, 'aq_parent'):
##                 o=obj.aq_parent
##                 n=p._p
##                 while 1:
##                     if hasattr(o, n):
##                         roles=getattr(o, n)
##                         if roles is None:
##                             if not ('Anonymous' in r):
##                                 r.append('Anonymous')
##                             return r
##                         if type(roles) is type(()):
##                             return r+list(roles)
##                         r=r+list(roles)
##                     if hasattr(o, 'aq_parent'):
##                         o=o.aq_parent
##                     else: break
##             return r
##     return []













##     def PrincipiaFind1(self, start, _initial=None, prefix='',
##                       type=None, substring=None, name=None,
##                       ):
##         if _initial is None: _initial=[]
        
##         if hasattr(start,'aq_base'): start=start.aq_base
##         if not hasattr(start, 'objectItems'): return _initial
##         try: items=start.objectItems()
##         except: return _initial
##         for oname, o in items:
##             if prefix: p="%s/%s" % (prefix, oname)
##             else: p=oname
##             if hasattr(o,'aq_base'): o=o.aq_base
##             if (
##                 (type is None or not hasattr(o,'meta_type') or
##                  type==o.meta_type)
##                 and
##                 (name is None or oname==name)
##                 and
##                 (substring is None or
##                  (hasattr(o,'PrincipiaSearchSource') and
##                   find(o.PrincipiaSearchSource(),substring) >= 0
##                   ))
##                 ):
##                 _initial.append(p)
##             if hasattr(o, 'objectItems'):
##                 self.PrincipiaFind(o,_initial,p,type,substring,name)

##         return _initial
