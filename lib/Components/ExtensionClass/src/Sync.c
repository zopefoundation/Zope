/*****************************************************************************

  Copyright (c) 1996-2002 Zope Corporation and Contributors.
  All Rights Reserved.

  This software is subject to the provisions of the Zope Public License,
  Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE

 ****************************************************************************/

static char Sync_module_documentation[] = 
""
"\n$Id: Sync.c,v 1.5 2002/06/10 22:48:46 jeremy Exp $"
;

#include "ExtensionClass.h"

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
initSync(void)
{
  PyObject *m, *d;
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

  CHECK_FOR_ERRORS("can't initialize module MethodObject");
}
