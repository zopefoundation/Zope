/***********************************************************
     Copyright 

       Copyright 1997 Digital Creations, L.L.C., 910 Princess Anne
       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
       rights reserved.  Copyright in this software is owned by DCLC,
       unless otherwise indicated.  Note that any product, process or
       technology described in this software may be the subject of
       other Intellectual Property rights reserved by Digital
       Creations, L.C. and are not licensed hereunder.

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


static char Sync_module_documentation[] = 
""
"\n$Id: Sync.c,v 1.1 1997/09/18 20:36:37 jim Exp $"
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
  {NULL,		NULL}		/* sentinel */
};

/* List of methods defined in the module */

static struct PyMethodDef Module_Level__methods[] = {
  
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/* Initialization function for the module (*must* be called initSync) */

void
initSync()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.1 $";
  PURE_MIXIN_CLASS(Synchronized,
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

  /* Create the module and add the functions */
  m = Py_InitModule4("Sync", Module_Level__methods,
		     Sync_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  PyExtensionClass_Export(d,"Synchronized",SynchronizedType);
  PyDict_SetItemString(d,"__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));

  /* Check for errors */
  CHECK_FOR_ERRORS("can't initialize module MethodObject");
}

/*****************************************************************************
Revision Log:

  $Log: Sync.c,v $
  Revision 1.1  1997/09/18 20:36:37  jim
  *** empty log message ***

  $Revision 1.2  1997/06/21 15:22:03  jim
  $Removed "object" suffix from generates C type names
  $
  $Revision 1.1  1997/02/24 23:25:42  jim
  $initial
  $

*****************************************************************************/
