/*

  Copyright (c) 1996-1998, Digital Creations, Fredericksburg, VA, USA.  
  All rights reserved.
  
  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are
  met:
  
    o Redistributions of source code must retain the above copyright
      notice, this list of conditions, and the disclaimer that follows.
  
    o Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions, and the following disclaimer in
      the documentation and/or other materials provided with the
      distribution.
  
    o Neither the name of Digital Creations nor the names of its
      contributors may be used to endorse or promote products derived
      from this software without specific prior written permission.
  
  
  THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS AND CONTRIBUTORS *AS
  IS* AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
  TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
  PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL
  CREATIONS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
  OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
  TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
  USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
  DAMAGE.

  $Id: Acquisition.c,v 1.30 1999/07/28 17:59:46 jim Exp $

  If you have questions regarding this software,
  contact:
 
    Digital Creations L.C.  
    info@digicool.com
 
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
#define UNLESS(E) if (!(E))
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
  if (! args && PyErr_Occurred()) return NULL;
  UNLESS(name=PyObject_GetAttr(self,name)) return NULL;
  ASSIGN(name,PyEval_CallObjectWithKeywords(name,args,kw));
  if (args) Py_DECREF(args);
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
  
  if (freeWrappers)
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

  switch(*name)
    {
    case 'b':
      if (strcmp(name,"base")==0)
	{
	  if (self->obj)
	    {
	      r=self->obj;
	      while (isWrapper(r) && WRAPPER(r)->obj) r=WRAPPER(r)->obj;
	    }
	  else r=Py_None;
	  Py_INCREF(r);
	  return r;
	}
      break;
    case 'p':
      if (strcmp(name,"parent")==0)
	{
	  if (self->container) r=self->container;
	  else r=Py_None;
	  Py_INCREF(r);
	  return r;
	}
      break;
    case 's':
      if (strcmp(name,"self")==0)
	{
	  if (self->obj) r=self->obj;
	  else r=Py_None;
	  Py_INCREF(r);
	  return r;
	}
      break;
    case 'e':
      if (strcmp(name,"explicit")==0)
	{
	  if (self->ob_type != (PyTypeObject *)&XaqWrappertype)
	    return newWrapper(self->obj, self->container, 
			      (PyTypeObject *)&XaqWrappertype);
	  Py_INCREF(self);
	  return OBJECT(self);
	}
      break;
    case 'a':
      if (strcmp(name,"acquire")==0)
	{
	  return Py_FindAttr(OBJECT(self),oname);
	}
      break;
    case 'c':
      if (strcmp(name,"chain")==0)
	{
	  if (r=PyList_New(0)) 
	    while (1)
	      {
		if (PyList_Append(r,OBJECT(self)) >= 0)
		  {
		    if (isWrapper(self) && self->container) 
		      {
			self=WRAPPER(self->container);
			continue;
		      }
		  }
		else
		  {
		    Py_DECREF(r);
		  }
		break;
	      }
	  return r;
	}
      break;
    case 'i':
      if (strcmp(name,"inContextOf")==0)
	{
	  return Py_FindAttr(OBJECT(self),oname);
	}
      if (strcmp(name,"inner")==0)
	{
	  if (self->obj)
	    {
	      r=self->obj;
	      while (isWrapper(r) && WRAPPER(r)->obj) 
		{
		  self=WRAPPER(r);
		  r=WRAPPER(r)->obj;
		}
	      r=OBJECT(self);
	    }
	  else r=Py_None;

	  Py_INCREF(r);
	  return r;
	}
      break;

    case 'u':
      if (strcmp(name,"uncle")==0)
	{
	  return PyString_FromString("Bob");
	}
      break;
      
    }

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
  if (ir) return 1;
  Py_DECREF(r);
  return 0;
err:
  Py_DECREF(r);
  return -1;
}

static PyObject *
Wrapper_acquire(Wrapper *self, PyObject *oname,
		PyObject *filter, PyObject *extra, PyObject *orig,
		int sob, int sco)
{
  PyObject *r, *v, *tb;
  char *name;

  name=PyString_AsString(oname);
  if (*name++=='a' && *name++=='q' && *name++=='_'
     && (r=Wrapper_special(self, name, oname))) 
    {
      if (filter)
	switch(apply_filter(filter,OBJECT(self),oname,r,extra,orig))
	  {
	  case -1: return NULL;
	  case 1: return r;
	  }
      else return r;
    }

  if (sob && self->obj)
    {
      if (isWrapper(self->obj))
	{
	  r=Wrapper_acquire((Wrapper*)self->obj,
			    oname,filter,extra,orig,1,1);
	  if (r) goto acquired;
	  PyErr_Fetch(&r,&v,&tb);
	  if (r && (r != PyExc_AttributeError || PyObject_Compare(v,oname) != 0))
	    {
	      PyErr_Restore(r,v,tb);
	      return NULL;
	    }
	  Py_XDECREF(r); Py_XDECREF(v); Py_XDECREF(tb);
	  r=NULL;
	}
      else if ((r=PyObject_GetAttr(self->obj,oname)))
	{
	  if (isWrapper(r) && WRAPPER(r)->container==self->obj)
	    {
	      if (r->ob_refcnt==1)
		{
		  Py_INCREF(self);
		  ASSIGN(((Wrapper*)r)->container,OBJECT(self));
		}
	      else
		ASSIGN(r,newWrapper(((Wrapper*)r)->obj,
				    OBJECT(self), r->ob_type));
	    }
	  else if (PyECMethod_Check(r) && PyECMethod_Self(r)==self->obj)
	    ASSIGN(r,PyECMethod_New(r,OBJECT(self)));
	  else if (has__of__(r)) ASSIGN(r,__of__(r,OBJECT(self)));
	  if (filter)
	    switch(apply_filter(filter,OBJECT(self),oname,r,extra,orig))
	      {
	      case -1: return NULL;
	      case 1: return r;
	      }
	  else return r;
	}
      else {
	PyErr_Fetch(&r,&v,&tb);
	if (r != PyExc_AttributeError || PyObject_Compare(v,oname) != 0)
	  {
	    PyErr_Restore(r,v,tb);
	    return NULL;
	  }
	Py_XDECREF(r); Py_XDECREF(v); Py_XDECREF(tb);
	r=NULL;
      }
      PyErr_Clear();
    }

  if (sco && self->container) 
    {
      if (isWrapper(self->container))
	{
	  if (self->obj && self->obj->ob_type == (PyTypeObject*)&Wrappertype)
	    {
	      if (WRAPPER(self->obj)->container==
		 WRAPPER(self->container)->container) sob=1, sco=0;
	      else if (WRAPPER(self->obj)->container==
		      WRAPPER(self->container)->obj)  sob=0, sco=1;
	      else                                    sob=1, sco=1;
	      r=Wrapper_acquire((Wrapper*)self->container,
				oname,filter,extra,orig, sob, sco);
	   }
	  else
	    r=Wrapper_acquire((Wrapper*)self->container,
			      oname,filter,extra,orig,1,1);

	  
	  if (r) goto acquired;
	  return NULL;
	}
      else
	{
	  if ((r=PyObject_GetAttr(self->container,oname)))
	    if (filter)
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
  if (has__of__(r)) ASSIGN(r,__of__(r,OBJECT(self)));
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
  if (isWrapper(self->container))
    ASSIGN(r,Wrapper_acquire(WRAPPER(self->container),
			     oname,NULL,NULL,NULL,1,1));
  else
    ASSIGN(r,PyObject_GetAttr(self->container,oname));
  
  if (r && has__of__(r)) ASSIGN(r, __of__(r,OBJECT(self)));
  return r;
}

static PyObject *
Wrapper_getattro_(Wrapper *self, PyObject *oname, int sob, int sco)
{
  PyObject *r, *v, *tb;
  char *name;

  name=PyString_AsString(oname);
  if (*name=='a' && name[1]=='q' && name[2]=='_'
     && (r=Wrapper_special(self, name+3, oname))) return r;

  if (sob && self->obj && (r=PyObject_GetAttr(self->obj,oname)))
    {
      if (r == Acquired) return handle_Acquired(self, oname, r);
      if (isWrapper(r) && WRAPPER(r)->container==self->obj)
	{
	  if (r->ob_refcnt==1)
	    {
	      Py_INCREF(self);
	      ASSIGN(((Wrapper*)r)->container,OBJECT(self));
	    }
	  else
	    ASSIGN(r, newWrapper(((Wrapper*)r)->obj,OBJECT(self),r->ob_type));
	}
      else if (PyECMethod_Check(r) && PyECMethod_Self(r)==self->obj)
	ASSIGN(r,PyECMethod_New(r,OBJECT(self)));
      else if (has__of__(r))
	ASSIGN(r,__of__(r,OBJECT(self)));
      return r;
    }
  if (self->obj) 
    if (sob) {
      PyErr_Fetch(&r,&v,&tb);
      if (r != PyExc_AttributeError || PyObject_Compare(v,oname) != 0)
	{
	  PyErr_Restore(r,v,tb);
	  return NULL;
	}
      Py_XDECREF(r); Py_XDECREF(v); Py_XDECREF(tb);
      r=NULL;
    }
  else PyErr_Clear();

  if ((*name != '_')
     && self->container && sco)
    {
      if (self->container->ob_type == self->ob_type &&
	 self->obj->ob_type==self->ob_type)
	{
	  if (WRAPPER(self->obj)->container==
	     WRAPPER(self->container)->container) sob=1, sco=0;
	  else if (WRAPPER(self->obj)->container==
		  WRAPPER(self->container)->obj)  sob=0, sco=1;
	  else                                    sob=1, sco=1;
	  r=Wrapper_getattro_(WRAPPER(self->container), oname, sob, sco);
	}
      else r=PyObject_GetAttr(self->container,oname);

      if (r)
	{
	  if (has__of__(r))
	    ASSIGN(r, __of__(r,OBJECT(self)));
	  return r;
	}
      PyErr_Clear();
    }

  if (*name++=='_' && strcmp(name,"_init__")==0)
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
  PyObject *r, *v, *tb;
  char *name;

  name=PyString_AsString(oname);

  if (*name=='_')
    {
      if (strcmp(name,"__init__")==0) return Py_FindAttr(OBJECT(self),oname);
    }  

  if (*name=='a')
    {
      if (name[1]=='c')
	{
	  if (strcmp(name+2,"quire")==0)
	    return Py_FindAttr(OBJECT(self),oname);
	}      
      else if (name[1]=='q' && name[2]=='_'
	      && (r=Wrapper_special(self, name+3, oname))) return r;
    }

  if (self->obj && (r=PyObject_GetAttr(self->obj,oname)))
    {
      if (r==Acquired) return handle_Acquired(self,oname,r);
      if (isWrapper(r) && WRAPPER(r)->container==self->obj)
	{
	  if (r->ob_refcnt==1)
	    {
	      Py_INCREF(self);
	      ASSIGN(((Wrapper*)r)->container,OBJECT(self));
	    }
	  else
	    ASSIGN(r, newWrapper(((Wrapper*)r)->obj,
				 OBJECT(self), r->ob_type));
	}
      else if (PyECMethod_Check(r) && PyECMethod_Self(r)==self->obj)
	ASSIGN(r,PyECMethod_New(r,OBJECT(self)));
      else if (has__of__(r)) ASSIGN(r,__of__(r,OBJECT(self)));
      return r;
    }
  if (self->obj) {
    PyErr_Fetch(&r,&v,&tb);
    if (r != PyExc_AttributeError || PyObject_Compare(v,oname) != 0)
      {
	PyErr_Restore(r,v,tb);
	return NULL;
      }
    Py_XDECREF(r); Py_XDECREF(v); Py_XDECREF(tb);
    r=NULL;
  }

  PyErr_SetObject(PyExc_AttributeError,oname);
  return NULL;
}

static int
Wrapper_setattro(Wrapper *self, PyObject *name, PyObject *v)
{
  if (v && v->ob_type==(PyTypeObject*)&Wrappertype) v=((Wrapper*)v)->obj;
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

  if ((r=PyObject_GetAttr(OBJECT(self),py__repr__)))
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

  if ((r=PyObject_GetAttr(OBJECT(self),py__str__)))
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
      if ((r=PyObject_GetAttr(OBJECT(self), py__getitem__)))
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
  if (v)
    {
      UNLESS(v=CallMethodO(OBJECT(self),py__setitem__,
			   Build("(iO)", i, v),NULL))
	return -1;
    }
  else
    {
      UNLESS(v=CallMethodO(OBJECT(self),py__delitem__,
			   Build("(i)", i),NULL))
	return -1;
    }
  Py_DECREF(v);
  return 0;
}

static int
Wrapper_ass_slice(Wrapper *self, int  ilow, int  ihigh, PyObject *v)
{
  if (v)
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
  if (v)
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

static PyObject *
Wrapper_inContextOf(Wrapper *self, PyObject *args)
{
  PyObject *o, *c;
  int inner=0;

  UNLESS(PyArg_ParseTuple(args,"O|i",&o,&inner)) return NULL;

  if (inner)
    while (self->obj && isWrapper(self->obj))
      self=WRAPPER(self->obj);

  if (OBJECT(self)==o) return PyInt_FromLong(1);
  c=self->container;
  while (1)
    {
      if (c==o) return PyInt_FromLong(1);
      if (isWrapper(c)) c=WRAPPER(c)->container;
      else return PyInt_FromLong(0);
    }
}

static struct PyMethodDef Wrapper_methods[] = {
  {"__init__", (PyCFunction)Wrapper__init__, 0,
   "Initialize an Acquirer Wrapper"},
  {"acquire", (PyCFunction)Wrapper_acquire_method, METH_VARARGS,
   "Get an attribute, acquiring it if necessary"},
  {"aq_acquire", (PyCFunction)Wrapper_acquire_method, METH_VARARGS,
   "Get an attribute, acquiring it if necessary"},
  {"aq_inContextOf", (PyCFunction)Wrapper_inContextOf, METH_VARARGS,
   "Test whether the object is currently in the context of the argument"},
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

  UNLESS(PyArg_ParseTuple(args, "O", &inst)) return NULL;

  UNLESS(PyExtensionInstance_Check(inst))
    {
      PyErr_SetString(PyExc_TypeError,
		      "attempt to wrap extension method using an object that\n"
		      "is not an extension class instance.");
      return NULL;
    }

  return newWrapper(self, inst, (PyTypeObject *)&Wrappertype);
}

static PyObject *
xaq_of(PyObject *self, PyObject *args)
{
  PyObject *inst;

  UNLESS(PyArg_ParseTuple(args, "O", &inst)) return NULL;

  UNLESS(PyExtensionInstance_Check(inst))
    {
      PyErr_SetString(PyExc_TypeError,
		      "attempt to wrap extension method using an object that\n"
		      "is not an extension class instance.");
      return NULL;
    }

  return newWrapper(self, inst, (PyTypeObject *)&XaqWrappertype);
}

static struct PyMethodDef Acquirer_methods[] = {
  {"__of__",(PyCFunction)acquire_of, METH_VARARGS, 
   "__of__(context) -- return the object in a context"},
  
  {NULL,		NULL}		/* sentinel */
};

static struct PyMethodDef Xaq_methods[] = {
  {"__of__",(PyCFunction)xaq_of, METH_VARARGS,""},
  
  {NULL,		NULL}		/* sentinel */
};

static struct PyMethodDef methods[] = {{NULL,	NULL}};

void
initAcquisition()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.30 $";
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
	   "$Id: Acquisition.c,v 1.30 1999/07/28 17:59:46 jim Exp $\n",
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
