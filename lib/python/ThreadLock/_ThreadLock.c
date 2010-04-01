/*****************************************************************************

  Copyright (c) 1996-2003 Zope Foundation and Contributors.
  All Rights Reserved.

  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE

 ****************************************************************************/

static char ThreadLock_module_documentation[] = 
""
"\n$Id: _ThreadLock.c,v 1.2 2003/11/28 16:46:39 jim Exp $"
;

#include "Python.h"

#ifdef WITH_THREAD

#include "listobject.h"

#ifdef PyList_SET_ITEM

#include "pythread.h"
#define get_thread_ident PyThread_get_thread_ident
#define acquire_lock PyThread_acquire_lock
#define release_lock PyThread_release_lock
#define type_lock PyThread_type_lock
#define free_lock PyThread_free_lock
#define allocate_lock PyThread_allocate_lock

#else

#include "thread.h"

#endif

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

static int
cacquire(ThreadLockObject *self, int wait)
{
  int acquired = 1;
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
      acquired = acquire_lock(self->lock, wait ? WAIT_LOCK : NOWAIT_LOCK);
      Py_END_ALLOW_THREADS
#endif
      if (acquired)
        {
          self->count=0;
          self->id=id;
        }
    }
  return acquired;
}

static PyObject *
acquire(ThreadLockObject *self, PyObject *args)
{
  int wait = -1, acquired;
  if (! PyArg_ParseTuple(args, "|i", &wait)) return NULL;
  acquired=cacquire(self, wait);
  if(acquired < 0) return NULL;
  if (wait >= 0) return PyInt_FromLong(acquired);
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
  if (! PyArg_ParseTuple(args, "")) return NULL;
  if(crelease(self) < 0) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
call_method(ThreadLockObject *self, PyObject *args)
{
  PyObject *f, *a=0, *k=0;

  UNLESS(PyArg_ParseTuple(args,"OO|O",&f, &a, &k)) return NULL;
  if(cacquire(self, -1) < 0) return NULL;
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
   "acquire([wait]) -- Acquire a lock, taking the thread ID into account"
  },
  {"release", (PyCFunction)release, 1,
   "release() -- Release a lock, taking the thread ID into account"
  },
  {NULL,		NULL}		/* sentinel */
};

static void
ThreadLock_dealloc(ThreadLockObject *self)
{
#ifdef WITH_THREAD
  free_lock(self->lock);
#endif
  PyObject_DEL(self);
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

static PyObject *
newThreadLockObject(ThreadLockObject *self, PyObject *args)
{
	
  UNLESS(PyArg_ParseTuple(args,"")) return NULL;
  UNLESS(self = PyObject_NEW(ThreadLockObject, &ThreadLockType)) return NULL;
  self->count=-1;
#ifdef WITH_THREAD
  self->lock = allocate_lock();
  if (self->lock == NULL) {
    PyObject_DEL(self);
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

static struct PyMethodDef Module_methods[] = {
  { "allocate_lock", (PyCFunction)newThreadLockObject, 1,
    "allocate_lock() -- Return a new lock object"
  },
  { "get_ident", (PyCFunction)ident, 1,
    "get_ident() -- Get the id of the current thread"
  },
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

void
init_ThreadLock(void)
{
  PyObject *m, *d;

  m = Py_InitModule4("_ThreadLock", Module_methods,
		     ThreadLock_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  d = PyModule_GetDict(m);

  ThreadLockType.ob_type=&PyType_Type;
  PyDict_SetItemString(d,"ThreadLockType", (PyObject*)&ThreadLockType);

  ErrorObject = PyString_FromString("ThreadLock.error");
  PyDict_SetItemString(d, "error", ErrorObject);

#ifdef WITH_THREAD
  PyDict_SetItemString(d, "WITH_THREAD", PyInt_FromLong(1));
#else
  PyDict_SetItemString(d, "WITH_THREAD", Py_None);
#endif  
	
  /* Check for errors */
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module ThreadLock");
}
