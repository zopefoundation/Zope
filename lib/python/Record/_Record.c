/*****************************************************************************

  Copyright (c) 1996-2002 Zope Foundation and Contributors.
  All Rights Reserved.

  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE

 ****************************************************************************/

static char Record_module_documentation[] = 
""
"\n$Id: _Record.c,v 1.2 2003/11/28 16:46:36 jim Exp $"
;

#include "ExtensionClass/ExtensionClass.h"

/* ----------------------------------------------------- */

static void PyVar_Assign(PyObject **v, PyObject *e) { Py_XDECREF(*v); *v=e;}
#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)
#define OBJECT(O) ((PyObject*)(O))

static PyObject *py___record_schema__;

/* Declarations for objects of type Record */

typedef struct {
  PyObject_HEAD
  PyObject **data;
  PyObject *schema;
} Record;

staticforward PyExtensionClass RecordType;

/* ---------------------------------------------------------------- */

static int
Record_init(Record *self)
{
  int l;

  UNLESS(self->schema)
    UNLESS(self->schema=PyObject_GetAttr(OBJECT(self->ob_type),
					 py___record_schema__)) return -1;
  if((l=PyObject_Length(self->schema)) < 0) return -1;
  UNLESS(self->data) 
    {
      UNLESS(self->data=malloc(sizeof(PyObject*)*(l+1)))
	{
	  PyErr_NoMemory();
	  return -1;
	}
      memset(self->data, 0, sizeof(PyObject*)*(l+1));
    }
  
  return l;
} 

static PyObject *
Record___setstate__(Record *self, PyObject *args)
{
  PyObject *state=0, *parent, **d;
  int l, ls, i;

  if((l=Record_init(self)) < 0) return NULL;

  UNLESS(PyArg_ParseTuple(args, "|OO", &state, &parent)) return NULL;

  if(state) {
    if(PyDict_Check(state))
      {
	PyObject *k, *v;
	
	for(i=0; PyDict_Next(state, &i, &k, &v);)
	  if(k && v && PyObject_SetAttr(OBJECT(self),k,v) < 0)
	    PyErr_Clear();
      }
    else
      {
	if((ls=PyObject_Length(state)) < 0) return NULL;
	
	for(i=0, d=self->data; i < l && i < ls; i++, d++)
	  {
	    ASSIGN(*d, PySequence_GetItem(state, i));
	    UNLESS(*d) return NULL;
	  }
      }
  }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
Record___getstate__( Record *self, PyObject *args)
{
  PyObject *r, **d, *v;
  int i, l;

  UNLESS(self->data) return PyTuple_New(0);

  if((l=Record_init(self)) < 0) return NULL;
  UNLESS(r=PyTuple_New(l)) return NULL;
  for(d=self->data, i=0; i < l; i++, d++)
    {
      v= *d;
      if(!v) v=Py_None;
      Py_INCREF(v);
      PyTuple_SET_ITEM(r,i,v);
    }
  return r;
}

static void
Record_deal(Record *self)
{
  int l;
  PyObject **d;

  if(self->schema)
    {
      l=PyObject_Length(self->schema);
      for(d=self->data; --l >= 0; d++)
	{
	  Py_XDECREF(*d);
	}
      Py_DECREF(self->schema);
      free(self->data);
    }
}

static struct PyMethodDef Record_methods[] = {
  {"__getstate__",	(PyCFunction)Record___getstate__,	METH_VARARGS,
   "__getstate__() -- Get the record's data"
  },
  {"__setstate__",	(PyCFunction)Record___setstate__,	METH_VARARGS,
   "__setstate__(v) -- Set the record's data"
  },
  {"__init__",	(PyCFunction)Record___setstate__,	METH_VARARGS,
   "__init__([v]) -- Initialize a record, possibly with state"
  },
  {NULL,		NULL}		/* sentinel */
};

/* ---------- */

static void
Record_dealloc(Record *self)
{
  Record_deal(self);
  Py_DECREF(self->ob_type);
  PyObject_DEL(self);
}

static PyObject *
Record_getattr(Record *self, PyObject *name)
{
  int l, i;
  PyObject *io;

  if((l=Record_init(self)) < 0) return NULL;

  if ((io=Py_FindAttr((PyObject *)self, name))) return io;

  PyErr_Clear();

  if((io=PyObject_GetItem(self->schema, name)))
    {
      UNLESS(PyInt_Check(io))
	{
	  PyErr_SetString(PyExc_TypeError, "invalid record schema");
	  return NULL;
	}
      i=PyInt_AsLong(io);
      if(i >= 0 && i < l)
	{
	  ASSIGN(io, self->data[i]);
	  UNLESS(io) io=Py_None;
	}
      else ASSIGN(io, Py_None);
      Py_INCREF(io);
      return io;
    }

  PyErr_SetObject(PyExc_AttributeError, name);  
  
  return NULL;
}

static int
Record_setattr(Record *self, PyObject *name, PyObject *v)
{
  int l, i;
  PyObject *io;

  if((l=Record_init(self)) < 0) return -1;
  if((io=PyObject_GetItem(self->schema, name)))
    {
      UNLESS(PyInt_Check(io))
	{
	  PyErr_SetString(PyExc_TypeError, "invalid record schema");
	  return -1;
	}
      i=PyInt_AsLong(io);
      Py_DECREF(io);
      if(i >= 0 && i < l)
	{
	  Py_XINCREF(v);
	  ASSIGN(self->data[i],v);
	  return 0;
	}
    }

  PyErr_SetObject(PyExc_AttributeError, name);
  return -1;
}

static int
Record_compare(Record *v, Record *w)
{
  int lv, lw, i, c;
  PyObject **dv, **dw;

  if((lv=Record_init(v)) < 0) return -1;
  if((lw=Record_init(w)) < 0) return -1;
  if(lw < lv) lv=lw;

  for(i=0, dv=v->data, dw=w->data; i < lv; i++, dv++, dw++)
    {
      if(*dv)
	if(*dw)
	  {
	    if((c=PyObject_Compare(*dv,*dw))) return c;
	  }
	else return 1;
      else if(*dw) return -1;
    }
  if(*dv) return 1;
  if(*dw) return -1;
  return 0;
}

/* Code to handle accessing Record objects as sequence objects */

static PyObject * 
Record_concat(Record *self, PyObject *bb)
{
  PyErr_SetString(PyExc_TypeError,
		  "Record objects do not support concatenation");
  return NULL;
}

static PyObject *
Record_repeat(Record *self, int n)
{
  PyErr_SetString(PyExc_TypeError,
		  "Record objects do not support repetition");
  return NULL;
}

static PyObject *
IndexError(int i)
{
  PyObject *v;

  if((v=PyInt_FromLong(i)))
    {
      PyErr_SetObject(PyExc_IndexError, v);
      Py_DECREF(v);
    }

  return NULL;
}

static PyObject *
Record_item(Record *self, int i)
{
  PyObject *o;
  int l;

  if((l=Record_init(self)) < 0) return NULL;
  if(i < 0 || i >= l) return IndexError(i);

  o=self->data[i];
  UNLESS(o) o=Py_None;

  Py_INCREF(o);
  return o;
}

static PyObject *
Record_slice(Record *self, int ilow, int ihigh)
{
  PyErr_SetString(PyExc_TypeError,
		  "Record objects do not support slicing");
  return NULL;
}

static int
Record_ass_item(Record *self, int i, PyObject *v)
{
  int l;

  if((l=Record_init(self)) < 0) return -1;
  if(i < 0 || i >= l)
    {
      IndexError(i);
      return -1;
    }

  UNLESS(v)
    {
      PyErr_SetString(PyExc_TypeError,"cannot delete record items");
      return -1;
    }

  Py_INCREF(v);
  ASSIGN(self->data[i], v);
  return 0;
}

static int
Record_ass_slice(Record *self, int ilow, int ihigh, PyObject *v)
{
  PyErr_SetString(PyExc_TypeError,
		  "Record objects do not support slice assignment");
  return -1;
}

static PySequenceMethods Record_as_sequence = {
  (inquiry)Record_init,			/*sq_length*/
  (binaryfunc)Record_concat,		/*sq_concat*/
  (intargfunc)Record_repeat,		/*sq_repeat*/
  (intargfunc)Record_item,		/*sq_item*/
  (intintargfunc)Record_slice,		/*sq_slice*/
  (intobjargproc)Record_ass_item,	/*sq_ass_item*/
  (intintobjargproc)Record_ass_slice,	/*sq_ass_slice*/
};

/* -------------------------------------------------------------- */

static PyObject *
Record_subscript(Record *self, PyObject *key)
{
  int i, l;
  PyObject *io;

  if((l=Record_init(self)) < 0) return NULL;

  if(PyInt_Check(key))
    {
      i=PyInt_AsLong(key);
      if(i<0) i+=l;
      return Record_item(self, i);
    }

  if((io=PyObject_GetItem(self->schema, key)))
    {
      UNLESS(PyInt_Check(io))
	{
	  PyErr_SetString(PyExc_TypeError, "invalid record schema");
	  return NULL;
	}
      i=PyInt_AsLong(io);
      if(i >= 0 && i < l)
	{
	  ASSIGN(io, self->data[i]);
	  UNLESS(io) io=Py_None;
	}
      else ASSIGN(io, Py_None);
      Py_INCREF(io);
      return io;
    }

  PyErr_Clear();
  if ((io=PyObject_GetAttr(OBJECT(self), key))) return io;

  PyErr_SetObject(PyExc_KeyError, key);					   
  return NULL;
}

static int
Record_ass_sub(Record *self, PyObject *key, PyObject *v)
{
  int i, l;
  PyObject *io;

  if((l=Record_init(self)) < 0) return -1;

  if(PyInt_Check(key))
    {
      i=PyInt_AsLong(key);
      if(i<0) i+=l;
      return Record_ass_item(self, i, v);
    }

  if((io=PyObject_GetItem(self->schema, key)))
    {
      UNLESS(PyInt_Check(io))
	{
	  PyErr_SetString(PyExc_TypeError, "invalid record schema");
	  return -1;
	}
      i=PyInt_AsLong(io);
      Py_DECREF(io);
      if(i >= 0 && i < l)
	{
	  Py_XINCREF(v);
	  ASSIGN(self->data[i],v);
	  return 0;
	}
    }

  return -1;
}

static PyMappingMethods Record_as_mapping = {
  (inquiry)Record_init,		/*mp_length*/
  (binaryfunc)Record_subscript,		/*mp_subscript*/
  (objobjargproc)Record_ass_sub,	/*mp_ass_subscript*/
};

/* -------------------------------------------------------- */

static PyExtensionClass RecordType = {
  PyObject_HEAD_INIT(NULL)
  0,					/*ob_size*/
  "Record",				/*tp_name*/
  sizeof(Record),			/*tp_basicsize*/
  0,					/*tp_itemsize*/
  /* methods */
  (destructor)Record_dealloc,		/*tp_dealloc*/
  (printfunc)0,				/*tp_print*/
  (getattrfunc)0,			/*obsolete tp_getattr*/
  (setattrfunc)0,			/*obsolete tp_setattr*/
  (cmpfunc)Record_compare,		/*tp_compare*/
  (reprfunc)0,				/*tp_repr*/
  0,					/*tp_as_number*/
  &Record_as_sequence,					/*tp_as_sequence*/
  &Record_as_mapping,					/*tp_as_mapping*/
  (hashfunc)0,				/*tp_hash*/
  (ternaryfunc)0,			/*tp_call*/
  (reprfunc)0,				/*tp_str*/
  (getattrofunc)Record_getattr,			/*tp_getattro*/
  (setattrofunc)Record_setattr,			/*tp_setattro*/
  /* Space for future expansion */
  0L,0L,
  "Simple Record Types", 		/* Documentation string */
  METHOD_CHAIN(Record_methods),
  (void*)(EXTENSIONCLASS_NOINSTDICT_FLAG),
};

/* End of code for Record objects */
/* -------------------------------------------------------- */


/* List of methods defined in the module */

static struct PyMethodDef Module_Level__methods[] = {
  
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/* Initialization function for the module (*must* be called initRecord) */

void
init_Record(void)
{
  PyObject *m, *d;

  UNLESS(py___record_schema__=PyString_FromString("__record_schema__")) return;

  UNLESS(ExtensionClassImported) return;

  /* Create the module and add the functions */
  m = Py_InitModule4("_Record", Module_Level__methods,
		     Record_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);

  PyExtensionClass_Export(d,"Record",RecordType);
}
