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

  $Id: ComputedAttribute.c,v 1.4 2001/01/23 14:37:20 jim Exp $

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
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)
#define OBJECT(O) ((PyObject*)(O))

typedef struct {
  PyObject_HEAD
  PyObject *callable;
  int level;
} CA;

static PyObject *
CA__init__(CA *self, PyObject *args)
{
  PyObject *callable;
  int level=0;

  UNLESS(PyArg_ParseTuple(args,"O|i",&callable, &level)) return NULL;

  if (level > 0) 
    {
      callable=PyObject_CallFunction(OBJECT(self->ob_type), "Oi", 
				     callable, self->level-1);
      UNLESS (callable) return NULL;
      self->level=level;
    }
  else
    {
      Py_INCREF(callable);
      self->level=0;
    }

  self->callable=callable;

  Py_INCREF(Py_None);
  return Py_None;
}

static void
CA_dealloc(CA *self)     
{
  Py_DECREF(self->callable);
  Py_DECREF(self->ob_type);
  PyMem_DEL(self);
}

static PyObject *
CA_of(CA *self, PyObject *args)
{
  if (self->level > 0) 
    {
      Py_INCREF(self->callable);
      return self->callable;
    }

  if (PyString_Check(self->callable))
    {
      /* Special case string as simple alias. */
      PyObject *o;

      UNLESS (PyArg_ParseTuple(args,"O", &o)) return NULL;
      return PyObject_GetAttr(o, self->callable);
    }

  return PyObject_CallObject(self->callable, args);
}

static struct PyMethodDef CA_methods[] = {
  {"__init__",(PyCFunction)CA__init__, METH_VARARGS, ""},
  {"__of__",  (PyCFunction)CA_of,      METH_VARARGS, ""},
  {NULL,		NULL}		/* sentinel */
};

static PyExtensionClass ComputedAttributeType = {
  PyObject_HEAD_INIT(NULL) 0,
  "ComputedAttribute", sizeof(CA),
  0,
  (destructor)CA_dealloc,
  0,0,0,0,0,   0,0,0,   0,0,0,0,0,   0,0,
  "ComputedAttribute(callable) -- Create a computed attribute",
  METHOD_CHAIN(CA_methods), 
  EXTENSIONCLASS_BINDABLE_FLAG
};

static struct PyMethodDef methods[] = {
  {NULL,		NULL}
};

void
initComputedAttribute()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.4 $";

  UNLESS(ExtensionClassImported) return;

  ComputedAttributeType.tp_getattro=
    (getattrofunc)PyExtensionClassCAPI->getattro;
  
  /* Create the module and add the functions */
  m = Py_InitModule4("ComputedAttribute", methods,
	   "Provide Computed Attributes\n\n"
	   "$Id: ComputedAttribute.c,v 1.4 2001/01/23 14:37:20 jim Exp $\n",
		     OBJECT(NULL),PYTHON_API_VERSION);

  d = PyModule_GetDict(m);
  PyExtensionClass_Export(d,"ComputedAttribute",ComputedAttributeType);
  PyDict_SetItemString(d,"__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));
  CHECK_FOR_ERRORS("can't initialize module Acquisition");
}
