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


static char ThreadLock_module_documentation[] = 
""
"\n$Id: ThreadLock.c,v 1.3 1997/10/30 15:29:21 jim Exp $"
;

#include "Python.h"
#ifdef WITH_THREAD
#include "thread.h"
#endif

static PyObject *ErrorObject;

/* ----------------------------------------------------- */

#define UNLESS(E) if(!(E))

/* Declarations for objects of type ThreadLock */

typedef struct {
  PyObject_HEAD
  int count;
  long id;
#ifdef WITH_THREAD
  type_lock lock;
#endif
} ThreadLockObject;

staticforward PyTypeObject ThreadLockType;

/* ---------------------------------------------------------------- */

static int
cacquire(ThreadLockObject *self)
{
#ifdef WITH_THREAD
  long id = get_thread_ident();
#else
  long id = 1;
#endif
  if(self->count >= 0 && self->id==id)
    {
      /* Somebody has locked me.  It is either the current thread or
         another thread. */
      /* So this thread has it.  I can't have a race condition, because,
	 if another thread had the lock, then the id would not be this
	 one. */
      self->count++;
    }
  else
    {
#ifdef WITH_THREAD
      Py_BEGIN_ALLOW_THREADS
      acquire_lock(self->lock, 1);
      Py_END_ALLOW_THREADS
#endif
      self->count=0;
      self->id=id;
    }
  return 0;
}

static PyObject *
acquire(ThreadLockObject *self, PyObject *args)
{
  if(cacquire(self) < 0) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static int
crelease(ThreadLockObject *self)
{
#ifdef WITH_THREAD
  long id = get_thread_ident();
#else
  long id = 1;
#endif
  if(self->count >= 0 && self->id==id)
    {
      /* Somebody has locked me.  It is either the current thread or
         another thread. */
      /* So this thread has it.  I can't have a race condition, because,
	 if another thread had the lock, then the id would not be this
	 one. */
      self->count--;
#ifdef WITH_THREAD
      if(self->count < 0) release_lock(self->lock);
#endif
    }
  else
    {
      PyErr_SetString(ErrorObject, "release unlocked lock");
      return -1;
    }
  return 0;
}

static PyObject *
release(ThreadLockObject *self, PyObject *args)
{
  if(crelease(self) < 0) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
call_method(ThreadLockObject *self, PyObject *args)
{
  PyObject *f, *a=0, *k=0;

  UNLESS(PyArg_ParseTuple(args,"OO|O",&f, &a, &k)) return NULL;
  if(cacquire(self) < 0) return NULL;
  f=PyEval_CallObjectWithKeywords(f,a,k);
  if(crelease(self) < 0)
    {
      Py_XDECREF(f);
      f=NULL;
    }
  return f;
}

static struct PyMethodDef ThreadLock_methods[] = {
  {"guarded_apply", (PyCFunction)call_method, 1,
   "guarded_apply(FUNCTION, ARGS[, KEYWORDS]) -- Make a guarded function call\n"
   "\n"
   "Acquire the lock, call the function, and then release the lock.\n"
  },
  {"acquire", (PyCFunction)acquire, 1,
   "acquire() -- Acquire a lock, taking the thread ID into account"
  },
  {"release", (PyCFunction)release, 1,
   "release() -- Release a lock, taking the thread ID into account"
  },
  {NULL,		NULL}		/* sentinel */
};

/* ---------- */


static void
ThreadLock_dealloc(ThreadLockObject *self)
{
#ifdef WITH_THREAD
  free_lock(self->lock);
#endif
  PyMem_DEL(self);
}

static PyObject *
ThreadLock_getattr(ThreadLockObject *self, PyObject *name)
{
  char *cname;

  if((cname=PyString_AsString(name)))
    {
      if(*cname=='c' && strcmp(cname,"count")==0)
	return PyInt_FromLong(self->count);
      if(*cname=='i' && strcmp(cname,"id")==0)
	return PyInt_FromLong(self->id);
      return Py_FindMethod(ThreadLock_methods, (PyObject *)self, cname);
    }
  PyErr_SetObject(PyExc_AttributeError, name);
  return NULL;
}

static PyTypeObject ThreadLockType = {
  PyObject_HEAD_INIT(NULL)
  0,				/*ob_size*/
  "ThreadLock",			/*tp_name*/
  sizeof(ThreadLockObject),	/*tp_basicsize*/
  0,				/*tp_itemsize*/
  /* methods */
  (destructor)ThreadLock_dealloc,	/*tp_dealloc*/
  (printfunc)0,	/*tp_print*/
  (getattrfunc)0,		/*obsolete tp_getattr*/
  (setattrfunc)0,		/*obsolete tp_setattr*/
  (cmpfunc)0,	/*tp_compare*/
  (reprfunc)0,		/*tp_repr*/
  0,		/*tp_as_number*/
  0,		/*tp_as_sequence*/
  0,		/*tp_as_mapping*/
  (hashfunc)0,		/*tp_hash*/
  (ternaryfunc)0,	/*tp_call*/
  (reprfunc)0,		/*tp_str*/
  (getattrofunc)ThreadLock_getattr,			/*tp_getattro*/
  0,			/*tp_setattro*/
  
  /* Space for future expansion */
  0L,0L,
  "Thread-based lock objects\n"
  "\n"
  "These lock objects may be allocated multiple times by the same\n"
  "thread, but may only be allocated by one thread at a time.\n"
  "This is useful for locking instances in possibly nested method calls\n"
};

/* End of code for ThreadLock objects */
/* -------------------------------------------------------- */

static PyObject *
newThreadLockObject(ThreadLockObject *self, PyObject *args)
{
	
  UNLESS(PyArg_ParseTuple(args,"")) return NULL;
  UNLESS(self = PyObject_NEW(ThreadLockObject, &ThreadLockType)) return NULL;
  self->count=-1;
#ifdef WITH_THREAD
  self->lock = allocate_lock();
  if (self->lock == NULL) {
    PyMem_DEL(self);
    self = NULL;
    PyErr_SetString(ErrorObject, "can't allocate lock");
  }
#endif
  return (PyObject*)self;
}

static PyObject *
ident(PyObject *self, PyObject *args)
{
#ifdef WITH_THREAD
  return PyInt_FromLong(get_thread_ident());
#else
  return PyInt_FromLong(0);
#endif
}

/* List of methods defined in the module */

static struct PyMethodDef Module_methods[] = {
  { "allocate_lock", (PyCFunction)newThreadLockObject, 1,
    "allocate_lock() -- Return a new lock object"
  },
  { "get_ident", (PyCFunction)ident, 1,
    "get_ident() -- Get the id of the current thread"
  },
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/* Initialization function for the module (*must* be called initThreadLock) */

void
initThreadLock()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.3 $";

  /* Create the module and add the functions */
  m = Py_InitModule4("ThreadLock", Module_methods,
		     ThreadLock_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);

  ThreadLockType.ob_type=&PyType_Type;
  PyDict_SetItemString(d,"ThreadLockType", (PyObject*)&ThreadLockType);

  ErrorObject = PyString_FromString("ThreadLock.error");
  PyDict_SetItemString(d, "error", ErrorObject);

  PyDict_SetItemString(d, "__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));

#ifdef WITH_THREAD
  PyDict_SetItemString(d, "WITH_THREAD", PyInt_FromLong(1));
#else
  PyDict_SetItemString(d, "WITH_THREAD", Py_None);
#endif  
	
  /* Check for errors */
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module ThreadLock");
}

/*****************************************************************************
Revision Log:

  $Log: ThreadLock.c,v $
  Revision 1.3  1997/10/30 15:29:21  jim
  Added conditional compilation logic to allow compilation in
  non-threaded environments.

  Revision 1.2  1997/07/02 20:21:02  jim
  Added stupid parens and other changes to make 'gcc -Wall -pedantic'
  happy.  Got rid of unused macros.

  Revision 1.1  1997/04/11 21:44:58  jim
  *** empty log message ***

  $Revision 1.1  1997/02/24 23:25:42  jim
  $initial
  $

*****************************************************************************/
