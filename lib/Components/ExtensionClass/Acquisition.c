/*

  $Id: Acquisition.c,v 1.9 1997/10/28 19:36:46 jim Exp $

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


  Full description

  $Log: Acquisition.c,v $
  Revision 1.9  1997/10/28 19:36:46  jim
  Changed semantics is acquire method:

    - Available for Impleicit and Explicit,

    - Does not filter names with leading underscore,

    - Accepts optional 'filter' and 'extra' arguments.  If 'filter'
      is provided, then it must be a callable object and it is
      called with four arguments:

        inst -- The object in which an attribute is found

        name -- The attribute name

        v -- The attribute value

        extra -- The 'extra' value passed to 'acquire' or None.

      The filter function should return 1 if the attribute should
      be returned by acquire and 0 otherwise.  It may also raise an
      error, in which case the error is propigated.

  Revision 1.8  1997/07/02 20:15:27  jim
  Added stupid parens to make 'gcc -Wall -pedantic' and Barry happy.

  Revision 1.7  1997/06/19 19:32:31  jim
  *** empty log message ***

  Revision 1.6  1997/06/19 19:31:39  jim
  Added ident string.

  Revision 1.5  1997/06/19 19:24:21  jim
  Many fixes and consolodation with Xaq.

  Revision 1.4  1997/02/20 00:55:29  jim
  *** empty log message ***

  Revision 1.3  1997/02/19 22:30:33  jim
  Added $#@! missing static declaration.

  Revision 1.2  1997/02/17 16:20:11  jim
  Fixed bug in mix-in class declaration.
  Added __version__.

  Revision 1.1  1997/02/17 15:05:40  jim
  *** empty log message ***


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

staticforward PyExtensionClass Wrappertype, XaqWrappertype;

#define isWrapper(O) ((O)->ob_type==(PyTypeObject*)&Wrappertype || \
		      (O)->ob_type==(PyTypeObject*)&XaqWrappertype)

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

static Wrapper *
newWrapper(PyObject *obj, PyObject *container, PyTypeObject *Wrappertype)
{
  Wrapper *self;
  
  UNLESS(self = PyObject_NEW(Wrapper, Wrappertype)) return NULL;
  Py_INCREF(obj);
  Py_INCREF(container);
  self->obj=obj;
  self->container=container;
  return self;
}


static void
Wrapper_dealloc(Wrapper *self)     
{
  Py_DECREF(self->obj);
  Py_DECREF(self->container);
  PyMem_DEL(self);
}

static PyObject *
Wrapper_getattro(Wrapper *self, PyObject *oname)
{
  PyObject *r;
  char *name;

  if(self->obj && (r=PyObject_GetAttr(self->obj,oname)))
    {
      if(r->ob_type==self->ob_type)
	{
	  if(r->ob_refcnt==1)
	    {
	      Py_INCREF(self);
	      ASSIGN(((Wrapper*)r)->container,(PyObject*)self);
	    }
	  else
	    ASSIGN(r,(PyObject*)newWrapper(((Wrapper*)r)->obj,
					   (PyObject*)self,self->ob_type));
	}
      else if(PyECMethod_Check(r) && PyECMethod_Self(r)==self->obj)
	ASSIGN(r,PyECMethod_New(r,(PyObject*)self));
      else if(has__of__(r))
	ASSIGN(r,CallMethodO(r,py__of__,Build("(O)", self), NULL));
      return r;
    }
  if(self->obj) PyErr_Clear();

  name=PyString_AsString(oname);

  if(*name=='a' && strcmp(name,"acquire")==0)
    return Py_FindAttr((PyObject*)self,oname);

  if(*name != '_')
    {
      
      if(*name++=='a' && *name++=='q' && *name++=='_')
	{
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
	}

      if(self->container) 
	{
	  if((r=PyObject_GetAttr(self->container,oname)))
	    return r;
	  PyErr_Clear();
	}
    }

  if(*name++=='_' && strcmp(name,"_init__")==0)
    return Py_FindAttr((PyObject*)self,oname);

  PyErr_SetObject(PyExc_AttributeError,oname);
  return NULL;
}

static PyObject *
Xaq_getattro(Wrapper *self, PyObject *oname)
{
  PyObject *r;
  char *name;

  if(self->obj && (r=PyObject_GetAttr(self->obj,oname)))
    {
      if(r->ob_type==self->ob_type)
	{
	  if(r->ob_refcnt==1)
	    {
	      Py_INCREF(self);
	      ASSIGN(((Wrapper*)r)->container,(PyObject*)self);
	    }
	  else
	    ASSIGN(r,(PyObject*)newWrapper(((Wrapper*)r)->obj,
					   (PyObject*)self, self->ob_type));
	}
      else if(PyECMethod_Check(r) && PyECMethod_Self(r)==self->obj)
	ASSIGN(r,PyECMethod_New(r,(PyObject*)self));
      else if(has__of__(r))
	ASSIGN(r,CallMethodO(r,py__of__,Build("(O)", self), NULL));
      return r;
    }
  if(self->obj) PyErr_Clear();

  name=PyString_AsString(oname);

  if(*name=='a' && strcmp(name,"acquire")==0)
    return Py_FindAttr((PyObject*)self,oname);

  if(*name=='_' && strcmp(name,"__init__")==0)
    return Py_FindAttr((PyObject*)self,oname);

  if(*name++=='a' && *name++=='q' && *name++=='_')
    {
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
    }

  PyErr_SetObject(PyExc_AttributeError,oname);
  return NULL;
}

static int
apply_filter(PyObject *filter, PyObject *inst, PyObject *oname, PyObject *r,
	     PyObject *extra)
{
  PyObject *fr;
  int ir;

  UNLESS(fr=PyTuple_New(4)) goto err;
  PyTuple_SET_ITEM(fr,0,inst);
  Py_INCREF(inst);
  PyTuple_SET_ITEM(fr,1,oname);
  Py_INCREF(oname);
  PyTuple_SET_ITEM(fr,2,r);
  Py_INCREF(r);
  PyTuple_SET_ITEM(fr,3,extra);
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

static PyObject *
Wrapper_acquire(Wrapper *self, PyObject *oname,
		PyObject *filter, PyObject *extra)
{
  PyObject *r;
  char *name;
  int ir;

  if(self->obj)
    {
      if(r=PyObject_GetAttr(self->obj,oname))
	{
	  if(r->ob_type==self->ob_type)
	    {
	      if(r->ob_refcnt==1)
		{
		  Py_INCREF(self);
		  ASSIGN(((Wrapper*)r)->container,(PyObject*)self);
		}
	      else
		ASSIGN(r,(PyObject*)newWrapper(((Wrapper*)r)->obj,
					       (PyObject*)self, self->ob_type));
	    }
	  else if(PyECMethod_Check(r) && PyECMethod_Self(r)==self->obj)
	    ASSIGN(r,PyECMethod_New(r,(PyObject*)self));
	  else if(has__of__(r))
	    ASSIGN(r,CallMethodO(r,py__of__,Build("(O)", self), NULL));
	  if(filter)
	    switch(apply_filter(filter,self->obj,oname,r,extra))
	      {
	      case -1: return NULL;
	      case 1: return r;
	      }
	  else return r;
	}
      PyErr_Clear();
    }

  name=PyString_AsString(oname);
  if(*name++=='a' && *name++=='q' && *name++=='_')
    {
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
    }
  
  if(self->container) 
    {
      if(isWrapper(self->container))
	{
	  if((r=Wrapper_acquire((Wrapper*)self->container,oname,filter,extra)))
	    return r;
	}
      else
	{
	  if((r=PyObject_GetAttr(self->container,oname)))
	    if(filter)
	      switch(apply_filter(filter,self->container,oname,r,extra))
		{
		case -1: return NULL;
		case 1: return r;
		}
	    else return r;
	}
      PyErr_Clear();
    }

  PyErr_SetObject(PyExc_AttributeError,oname);
  return NULL;
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

  if((r=PyObject_GetAttr((PyObject*)self,py__repr__)))
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

  if((r=PyObject_GetAttr((PyObject*)self,py__str__)))
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
  return CallMethodO((PyObject*)self,py__call__,args,kw);
}



/* Code to handle accessing Wrapper objects as sequence objects */

static int
Wrapper_length(Wrapper *self)
{
  long l;
  PyObject *r;

  UNLESS(r=CallMethodO((PyObject*)self,py__len__,NULL,NULL))  return -1;
  l=PyInt_AsLong(r);
  Py_DECREF(r);
  return l;
}

static PyObject *
Wrapper_concat(Wrapper *self, PyObject *bb)
{
  return CallMethodO((PyObject*)self,py__concat__,Build("(O)", bb) ,NULL);
}

static PyObject *
Wrapper_repeat(Wrapper *self, int  n)
{
  return CallMethodO((PyObject*)self,py__repeat__,Build("(i)", n),NULL);
}

static PyObject *
Wrapper_item(Wrapper *self, int  i)
{
  return CallMethodO((PyObject*)self,py__getitem__, Build("(i)", i),NULL);
}

static PyObject *
Wrapper_slice(Wrapper *self, int  ilow, int  ihigh)
{
  return CallMethodO((PyObject*)self,py__getslice__,
		     Build("(ii)", ilow, ihigh),NULL);
}

static int
Wrapper_ass_item(Wrapper *self, int  i, PyObject *v)
{
  if(v)
    {
      UNLESS(v=CallMethodO((PyObject*)self,py__setitem__,
			   Build("(iO)", i, v),NULL))
	return -1;
    }
  else
    {
      UNLESS(v=CallMethodO((PyObject*)self,py__delitem__,
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
      UNLESS(v=CallMethodO((PyObject*)self,py__setslice__,
			   Build("(iiO)", ilow, ihigh, v),NULL))
	return -1;
    }
  else
    {
      UNLESS(v=CallMethodO((PyObject*)self,py__delslice__,
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
  return CallMethodO((PyObject*)self,py__getitem__,Build("(O)", key),NULL);
}

static int
Wrapper_ass_sub(Wrapper *self, PyObject *key, PyObject *v)
{
  if(v)
    {
      UNLESS(v=CallMethodO((PyObject*)self,py__setitem__,
			   Build("(OO)", key, v),NULL))
	return -1;
    }
  else
    {
      UNLESS(v=CallMethodO((PyObject*)self,py__delitem__,
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

  return Wrapper_acquire(self,name,filter,extra);
}

static struct PyMethodDef Wrapper_methods[] = {
  {"__init__", (PyCFunction)Wrapper__init__, 0,
   "Initialize an Acquirer Wrapper"},
  {"acquire", (PyCFunction)Wrapper_acquire_method, METH_VARARGS,
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

  return (PyObject*)newWrapper(self,args,(PyTypeObject *)&Wrappertype);
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

  return (PyObject*)newWrapper(self,args,(PyTypeObject *)&XaqWrappertype);
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
  char *rev="$Revision: 1.9 $";
  PURE_MIXIN_CLASS(Acquirer,
    "Base class for objects that implicitly"
    " acquire attributes from containers\n"
    , Acquirer_methods);
  PURE_MIXIN_CLASS(ExplicitAcquirer,
    "Base class for objects that explicitly"
    " acquire attributes from containers\n"
    , Xaq_methods);

  UNLESS(ExtensionClassImported) return;

  /* Create the module and add the functions */
  m = Py_InitModule4("Acquisition", methods,
		     "Provide base classes for acquiring objects\n\n"
		     "$Id: Acquisition.c,v 1.9 1997/10/28 19:36:46 jim Exp $\n",
		     (PyObject*)NULL,PYTHON_API_VERSION);

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

  CHECK_FOR_ERRORS("can't initialize module Acquisition");
}
