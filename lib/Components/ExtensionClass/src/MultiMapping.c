/*

  $Id: MultiMapping.c,v 1.5 1997/07/02 20:20:12 jim Exp $

  Sample extension class program that implements multi-mapping objects. 


     Copyright 

       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
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


*****************************************************************************/
#include "Python.h"
#include "ExtensionClass.h"

#define UNLESS(E) if(!(E))

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
	PyObject_HEAD_INIT(&PyType_Type)
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
  char *rev="$Revision: 1.5 $";

  m = Py_InitModule4("MultiMapping", MultiMapping_methods,
		     "MultiMapping -- Wrap multiple mapping objects for lookup"
		     "\n\n$Id: MultiMapping.c,v 1.5 1997/07/02 20:20:12 jim Exp $\n",
		     (PyObject*)NULL,PYTHON_API_VERSION);
  d = PyModule_GetDict(m);
  PyExtensionClass_Export(d,"MultiMapping",MMtype);
  PyDict_SetItemString(d,"__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));

  if (PyErr_Occurred()) Py_FatalError("can't initialize module MultiMapping");
}


/*****************************************************************************

  $Log: MultiMapping.c,v $
  Revision 1.5  1997/07/02 20:20:12  jim
  Added stupid parens and other changes to make 'gcc -Wall -pedantic'
  happy.

  Revision 1.4  1997/06/19 19:36:22  jim
  Added ident string.

  Revision 1.3  1997/02/17 16:34:09  jim
  Made changes to be more useful for DocumentTemplates.

  Revision 1.2  1996/10/23 18:37:45  jim
  Fixed misspelling in class name.

  Revision 1.1  1996/10/22 22:27:42  jim
  *** empty log message ***

 *****************************************************************************/
