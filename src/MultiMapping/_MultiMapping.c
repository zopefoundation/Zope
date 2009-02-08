/*****************************************************************************

  Copyright (c) 1996-2003 Zope Corporation and Contributors.
  All Rights Reserved.

  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE

 ****************************************************************************/

#include "ExtensionClass/ExtensionClass.h"

#define UNLESS(E) if(!(E))

typedef struct {
  PyObject_HEAD
  PyObject *data;
} MMobject;

staticforward PyExtensionClass MMtype;

static PyObject *
MM_push(MMobject *self, PyObject *args)
{
  PyObject *src;
  UNLESS(PyArg_ParseTuple(args, "O", &src)) return NULL;
  UNLESS(-1 != PyList_Append(self->data,src)) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
MM_pop(MMobject *self, PyObject *args)
{
  int i=1, l;
  PyObject *r;

  if(args) UNLESS(PyArg_ParseTuple(args, "|i", &i)) return NULL;
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
MM__init__(MMobject *self, PyObject *args)
{
  UNLESS(self->data=PyList_New(0)) return NULL;
  if (args)
    {
      int l, i;

      if ((l=PyTuple_Size(args)) < 0) return NULL;
      for (i=0; i < l; i++) 
	if (PyList_Append(self->data, PyTuple_GET_ITEM(args, i)) < 0)
	  return NULL;
    }
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
MM_subscript(MMobject *self, PyObject *key)
{
  long i;
  PyObject *e;

  UNLESS(-1 != (i=PyList_Size(self->data))) return NULL;
  while(--i >= 0)
    {
      e=PyList_GetItem(self->data,i);
      if((e=PyObject_GetItem(e,key))) return e;
      PyErr_Clear();
    }
  PyErr_SetObject(PyExc_KeyError,key);
  return NULL;
}

static PyObject *
MM_has_key(MMobject *self, PyObject *args)
{
  PyObject *key;

  UNLESS(PyArg_ParseTuple(args,"O",&key)) return NULL;
  if((key=MM_subscript(self, key)))
    {
      Py_DECREF(key);
      return PyInt_FromLong(1);
    }
  PyErr_Clear();
  return PyInt_FromLong(0);
}

static PyObject *
MM_get(MMobject *self, PyObject *args)
{
  PyObject *key, *d=Py_None;

  UNLESS(PyArg_ParseTuple(args,"O|O",&key,&d)) return NULL;
  if((key=MM_subscript(self, key))) return key;
  PyErr_Clear();
  Py_INCREF(d);
  return d;
}

static struct PyMethodDef MM_methods[] = {
  {"__init__", (PyCFunction)MM__init__, METH_VARARGS,
   "__init__([m1, m2, ...]) -- Create a new empty multi-mapping"},
  {"get",  (PyCFunction) MM_get,  METH_VARARGS,
   "get(key,[default]) -- Return a value for the given key or a default"}, 
  {"has_key",  (PyCFunction) MM_has_key,  METH_VARARGS,
   "has_key(key) -- Return 1 if the mapping has the key, and 0 otherwise"}, 
  {"push", (PyCFunction) MM_push, METH_VARARGS,
   "push(mapping_object) -- Add a data source"},
  {"pop",  (PyCFunction) MM_pop,  METH_VARARGS,
   "pop([n]) -- Remove and return the last data source added"}, 
  {NULL,		NULL}		/* sentinel */
};

static void
MM_dealloc(MMobject *self)
{
  Py_XDECREF(self->data);
  Py_DECREF(self->ob_type);
  PyObject_DEL(self);
}

static PyObject *
MM_getattr(MMobject *self, char *name)
{
  return Py_FindMethod(MM_methods, (PyObject *)self, name);
}

static int
MM_length(MMobject *self)
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

static PyMappingMethods MM_as_mapping = {
	(inquiry)MM_length,		/*mp_length*/
	(binaryfunc)MM_subscript,      	/*mp_subscript*/
	(objobjargproc)NULL,		/*mp_ass_subscript*/
};

/* -------------------------------------------------------- */

static char MMtype__doc__[] = 
"MultiMapping -- Combine multiple mapping objects for lookup"
;

static PyExtensionClass MMtype = {
	PyObject_HEAD_INIT(NULL)
	0,				/*ob_size*/
	"MultiMapping",			/*tp_name*/
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

static struct PyMethodDef MultiMapping_methods[] = {
  {NULL,		NULL}		/* sentinel */
};

void
init_MultiMapping(void)
{
  PyObject *m, *d;

  m = Py_InitModule4(
      "_MultiMapping", MultiMapping_methods,
      "MultiMapping -- Wrap multiple mapping objects for lookup"
      "\n\n"
      "$Id$\n",
      (PyObject*)NULL,PYTHON_API_VERSION);
  d = PyModule_GetDict(m);
  PyExtensionClass_Export(d,"MultiMapping",MMtype);

  if (PyErr_Occurred()) Py_FatalError("can't initialize module MultiMapping");
}
