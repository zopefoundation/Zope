/*

  $Id: Acquisition.c,v 1.16 1998/03/23 20:23:35 jim Exp $

  Acquisition Wrappers -- Implementation of acquisition through wrappers


     Copyright 

       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
       rights reserved.  Copyright in this software is owned by DCLC,
       unless otherwise indicated. Permission to use, copy and
       distribute this software is hereby granted, provided that the
       above copyright notice appear in all copies and that both that
       copyright notice and this permission notice appear. Note that
       any product, process or technology described in this software
       may be the subject of other Intellectual Property rights
       reserved by Digital Creations, L.C. and are not licensed
       hereunder.

     Trademarks 

       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
       All other trademarks are owned by their respective companies. 

     No Warranty 

       The software is provided "as is" without warranty of any kind,
       either express or implied, including, but not limited to, the
       implied warranties of merchantability, fitness for a particular
       purpose, or non-infringement. This software could include
       technical inaccuracies or typographical errors. Changes are
       periodically made to the software; these changes will be
       incorporated in new editions of the software. DCLC may make
       improvements and/or changes in this software at any time
       without notice.

     Limitation Of Liability 

       In no event will DCLC be liable for direct, indirect, special,
       incidental, economic, cover, or consequential damages arising
       out of the use of or inability to use this software even if
       advised of the possibility of such damages. Some states do not
       allow the exclusion or limitation of implied warranties or
       limitation of liability for incidental or consequential
       damages, so the above limitation or exclusion may not apply to
       you.

    If you have questions regarding this software,
    contact:
   
      Jim Fulton, jim@digicool.com
      Digital Creations L.C.  
   
      (540) 371-6909

*/
#include "ExtensionClass.h"

static void
PyVar_Assign(PyObject **v,  PyObject *e)
{
  Py_XDECREF(*v);
  *v=e;
}

#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)
#define OBJECT(O) ((PyObject*)(O))

static PyObject *py__add__, *py__sub__, *py__mul__, *py__div__,
  *py__mod__, *py__pow__, *py__divmod__, *py__lshift__, *py__rshift__,
  *py__and__, *py__or__, *py__xor__, *py__coerce__, *py__neg__,
  *py__pos__, *py__abs__, *py__nonzero__, *py__inv__, *py__int__,
  *py__long__, *py__float__, *py__oct__, *py__hex__,
  *py__getitem__, *py__setitem__, *py__delitem__,
  *py__getslice__, *py__setslice__, *py__delslice__,
  *py__concat__, *py__repeat__, *py__len__, *py__of__, *py__call__,
  *py__repr__, *py__str__;

static PyObject *Acquired=0;

static void
init_py_names()
{
#define INIT_PY_NAME(N) py ## N = PyString_FromString(#N)
  INIT_PY_NAME(__add__);
  INIT_PY_NAME(__sub__);
  INIT_PY_NAME(__mul__);
  INIT_PY_NAME(__div__);
  INIT_PY_NAME(__mod__);
  INIT_PY_NAME(__pow__);
  INIT_PY_NAME(__divmod__);
  INIT_PY_NAME(__lshift__);
  INIT_PY_NAME(__rshift__);
  INIT_PY_NAME(__and__);
  INIT_PY_NAME(__or__);
  INIT_PY_NAME(__xor__);
  INIT_PY_NAME(__coerce__);
  INIT_PY_NAME(__neg__);
  INIT_PY_NAME(__pos__);
  INIT_PY_NAME(__abs__);
  INIT_PY_NAME(__nonzero__);
  INIT_PY_NAME(__inv__);
  INIT_PY_NAME(__int__);
  INIT_PY_NAME(__long__);
  INIT_PY_NAME(__float__);
  INIT_PY_NAME(__oct__);
  INIT_PY_NAME(__hex__);
  INIT_PY_NAME(__getitem__);
  INIT_PY_NAME(__setitem__);
  INIT_PY_NAME(__delitem__);
  INIT_PY_NAME(__getslice__);
  INIT_PY_NAME(__setslice__);
  INIT_PY_NAME(__delslice__);
  INIT_PY_NAME(__concat__);
  INIT_PY_NAME(__repeat__);
  INIT_PY_NAME(__len__);
  INIT_PY_NAME(__of__);
  INIT_PY_NAME(__call__);
  INIT_PY_NAME(__repr__);
  INIT_PY_NAME(__str__);
  
#undef INIT_PY_NAME
}

static PyObject *
CallMethodO(PyObject *self, PyObject *name,
		     PyObject *args, PyObject *kw)
{
  if(! args && PyErr_Occurred()) return NULL;
  UNLESS(name=PyObject_GetAttr(self,name)) return NULL;
  ASSIGN(name,PyEval_CallObjectWithKeywords(name,args,kw));
  if(args) Py_DECREF(args);
  return name;
}

#define Build Py_BuildValue

/* Declarations for objects of type Wrapper */

typedef struct {
  PyObject_HEAD
  PyObject *obj;
  PyObject *container;
} Wrapper;

static Wrapper *freeWrappers=0;

staticforward PyExtensionClass Wrappertype, XaqWrappertype;

#define isWrapper(O) ((O)->ob_type==(PyTypeObject*)&Wrappertype || \
		      (O)->ob_type==(PyTypeObject*)&XaqWrappertype)
#define WRAPPER(O) ((Wrapper*)(O))

static PyObject *
Wrapper__init__(Wrapper *self, PyObject *args)
{
  PyObject *obj, *container;

  UNLESS(PyArg_Parse(args,"(OO)",&obj,&container)) return NULL;
  Py_INCREF(obj);
  Py_INCREF(container);
  self->obj=obj;
  self->container=container;
  Py_INCREF(Py_None);
  return Py_None;
}

/* ---------------------------------------------------------------- */

/* ---------- */

static PyObject *
__of__(PyObject *inst, PyObject *parent)
{
  PyObject *r, *t;

  UNLESS(r=PyObject_GetAttr(inst, py__of__)) return NULL;
  UNLESS(t=PyTuple_New(1)) goto err;
  PyTuple_SET_ITEM(t,0,parent);
  ASSIGN(r,PyObject_CallObject(r,t));
  PyTuple_SET_ITEM(t,0,NULL);
  Py_DECREF(t);
  return r;
err:
  Py_DECREF(r);
  return NULL;
}

static PyObject *
newWrapper(PyObject *obj, PyObject *container, PyTypeObject *Wrappertype)
{
  Wrapper *self;
  
  if(freeWrappers)
    {
      self=freeWrappers;
      freeWrappers=(Wrapper*)self->obj;
      self->ob_type=Wrappertype;
      self->ob_refcnt=1;
    }
  else
    UNLESS(self = PyObject_NEW(Wrapper, Wrappertype)) return NULL;

  Py_INCREF(obj);
  Py_INCREF(container);
  self->obj=obj;
  self->container=container;
  return OBJECT(self);
}


static void
Wrapper_dealloc(Wrapper *self)     
{
  Py_DECREF(self->obj);
  Py_DECREF(self->container);
  self->obj=OBJECT(freeWrappers);
  freeWrappers=self;
}

static PyObject *
Wrapper_special(Wrapper *self, char *name, PyObject *oname)
{
  PyObject *r=0;

  if(strcmp(name,"base")==0)
    {
      if(self->obj)
	{
	  r=self->obj;
	  while(isWrapper(r) && WRAPPER(r)->obj) r=WRAPPER(r)->obj;
	}
      else r=Py_None;
      Py_INCREF(r);
      return r;
    }
  if(strcmp(name,"parent")==0)
    {
      if(self->container) r=self->container;
      else r=Py_None;
      Py_INCREF(r);
      return r;
    }
  if(strcmp(name,"self")==0)
    {
      if(self->obj) r=self->obj;
      else r=Py_None;
      Py_INCREF(r);
      return r;
    }
  if(strcmp(name,"acquire")==0)
    {
      return Py_FindAttr(OBJECT(self),oname);
    }
}

static PyObject *
Wrapper_acquire(Wrapper *self, PyObject *oname,
		PyObject *filter, PyObject *extra, PyObject *orig,
		int sob, int sco)
{
  PyObject *r;
  char *name;
  int ir;

  name=PyString_AsString(oname);
  if(*name++=='a' && *name++=='q' && *name++=='_'
     && (r=Wrapper_special(self, name, oname))) return r;

  if(sob && self->obj)
    {
      if(r=PyObject_GetAttr(self->obj,oname))
	{
	  if(r->ob_type==self->ob_type)
	    {
	      if(r->ob_refcnt==1)
		{
		  Py_INCREF(self);
		  ASSIGN(((Wrapper*)r)->container,OBJECT(self));
		}
	      else
		ASSIGN(r,newWrapper(((Wrapper*)r)->obj,
				    OBJECT(self), self->ob_type));
	    }
	  else if(PyECMethod_Check(r) && PyECMethod_Self(r)==self->obj)
	    ASSIGN(r,PyECMethod_New(r,OBJECT(self)));
	  else if(has__of__(r)) ASSIGN(r,__of__(r,OBJECT(self)));
	  if(filter)
	    switch(apply_filter(filter,OBJECT(self),oname,r,extra,orig))
	      {
	      case -1: return NULL;
	      case 1: return r;
	      }
	  else return r;
	}
      PyErr_Clear();
    }
  
  if(sco && self->container) 
    {
      if(isWrapper(self->container))
	{
	  if(self->obj && self->obj->ob_type == (PyTypeObject*)&Wrappertype)
	    {
	      if(WRAPPER(self->obj)->container==
		 WRAPPER(self->container)->container) sob=1, sco=0;
	      else if(WRAPPER(self->obj)->container==
		      WRAPPER(self->container)->obj)  sob=0, sco=1;
	      else                                    sob=1, sco=1;
	      r=Wrapper_acquire((Wrapper*)self->container,
				oname,filter,extra,orig, sob, sco);
	   }
	  else
	    r=Wrapper_acquire((Wrapper*)self->container,
			      oname,filter,extra,orig,1,1);

	  
	  if(r) goto acquired;
	}
      else
	{
	  if((r=PyObject_GetAttr(self->container,oname)))
	    if(filter)
	      switch(apply_filter(filter,self->container,oname,r,extra,orig))
		{
		case -1: return NULL;
		case 1: goto acquired;
		}
	    else goto acquired;
	}
      PyErr_Clear();
    }

  PyErr_SetObject(PyExc_AttributeError,oname);
  return NULL;

acquired:
  if(has__of__(r)) ASSIGN(r,__of__(r,OBJECT(self)));
  return r;
}

static PyObject *
handle_Acquired(Wrapper *self, PyObject *oname, PyObject *r)
{
  UNLESS(self->container)
    {
      PyErr_SetObject(PyExc_AttributeError, oname);
      return NULL;
    }
  if(isWrapper(self->container))
    ASSIGN(r,Wrapper_acquire(WRAPPER(self->container),
			     oname,NULL,NULL,NULL,1,1));
  else
    ASSIGN(r,PyObject_GetAttr(self->container,oname));
  
  if(r && has__of__(r)) ASSIGN(r, __of__(r,OBJECT(self)));
  return r;
}

static PyObject *
Wrapper_getattro_(Wrapper *self, PyObject *oname, int sob, int sco)
{
  PyObject *r;
  char *name;

  name=PyString_AsString(oname);
  if(*name=='a' && name[1]=='q' && name[2]=='_'
     && (r=Wrapper_special(self, name+3, oname))) return r;

  if(sob && self->obj && (r=PyObject_GetAttr(self->obj,oname)))
    {
      if(r == Acquired) return handle_Acquired(self, oname, r);
      if(r->ob_type==self->ob_type)
	{
	  if(r->ob_refcnt==1)
	    {
	      Py_INCREF(self);
	      ASSIGN(((Wrapper*)r)->container,OBJECT(self));
	    }
	  else
	    ASSIGN(r, newWrapper(((Wrapper*)r)->obj,
				 OBJECT(self),self->ob_type));
	}
      else if(PyECMethod_Check(r) && PyECMethod_Self(r)==self->obj)
	ASSIGN(r,PyECMethod_New(r,OBJECT(self)));
      else if(has__of__(r))
	ASSIGN(r,__of__(r,OBJECT(self)));
      return r;
    }
  if(self->obj) PyErr_Clear();

  if((*name != '_'
#ifdef IMPLICIT_ACQUIRE___ROLES__
      || strcmp(name,"__roles__")==0
#endif
      )
     && self->container && sco)
    {
      if(self->container->ob_type == self->ob_type &&
	 self->obj->ob_type==self->ob_type)
	{
	  if(WRAPPER(self->obj)->container==
	     WRAPPER(self->container)->container) sob=1, sco=0;
	  else if(WRAPPER(self->obj)->container==
		  WRAPPER(self->container)->obj)  sob=0, sco=1;
	  else                                    sob=1, sco=1;
	  r=Wrapper_getattro_(WRAPPER(self->container), oname, sob, sco);
	}
      else r=PyObject_GetAttr(self->container,oname);

      if(r)
	{
	  if(has__of__(r))
	    ASSIGN(r, __of__(r,OBJECT(self)));
	  return r;
	}
      PyErr_Clear();
    }

  if(*name++=='_' && strcmp(name,"_init__")==0)
    return Py_FindAttr(OBJECT(self),oname);

  PyErr_SetObject(PyExc_AttributeError,oname);
  return NULL;
}

static PyObject *
Wrapper_getattro(Wrapper *self, PyObject *oname)
{
  return Wrapper_getattro_(self, oname, 1, 1);
}

static PyObject *
Xaq_getattro(Wrapper *self, PyObject *oname)
{
  PyObject *r;
  char *name;

  name=PyString_AsString(oname);

  if(*name=='_')
    {
      if(strcmp(name,"__init__")==0) return Py_FindAttr(OBJECT(self),oname);
#ifdef IMPLICIT_ACQUIRE___ROLES__
      if(strcmp(name,"__roles__")==0) return Wrapper_getattro_(self,oname,1,1);
#endif
    }  

  if(*name=='a')
    {
      if(name[1]=='c')
	{
	  if(strcmp(name+2,"quire")==0)
	    return Py_FindAttr(OBJECT(self),oname);
	}      
      else if(name[1]=='q' && name[2]=='_'
	      && (r=Wrapper_special(self, name+3, oname))) return r;
    }

  if(self->obj && (r=PyObject_GetAttr(self->obj,oname)))
    {
      if(r==Acquired) return handle_Acquired(self,oname,r);
      if(r->ob_type==self->ob_type)
	{
	  if(r->ob_refcnt==1)
	    {
	      Py_INCREF(self);
	      ASSIGN(((Wrapper*)r)->container,OBJECT(self));
	    }
	  else
	    ASSIGN(r, newWrapper(((Wrapper*)r)->obj,
				 OBJECT(self), self->ob_type));
	}
      else if(PyECMethod_Check(r) && PyECMethod_Self(r)==self->obj)
	ASSIGN(r,PyECMethod_New(r,OBJECT(self)));
      else if(has__of__(r)) ASSIGN(r,__of__(r,OBJECT(self)));
      return r;
    }
  if(self->obj) PyErr_Clear();

  PyErr_SetObject(PyExc_AttributeError,oname);
  return NULL;
}

static int
apply_filter(PyObject *filter, PyObject *inst, PyObject *oname, PyObject *r,
	     PyObject *extra, PyObject *orig)
{
  PyObject *fr;
  int ir;

  UNLESS(fr=PyTuple_New(5)) goto err;
  PyTuple_SET_ITEM(fr,0,orig);
  Py_INCREF(orig);
  PyTuple_SET_ITEM(fr,1,inst);
  Py_INCREF(inst);
  PyTuple_SET_ITEM(fr,2,oname);
  Py_INCREF(oname);
  PyTuple_SET_ITEM(fr,3,r);
  Py_INCREF(r);
  PyTuple_SET_ITEM(fr,4,extra);
  Py_INCREF(extra);
  UNLESS_ASSIGN(fr,PyObject_CallObject(filter, fr)) goto err;
  ir=PyObject_IsTrue(fr);
  Py_DECREF(fr);
  if(ir) return 1;
  Py_DECREF(r);
  return 0;
err:
  Py_DECREF(r);
  return -1;
}

static int
Wrapper_setattro(Wrapper *self, PyObject *name, PyObject *v)
{
  if(v && v->ob_type==(PyTypeObject*)&Wrappertype) v=((Wrapper*)v)->obj;
  return PyObject_SetAttr(self->obj, name, v);
}

static int
Wrapper_compare(Wrapper *v, Wrapper *w)
{
  return PyObject_Compare(v->obj,w->obj);
}

static PyObject *
Wrapper_repr(Wrapper *self)
{
  PyObject *r;

  if((r=PyObject_GetAttr(OBJECT(self),py__repr__)))
    {
      ASSIGN(r,PyObject_CallFunction(r,NULL,NULL));
      return r;
    }
  else
    {
      PyErr_Clear();
      return PyObject_Repr(self->obj);
    }
}

static PyObject *
Wrapper_str(Wrapper *self)
{
  PyObject *r;

  if((r=PyObject_GetAttr(OBJECT(self),py__str__)))
    {
      ASSIGN(r,PyObject_CallFunction(r,NULL,NULL));
      return r;
    }
  else
    {
      PyErr_Clear();
      return PyObject_Str(self->obj);
    }
}

static long
Wrapper_hash(Wrapper *self)
{
  return PyObject_Hash(self->obj);
}

static PyObject *
Wrapper_call(Wrapper *self, PyObject *args, PyObject *kw)
{
  Py_INCREF(args);
  return CallMethodO(OBJECT(self),py__call__,args,kw);
}

/* Code to handle accessing Wrapper objects as sequence objects */

static int
Wrapper_length(Wrapper *self)
{
  long l;
  PyObject *r;

  UNLESS(r=PyObject_GetAttr(OBJECT(self), py__len__))
    {
      /* Hm. Maybe we are being checked to see if we are true.
	 
	 Check to see if we have a __getitem__.  If we don't, then
	 answer that we are true, otherwise raise an error.
	 */
      PyErr_Clear();
      if(r=PyObject_GetAttr(OBJECT(self), py__getitem__))
	{
	  /* Hm, we have getitem, must be error */
	  Py_DECREF(r);
	  PyErr_SetObject(PyExc_AttributeError, py__len__);
	  return -1;
	}
      PyErr_Clear();

      /* Try nonzero */
      UNLESS(r=PyObject_GetAttr(OBJECT(self), py__nonzero__))
	{
	  /* No nonzero, it's true :-) */
	  PyErr_Clear();
	  return 1;
	}
    }
  
  UNLESS_ASSIGN(r,PyObject_CallObject(r,NULL)) return -1;
  l=PyInt_AsLong(r);
  Py_DECREF(r);
  return l;
}

static PyObject *
Wrapper_concat(Wrapper *self, PyObject *bb)
{
  return CallMethodO(OBJECT(self),py__concat__,Build("(O)", bb) ,NULL);
}

static PyObject *
Wrapper_repeat(Wrapper *self, int  n)
{
  return CallMethodO(OBJECT(self),py__repeat__,Build("(i)", n),NULL);
}

static PyObject *
Wrapper_item(Wrapper *self, int  i)
{
  return CallMethodO(OBJECT(self),py__getitem__, Build("(i)", i),NULL);
}

static PyObject *
Wrapper_slice(Wrapper *self, int  ilow, int  ihigh)
{
  return CallMethodO(OBJECT(self),py__getslice__,
		     Build("(ii)", ilow, ihigh),NULL);
}

static int
Wrapper_ass_item(Wrapper *self, int  i, PyObject *v)
{
  if(v)
    {
      UNLESS(v=CallMethodO(OBJECT(self),py__setitem__,
			   Build("(iO)", i, v),NULL))
	return -1;
    }
  else
    {
      UNLESS(v=CallMethodO(OBJECT(self),py__delitem__,
			   Build("(iO)", i),NULL))
	return -1;
    }
  Py_DECREF(v);
  return 0;
}

static int
Wrapper_ass_slice(Wrapper *self, int  ilow, int  ihigh, PyObject *v)
{
  if(v)
    {
      UNLESS(v=CallMethodO(OBJECT(self),py__setslice__,
			   Build("(iiO)", ilow, ihigh, v),NULL))
	return -1;
    }
  else
    {
      UNLESS(v=CallMethodO(OBJECT(self),py__delslice__,
			   Build("(ii)", ilow, ihigh),NULL))
	return -1;
    }
  Py_DECREF(v);
  return 0;
}

static PySequenceMethods Wrapper_as_sequence = {
	(inquiry)Wrapper_length,		/*sq_length*/
	(binaryfunc)Wrapper_concat,		/*sq_concat*/
	(intargfunc)Wrapper_repeat,		/*sq_repeat*/
	(intargfunc)Wrapper_item,		/*sq_item*/
	(intintargfunc)Wrapper_slice,		/*sq_slice*/
	(intobjargproc)Wrapper_ass_item,	/*sq_ass_item*/
	(intintobjargproc)Wrapper_ass_slice,	/*sq_ass_slice*/
};

/* -------------------------------------------------------------- */

/* Code to access Wrapper objects as mappings */

static PyObject *
Wrapper_subscript(Wrapper *self, PyObject *key)
{
  return CallMethodO(OBJECT(self),py__getitem__,Build("(O)", key),NULL);
}

static int
Wrapper_ass_sub(Wrapper *self, PyObject *key, PyObject *v)
{
  if(v)
    {
      UNLESS(v=CallMethodO(OBJECT(self),py__setitem__,
			   Build("(OO)", key, v),NULL))
	return -1;
    }
  else
    {
      UNLESS(v=CallMethodO(OBJECT(self),py__delitem__,
			   Build("(O)", key),NULL))
	return -1;
    }
  Py_XDECREF(v);
  return 0;
}

static PyMappingMethods Wrapper_as_mapping = {
  (inquiry)Wrapper_length,		/*mp_length*/
  (binaryfunc)Wrapper_subscript,	/*mp_subscript*/
  (objobjargproc)Wrapper_ass_sub,	/*mp_ass_subscript*/
};

/* -------------------------------------------------------- */

static PyObject *
Wrapper_acquire_method(Wrapper *self, PyObject *args)
{
  PyObject *name, *filter=0, *extra=Py_None;

  UNLESS(PyArg_ParseTuple(args,"O|OO",&name,&filter,&extra)) return NULL;

  return Wrapper_acquire(self,name,filter,extra,OBJECT(self),1,1);
}

static struct PyMethodDef Wrapper_methods[] = {
  {"__init__", (PyCFunction)Wrapper__init__, 0,
   "Initialize an Acquirer Wrapper"},
  {"acquire", (PyCFunction)Wrapper_acquire_method, METH_VARARGS,
   "Get an attribute, acquiring it if necessary"},
  {"aq_acquire", (PyCFunction)Wrapper_acquire_method, METH_VARARGS,
   "Get an attribute, acquiring it if necessary"},
  {NULL,		NULL}		/* sentinel */
};

static PyExtensionClass Wrappertype = {
  PyObject_HEAD_INIT(NULL)
  0,					/*ob_size*/
  "ImplicitAcquirerWrapper",		/*tp_name*/
  sizeof(Wrapper),       		/*tp_basicsize*/
  0,					/*tp_itemsize*/
  /* methods */
  (destructor)Wrapper_dealloc,		/*tp_dealloc*/
  (printfunc)0,				/*tp_print*/
  (getattrfunc)0,			/*tp_getattr*/
  (setattrfunc)0,			/*tp_setattr*/
  (cmpfunc)Wrapper_compare,    		/*tp_compare*/
  (reprfunc)Wrapper_repr,      		/*tp_repr*/
  0,					/*tp_as_number*/
  &Wrapper_as_sequence,			/*tp_as_sequence*/
  &Wrapper_as_mapping,			/*tp_as_mapping*/
  (hashfunc)Wrapper_hash,      		/*tp_hash*/
  (ternaryfunc)Wrapper_call,		/*tp_call*/
  (reprfunc)Wrapper_str,       		/*tp_str*/
  (getattrofunc)Wrapper_getattro,	/*tp_getattr with object key*/
  (setattrofunc)Wrapper_setattro,      	/*tp_setattr with object key*/

  /* Space for future expansion */
  0L,0L,
  "Wrapper object for implicit acquisition", /* Documentation string */
  METHOD_CHAIN(Wrapper_methods),
  EXTENSIONCLASS_BINDABLE_FLAG,
};

static PyExtensionClass XaqWrappertype = {
  PyObject_HEAD_INIT(NULL)
  0,					/*ob_size*/
  "ExplicitAcquirerWrapper",		/*tp_name*/
  sizeof(Wrapper),       		/*tp_basicsize*/
  0,					/*tp_itemsize*/
  /* methods */
  (destructor)Wrapper_dealloc,		/*tp_dealloc*/
  (printfunc)0,				/*tp_print*/
  (getattrfunc)0,			/*tp_getattr*/
  (setattrfunc)0,			/*tp_setattr*/
  (cmpfunc)Wrapper_compare,    		/*tp_compare*/
  (reprfunc)Wrapper_repr,      		/*tp_repr*/
  0,					/*tp_as_number*/
  &Wrapper_as_sequence,			/*tp_as_sequence*/
  &Wrapper_as_mapping,			/*tp_as_mapping*/
  (hashfunc)Wrapper_hash,      		/*tp_hash*/
  (ternaryfunc)Wrapper_call,		/*tp_call*/
  (reprfunc)Wrapper_str,       		/*tp_str*/
  (getattrofunc)Xaq_getattro,		/*tp_getattr with object key*/
  (setattrofunc)Wrapper_setattro,      	/*tp_setattr with object key*/

  /* Space for future expansion */
  0L,0L,
  "Wrapper object for explicit acquisition", /* Documentation string */
  METHOD_CHAIN(Wrapper_methods),
  EXTENSIONCLASS_BINDABLE_FLAG,
};

static PyObject *
acquire_of(PyObject *self, PyObject *args)
{
  PyObject *inst;

  UNLESS(PyArg_Parse(args,"O",&inst)) return NULL;

  UNLESS(PyExtensionInstance_Check(inst))
    {
      PyErr_SetString(PyExc_TypeError,
		      "attempt to wrap extension method using an object that\n"
		      "is not an extension class instance.");
      return NULL;
    }

  return newWrapper(self,args,(PyTypeObject *)&Wrappertype);
}

static PyObject *
xaq_of(PyObject *self, PyObject *args)
{
  PyObject *inst;

  UNLESS(PyArg_Parse(args,"O",&inst)) return NULL;

  UNLESS(PyExtensionInstance_Check(inst))
    {
      PyErr_SetString(PyExc_TypeError,
		      "attempt to wrap extension method using an object that\n"
		      "is not an extension class instance.");
      return NULL;
    }

  return newWrapper(self,args,(PyTypeObject *)&XaqWrappertype);
}

static struct PyMethodDef Acquirer_methods[] = {
  {"__of__",(PyCFunction)acquire_of,0,""},
  
  {NULL,		NULL}		/* sentinel */
};

static struct PyMethodDef Xaq_methods[] = {
  {"__of__",(PyCFunction)xaq_of,0,""},
  
  {NULL,		NULL}		/* sentinel */
};

static struct PyMethodDef methods[] = {{NULL,	NULL}};

void
initAcquisition()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.16 $";
  PURE_MIXIN_CLASS(Acquirer,
    "Base class for objects that implicitly"
    " acquire attributes from containers\n"
    , Acquirer_methods);
  PURE_MIXIN_CLASS(ExplicitAcquirer,
    "Base class for objects that explicitly"
    " acquire attributes from containers\n"
    , Xaq_methods);

  UNLESS(ExtensionClassImported) return;

  UNLESS(Acquired=PyString_FromStringAndSize(NULL,42)) return;
  strcpy(PyString_AsString(Acquired),
	 "<Special Object Used to Force Acquisition>");

  /* Create the module and add the functions */
  m = Py_InitModule4("Acquisition", methods,
	   "Provide base classes for acquiring objects\n\n"
	   "$Id: Acquisition.c,v 1.16 1998/03/23 20:23:35 jim Exp $\n",
		     OBJECT(NULL),PYTHON_API_VERSION);

  d = PyModule_GetDict(m);
  init_py_names();
  PyExtensionClass_Export(d,"Acquirer",AcquirerType);
  PyExtensionClass_Export(d,"ImplicitAcquisitionWrapper",Wrappertype);
  PyExtensionClass_Export(d,"ExplicitAcquirer",ExplicitAcquirerType);
  PyExtensionClass_Export(d,"ExplicitAcquisitionWrapper",XaqWrappertype);

  /* Create aliases */
  PyDict_SetItemString(d,"Implicit",OBJECT(&AcquirerType));
  PyDict_SetItemString(d,"Explicit",OBJECT(&ExplicitAcquirerType));
  
  PyDict_SetItemString(d,"__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));
  PyDict_SetItemString(d,"Acquired",Acquired);

  CHECK_FOR_ERRORS("can't initialize module Acquisition");
}

/*****************************************************************************
  $Log: Acquisition.c,v $
  Revision 1.16  1998/03/23 20:23:35  jim
  Added lots of new machinery to handle wrapping of acquired objects.

  Revision 1.15  1998/01/21 19:00:48  jim
  Fixed __len__ bugs and added free lists for methods and wrappers

  Revision 1.14  1998/01/05 13:38:31  jim
  Added special module variable, 'Acquired'.  If the value of this
  variable is assigned to an attribute, then the value of the attribute
  will be acquired, even if it might not otherwize be acquired.

  Revision 1.13  1997/11/19 13:51:14  jim
  Extended compile option to implicitly acquire __roles__ to
  implicitly acquire roles even for explicit acquirers.

  Revision 1.12  1997/11/19 13:39:32  jim
  Changed filter machinery so that wrapped objects are used as
  inst and parent in filter.

  Revision 1.11  1997/11/07 19:00:34  jim
  Added compile option to implicitly acquire __roles__.

  Revision 1.10  1997/10/28 22:09:17  jim
  Added another argument to the aq_acquire filter signature.
  Changed name of acquire method to aq_acquire.  Explicit.acquire is
  an alias.

  Revision 1.9  1997/10/28 19:36:46  jim
  Changed semantics is acquire method:

    - Available for Implicit and Explicit,

    - Does not filter names with leading underscore,

    - Accepts optional 'filter' and 'extra' arguments.  If 'filter'
      is provided, then it must be a callable object and it is
      called with five arguments:

        orig -- The original (unwrapped) object

        inst -- The object in which an attribute is found

        name -- The attribute name

        v -- The attribute value

        extra -- The 'extra' value passed to 'acquire' or None.

      The filter function should return 1 if the attribute should
      be returned by acquire and 0 otherwise.  It may also raise an
      error, in which case the error is propigated.

  Revision 1.8  1997/07/02 20:15:27  jim
  Added stupid parens to make 'gcc -Wall -pedantic' and Barry happy.

  Revision 1.6  1997/06/19 19:31:39  jim
  Added ident string.

  Revision 1.5  1997/06/19 19:24:21  jim
  Many fixes and consolodation with Xaq.

  Revision 1.3  1997/02/19 22:30:33  jim
  Added $#@! missing static declaration.

  Revision 1.2  1997/02/17 16:20:11  jim
  Fixed bug in mix-in class declaration.
  Added __version__.


*/
