"""Help system and documentation support"""

__version__='$Revision: 1.1 $'[11:-2]


import sys, os, string, ts_regex
import Globals, Acquisition
from HelpUtil import classobject, methodobject, is_class, is_module
from App.Dialogs import MessageDialog
from ImageFile import ImageFile
from StructuredText import HTML
from Globals import HTMLFile






class ObjectItem(classobject):
    """Object type wrapper"""

    index_html=HTMLFile('objectitem_index', globals())

    __roles__=None

    def __getattr__(self, name):
        if name in ('isDocTemp', '__call__'):
            raise AttributeError, name
        return getattr(self.__dict__['_obj_'], name)

    def get_method_list(self):
        rdict=classobject.get_method_dict(self)
        perms=self.__ac_permissions__
        mdict={}
        mlist=[]
        for p in self.__ac_permissions__:
            pname=p[0]
            fnames=p[1]
            for fname in fnames:
                if rdict.has_key(fname):
                    fn=rdict[fname]
                    fn.permission=pname
                    mdict[fname]=fn                    
        keys=mdict.keys()
        keys.sort()
        for key in keys:
            fn=mdict[key]
            if not hasattr(fn._obj_, '__doc__'):
                continue
            doc=fn._obj_.__doc__
            if hasattr(fn._obj_, '__class__') and \
               fn._obj_.__class__.__doc__ is doc:
                continue
            
            mlist.append(mdict[key])
        del rdict
        del mdict
        return mlist

        

class ObjectRef(Acquisition.Implicit):
    """Object reference"""
    __roles__=None
    
    index_html=HTMLFile('objectref_index', globals())

    def __init__(self):
        dict={}
        for k, v in sys.modules.items():
            if v is not None and k != '__builtins__':
                dict=self.search_mod(v, dict)
        keys=dict.keys()
        keys.sort()
        for key in keys:
            setattr(self, key, dict[key])
        self._ids_=keys

    objectValues__roles__=None
    def objectValues(self):
        items=[]
        for id in self._ids_:
            items.append(getattr(self, id))
        return items

    def search_mod(self, mod, dict):
        for k, v in mod.__dict__.items():
            if is_class(v) and hasattr(v, 'meta_type') and \
               hasattr(v, '__ac_permissions__'):
                dict[v.meta_type]=ObjectItem(k, v)
            if is_module(v) and hasattr(v, '__path__'):
                dict=self.search_mod(v, dict)
        return dict

    def __getitem__(self, key):
        return self.__dict__[key].__of__(self)

    def tpId(self):
        return 'ObjectRef'

    tpURL=tpId

    def tpValues(self):
        return self.objectValues()

    def __len__(self):
        return 1



class HelpSys(Acquisition.Implicit):
    """Help system root"""
    __roles__=None
    
    index_html=HTMLFile('helpsys_index', globals())
    u_arrow=ImageFile('u_arrow.gif', globals())
    d_arrow=ImageFile('d_arrow.gif', globals())
    r_arrow=ImageFile('r_arrow.gif', globals())
    l_arrow=ImageFile('l_arrow.gif', globals())
    
    ObjectRef=ObjectRef()


    def __len__(self):
        return 1




