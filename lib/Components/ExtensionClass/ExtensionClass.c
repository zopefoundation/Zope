/*

  $Id: ExtensionClass.c,v 1.4 1996/12/06 17:12:29 jim Exp $

  Extension Class


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

  $Log: ExtensionClass.c,v $
  Revision 1.4  1996/12/06 17:12:29  jim
  Major speed enhancements for attribute lookup and calling special
  methods.

  Revision 1.3  1996/10/24 21:07:49  jim
  Fixed bug in returning __bases__ for base classes.
  Added missing PyErr_Clear() call.

  Revision 1.2  1996/10/23 18:36:56  jim
  Changed a bunch of single quotes to double and got rid of
  some superfluous semicolns that caused warning on SGI.

  Fixed bug in CCL_getattr when getting the __base__ attribute of a base
  class.

  Fixed a doc string.

  Revision 1.1  1996/10/22 22:26:08  jim
  *** empty log message ***


*/

static char ExtensionClass_module_documentation[] = 
"ExtensionClass - Classes implemented in c\n"
"\n"
"Built-in C classes are like Built-in types except that\n"
"they provide some of the behavior of Python classes:\n"
"\n"
"  - They provide access to unbound methods,\n"
"  - They can be called to create instances.\n"
"\n"
"$Id: ExtensionClass.c,v 1.4 1996/12/06 17:12:29 jim Exp $\n"
;

#include "Python.h"

#define ASSIGN(V,E) {PyObject *__e; __e=(E); Py_XDECREF(V); (V)=__e;}
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E) UNLESS(V)

#define INSTANCE_DICT(inst) \
*(((PyObject**)inst) + (inst->ob_type->tp_basicsize/sizeof(PyObject*) - 1))

typedef struct { PyObject_HEAD } Dataless;

/* Declarations for objects of type ExtensionClass */
#include "ExtensionClass.h"
staticforward PyExtensionClass CCLtype;

#define PyExtensionClass_Check(O) ((O)->ob_type == (PyTypeObject*)&CCLtype)
#define PyExtensionInstance_Check(O) \
   ((O)->ob_type->ob_type == (PyTypeObject*)&CCLtype)
#define AsPyExtensionClass(O) ((PyExtensionClass*)(O))
#define PyExtensionClassOf(O) ((PyExtensionClass*)((O)->ob_type))
#define AsPyObject(O) ((PyObject*)(O))

static PyObject *py__add__, *py__sub__, *py__mul__, *py__div__,
  *py__mod__, *py__pow__, *py__divmod__, *py__lshift__, *py__rshift__,
  *py__and__, *py__or__, *py__xor__, *py__coerce__, *py__neg__,
  *py__pos__, *py__abs__, *py__nonzero__, *py__inv__, *py__int__,
  *py__long__, *py__float__, *py__oct__, *py__hex__, *py__getitem__,
  *py__setitem__, *py__getslice__, *py__setslice__, *py__concat__,
  *py__repeat__, *py__len__, *py__bind_to_object__, *py__call__,
  *py__getattr__, *py__setattr__, *py__del__, *py__repr__, *py__str__,
  *py__hash__, *py__cmp__, *py__var_size__, *py__init__;

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
  INIT_PY_NAME(__getslice__);
  INIT_PY_NAME(__setslice__);
  INIT_PY_NAME(__concat__);
  INIT_PY_NAME(__repeat__);
  INIT_PY_NAME(__len__);
  INIT_PY_NAME(__bind_to_object__);
  INIT_PY_NAME(__call__);
  INIT_PY_NAME(__getattr__);
  INIT_PY_NAME(__setattr__);
  INIT_PY_NAME(__del__);
  INIT_PY_NAME(__repr__);
  INIT_PY_NAME(__str__);
  INIT_PY_NAME(__hash__);
  INIT_PY_NAME(__cmp__);
  INIT_PY_NAME(__var_size__);
  INIT_PY_NAME(__init__);
  
#undef INIT_PY_NAME
}

/* CMethod objects: */

typedef struct {
  PyObject_HEAD
  PyTypeObject *type;
  PyObject *self;
  char		*name;
  PyCFunction	meth;
  int		flags;
  char		*doc;
} CMethod;

staticforward PyTypeObject CMethodType;

#define CMethod_Check(O) ((O)->ob_type==&CMethodType)
#define UnboundCMethod_Check(O) \
  ((O)->ob_type==&CMethodType && ! ((CMethod*)(O))->self)
#define AsCMethod(O) ((CMethod*)(O))

static int
CMethod_issubclass(PyExtensionClass *sub, PyExtensionClass *type)
{
  int i,l;
  PyObject *t;

  if(sub==type) return 1;
  if(! sub->bases) return 0;
  l=PyTuple_Size(sub->bases);
  for(i=0; i < l; i++)
    {
      t=PyTuple_GET_ITEM(sub->bases, i);
      if(t==(PyObject*)type) return 1;
      if(PyExtensionClass_Check(t)
	 && AsPyExtensionClass(t)->bases
	 && CMethod_issubclass(AsPyExtensionClass(t),type)
	 ) return 1;
    }
  return 0;
}

#define Subclass_Check(C1,C2) \
  CMethod_issubclass((PyExtensionClass *)(C1), (PyExtensionClass *)(C2))

#define SubclassInstance_Check(C1,C2) \
  CMethod_issubclass((PyExtensionClass *)((C1)->ob_type), \
		     (PyExtensionClass *)(C2))


static CMethod *
newCMethod(PyTypeObject *type,
	   char *name, PyCFunction meth, int flags, char *doc)
{
  CMethod *self;

  
  UNLESS(self = PyObject_NEW(CMethod, &CMethodType)) return NULL;
  Py_INCREF(type);
  self->type=type;
  self->self=NULL;
  self->name=name;
  self->meth=meth;
  self->flags=flags;
  self->doc=doc;
  return self;
}

static CMethod *
bindCMethod(CMethod *m, PyObject *inst)
{
  CMethod *self;
  
  UNLESS(inst->ob_type==m->type ||
	 (PyExtensionInstance_Check(inst)
	  && SubclassInstance_Check(inst,m->type))
	 )
    {
      Py_INCREF(m);
      return m;
    }

  UNLESS(self = PyObject_NEW(CMethod, &CMethodType)) return NULL;

  Py_INCREF(inst);
  Py_INCREF(m->type);
  self->type=m->type;
  self->self=inst;
  self->name=m->name;
  self->meth=m->meth;
  self->flags=m->flags;
  self->doc=m->doc;
  return self;
}

static void
CMethod_dealloc(CMethod *self)
{
  Py_DECREF(self->type);
  Py_XDECREF(self->self);
  PyMem_DEL(self);
}

static PyObject *
call_cmethod(CMethod *self, PyObject *inst, PyObject *args, PyObject *kw)
{
  if (!(self->flags & METH_VARARGS)) {
    int size = PyTuple_Size(args);
    if (size == 1)
      args = PyTuple_GET_ITEM(args, 0);
    else if (size == 0)
      args = NULL;
  }
  if (self->flags & METH_KEYWORDS)
    return (*(PyCFunctionWithKeywords)self->meth)(inst, args, kw);
  else
    {
      if (kw != NULL && PyDict_Size(kw) != 0)
	{
	  PyErr_SetString(PyExc_TypeError,
			  "this function takes no keyword arguments");
	  return NULL;
	}
      return (*self->meth)(inst, args);
    }
}


static PyObject *
CMethod_call(CMethod *self, PyObject *args, PyObject *kw)
{
  int size;
  char *buf;
  PyObject *s;

  if(self->self) return call_cmethod(self,self->self,args,kw);

  if((size=PyTuple_Size(args)) > 0)
    {
      PyObject *first=0;
      UNLESS(first=PyTuple_GET_ITEM(args, 0)) return NULL;
      if(first->ob_type==self->type
	 ||
	 (PyExtensionInstance_Check(first)
	  &&
	  CMethod_issubclass(PyExtensionClassOf(first),
			     AsPyExtensionClass(self->type))
	  )
	 );
      {
	PyObject *rest=0;
	UNLESS(rest=PySequence_GetSlice(args,1,size)) return NULL;
	return call_cmethod(self,first,rest,kw);
      }
    }

  /* Call of unbound method without instance argument */
  size=strlen(self->type->tp_name);
  UNLESS(s=PyString_FromStringAndSize(NULL,size+48)) return NULL;
  buf=PyString_AsString(s);
  sprintf(buf,
	  "unbound C method must be called with %s 1st argument",
	  self->type->tp_name);	
  PyErr_SetObject(PyExc_TypeError,s);
  Py_DECREF(s);
  return NULL;
}

static PyObject *
CMethod_getattr(CMethod *self, char *name)
{
  PyObject *r;

  if(strcmp(name,"__name__")==0 || strcmp(name,"func_name")==0 )
    return PyString_FromString(self->name);
  if(strcmp(name,"func_code")==0 ||
     strcmp(name,"im_func")==0)
    {
      Py_INCREF(self);
      return (PyObject *)self;
    }
  if(strcmp(name,"__doc__")==0 ||
     strcmp(name,"func_doc")==0 ||
     strcmp(name,"func_doc")==0)
    {
      if(self->doc)
	return PyString_FromString(self->doc);
      else
	return PyString_FromString("");
    }
  if(strcmp(name,"im_class")==0)
    {
      Py_INCREF(self->type);
      return (PyObject *)self->type;
    }
  if(strcmp(name,"im_self")==0)
    {
      if(self->self) r=self->self;
      else           r=Py_None;
      Py_INCREF(r);
      return r;
    }
}

static PyTypeObject CMethodType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"CMethod",			/*tp_name*/
	sizeof(CMethod),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)CMethod_dealloc,	/*tp_dealloc*/
	(printfunc)0,			/*tp_print*/
	(getattrfunc)CMethod_getattr,	/*tp_getattr*/
	(setattrfunc)0,			/*tp_setattr*/
	(cmpfunc)0,			/*tp_compare*/
	(reprfunc)0,			/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	(hashfunc)0,			/*tp_hash*/
	(ternaryfunc)CMethod_call,	/*tp_call*/
	(reprfunc)0,			/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	"Storage manager for unbound C function PyObject data"
	/* Documentation string */
};

/* PMethod objects: */

typedef struct {
  PyObject_HEAD
  PyTypeObject *type;
  PyObject     *self;
  PyObject     *meth;
} PMethod;

staticforward PyTypeObject PMethodType;

#define PMethod_Check(O) ((O)->ob_type==&PMethodType)
#define UnboundPMethod_Check(O) \
  ((O)->ob_type==&PMethodType && ! ((PMethod*)(O))->self)

#define UnboundEMethod_Check(O) \
  (((O)->ob_type==&PMethodType ||(O)->ob_type==&CMethodType) \
   && ! ((PMethod*)(O))->self)


static PMethod *
newPMethod(PyTypeObject *type, PyObject *meth)
{
  PMethod *self;
  
  UNLESS(self = PyObject_NEW(PMethod, &PMethodType)) return NULL;
  Py_INCREF(type);
  Py_INCREF(meth);
  self->type=type;
  self->self=NULL;
  self->meth=meth;
  return self;
}

static PMethod *
bindPMethod(PMethod *m, PyObject *inst)
{
  PMethod *self;

  UNLESS(PyExtensionInstance_Check(inst))
    {
      PyErr_SetString(PyExc_TypeError,
		      "attempt to wrap extension method using an object that\n"
		      "is not an extension class instance.");
      return NULL;
    }
  
  UNLESS(self = PyObject_NEW(PMethod, &PMethodType)) return NULL;

  Py_INCREF(inst);
  Py_INCREF(m->type);
  self->type=m->type;
  self->self=inst;
  self->meth=m->meth;
  return self;
}

static void
PMethod_dealloc(PMethod *self)
{
  Py_DECREF(self->type);
  Py_XDECREF(self->self);
  PyMem_DEL(self);
}  

static PyObject *
call_PMethod(PMethod *self, PyObject *inst, PyObject *args, PyObject *kw)
{
  PyObject *a;

  UNLESS(a=Py_BuildValue("(O)",inst)) return NULL;
  UNLESS_ASSIGN(a,PySequence_Concat(a,args)) return NULL;
  UNLESS_ASSIGN(a,PyEval_CallObjectWithKeywords(self->meth,a,kw)) return NULL;
  return a;
}

static PyObject *
PMethod_call(PMethod *self, PyObject *args, PyObject *kw)
{
  int size;
  char *buf;
  PyObject *s;

  if(self->self) return call_PMethod(self,self->self,args,kw);

  if((size=PyTuple_Size(args)) > 0)
    {
      PyObject *first=0;
      UNLESS(first=PyTuple_GET_ITEM(args, 0)) return NULL;
      if(first->ob_type==self->type
	 ||
	 (PyExtensionInstance_Check(first)
	  &&
	  CMethod_issubclass(PyExtensionClassOf(first),
			     AsPyExtensionClass(self->type))
	  )
	 );
      {
	PyObject *rest=0;
	UNLESS(rest=PySequence_GetSlice(args,1,size)) return NULL;
	return call_PMethod(self,first,rest,kw);
      }
    }

  /* Call of unbound method without instance argument */
  size=strlen(self->type->tp_name);
  UNLESS(s=PyString_FromStringAndSize(NULL,size+48)) return NULL;
  buf=PyString_AsString(s);
  sprintf(buf,
	  "unbound Python method must be called with %s 1st argument",
	  self->type->tp_name);	
  PyErr_SetObject(PyExc_TypeError,s);
  Py_DECREF(s);
  return NULL;
}

static PyObject *
PMethod_getattr(PMethod *self, char *name)
{
  PyObject *r;

  if(strcmp(name,"__name__")==0 || strcmp(name,"func_name")==0 )
    return PyObject_GetAttrString(self->meth,"__name__");
  if(strcmp(name,"im_func")==0)
    {
      Py_INCREF(self->meth);
      return self->meth;
    }
  if(strcmp(name,"__doc__")==0 ||
     strcmp(name,"func_doc")==0 ||
     strcmp(name,"func_doc")==0)
    return PyObject_GetAttrString(self->meth,"__doc__");
  if(strcmp(name,"im_class")==0)
    {
      Py_INCREF(self->type);
      return (PyObject *)self->type;
    }
  if(strcmp(name,"im_self")==0)
    {
      if(self->self) r=self->self;
      else           r=Py_None;
      Py_INCREF(r);
      return r;
    }
}

static PyTypeObject PMethodType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"Python Method",			/*tp_name*/
	sizeof(PMethod),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)PMethod_dealloc,	/*tp_dealloc*/
	(printfunc)0,			/*tp_print*/
	(getattrfunc)PMethod_getattr,	/*tp_getattr*/
	(setattrfunc)0,			/*tp_setattr*/
	(cmpfunc)0,			/*tp_compare*/
	(reprfunc)0,			/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	(hashfunc)0,			/*tp_hash*/
	(ternaryfunc)PMethod_call,	/*tp_call*/
	(reprfunc)0,			/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	"Storage manager for unbound C function PyObject data"
	/* Documentation string */
};

/* Special Methods */

#define HAS(M) (M && ((void*)M != (void*)MetaTypeUndefinedMethod))

#define UNARY_OP(OP) \
static PyObject * \
OP ## _by_name(PyObject *self, PyObject *args) { \
  UNLESS(PyArg_Parse(args,"")) return NULL; \
  return self->ob_type->tp_ ## OP(self); \
} 

UNARY_OP(repr)
UNARY_OP(str)

static PyObject * 
hash_by_name(PyObject *self, PyObject *args) { 
  long r; 
  UNLESS(PyArg_Parse(args,"")) return NULL; 
  UNLESS(-1 != (r=self->ob_type->tp_hash(self))) return NULL; 
  return PyInt_FromLong(r); 
} 

static PyObject *
call_by_name(PyObject *self, PyObject *args, PyObject *kw)
{
  return self->ob_type->tp_call(self,args,kw);
}

static PyObject *
compare_by_name(PyObject *self, PyObject *args)
{
  PyObject *other;
  long r;
  UNLESS(PyArg_Parse(args,"O", &other)) return NULL; 
  return PyInt_FromLong(self->ob_type->tp_compare(self,other)); 
} 

static PyObject *
getattr_by_name(PyObject *self, PyObject *args)
{
  char *name;
  UNLESS(PyArg_Parse(args,"s",&name)) return NULL;
  return self->ob_type->tp_getattr(self,name);
}

static PyObject *
setattr_by_name(PyObject *self, PyObject *args)
{
  char *name;
  PyObject *v;
  UNLESS(PyArg_Parse(args,"sO",&name,&v)) return NULL;
  UNLESS(-1 != self->ob_type->tp_setattr(self,name,v)) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

#if PYTHON_API_VERSION >= 1005

static PyObject *
getattro_by_name(PyObject *self, PyObject *args)
{
  PyObject *name;
  UNLESS(PyArg_Parse(args,"O",&name)) return NULL;
  return self->ob_type->tp_getattro(self,name);
}

static PyObject *
setattro_by_name(PyObject *self, PyObject *args)
{
  PyObject *name;
  PyObject *v;
  UNLESS(PyArg_Parse(args,"OO",&name,&v)) return NULL;
  UNLESS(-1 != self->ob_type->tp_setattro(self,name,v)) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

#endif
  
static PyObject * 
length_by_name(PyObject *self, PyObject *args)
{ 
  long r; 
  UNLESS(PyArg_Parse(args,"")) return NULL; 
  if(self->ob_type->tp_as_sequence)
    {
      UNLESS(-1 != (r=self->ob_type->tp_as_sequence->sq_length(self)))
	return NULL;
    }
  else
    {
      UNLESS(-1 != (r=self->ob_type->tp_as_mapping->mp_length(self)))
	return NULL;
    }
  return PyInt_FromLong(r); 
} 
  
static PyObject * 
getitem_by_name(PyObject *self, PyObject *args)
{ 
  PyObject *key;
  
  UNLESS(PyArg_Parse(args,"O",&key)) return NULL; 
  if(self->ob_type->tp_as_mapping)
    return self->ob_type->tp_as_mapping->mp_subscript(self,key);
  else
    {
      int index;
      UNLESS(-1 != (index=PyInt_AsLong(key))) return NULL;
      return self->ob_type->tp_as_sequence->sq_item(self,index);
    }
} 

static PyCFunction item_by_name=(PyCFunction)getitem_by_name;
static PyCFunction subscript_by_name=(PyCFunction)getitem_by_name;
  
static int
setitem_by_name(PyObject *self, PyObject *args)
{ 
  PyObject *key, *v;
  
  UNLESS(PyArg_Parse(args,"OO",&key,&v)) return NULL; 
  if(self->ob_type->tp_as_mapping)
    return self->ob_type->tp_as_mapping->mp_ass_subscript(self,key,v);
  else
    {
      int index;
      UNLESS(-1 != (index=PyInt_AsLong(key))) return -1;
      return self->ob_type->tp_as_sequence->sq_ass_item(self,index,v);
    }
}

static PyCFunction ass_item_by_name=(PyCFunction)setitem_by_name;
static PyCFunction ass_subscript_by_name=(PyCFunction)setitem_by_name;

static PyObject *
slice_by_name(PyObject *self, PyObject *args)
{
  int i1,i2;

  UNLESS(PyArg_Parse(args,"ii",&i1,&i2)) return NULL;
  return self->ob_type->tp_as_sequence->sq_slice(self,i1,i2);
}

static int
ass_slice_by_name(PyObject *self, PyObject *args)
{
  int i1,i2;
  PyObject *v;

  UNLESS(PyArg_Parse(args,"iiO",&i1,&i2,&v)) return -1;
  return self->ob_type->tp_as_sequence->sq_ass_slice(self,i1,i2,v);
}

static PyObject *
concat_by_name(PyObject *self, PyObject *args)
{
  PyObject *other;
  UNLESS(PyArg_Parse(args,"O",&other)) return NULL;
  return self->ob_type->tp_as_sequence->sq_concat(self,other);
}

static PyObject *
repeat_by_name(PyObject *self, PyObject *args)
{
  int r;
  UNLESS(PyArg_Parse(args,"i",&r)) return NULL;
  return self->ob_type->tp_as_sequence->sq_repeat(self,r);
}

#define BINOP(OP,AOP) \
static PyObject * \
OP ## _by_name(PyObject *self, PyObject *args) { \
  PyObject *v; \
  UNLESS(PyArg_Parse(args,"O",&v)) return NULL; \
  return PyNumber_ ## AOP(self,v); \
}

BINOP(add,Add)
BINOP(subtract,Subtract)
BINOP(multiply,Multiply)
BINOP(divide,Divide)
BINOP(remainder,Remainder)
BINOP(divmod,Divmod)

static PyObject *
power_by_name(PyObject *self, PyObject *args)
{
  PyObject *v, *z=NULL;
  UNLESS(PyArg_ParseTuple(args,"O|O",&v,&z)) return NULL; 
  return self->ob_type->tp_as_number->nb_power(self,v,z);
}

#define UNOP(OP) \
static PyObject * \
OP ## _by_name(PyObject *self, PyObject *args) { \
  UNLESS(PyArg_Parse(args,"")) return NULL; \
  return self->ob_type->tp_as_number->nb_ ## OP(self); \
}

UNOP(negative)
UNOP(positive)
UNOP(absolute)

static PyObject * 
nonzero_by_name(PyObject *self, PyObject *args) { 
  long r; 
  UNLESS(PyArg_Parse(args,"")) return NULL; 
  UNLESS(-1 != (r=self->ob_type->tp_as_number->nb_nonzero(self))) return NULL; 
  return PyInt_FromLong(r); 
} 

UNOP(invert)

BINOP(lshift,Lshift)
BINOP(rshift,Rshift)
BINOP(and,And)
BINOP(or,Or)
BINOP(xor,Xor)

static PyObject *
coerce_by_name(PyObject *self, PyObject *args)
{
  PyObject *v;
  int r;
  UNLESS(PyArg_Parse(args,"O", &v)) return NULL;
  UNLESS(-1 != (r=self->ob_type->tp_as_number->nb_coerce(&self,&v)))
    {
      Py_INCREF(Py_None);
      return Py_None;
    }
  args=Py_BuildValue("OO",self,v);
  Py_DECREF(self);
  Py_DECREF(v);
  return args;
} 

UNOP(long)
UNOP(int)
UNOP(float)
UNOP(oct)
UNOP(hex)

#define FILLENTRY(T,MN,N,F,D) if(T ## _ ## MN) { \
  UNLESS(-1 != PyMapping_SetItemString(dict,"__" # N "__", \
	 (PyObject*)newCMethod((PyTypeObject *)type,"__" # N "__", \
			       (PyCFunction)MN ## _by_name, F, # D))) \
    goto err; \
}

static PyObject *
getBaseDictionary(PyExtensionClass *type)
{
  PyNumberMethods *nm;
  PySequenceMethods *sm;
  PyMappingMethods *mm;
  PyObject *dict;

  UNLESS(dict=PyDict_New()) return NULL;
  
  FILLENTRY(type->tp, repr, repr, 0, "convert to an expression string");
  FILLENTRY(type->tp, hash, hash, 0, "compute a hash value");
  FILLENTRY(type->tp, call, call, 2, "call as a function");
  FILLENTRY(type->tp, compare, comp, 0, "compare with another object");
  FILLENTRY(type->tp, getattr, getattr, 0, "Get an attribute");
  FILLENTRY(type->tp, setattr, setattr, 0, "Set an attribute");

#if PYTHON_API_VERSION >= 1005
  FILLENTRY(type->tp, getattro, getattr, 0, "Get an attribute");
  FILLENTRY(type->tp, setattro, setattr, 0, "Set an attribute");
#endif

  if(sm=type->tp_as_sequence)
    {
      FILLENTRY(sm->sq, length, len, 0, "Get the object length");
      FILLENTRY(sm->sq, concat, concat, 0,
		"Concatinate the object with another");
      FILLENTRY(sm->sq, repeat, repeat, 0,
		"Get a new object that is the object repeated.");
      FILLENTRY(sm->sq, item, getitem, 0, "Get an item");
      FILLENTRY(sm->sq, slice, getslice, 0, "Get a slice");
      FILLENTRY(sm->sq, ass_item, setitem, 0, "Assign an item");
      FILLENTRY(sm->sq, ass_slice, setslice, 0, "Assign a slice");
    }      

  if(mm=type->tp_as_mapping)
    {
      FILLENTRY(mm->mp, length, len, 0, "Get the object length");
      FILLENTRY(mm->mp, subscript, getitem, 0, "Get an item");
      FILLENTRY(mm->mp, ass_subscript, setitem, 0, "Assign an item");
    }      

  if((nm=type->tp_as_number) != NULL)
    {
      FILLENTRY(nm->nb, add, add, 0, "Add to another");
      FILLENTRY(nm->nb, subtract, sub, 0, "Subtract another");
      FILLENTRY(nm->nb, multiply, mul, 0, "Multiple by another");
      FILLENTRY(nm->nb, divide, div, 0, "Divide by another");
      FILLENTRY(nm->nb, remainder, mod, 0, "Compute a remainder");
      FILLENTRY(nm->nb, power, pow, 1, "Raise to a power");
      FILLENTRY(nm->nb, divmod, divmod, 0,
		"Compute the whole result and remainder of dividing\n"
		"by another");
      FILLENTRY(nm->nb, negative, neg, 0, "Get the negative value.");
      FILLENTRY(nm->nb, positive, pos, 0, "Compute positive value");
      FILLENTRY(nm->nb, absolute, abs, 0, "Compute absolute value");
      FILLENTRY(nm->nb, nonzero, nonzero, 0, "Determine whether nonzero");
      FILLENTRY(nm->nb, invert, inv, 0, "Compute inverse");
      FILLENTRY(nm->nb, lshift, lshift, 0, "Shist left");
      FILLENTRY(nm->nb, rshift, rshift, 0, "Shist right");
      FILLENTRY(nm->nb, and, and, 0, "bitwize logical and");
      FILLENTRY(nm->nb, or, or, 0, "bitwize logical or");
      FILLENTRY(nm->nb, xor, xor, 0, "bitwize logical excusive or");
      FILLENTRY(nm->nb, coerce, coerce, 0,
		"Coerce woth another to a common type");
      FILLENTRY(nm->nb, int, int, 0, "Convert to an integer");
      FILLENTRY(nm->nb, long, long, 0,
		"Convert to an infinite-precision integer");
      FILLENTRY(nm->nb, float, float, 0, "Convert to floating point number");
      FILLENTRY(nm->nb, oct, oct, 0, "Convert to an octal string");
      FILLENTRY(nm->nb, hex, hex, 0, "Convert to a hexadecimal string");
    }
  return dict;
err:
  Py_DECREF(dict);
  return NULL;
}

#undef HAS
#undef UNARY_OP
#undef BINOP
#undef UNOP
#undef FILLENTRY

static PyObject *
initializeBaseExtensionClass(PyExtensionClass *self)
{
  PyMethodChain *chain;
  PyObject *dict;

  self->ob_type=(PyTypeObject*)&CCLtype;
  Py_INCREF(self->ob_type);

  UNLESS(dict=self->class_dictionary=getBaseDictionary(self)) return NULL;
  
  chain=&(self->methods);
  while (chain != NULL)
    {
      PyMethodDef *ml = chain->methods;
      for (; ml && ml->ml_name != NULL; ml++) 
	{
	  if(ml->ml_meth)
	    {
	      UNLESS(-1 != PyMapping_SetItemString(
                               dict,ml->ml_name,
			       (PyObject*)
			       newCMethod((PyTypeObject *)self,
					  ml->ml_name,
					  ml->ml_meth,
					  ml->ml_flags,
					  ml->ml_doc)))
		return NULL;
	    }
	  else if(ml->ml_doc && *(ml->ml_doc))
	    {
	      /* No actual meth, this is probably to hook a doc string
		 onto a special method. */
	      PyObject *m;

	      if(m=PyMapping_GetItemString(dict,ml->ml_name))
		{
		  if(m->ob_type==&CMethodType)
		    ((CMethod *)(m))->doc=ml->ml_doc;
		}
	      else
		PyErr_Clear();
	    }
	}
      chain=chain->link;
    }
  return (PyObject*)self;
}

static void
CCL_dealloc(PyExtensionClass *self)
{
  Py_XDECREF(self->class_dictionary);
  Py_XDECREF(self->bases);
  Py_XDECREF(self->ob_type);
  PyMem_DEL(self);
}

static PyObject *CCL_getattr();
  
static PyObject *
ExtensionClass_FindInstanceAttribute(PyObject *inst, PyObject *oname,
				     char *name)
{
  /* Look up an attribute for an instance from:

     The instance dictionary,
     The class dictionary, or
     The base objects.
   */
  PyObject *r=0;
  PyExtensionClass *self;

  if(! name) return NULL;

  self=(PyExtensionClass*)(inst->ob_type);

  if(*name=='_' && name[1]=='_')
    {
      if(strcmp(name+2,"class__")==0)
	{
	  Py_INCREF(self);
	  return (PyObject*)self;
	}
      if(self->bases && strcmp(name+2,"dict__")==0)
	{
	  r = INSTANCE_DICT(inst);
	  Py_INCREF(r);
	  return r;
	}
    }

  if(self->bases)
    {
      r= INSTANCE_DICT(inst);
      r = PyObject_GetItem(r,oname);
    }
  UNLESS(r)
    {
      PyErr_Clear();
      UNLESS(r=CCL_getattr(self,oname,name)) return NULL;

      /* We got something from our class, maybe its an unbound method. */
      if(UnboundCMethod_Check(r))
	{
	  UNLESS_ASSIGN(r,(PyObject*)bindCMethod((CMethod*)r,inst))
	    return NULL;
	}
      else if(UnboundPMethod_Check(r))
	{
	  PyObject *m;
	  m=((PMethod *)r)->meth;
	  if(PyExtensionInstance_Check(m) &&
	     (PyExtensionClassOf(m)->class_flags &
	      EXTENSIONCLASS_BINDABLE_FLAG
	      )
	     )
	    {
	      UNLESS_ASSIGN(r,PyObject_CallMethod(m,"__bind_to_object__",
						  "O", inst))
		return NULL;
	    }
	  else
	    {
	      UNLESS_ASSIGN(r,(PyObject*)bindPMethod((PMethod*)r,inst))
		return NULL;
	    }
	}
    }
      
  return r;
}

static PyObject *
EC_findiattrs(PyObject *self, char *name)
{
  PyObject *s, *r;

  UNLESS(s=PyString_FromString(name)) return NULL;
  r=ExtensionClass_FindInstanceAttribute(self,s,name);
  Py_DECREF(s);
  return r;
}
  
static PyObject *
EC_findiattro(PyObject *self, PyObject *name)
{
  return ExtensionClass_FindInstanceAttribute(self,name,
					      PyString_AsString(name));
}

static int
subclass_simple_setattr(PyObject *self, char *name, PyObject *v);

static PyObject *
CCL_getattr(PyExtensionClass *self, PyObject *oname, char *name)
{
  PyObject *r;
  int local=1;
  char *n;

  if(! name) return NULL;

  if(*name=='.')
    {
      n=name+1;
      if(*n==0)
	return (PyObject*)EC_findiattrs;
      if(*n=='o' && n[1]==0)
	return (PyObject*)EC_findiattro;
      if(*n=='s' && n[1]==0)
	return (PyObject*)subclass_simple_setattr;
    }
  if(*name=='_' && name[1]=='_')
    {
      n=name+2;
      if(strcmp(n,"doc__")==0 && self->tp_doc)
	return PyString_FromString(self->tp_doc);
      if(strcmp(n,"name__")==0)
	return PyString_FromString(self->tp_name);
      if(strcmp(n,"dict__")==0)
	{
	  Py_INCREF(self->class_dictionary);
	  return self->class_dictionary;
	}
      if(strcmp(n,"bases__")==0)
	{
	  if(self->bases)
	    {
	      Py_INCREF(self->bases);
	      return self->bases;
	    }
	  else
	    return PyTuple_New(0);
	}
    }
  
  r=PyObject_GetItem(self->class_dictionary,oname);
  UNLESS(r)
    {
      local=0;
      if(self->bases)
	{
	  int n, i;
	  PyObject *c;

	  n=PyTuple_Size(self->bases);
	  for(i=0; i < n; i++)
	    {
	      PyErr_Clear();
	      c=PyTuple_GET_ITEM(self->bases, i);
	      if(r=PyObject_GetAttr(c,oname)) break;
	    }
	}
      UNLESS(r)
	{
	  PyObject *t, *v, *tb;
	  char *s;

	  PyErr_Fetch(&t,&v,&tb);
	  if(t==PyExc_KeyError && PyObject_Compare(v,oname) == 0)
	    {
	      Py_DECREF(t);
	      t=PyExc_AttributeError;
	      Py_INCREF(t);
	    }
	  PyErr_Restore(t,v,tb);	  
	  return NULL;
	}
    }

  if(PyFunction_Check(r) ||
     (PyExtensionInstance_Check(r) &&
      (PyExtensionClassOf(r)->class_flags &
       EXTENSIONCLASS_BINDABLE_FLAG
       )
      )
     )
    {
      UNLESS_ASSIGN(r,(PyObject*)newPMethod((PyTypeObject *)self,r))
	return NULL;
    }
  else if(PyMethod_Check(r) && ! PyMethod_Self(r))
    {
      UNLESS_ASSIGN(r,(PyObject*)newPMethod((PyTypeObject *)self,
					    PyMethod_Function(r)))
	return NULL;
    }
  else local=0;

  if(local) /* We have a PMethod that we built from our dict, cache it */
    {
      UNLESS(-1 != PyObject_SetItem(self->class_dictionary, oname, r))
	PyErr_Clear();		/* Oh well */
    }
  
  return r;
}

PyObject *
CCL_getattrs(PyExtensionClass *self, char *name)
{
  PyObject *s, *r;

  UNLESS(s=PyString_FromString(name)) return NULL;
  r=CCL_getattr(self,s,name);
  Py_DECREF(s);
  return r;
}

static int
CCL_setattrs(self, name, v)
     PyExtensionClass *self;
     char *name;
     PyObject *v;
{
  return PyMapping_SetItemString(self->class_dictionary, name, v);
}

PyObject *
CCL_getattro(PyExtensionClass *self, PyObject *name)
{
  return CCL_getattr(self,name,PyString_AsString(name));
}

static int
CCL_setattro(PyExtensionClass *self, PyObject *name, PyObject *v)
{
  if(UnboundCMethod_Check(v))
    {
      char *n;
      PyNumberMethods *nm;
      PySequenceMethods *s, *ms;
      PyMappingMethods *m, *mm;

      UNLESS(n=PyString_AsString(name)) return -1;
      if(*n=='_' && n[1]=='_')
	{
	  n+=2;

#define SET_SPECIAL(C,P) \
	  if(strcmp(n,#P "__")==0 \
	     && AsCMethod(v)->meth==(PyCFunction)C ## _by_name \
	     && Subclass_Check(self,AsCMethod(v)->type)) { \
	      self->tp_ ## C=AsCMethod(v)->type->tp_ ## C; \
	      return PyObject_SetItem(self->class_dictionary, name, v); }
	  /*
	  SET_SPECIAL(setattr,setattr);
	  SET_SPECIAL(setattro,setattr);
	  */
	  SET_SPECIAL(compare,cmp);
	  SET_SPECIAL(hash,hash);
	  SET_SPECIAL(repr,repr);
	  SET_SPECIAL(call,call);
	  SET_SPECIAL(str,str);
#undef SET_SPECIAL

#define SET_SPECIAL(C,P) \
	  if(strcmp(n,#P "__")==0 && AsCMethod(v)->meth==C ## _by_name \
	     && Subclass_Check(self,AsCMethod(v)->type) \
	     && (nm=self->tp_as_number)) { \
	      nm->nb_ ## C=AsCMethod(v)->type->tp_as_number->nb_ ## C; \
	      return PyObject_SetItem(self->class_dictionary, name, v); } 
	  SET_SPECIAL(add,add);
	  SET_SPECIAL(subtract,sub);
	  SET_SPECIAL(multiply,mult);
	  SET_SPECIAL(divide,div);
	  SET_SPECIAL(remainder,mod);
	  SET_SPECIAL(power,pow);
	  SET_SPECIAL(divmod,divmod);
	  SET_SPECIAL(lshift,lshift);
	  SET_SPECIAL(rshift,rshift);
	  SET_SPECIAL(and,and);
	  SET_SPECIAL(or,or);
	  SET_SPECIAL(xor,xor);
	  SET_SPECIAL(coerce,coerce);
	  SET_SPECIAL(negative,neg);
	  SET_SPECIAL(positive,pos);
	  SET_SPECIAL(absolute,abs);
	  SET_SPECIAL(nonzero,nonzero);
	  SET_SPECIAL(invert,inv);
	  SET_SPECIAL(int,int);
	  SET_SPECIAL(long,long);
	  SET_SPECIAL(float,float);
	  SET_SPECIAL(oct,oct);
	  SET_SPECIAL(hex,hex);
#undef SET_SPECIAL

	  if(strcmp(n,"len__")==0 && AsCMethod(v)->meth==length_by_name 
	     && Subclass_Check(self,AsCMethod(v)->type))
	     {
	       if((s=self->tp_as_sequence) &&
		  (ms=AsCMethod(v)->type->tp_as_sequence) &&
		  ms->sq_length)
		 s->sq_length=ms->sq_length;
	       if((m=self->tp_as_mapping) &&
		  (mm=AsCMethod(v)->type->tp_as_mapping) &&
		  mm->mp_length)
		 m->mp_length=mm->mp_length;
	       return PyObject_SetItem(self->class_dictionary, name, v);
	     } 

	  if(strcmp(n,"getitem__")==0 && AsCMethod(v)->meth==getitem_by_name 
	     && Subclass_Check(self,AsCMethod(v)->type))
	     {
	       if((s=self->tp_as_sequence) &&
		  (ms=AsCMethod(v)->type->tp_as_sequence) &&
		  ms->sq_item)
		 s->sq_item=ms->sq_item;
	       if((m=self->tp_as_mapping) &&
		  (mm=AsCMethod(v)->type->tp_as_mapping) &&
		  mm->mp_subscript)
		 m->mp_subscript=mm->mp_subscript;
	       return PyObject_SetItem(self->class_dictionary, name, v);
	     } 

	  if(strcmp(n,"setitem__")==0 &&
	     AsCMethod(v)->meth==(PyCFunction)setitem_by_name 
	     && Subclass_Check(self,AsCMethod(v)->type))
	     {
	       if((s=self->tp_as_sequence) &&
		  (ms=AsCMethod(v)->type->tp_as_sequence) &&
		  ms->sq_ass_item)
		 s->sq_ass_item=ms->sq_ass_item;
	       if((m=self->tp_as_mapping) &&
		  (mm=AsCMethod(v)->type->tp_as_mapping) &&
		  mm->mp_ass_subscript)
		 m->mp_ass_subscript=mm->mp_ass_subscript;
	       return PyObject_SetItem(self->class_dictionary, name, v);
	     } 

#define SET_SPECIAL(C,P) \
	  if(strcmp(n,#P "__")==0 \
	     && AsCMethod(v)->meth==(PyCFunction)C ## _by_name \
	     && Subclass_Check(self,AsCMethod(v)->type) \
	     && (s=self->tp_as_sequence)) { \
	      s->sq_ ## C=AsCMethod(v)->type->tp_as_sequence->sq_ ## C; \
	      return PyObject_SetItem(self->class_dictionary, name, v); } 
	  SET_SPECIAL(slice,getslice);
	  SET_SPECIAL(ass_slice,setslice);
	  SET_SPECIAL(concat,concat);
	  SET_SPECIAL(repeat,repeat);
#undef SET_SPECIAL

	}
    }
  return PyObject_SetItem(self->class_dictionary, name, v);
}

static PyObject *
CCL_call(PyExtensionClass *self, PyObject *arg, PyObject *kw)
{
  PyObject *inst=0, *init=0, *args=0;
  int check;
  struct Dataless { PyObject_HEAD };
  typedef struct { PyObject_VAR_HEAD } PyVarObject__;

  if(PyArg_ParseTuple(arg,"Oi",&inst,&check))
    {
      if(check==42 && inst->ob_type==&PyType_Type)
	{
	  initializeBaseExtensionClass((PyExtensionClass*)inst);
	  return (PyObject*)inst;
	}
    }
  else PyErr_Clear();

  if(self->tp_itemsize)
    {
      /* We have a variable-sized object, we need to get it's size */
      PyObject *var_size;
      int size;
      
      if(var_size=CCL_getattro(self,py__var_size__))
	{
	  UNLESS_ASSIGN(var_size,PyObject_CallObject(var_size,args))
	    return NULL;
	}
      else
	{
	  UNLESS(-1 != (size=PyTuple_Size(args))) return NULL;
	  if(size > 0)
	    {
	      var_size=PyTuple_GET_ITEM(args, 0);
	      if(PyInt_Check(var_size))
		size=PyInt_AsLong(var_size);
	      else
		size=-1;
	    }
	  else
	    size=-1;
	  if(size < 0)
	    {
	      PyErr_SetString(PyExc_TypeError,
			      "object size expected as first argument");
	      return NULL;
	    }
	}
      UNLESS(inst=PyObject_NEW_VAR(PyObject,(PyTypeObject *)self, size))
	return NULL;
      memset(inst,0,self->tp_basicsize+self->tp_itemsize*size);
      inst->ob_refcnt=1;
      inst->ob_type=(PyTypeObject *)self;
      ((PyVarObject__*)inst)->ob_size=size;
    }
  else
    {
      UNLESS(inst=PyObject_NEW(PyObject,(PyTypeObject *)self)) return NULL;
      memset(inst,0,self->tp_basicsize);
      inst->ob_refcnt=1;
      inst->ob_type=(PyTypeObject *)self;
    }

  Py_INCREF(self);
  if(self->bases)
    {
      UNLESS(INSTANCE_DICT(inst)=PyDict_New()) goto err;
    }

  

  if(init=CCL_getattro(self,py__init__))
    {
      UNLESS(args=Py_BuildValue("(O)",inst)) goto err;
      if(arg) UNLESS_ASSIGN(args,PySequence_Concat(args,arg)) goto err;
      UNLESS_ASSIGN(args,PyEval_CallObjectWithKeywords(init,args,kw)) goto err;
      Py_DECREF(args);
      Py_DECREF(init);
    }
  else PyErr_Clear();


  return inst;
err:
  Py_DECREF(inst);
  Py_XDECREF(init);
  Py_XDECREF(args);
  return NULL;
}

static PyObject *
CCL_repr(PyExtensionClass *self)
{
  PyObject *s;
  int l;
  char *buf, p[64];
  
  sprintf(p,"%p",self);
  l=strlen(self->ob_type->tp_name)+strlen(p);
  UNLESS(s=PyString_FromStringAndSize(NULL,l+22)) return NULL;
  buf=PyString_AsString(s);
  sprintf(buf,"<extension class %s at %p>", self->tp_name, self);
  return s;
}

static PyTypeObject CCLtype_class = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,				/*ob_size*/
  "C Class Class",	       	/*tp_name*/
  sizeof(PyExtensionClass),    	/*tp_basicsize*/
  0,				/*tp_itemsize*/
  /* methods */
  (destructor)CCL_dealloc,	/*tp_dealloc*/
  (printfunc)0,			/*tp_print*/
  (getattrfunc)CCL_getattrs,	/*tp_getattr*/
  (setattrfunc)CCL_setattrs,	/*tp_setattr*/
  (cmpfunc)0,			/*tp_compare*/
  (reprfunc)CCL_repr,		/*tp_repr*/
  0,				/*tp_as_number*/
  0,				/*tp_as_sequence*/
  0,				/*tp_as_mapping*/
  (hashfunc)0,			/*tp_hash*/
  (ternaryfunc)CCL_call,       	/*tp_call*/
  (reprfunc)0,			/*tp_str*/
#if PYTHON_API_VERSION >= 1005
  (getattrofunc)CCL_getattro,	/*tp_getattr with object key*/
  (setattrofunc)CCL_setattro,	/*tp_setattr with object key*/
#else
  /* Space for future expansion */
  0L,0L,
#endif
  0L,0L,
  "Class of C classes" /* Documentation string */
};

/* End of code for ExtensionClass objects */
/* -------------------------------------------------------- */

/* subclassing code: */
  
static PyObject *
subclass_getspecial(PyObject *inst, PyObject *oname)
{
  PyObject *r=0;
  PyExtensionClass *self;

  self=(PyExtensionClass*)(inst->ob_type);
  r= INSTANCE_DICT(inst);
  r = PyObject_GetItem(r,oname);
  UNLESS(r)
    {
      PyErr_Clear();
      r=CCL_getattr(self,oname,"");
    }
      
  return r;
}

static PyObject *
subclass_getattro(PyObject *self, PyObject *name)
{
  PyObject *r=0;

  if(! name) return NULL;
  UNLESS(r=EC_findiattro(self,name))
    {
      PyErr_Clear();
      UNLESS(r=EC_findiattro(self,py__getattr__)) return NULL;
      UNLESS_ASSIGN(r,PyObject_CallFunction(r,"O",name)) return NULL;
    }
  return r;
}

static PyObject *
subclass_getattrs(PyObject *self, char *name)
{
  return subclass_getattro(self,PyString_FromString(name));
}

static int
subclass_simple_setattro(PyObject *self, PyObject *name, PyObject *v)
{
  Py_INCREF(v);
  return PyDict_SetItem(INSTANCE_DICT(self),name,v);
}

static int
subclass_simple_setattr(PyObject *self, char *name, PyObject *v)
{
  Py_INCREF(v);
  return PyDict_SetItemString(INSTANCE_DICT(self),name,v);
}

static int 
subclass_setattr(PyObject *self, PyObject *oname, char *name, PyObject *v)
{
  PyObject *m=0, *et, *ev, *etb;

  if(! name) return -1;

  UNLESS(m=subclass_getspecial(self,py__setattr__))
    goto default_setattr;
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==setattr_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      UNLESS(-1 != AsCMethod(m)->type->tp_setattr(self,name,v))
	goto dictionary_setattr;
      return 0;
    }
#if PYTHON_API_VERSION >= 1005
  else 
    if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==setattro_by_name
       && SubclassInstance_Check(self,AsCMethod(m)->type))
      {
	UNLESS(-1 != AsCMethod(m)->type->tp_setattro(self,oname,v))
	  goto dictionary_setattr;
	return 0;
      }
#endif
  if(UnboundEMethod_Check(m))
    {
      UNLESS_ASSIGN(m,PyObject_CallFunction(m,"OOO",self,oname,v)) return -1;
    }
  else UNLESS_ASSIGN(m,PyObject_CallFunction(m,"OO",oname,v)) return -1;
  Py_DECREF(m);
  return 0;

dictionary_setattr:

  Py_XDECREF(m);

  PyErr_Fetch(&et, &ev, &etb);
  if(et==PyExc_AttributeError)
    {
      char *s;
      
      if(ev && PyString_Check(ev) && (s=PyString_AsString(ev)) &&
	 strcmp(s,name)==0)
	{
	  Py_XDECREF(et);
	  Py_XDECREF(ev);
	  Py_XDECREF(etb);
	  et=0;
	}
    }
  if(et)
    {
      PyErr_Restore(et,ev,etb);
      return -1;
    }	
  
default_setattr:

  PyErr_Clear();
  
  return subclass_simple_setattro(self, oname, v);
}

static int
subclass_setattrs(PyObject *self, char *name, PyObject *v)
{
  PyObject *s;
  int r;

  UNLESS(s=PyString_FromString(name)) return -1;
  r=subclass_setattr(self,s,name,v);
  Py_DECREF(s);
  return r;
}

static int
subclass_setattro(PyObject *self, PyObject *name, PyObject *v)
{
  return subclass_setattr(self,name,PyString_AsString(name),v);
}


static int
subclass_compare(PyObject *self, PyObject *v)
{
  PyObject *m;
  long r;

  UNLESS(m=subclass_getspecial(self,py__cmp__)) return -1;
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==compare_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    r=AsCMethod(m)->type->tp_compare(self,v);
  else
    {
      if(UnboundEMethod_Check(m))
	{
	  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"OO",self,v))
	    return -1;
	}
      else UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",v)) return -1;
      r=PyInt_AsLong(m);
    }
  Py_DECREF(m);
  return r;
}  

static long
subclass_hash(PyObject *self)
{
  PyObject *m;
  long r;

  UNLESS(m=subclass_getspecial(self,py__hash__)) return -1;
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==hash_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    r=AsCMethod(m)->type->tp_hash(self);
  else
    {
      if(UnboundEMethod_Check(m))
	{
	  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",self))
	    return -1;
	}
      else UNLESS_ASSIGN(m,PyObject_CallFunction(m,"")) return -1;
      r=PyInt_AsLong(m);
    }
  Py_DECREF(m);
  return r;
}  

static PyObject *
subclass_repr(PyObject *self)
{
  PyObject *m;

  UNLESS(m=subclass_getspecial(self,py__repr__))
    {
      int l;
      char *buf, p[64];

      PyErr_Clear();
      sprintf(p,"%p",self);
      l=strlen(self->ob_type->tp_name)+strlen(p);
      UNLESS(m=PyString_FromStringAndSize(NULL,l+15)) return NULL;
      buf=PyString_AsString(m);
      sprintf(buf,"<%s instance at %s>",self->ob_type->tp_name,p);
      return m;
    }
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==repr_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      UNLESS_ASSIGN(m,AsCMethod(m)->type->tp_repr(self)) return NULL;
    }
  else
    {
      if(UnboundEMethod_Check(m))
	{
	  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",self))
	    return NULL;
	}
      else UNLESS_ASSIGN(m,PyObject_CallFunction(m,"")) return NULL;
    }
  return m;
}  

static PyObject *
subclass_call(PyObject *self, PyObject *args, PyObject *kw)
{
  PyObject *m, *a=0;

  UNLESS(m=subclass_getspecial(self,py__call__)) return NULL;
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==(PyCFunction)call_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      UNLESS_ASSIGN(m,AsCMethod(m)->type->tp_call(self,args,kw)) return NULL;
    }
  else
    {
      if(UnboundEMethod_Check(m))
	{
	  UNLESS(a=Py_BuildValue("(O)",self)) goto err;
	  UNLESS_ASSIGN(a,PySequence_Concat(a,args)) goto err;
	  args=a;
	}
      UNLESS_ASSIGN(m,PyEval_CallObjectWithKeywords(m,args,kw)) goto err;
    }
  Py_XDECREF(a);
  return m;
err:
  Py_XDECREF(m);
  Py_XDECREF(a);
}  

static PyObject *
subclass_str(PyObject *self)
{
  PyObject *m;

  UNLESS(m=subclass_getspecial(self,py__str__))
    {
      PyErr_Clear();
      return subclass_repr(self);
    }
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==str_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      UNLESS_ASSIGN(m,AsCMethod(m)->type->tp_str(self)) return NULL;
    }
  else
    {
      if(UnboundEMethod_Check(m))
	{
	  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",self))
	    return NULL;
	}
      else UNLESS_ASSIGN(m,PyObject_CallFunction(m,"")) return NULL;
    }
  return m;
}  

#define BINSUB(M,N,A) \
static PyObject * \
subclass_ ## M(PyObject *self, PyObject *v) \
{ \
  PyObject *m; \
  UNLESS(m=subclass_getspecial(self,py__ ## N ## __)) return NULL; \
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==M ## _by_name \
     && SubclassInstance_Check(self,AsCMethod(m)->type)) \
    { \
      UNLESS_ASSIGN(m,PyNumber_ ## A(self,v)) \
	return NULL; \
    } \
  else \
    { \
      if(UnboundEMethod_Check(m)) \
	{ \
	  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"OO",self,v)) \
	    return NULL; \
	} \
      else UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",v)) return NULL; \
    } \
  return m; \
}  
  
BINSUB(add,add,Add)
BINSUB(subtract,sub,Subtract)
BINSUB(multiply,mul,Multiply)
BINSUB(divide,div,Divide)
BINSUB(remainder,mod,Remainder)

static PyObject * 
subclass_power(PyObject *self, PyObject *v, PyObject *w) 
{ 
  PyObject *m; 
  UNLESS(m=subclass_getspecial(self,py__pow__)) return NULL; 
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==power_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type)) 
    { 
      UNLESS_ASSIGN(m,AsCMethod(m)->type->tp_as_number->nb_power(self,v,w)) 
	return NULL; 
    } 
  else 
    { 
      if(UnboundEMethod_Check(m))
	{
	  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"OOO",self,v,w))
	    return NULL;
	}
      else UNLESS_ASSIGN(m,PyObject_CallFunction(m,"OO",v,w)) return NULL; 
    } 
  return m; 
}  


BINSUB(divmod,divmod,Divmod)
BINSUB(lshift,lshift,Lshift)
BINSUB(rshift,rshift,Rshift)
BINSUB(and,and,And)
BINSUB(or,or,Or)
BINSUB(xor,xor,Xor)


static int
subclass_coerce(PyObject **self, PyObject **v) 
{ 
  PyObject *m; 
  int r;

  UNLESS(m=subclass_getspecial(*self,py__coerce__)) return -1; 
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==coerce_by_name
     && SubclassInstance_Check(*self,AsCMethod(m)->type)) 
    r=AsCMethod(m)->type->tp_as_number->nb_coerce(self,v);
  else 
    { 
      if(UnboundEMethod_Check(m))
	{
	  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"OO",*self,v))
	    return NULL;
	}
      UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",*v)) return -1;
      if(m==Py_None) r=-1;
      else
	{
	  PyArg_ParseTuple(m,"O",v);
	  Py_INCREF(*self);
	  Py_INCREF(*v);
	  r=0;
	}
    } 
  Py_DECREF(m);
  return r; 
}  

#define UNSUB(M,N) \
static PyObject * \
subclass_ ## M(PyObject *self) \
{ \
  PyObject *m; \
  UNLESS(m=subclass_getspecial(self,py__ ## N ## __)) return NULL; \
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==M ## _by_name \
     && SubclassInstance_Check(self,AsCMethod(m)->type)) \
    { \
      UNLESS_ASSIGN(m,AsCMethod(m)->type->tp_as_number->nb_ ## M(self)) \
	return NULL; \
    } \
  else \
    { \
      if(UnboundEMethod_Check(m)) \
	{ \
	  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",self)) \
	    return NULL; \
	} \
      else UNLESS_ASSIGN(m,PyObject_CallFunction(m,"")) return NULL; \
    } \
  return m; \
}  

UNSUB(negative, neg)
UNSUB(positive, pos)
UNSUB(absolute, abs)

static int
subclass_nonzero(PyObject *self)
{
  PyObject *m;
  long r;

  UNLESS(m=subclass_getspecial(self,py__nonzero__)) return -1;
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==nonzero_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    r=AsCMethod(m)->type->tp_as_number->nb_nonzero(self);
  else
    {
      if(UnboundEMethod_Check(m))
	{
	  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",self))
	    return -1;
	}
      else UNLESS_ASSIGN(m,PyObject_CallFunction(m,"")) return -1;
      r=PyInt_AsLong(m);
    }
  Py_DECREF(m);
  return r;
}  

UNSUB(invert, inv)
UNSUB(int, int)
UNSUB(long, long)
UNSUB(float, float)
UNSUB(oct, oct)
UNSUB(hex, hex)

#undef UNSUB
#undef BINSUB


static PyNumberMethods subclass_as_number = {
  (binaryfunc)subclass_add,		/*nb_add*/
  (binaryfunc)subclass_subtract,	/*nb_subtract*/
  (binaryfunc)subclass_multiply,	/*nb_multiply*/
  (binaryfunc)subclass_divide,		/*nb_divide*/
  (binaryfunc)subclass_remainder,	/*nb_remainder*/
  (binaryfunc)subclass_divmod,		/*nb_divmod*/
  (ternaryfunc)subclass_power,		/*nb_power*/
  (unaryfunc)subclass_negative,		/*nb_negative*/
  (unaryfunc)subclass_positive,		/*nb_positive*/
  (unaryfunc)subclass_absolute,		/*nb_absolute*/
  (inquiry)subclass_nonzero,		/*nb_nonzero*/
  (unaryfunc)subclass_invert,		/*nb_invert*/
  (binaryfunc)subclass_lshift,		/*nb_lshift*/
  (binaryfunc)subclass_rshift,		/*nb_rshift*/
  (binaryfunc)subclass_and,		/*nb_and*/
  (binaryfunc)subclass_xor,		/*nb_xor*/
  (binaryfunc)subclass_or,		/*nb_or*/
  (coercion)subclass_coerce,		/*nb_coerce*/
  (unaryfunc)subclass_int,		/*nb_int*/
  (unaryfunc)subclass_long,		/*nb_long*/
  (unaryfunc)subclass_float,		/*nb_float*/
  (unaryfunc)subclass_oct,		/*nb_oct*/
  (unaryfunc)subclass_hex,		/*nb_hex*/
};

static long
subclass_length(PyObject *self)
{
  PyObject *m;
  long r;
  PyExtensionClass *t;

  UNLESS(m=subclass_getspecial(self,py__len__)) return -1;
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==length_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      t=(PyExtensionClass*)AsCMethod(m)->type;
      Py_DECREF(m);
      if(t->tp_as_sequence)
	return t->tp_as_sequence->sq_length(self);
      else
	return t->tp_as_mapping->mp_length(self);
    }
  else
    {
      UNLESS_ASSIGN(m,PyObject_CallFunction(m,"")) return -1;
      r=PyInt_AsLong(m);
    }
  Py_DECREF(m);
  return r;
}

static PyObject *
subclass_item(PyObject *self, int index)
{
  PyObject *m;
  PyExtensionClass *t;

  UNLESS(m=subclass_getspecial(self,py__getitem__)) return NULL;
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==getitem_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      t=(PyExtensionClass*)AsCMethod(m)->type;
      if(t->tp_as_sequence && t->tp_as_sequence->sq_item)
	{
	  Py_DECREF(m);
	  return t->tp_as_sequence->sq_item(self,index);
	}
    }
  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"i",index)) goto err;
  return m;
err:
  Py_DECREF(m);
  return NULL;
}

static long
subclass_ass_item(PyObject *self, int index, PyObject *v)
{
  long r;
  PyObject *m;
  PyExtensionClass *t;

  UNLESS(m=subclass_getspecial(self,py__setitem__)) return -1;
  if(UnboundCMethod_Check(m) &&
     AsCMethod(m)->meth==(PyCFunction)setitem_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      t=(PyExtensionClass*)AsCMethod(m)->type;
      if(t->tp_as_sequence && t->tp_as_sequence->sq_ass_item)
	{
	  Py_DECREF(m);
	  return t->tp_as_sequence->sq_ass_item(self,index,v);
	}
    }
  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"iO",index,v)) return -1;
  r=PyInt_AsLong(m);
  Py_DECREF(m);
  return r;
err:
  Py_DECREF(m);
  return NULL;
}

static PyObject *
subclass_slice(PyObject *self, int i1, int i2)
{
  PyObject *m;

  UNLESS(m=subclass_getspecial(self,py__getslice__)) return NULL;
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==slice_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      UNLESS_ASSIGN(m,AsCMethod(m)->type->tp_as_sequence->sq_slice(self,i1,i2))
	return NULL;
    }
  else
    {
      UNLESS_ASSIGN(m,PyObject_CallFunction(m,"ii",i1,i2)) return NULL;
    }
  return m;
}

static int
subclass_ass_slice(PyObject *self, int i1, int i2, PyObject *v)
{
  PyObject *m;
  long r;

  UNLESS(m=subclass_getspecial(self,py__setslice__)) return -1;
  if(UnboundCMethod_Check(m) &&
     AsCMethod(m)->meth==(PyCFunction)ass_slice_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    r=AsCMethod(m)->type->tp_as_sequence->sq_ass_slice(self,i1,i2,v);
  else
    {
      UNLESS_ASSIGN(m,PyObject_CallFunction(m,"iiO",i1,i2,v)) return -1;
      r=PyInt_AsLong(m);
    }
  Py_DECREF(m);
  return r;
}  

static PyObject *
subclass_concat(PyObject *self, PyObject *v)
{
  PyObject *m;

  UNLESS(m=subclass_getspecial(self,py__concat__))
    { /* Maybe we should check for __add__ */
      PyObject *am;

      PyErr_Clear();
      UNLESS(am=subclass_getspecial(self,py__add__)) return NULL;
      if(m=subclass_getspecial(self,py__coerce__))
	{
	  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==coerce_by_name
	     && SubclassInstance_Check(self,AsCMethod(m)->type))
	    {
	      PyObject *x,*y;

	      x=self;
	      y=v;
	      if(0==AsCMethod(m)->type->tp_as_number->nb_coerce(&x,&y))
		{
		  Py_DECREF(am);
		  if(x->ob_type->tp_as_number)
		    am=x->ob_type->tp_as_number->nb_add(x,y);
		  else
		    am=NULL;
		  Py_DECREF(m);
		  Py_DECREF(x);
		  Py_DECREF(y);
		  if(am) return am;
		}
	    }
	  Py_DECREF(m);
	}
      Py_DECREF(am);
      PyErr_SetString(PyExc_AttributeError,
	 "No __add__ or __concat__ methods, or maybe I'm just being stupid.");
      return NULL;
    }
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==concat_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      UNLESS_ASSIGN(m,AsCMethod(m)->type->tp_as_sequence->sq_concat(self,v))
	return NULL;
    }
  else
    {
      UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",v)) return NULL;
    }
  return m;
}

static PyObject *
subclass_repeat(PyObject *self, int v)
{
  PyObject *m;

  UNLESS(m=subclass_getspecial(self,py__repeat__)) return NULL;
  if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==repeat_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      UNLESS_ASSIGN(m,AsCMethod(m)->type->tp_as_sequence->sq_repeat(self,v))
	return NULL;
    }
  else
    {
      UNLESS_ASSIGN(m,PyObject_CallFunction(m,"i",v)) return NULL;
    }
  return m;
}

PySequenceMethods subclass_as_sequence = {
	(inquiry)subclass_length,   		/*sq_length*/
	(binaryfunc)subclass_concat,		/*sq_concat*/
	(intargfunc)subclass_repeat,		/*sq_repeat*/
	(intargfunc)subclass_item,		/*sq_item*/
	(intintargfunc)subclass_slice,		/*sq_slice*/
	(intobjargproc)subclass_ass_item,	/*sq_ass_item*/
	(intintobjargproc)subclass_ass_slice,	/*sq_ass_slice*/
};

static PyObject *
subclass_subscript(PyObject *self, PyObject *key)
{
  PyObject *m;
  PyExtensionClass *t;

  UNLESS(m=subclass_getspecial(self,py__getitem__)) return NULL;
  if(UnboundCMethod_Check(m) &&
     AsCMethod(m)->meth==(PyCFunction)getitem_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      t=(PyExtensionClass*)AsCMethod(m)->type;
      if(t->tp_as_mapping && t->tp_as_mapping->mp_subscript)
	{
	  Py_DECREF(m);
	  return t->tp_as_mapping->mp_subscript(self,key);
	}
    }
  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"O",key)) goto err;
  return m;
err:
  Py_DECREF(m);
  return NULL;
}

static long
subclass_ass_subscript(PyObject *self, PyObject *index, PyObject *v)
{
  long r;
  PyObject *m;
  PyExtensionClass *t;

  UNLESS(m=subclass_getspecial(self,py__setitem__)) return -1;
  if(UnboundCMethod_Check(m) &&
     AsCMethod(m)->meth==(PyCFunction)setitem_by_name
     && SubclassInstance_Check(self,AsCMethod(m)->type))
    {
      t=(PyExtensionClass*)AsCMethod(m)->type;
      if(t->tp_as_sequence && t->tp_as_mapping->mp_ass_subscript)
	{
	  Py_DECREF(m);
	  return t->tp_as_mapping->mp_ass_subscript(self,index,v);
	}
    }
  UNLESS_ASSIGN(m,PyObject_CallFunction(m,"OO",index,v)) return -1;
  r=PyInt_AsLong(m);
  Py_DECREF(m);
  return r;
err:
  Py_DECREF(m);
  return NULL;
}

PyMappingMethods subclass_as_mapping = {
	(inquiry)subclass_length,		/*mp_length*/
	(binaryfunc)subclass_subscript,		/*mp_subscript*/
	(objobjargproc)subclass_ass_subscript,	/*mp_ass_subscript*/
};

static int
dealloc_base(PyObject *inst, PyExtensionClass* self)
{
  int i,l;
  PyObject *t;

  l=PyTuple_Size(self->bases);
  for(i=0; i < l; i++)
    {
      t=PyTuple_GET_ITEM(self->bases, i);
      if(PyExtensionClass_Check(t))
	{
	  if(AsPyExtensionClass(t)->bases)
	    {
	      if(dealloc_base(inst,AsPyExtensionClass(t))) return 1;
	    }
	  else
	    {
	      if(((PyExtensionClass*)t)->tp_dealloc)
		{
		  ((PyExtensionClass*)t)->tp_dealloc(inst);
		  return 1;
		}
	    }
	}
    }
  return 0;
}

static void
subclass_dealloc(PyObject *self)
{
  PyObject *m, *t, *v, *tb;

  PyErr_Fetch(&t,&v,&tb);

  if(m=subclass_getspecial(self,py__del__))
    PyObject_CallFunction(m,"");
  PyErr_Clear();
  
  Py_XDECREF(INSTANCE_DICT(self));
  Py_DECREF(self->ob_type);

  dealloc_base(self,(PyExtensionClass*)self->ob_type);

  PyErr_Restore(t,v,tb);
}

static int
datafull_baseclasses(PyExtensionClass *type)
{
  /* Find the number of classes that have data and return them.
     There should be only one.
     */
  int l, i, n=0;
  PyObject *base;
  typedef struct { PyObject_HEAD } Dataless;
  
  l=PyTuple_Size(type->bases);
  for(i=0; i < l; i++)
    {
      base=PyTuple_GET_ITEM(type->bases, i);
      if(PyExtensionClass_Check(base))
	{
	  if(AsPyExtensionClass(base)->bases)
	    n+=datafull_baseclasses(AsPyExtensionClass(base));
	  else
	    {
	      if(AsPyExtensionClass(base)->tp_basicsize > sizeof(Dataless) ||
		 AsPyExtensionClass(base)->tp_itemsize > 0)
		n++;
	    }
	}
    }
  return n;
}

static PyObject *
datafull_baseclass(PyExtensionClass *type)
{
  /* Find the number of classes that have data and return them.
     There should be only one.
     */
  int l, i, n=0;
  PyObject *base, *dbase;
  
  l=PyTuple_Size(type->bases);
  for(i=0; i < l; i++)
    {
      base=PyTuple_GET_ITEM(type->bases, i);
      if(PyExtensionClass_Check(base))
	{
	  if(AsPyExtensionClass(base)->bases)
	    {
	      if(dbase=datafull_baseclass(AsPyExtensionClass(base)))
		return dbase;
	    }
	  else
	    {
	      if(AsPyExtensionClass(base)->tp_basicsize > sizeof(Dataless) ||
		 AsPyExtensionClass(base)->tp_itemsize > 0)
		return base;
	    }
	}
    }
  return NULL;
}

static int 
subclass_hasattr(PyExtensionClass *type, PyObject *name)
{
  PyObject *o;

  if(o=CCL_getattro(type,name))
    {
      Py_DECREF(o);
      return 1;
    }
  PyErr_Clear();
  return 0;
}

static int
has_number_methods(PyExtensionClass *type)
{
  return (subclass_hasattr(type,py__add__) ||
	  subclass_hasattr(type,py__sub__) ||
	  subclass_hasattr(type,py__mul__) ||
	  subclass_hasattr(type,py__div__) ||
	  subclass_hasattr(type,py__mod__) ||
	  subclass_hasattr(type,py__pow__) ||
	  subclass_hasattr(type,py__divmod__) ||
	  subclass_hasattr(type,py__lshift__) ||
	  subclass_hasattr(type,py__rshift__) ||
	  subclass_hasattr(type,py__and__) ||
	  subclass_hasattr(type,py__or__) ||
	  subclass_hasattr(type,py__xor__) ||
	  subclass_hasattr(type,py__coerce__) ||
	  subclass_hasattr(type,py__neg__) ||
	  subclass_hasattr(type,py__pos__) ||
	  subclass_hasattr(type,py__abs__) ||
	  subclass_hasattr(type,py__nonzero__) ||
	  subclass_hasattr(type,py__inv__) ||
	  subclass_hasattr(type,py__int__) ||
	  subclass_hasattr(type,py__long__) ||
	  subclass_hasattr(type,py__float__) ||
	  subclass_hasattr(type,py__oct__) ||
	  subclass_hasattr(type,py__hex__)
	  );
}	  

static int
has_collection_methods(PyExtensionClass *type)
{
  return (subclass_hasattr(type,py__getitem__) ||
	  subclass_hasattr(type,py__setitem__) ||
	  subclass_hasattr(type,py__getslice__) ||
	  subclass_hasattr(type,py__setslice__) ||
	  subclass_hasattr(type,py__concat__) ||
	  subclass_hasattr(type,py__repeat__) ||
	  subclass_hasattr(type,py__len__) 
	  );
}	  

static void
subclass_init_getattr(PyExtensionClass *self, PyObject *methods)
{
  PyObject *m;

  if((m=CCL_getattr(self,py__getattr__,"__getattr__")))
    {
      if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==getattr_by_name
	 && Subclass_Check(self,AsCMethod(m)->type))
	{
	  self->tp_getattr=AsCMethod(m)->type->tp_getattr;
	}
#if PYTHON_API_VERSION >= 1005
      else if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==getattro_by_name
	   && Subclass_Check(self,AsCMethod(m)->type))
	  {
	    self->tp_getattro=AsCMethod(m)->type->tp_getattro;
	  }
#endif
      else
	{
	  PyDict_SetItem(methods,py__getattr__,m);
#if PYTHON_API_VERSION >= 1005
	  self->tp_getattro=subclass_getattro;
#else
	  self->tp_getattr=subclass_getattr;
#endif
	}
    }
  else
    {
      PyErr_Clear();
#if PYTHON_API_VERSION >= 1005
      self->tp_getattro=EC_findiattro;
#else
      self->tp_getattr=EC_findiattrs;
#endif
    }
}

static void
subclass_init_setattr(PyExtensionClass *self, PyObject *methods)
{
  PyObject *m;

  if((m=CCL_getattr(self,py__setattr__,"__setattr__")))
    {
      if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==setattr_by_name
	 && Subclass_Check(self,AsCMethod(m)->type))
	{
	  self->tp_setattr=AsCMethod(m)->type->tp_setattr;
	}
#if PYTHON_API_VERSION >= 1005
      else if(UnboundCMethod_Check(m) && AsCMethod(m)->meth==setattro_by_name
	   && Subclass_Check(self,AsCMethod(m)->type))
	  {
	    self->tp_setattro=AsCMethod(m)->type->tp_setattro;
	  }
#endif
      else
	{
	  PyDict_SetItem(methods,py__setattr__,m);
#if PYTHON_API_VERSION >= 1005
	  self->tp_setattro=subclass_setattro;
#else
	  self->tp_setattr=subclass_setattr;
#endif
	}
    }
  else
    {
      PyErr_Clear();
#if PYTHON_API_VERSION >= 1005
      self->tp_setattro=subclass_simple_setattro;
#else
      self->tp_setattro=subclass_simple_setattr;
#endif
    }
}


/* Constructor for building subclasses of C classes.

   That is, we want to build a C class object that described a
   subclass of a built-in type.
 */
static PyObject *
subclass__init__(PyExtensionClass *self, PyObject *args)
{
  PyObject *bases, *methods, *class_init;
  PyExtensionClass *type;
  char *name;
  int dynamic=1;

  UNLESS(PyArg_Parse(args,"(sOO)", &name, &bases, &methods)) return NULL;

  UNLESS(PyTuple_Check(bases) && PyTuple_Size(bases))
    {
      PyErr_SetString
	(PyExc_TypeError,
	 "second argument must be a tuple of 1 or more base classes");
    }

  self->bases=bases;
  Py_INCREF(bases);

  if(datafull_baseclasses(self) > 1)
    {
      PyErr_SetString(PyExc_TypeError, "too many datafull base classes");
      return NULL;
    }
  UNLESS(type=(PyExtensionClass *)datafull_baseclass(self))
    type=(PyExtensionClass*)PyTuple_GET_ITEM(bases, 0); 

  self->tp_name=name;
  self->bases=bases;
  Py_INCREF(methods);
  self->class_dictionary=methods;
#define copy_member(M) self->M=type->M
  copy_member(ob_size);
  copy_member(class_flags);

  if(type->bases)
    copy_member(tp_basicsize);
  else
    {
      self->tp_basicsize=type->tp_basicsize/sizeof(PyObject*)*sizeof(PyObject*);
      if(self->tp_basicsize < type->tp_basicsize)
	self->tp_basicsize += sizeof(PyObject*); /* To align on PyObject */
      self->tp_basicsize += sizeof(PyObject*); /* For instance dictionary */
    }

  copy_member(tp_itemsize);
  copy_member(tp_print);
  self->tp_dealloc=subclass_dealloc;

  subclass_init_getattr(self,methods);
  subclass_init_setattr(self,methods);

#define subclass_set(OP,N) \
  self->tp_ ##OP = subclass_ ##OP
  
  subclass_set(compare,cmp);
  subclass_set(repr,repr);

  if(subclass_hasattr(self,py__bind_to_object__) &&
     subclass_hasattr(self,py__call__))
    self->class_flags |= EXTENSIONCLASS_BINDABLE_FLAG;

  if(dynamic || has_number_methods(self))
    self->tp_as_number=&subclass_as_number;
  else
    self->tp_as_number=NULL;
    
  if(dynamic || has_collection_methods(self))
    {
      self->tp_as_sequence=&subclass_as_sequence;
      self->tp_as_mapping=&subclass_as_mapping;
    }
  else
    {
      self->tp_as_sequence=NULL;
      self->tp_as_sequence=NULL;
    }
  subclass_set(hash,hash);
  subclass_set(call,call);
  subclass_set(str,str);
  self->tp_doc=0;

  /* Check for and use __class_init__ */
  if(class_init=PyObject_GetAttrString(AsPyObject(self),"__class_init__"))
    {
      UNLESS_ASSIGN(class_init,PyObject_GetAttrString(class_init,"im_func"))
	return NULL;
      UNLESS_ASSIGN(class_init,PyObject_CallFunction(class_init,"O",self))
	return NULL;
      Py_DECREF(class_init);
    }
  else
    PyErr_Clear();

  Py_INCREF(Py_None);
  return Py_None;
}

struct PyMethodDef ExtensionClass_methods[] = {
  {"__init__",(PyCFunction)subclass__init__,0,""},
  
  {NULL,		NULL}		/* sentinel */
};


static PyExtensionClass CCLtype = {
  PyObject_HEAD_INIT(&CCLtype_class)
  0,				/*ob_size*/
  "C Class",			/*tp_name*/
  sizeof(PyExtensionClass),    	/*tp_basicsize*/
  0,				/*tp_itemsize*/
  /* methods */
  (destructor)CCL_dealloc,	/*tp_dealloc*/
  (printfunc)0,			/*tp_print*/
  (getattrfunc)CCL_getattrs,	/*tp_getattr*/
  (setattrfunc)CCL_setattrs,	/*tp_setattr*/
  (cmpfunc)0,			/*tp_compare*/
  (reprfunc)CCL_repr,		/*tp_repr*/
  0,				/*tp_as_number*/
  0,				/*tp_as_sequence*/
  0,				/*tp_as_mapping*/
  (hashfunc)0,			/*tp_hash*/
  (ternaryfunc)CCL_call,       	/*tp_call*/
  (reprfunc)0,			/*tp_str*/
#if PYTHON_API_VERSION >= 1005  
  (getattrofunc)CCL_getattro,	/*tp_getattr with object key*/
  (setattrofunc)CCL_setattro,	/*tp_setattr with object key*/
#else
  /* Space for future expansion */
  0L,0L,
#endif
  0L,0L,
  "C classes", /* Documentation string */
  METHOD_CHAIN(ExtensionClass_methods)
};

static PyExtensionClass Basetype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"Base",			/*tp_name*/
	sizeof(Dataless),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)0,			/*tp_dealloc*/
	(printfunc)0,			/*tp_print*/
	(getattrfunc)EC_findiattrs, 	/*tp_getattr*/
	(setattrfunc)0,			/*tp_setattr*/
	(cmpfunc)0,			/*tp_compare*/
	(reprfunc)0,			/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	(hashfunc)0,			/*tp_hash*/
	(ternaryfunc)0,			/*tp_call*/
	(reprfunc)0,			/*tp_str*/
#if PYTHON_API_VERSION >= 1005
	(getattrofunc)EC_findiattro,	/*tp_getattr with object key*/
	(setattrofunc)0,		/*tp_setattr with object key*/
#else
	/* Space for future expansion */
	0L,0L,
#endif
	0L,0L,
	"Base -- a do nothing base class\n"
	"\n"
	"A trivial base class that doesn't have any inheritable\n"
	"attributes but that can be listed first in the set of superclasses \n"
	"of a new subclass. \n",
	{NULL,NULL}
};

static PyObject *
bind_to_object(PyObject *self, PyObject *args)
{
  PyObject *inst;
  PMethod *r;

  UNLESS(PyArg_Parse(args,"O",&inst)) return NULL;

  UNLESS(PyExtensionInstance_Check(inst))
    {
      PyErr_SetString(PyExc_TypeError,
		      "attempt to wrap extension method using an object that\n"
		      "is not an extension class instance.");
      return NULL;
    }
  
  UNLESS(r = PyObject_NEW(PMethod, &PMethodType)) return NULL;

  Py_INCREF(inst);
  Py_INCREF(inst->ob_type);
  r->type=inst->ob_type;
  r->self=inst;
  r->meth=self;
  return AsPyObject(r);
}

struct PyMethodDef Method_methods[] = {
  {"__bind_to_object__",(PyCFunction)bind_to_object,0,""},
  
  {NULL,		NULL}		/* sentinel */
};

static PyExtensionClass Methodtype = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"Method",			/*tp_name*/
	sizeof(Dataless),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)0,			/*tp_dealloc*/
	(printfunc)0,			/*tp_print*/
	(getattrfunc)EC_findiattrs, 	/*tp_getattr*/
	(setattrfunc)0,			/*tp_setattr*/
	(cmpfunc)0,			/*tp_compare*/
	(reprfunc)0,			/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	(hashfunc)0,			/*tp_hash*/
	(ternaryfunc)0,			/*tp_call*/
	(reprfunc)0,			/*tp_str*/
#if PYTHON_API_VERSION >= 1005
	(getattrofunc)EC_findiattro,	/*tp_getattr with object key*/
	(setattrofunc)0,		/*tp_setattr with object key*/
#else
	/* Space for future expansion */
	0L,0L,
#endif
	0L,0L,

	"Base class for objects that want to be treated as methods\n"
	"\n"
	"The method class provides a method, __bind_to_object__, that\n"
	"binds an object to an instance.  If a method is a subobject\n"
	"of an extension-class instance, the the method will be bound\n"
	"to the instance and when the resulting object is called, it\n"
	"will call the method and pass the instance in addition to\n"
	"other arguments.  It is the responsibility of Method objects\n"
	"to implement (or inherit) a __call__ method.\n",

	METHOD_CHAIN(Method_methods)
};


PyObject *
MetaTypeUndefinedMethod()
{
  PyErr_SetString(PyExc_TypeError,
		  "undefined operation on partially numeric PyObject");
  return NULL;
}


/* List of methods defined in the module */

static struct PyMethodDef CC_methods[] = {
	
	{NULL,		NULL}		/* sentinel */
};


void
initExtensionClass()
{
  PyObject *m, *d;

  /* Create the module and add the functions */
  m = Py_InitModule4("ExtensionClass", CC_methods,
		     ExtensionClass_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);

  init_py_names();

  initializeBaseExtensionClass(&CCLtype);
  PyDict_SetItemString(d, "ExtensionClassType", (PyObject*)&CCLtype);

  initializeBaseExtensionClass(&Basetype);
  PyDict_SetItemString(d, "Base", (PyObject*)&Basetype);

  initializeBaseExtensionClass(&Methodtype);
  PyDict_SetItemString(d, "Method", (PyObject*)&Methodtype);

#ifdef Py_COBJECT_H
  /* Export C attribute lookup API */
  PyDict_SetItemString(d, "_PyEC_getattrs",
		       PyCObject_FromVoidPtr(EC_findiattrs,NULL));
  PyDict_SetItemString(d, "_PyEC_getattro",
		       PyCObject_FromVoidPtr(EC_findiattro,NULL));
  PyDict_SetItemString(d, "_PyEC_setattrs",
		       PyCObject_FromVoidPtr(subclass_simple_setattr,NULL));
  PyDict_SetItemString(d, "_PyEC_setattro",
		       PyCObject_FromVoidPtr(subclass_simple_setattro,NULL));
#endif

  /* Check for errors */
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module ExtensionClass");
}
