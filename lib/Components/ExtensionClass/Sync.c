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

  $Id: Sync.c,v 1.2 1998/11/17 20:22:34 jim Exp $

  If you have questions regarding this software,
  contact:
 
    Digital Creations L.C.  
    info@digicool.com
 
    (540) 371-6909

*/

static char Sync_module_documentation[] = 
""
"\n$Id: Sync.c,v 1.2 1998/11/17 20:22:34 jim Exp $"
;

#include "ExtensionClass.h"

static PyObject *ErrorObject;

/* ----------------------------------------------------- */

static void PyVar_Assign(PyObject **v, PyObject *e) { Py_XDECREF(*v); *v=e;}
#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)
#define OBJECT(O) ((PyObject*)(O))

PyObject *lockstr, *aqstr, *restr, *newlock;

static PyObject *
Synchronized___call_method__(PyObject *self, PyObject *args)
{
  PyObject *f, *a, *k=0, *l=0, *aq=0, *t, *v, *tb, *r;
  UNLESS(PyArg_ParseTuple(args, "OO|O", &f, &a, &k)) return NULL;

  UNLESS(l=PyObject_GetAttr(self, lockstr))
    {
      PyErr_Clear();
      UNLESS(l=PyObject_CallObject(newlock, NULL)) return NULL;
      if(PyObject_SetAttr(self, lockstr, l) < 0) goto err;
    }

  UNLESS(aq=PyObject_GetAttr(l, aqstr)) goto err;
  UNLESS_ASSIGN(aq,PyObject_CallObject(aq,NULL)) goto err;

  if(k) r=PyEval_CallObjectWithKeywords(f,a,k);
  else  r=PyObject_CallObject(f,a);

  PyErr_Fetch(&t, &v, &tb);

  ASSIGN(aq,PyObject_GetAttr(l, restr));
  if(aq) ASSIGN(aq,PyObject_CallObject(aq,NULL));

  Py_XDECREF(aq);
  Py_DECREF(l);

  PyErr_Restore(t, v, tb);

  return r;

err:
  Py_DECREF(l);
  return NULL;
}


static struct PyMethodDef Synchronized_methods[] = {
  {"__call_method__", (PyCFunction)Synchronized___call_method__, METH_VARARGS,
   "Call a method by first getting a thread lock"
  },
  {NULL,		NULL}
};

static struct PyMethodDef Module_Level__methods[] = {  
  {NULL, (PyCFunction)NULL, 0, NULL}
};

void
initSync()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.2 $";
  PURE_MIXIN_CLASS(
       Synchronized,
       "Mix-in class that provides synchonization of method calls\n"
       "\n"
       "Only one thread is allowed to call a synchronized \n"
       "object's methods.\n",
       Synchronized_methods);

  UNLESS((lockstr=PyString_FromString("_sync__lock")) &&
	 (aqstr=PyString_FromString("acquire")) &&
	 (restr=PyString_FromString("release")) &&
	 (newlock=PyImport_ImportModule("ThreadLock"))
	 ) return;

  ASSIGN(newlock, PyObject_GetAttrString(newlock, "allocate_lock"));
  UNLESS(newlock) return;

  m = Py_InitModule4("Sync", Module_Level__methods,
		     Sync_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  d = PyModule_GetDict(m);
  PyExtensionClass_Export(d,"Synchronized",SynchronizedType);
  PyDict_SetItemString(d,"__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));

  CHECK_FOR_ERRORS("can't initialize module MethodObject");
}
