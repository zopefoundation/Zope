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

  $Id: MultiMapping.c,v 1.7 1998/11/17 20:20:17 jim Exp $

  If you have questions regarding this software,
  contact:
 
    Digital Creations L.C.  
    info@digicool.com
 
    (540) 371-6909

*/
#include "Python.h"
#include "ExtensionClass.h"

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
  PyMem_DEL(self);
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
initMultiMapping()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.7 $";

  m = Py_InitModule4(
      "MultiMapping", MultiMapping_methods,
      "MultiMapping -- Wrap multiple mapping objects for lookup"
      "\n\n"
      "$Id: MultiMapping.c,v 1.7 1998/11/17 20:20:17 jim Exp $\n",
      (PyObject*)NULL,PYTHON_API_VERSION);
  d = PyModule_GetDict(m);
  PyExtensionClass_Export(d,"MultiMapping",MMtype);
  PyDict_SetItemString(d,"__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));

  if (PyErr_Occurred()) Py_FatalError("can't initialize module MultiMapping");
}
