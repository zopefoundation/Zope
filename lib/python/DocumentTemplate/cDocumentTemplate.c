/***********************************************************
     Copyright 

       Copyright 1997 Digital Creations, L.L.C., 910 Princess Anne
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
   
      Digital Creations L.L.C.  
      info@digicool.com
      (540) 371-6909

******************************************************************/


static char cDocumentTemplate_module_documentation[] = 
""
"\n$Id: cDocumentTemplate.c,v 1.1 1997/08/27 18:55:47 jim Exp $"
;

#include "ExtensionClass.h"

static PyObject *py_isDocTemp=0, *py_blocks=0, *py_=0, *join=0;

/* ----------------------------------------------------- */

static void PyVar_Assign(PyObject **v, PyObject *e) { Py_XDECREF(*v); *v=e;}
#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)

typedef struct {
  PyObject_HEAD
  PyObject *inst;
  PyObject *cache;
  PyObject *namespace;
} InstanceDictobject;

staticforward PyExtensionClass InstanceDictType;

static PyObject *
InstanceDict___init__( InstanceDictobject *self, PyObject *args)
{
  UNLESS(PyArg_ParseTuple(args, "OO", &(self->inst), &(self->namespace)))
    return NULL;
  Py_INCREF(self->inst);
  Py_INCREF(self->namespace);
  UNLESS(self->cache=PyDict_New()) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static struct PyMethodDef InstanceDict_methods[] = {
  {"__init__",	(PyCFunction)InstanceDict___init__, 1,
   ""},
  
  {NULL,		NULL}		/* sentinel */
};

/* ---------- */

static void
InstanceDict_dealloc(InstanceDictobject *self)
{
  Py_XDECREF(self->inst);
  Py_XDECREF(self->cache);
  Py_XDECREF(self->namespace);
  PyMem_DEL(self);
}

static PyObject *
InstanceDict_getattr(InstanceDictobject *self, PyObject *name)
{
  return Py_FindAttr((PyObject *)self, name);
}

static PyObject *
InstanceDict_repr(InstanceDictobject *self)
{
  return PyObject_Repr(self->inst);
}

/* Code to access InstanceDict objects as mappings */

static int
InstanceDict_length( InstanceDictobject *self)
{
  return 1;
}

static PyObject *
InstanceDict_subscript( InstanceDictobject *self, PyObject *key)
{
  PyObject *r;
  char *name;
  
  /* Try to get value from the cache */
  if(r=PyObject_GetItem(self->cache, key)) return r;
  PyErr_Clear();
  
  /* Check for __str__ */
  UNLESS(name=PyString_AsString(key)) return NULL;
  if(*name=='_')
    {
      UNLESS(strcmp(name,"__str__")==0) goto KeyError;
      return PyObject_Str(self->inst);
    }
  
  /* OK, use getattr */
  UNLESS(r=PyObject_GetAttr(self->inst, key)) goto KeyError;
  
  if(r && PyObject_SetItem(self->cache, key, r) < 0) PyErr_Clear();
  
  return r;
  
KeyError:
  PyErr_SetObject(PyExc_KeyError, key);
  return NULL;
}

static int
InstanceDict_ass_sub( InstanceDictobject *self, PyObject *v, PyObject *w)
{
  PyErr_SetString(PyExc_TypeError,
		  "InstanceDict objects do not support item assignment");
  return -1;
}

static PyMappingMethods InstanceDict_as_mapping = {
  (inquiry)InstanceDict_length,		/*mp_length*/
  (binaryfunc)InstanceDict_subscript,		/*mp_subscript*/
  (objobjargproc)InstanceDict_ass_sub,	/*mp_ass_subscript*/
};

/* -------------------------------------------------------- */


static char InstanceDicttype__doc__[] = 
""
;

static PyExtensionClass InstanceDictType = {
  PyObject_HEAD_INIT(NULL)
  0,				/*ob_size*/
  "InstanceDict",			/*tp_name*/
  sizeof(InstanceDictobject),	/*tp_basicsize*/
  0,				/*tp_itemsize*/
  /* methods */
  (destructor)InstanceDict_dealloc,	/*tp_dealloc*/
  (printfunc)0,	/*tp_print*/
  (getattrfunc)0,		/*obsolete tp_getattr*/
  (setattrfunc)0,		/*obsolete tp_setattr*/
  (cmpfunc)0,	/*tp_compare*/
  (reprfunc)InstanceDict_repr,		/*tp_repr*/
  0,		/*tp_as_number*/
  0,		/*tp_as_sequence*/
  &InstanceDict_as_mapping,		/*tp_as_mapping*/
  (hashfunc)0,		/*tp_hash*/
  (ternaryfunc)0,	/*tp_call*/
  (reprfunc)0,		/*tp_str*/
  (getattrofunc)InstanceDict_getattr,			/*tp_getattro*/
  0,			/*tp_setattro*/
  
  /* Space for future expansion */
  0L,0L,
  InstanceDicttype__doc__, /* Documentation string */
  METHOD_CHAIN(InstanceDict_methods)
};

typedef struct {
  PyObject_HEAD
  PyObject *data;
} MMobject;

staticforward PyExtensionClass MMtype;

static PyObject *
MM_push(self, args)
	MMobject *self;
	PyObject *args;
{
  PyObject *src;
  UNLESS(PyArg_Parse(args, "O", &src)) return NULL;
  UNLESS(-1 != PyList_Append(self->data,src)) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
MM_pop(self, args)
	MMobject *self;
	PyObject *args;
{
  int i=1, l;
  PyObject *r;

  if(args) UNLESS(PyArg_Parse(args, "i", &i)) return NULL;
  if((l=PyList_Size(self->data)) < 0) return NULL;
  i=l-i;
  UNLESS(r=PySequence_GetItem(self->data,l-1)) return NULL;
  if(PyList_SetSlice(self->data,i,l,NULL) < 0) goto err;
  return r;
err:
  Py_DECREF(r);
  return NULL;
}

static PyObject *
MM__init__(self, args)
     MMobject *self;
     PyObject *args;
{
  UNLESS(PyArg_Parse(args, "")) return NULL;
  UNLESS(self->data=PyList_New(0)) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static struct PyMethodDef MM_methods[] = {
  {"__init__", (PyCFunction)MM__init__, 0,
   "__init__() -- Create a new empty multi-mapping"},
  {"push", (PyCFunction) MM_push, 0,
   "push(mapping_object) -- Add a data source"},
  {"pop",  (PyCFunction) MM_pop,  0,
   "pop() -- Remove and return the last data source added"}, 
  {NULL,		NULL}		/* sentinel */
};

static void
MM_dealloc(self)
     MMobject *self;
{
  Py_XDECREF(self->data);
  PyMem_DEL(self);
}

static PyObject *
MM_getattr(self, name)
	MMobject *self;
	char *name;
{
  return Py_FindMethod(MM_methods, (PyObject *)self, name);
}

static int
MM_length(self)
	MMobject *self;
{
  long l=0, el, i;
  PyObject *e=0;

  UNLESS(-1 != (i=PyList_Size(self->data))) return -1;
  while(--i >= 0)
    {
      e=PyList_GetItem(self->data,i);
      UNLESS(-1 != (el=PyObject_Length(e))) return -1;
      l+=el;
    }
  return l;
}

static PyObject *
MM_subscript(self, key)
	MMobject *self;
	PyObject *key;
{
  long i;
  int dt=0;
  PyObject *e, *rr, *tb;

  UNLESS(-1 != (i=PyList_Size(self->data))) return NULL;
  while(--i >= 0)
    {
      e=PyList_GetItem(self->data,i);
      if(e=PyObject_GetItem(e,key))
	{
	  dt=0;

	  if(PyCallable_Check(e))
	    {
	      /* Decide whether we have a document template */
	      if(rr=PyObject_GetAttr(e,py_isDocTemp))
		{
		  if(PyObject_IsTrue(rr)) dt=1;
		  Py_DECREF(rr);
		}
	      else PyErr_Clear();

	      /* Try calling the object */
	      if(dt)
		ASSIGN(e,PyObject_CallFunction(e,"OO", Py_None, self));
	      else if(rr=PyObject_CallObject(e,NULL))
		ASSIGN(e,rr);
	      else
		PyErr_Clear();
	    }

	  return e;
	}
      PyErr_Fetch(&e, &rr, &tb);
      if(dt || e != PyExc_KeyError)
	{
	  PyErr_Restore(e,rr,tb);
	  return NULL;
	}
      Py_XDECREF(e);
      Py_XDECREF(rr);
      Py_XDECREF(tb);
    }
  PyErr_SetObject(PyExc_KeyError,key);
  return NULL;
}

static PyMappingMethods MM_as_mapping = {
	(inquiry)MM_length,		/*mp_length*/
	(binaryfunc)MM_subscript,      	/*mp_subscript*/
	(objobjargproc)NULL,		/*mp_ass_subscript*/
};

/* -------------------------------------------------------- */

static char MMtype__doc__[] = 
"TemplateDict -- Combine multiple mapping objects for lookup"
;

static PyExtensionClass MMtype = {
	PyObject_HEAD_INIT(NULL)
	0,				/*ob_size*/
	"TemplateDict",			/*tp_name*/
	sizeof(MMobject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)MM_dealloc,		/*tp_dealloc*/
	(printfunc)0,			/*tp_print*/
	(getattrfunc)MM_getattr,	/*tp_getattr*/
	(setattrfunc)0,			/*tp_setattr*/
	(cmpfunc)0,			/*tp_compare*/
	(reprfunc)0,			/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	&MM_as_mapping,			/*tp_as_mapping*/
	(hashfunc)0,			/*tp_hash*/
	(ternaryfunc)0,			/*tp_call*/
	(reprfunc)0,			/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	MMtype__doc__, /* Documentation string */
	METHOD_CHAIN(MM_methods)
};

static struct PyMethodDef TemplateDict_methods[] = {
  {NULL,		NULL}		/* sentinel */
};



/* List of methods defined in the module */

static PyObject *
render_blocks(PyObject *self, PyObject *args)
{
  PyObject *md, *blocks, *rendered, *block;
  int l, i, k;

  UNLESS(PyArg_ParseTuple(args,"OO", &self, &md)) return NULL;
  UNLESS(md=Py_BuildValue("(O)",md)) return NULL;
  UNLESS(rendered=PyList_New(0)) goto err;
  UNLESS(blocks=PyObject_GetAttr(self,py_blocks)) goto err;
  if((l=PyList_Size(blocks)) < 0) goto err;
  for(i=0; i < l; i++)
    {
      block=PyList_GET_ITEM(((PyListObject*)blocks), i);
      if(PyString_Check(block))
	{
	  if(PyList_Append(rendered,block) < 0) goto err;
	}
      else
	{
	  UNLESS(block=PyObject_CallObject(block,md)) goto err;
	  k=PyList_Append(rendered,block);
	  Py_DECREF(block);
	  if(k < 0) goto err;
	}
    }
  Py_DECREF(md);
  Py_DECREF(blocks);
  ASSIGN(rendered,PyObject_CallFunction(join,"OO",rendered,py_));
  return rendered;

err:
  Py_DECREF(md);
  Py_XDECREF(rendered);
  Py_XDECREF(blocks);
  return NULL;
}

static struct PyMethodDef Module_Level__methods[] = {
  {"render_blocks", (PyCFunction)render_blocks,	METH_VARARGS,
   ""},
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/* Initialization function for the module (*must* be called initcDocumentTemplate) */

void
initcDocumentTemplate()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.1 $";

  UNLESS(py_isDocTemp=PyString_FromString("isDocTemp")) return;
  UNLESS(py_blocks=PyString_FromString("blocks")) return;
  UNLESS(py_=PyString_FromString("")) return;
  UNLESS(join=PyImport_ImportModule("string")) return;
  ASSIGN(join,PyObject_GetAttrString(join,"join"));
  UNLESS(join) return;

  m = Py_InitModule4("cDocumentTemplate", Module_Level__methods,
		     cDocumentTemplate_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  d = PyModule_GetDict(m);

  PyExtensionClass_Export(d,"InstanceDict",InstanceDictType);
  PyExtensionClass_Export(d,"TemplateDict",MMtype);

  PyDict_SetItemString(d, "__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));
  
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module cDocumentTemplate");
}

/*****************************************************************************
Revision Log:

  $Log: cDocumentTemplate.c,v $
  Revision 1.1  1997/08/27 18:55:47  jim
  initial

  Revision 1.4  1997/08/07 12:26:52  jim
  - InstanceDicts no longer try to evaluate results.  This is defered to
    the TemplateDict.
  - Fixed bug in the way TemplateDicts were evaluating
    document templates.
  - TemplateDicts now use PyCallable_Check before trying to call
    returned values.  This should speed common cases.

  Revision 1.3  1997/08/05 21:56:20  jim
  Changed the way InstanceDicts call template attributes to avoid
  problem with instance attributes overriding kw arguments.

  Revision 1.2  1997/04/11 19:53:36  jim
  Forgot NULL return on error in render_blocks.

  Revision 1.1  1997/04/09 22:24:23  jim
  *** empty log message ***

  $Revision 1.1  1997/02/24 23:25:42  jim
  $initial
  $

*****************************************************************************/
