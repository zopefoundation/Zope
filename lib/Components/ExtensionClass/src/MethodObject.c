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

  $Id: MethodObject.c,v 1.7 2002/01/25 15:34:06 gvanrossum Exp $

  If you have questions regarding this software,
  contact:
 
    Digital Creations L.C.  
    info@digicool.com
 
    (540) 371-6909

*/

#include "ExtensionClass.h"

static PyObject *
of(PyObject *self, PyObject *args)
{
  PyObject *inst;

  if(PyArg_Parse(args,"O",&inst)) return PyECMethod_New(self,inst);
  else return NULL;
}

struct PyMethodDef Method_methods[] = {
  {"__of__",(PyCFunction)of,0,""},  
  {NULL,		NULL}		/* sentinel */
};

static struct PyMethodDef methods[] = {{NULL,	NULL}};

void
initMethodObject(void)
{
  PyObject *m, *d;
  PURE_MIXIN_CLASS(Method,
	"Base class for objects that want to be treated as methods\n"
	"\n"
	"The method class provides a method, __of__, that\n"
	"binds an object to an instance.  If a method is a subobject\n"
	"of an extension-class instance, the the method will be bound\n"
	"to the instance and when the resulting object is called, it\n"
	"will call the method and pass the instance in addition to\n"
	"other arguments.  It is the responsibility of Method objects\n"
	"to implement (or inherit) a __call__ method.\n",
	Method_methods);

  /* Create the module and add the functions */
  m = Py_InitModule4("MethodObject", methods,
		     "Method-object mix-in class module\n\n"
		     "$Id: MethodObject.c,v 1.7 2002/01/25 15:34:06 gvanrossum Exp $\n",
		     (PyObject*)NULL,PYTHON_API_VERSION);

  d = PyModule_GetDict(m);
  PyExtensionClass_Export(d,"Method",MethodType);

  /* Check for errors */
  CHECK_FOR_ERRORS("can't initialize module MethodObject");
}

