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


static char Record_module_documentation[] = 
""
"\n$Id: Record.c,v 1.1 1997/09/25 22:12:28 jim Exp $"
;

#ifdef PERSISTENCE
#include "cPersistence.h"
#else
#include "ExtensionClass.h"
#endif

/* ----------------------------------------------------- */

static void PyVar_Assign(PyObject **v, PyObject *e) { Py_XDECREF(*v); *v=e;}
#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)
#define OBJECT(O) ((PyObject*)(O))

static PyObject *py___record_schema__;

/* Declarations for objects of type Record */

typedef struct {
#ifdef PERSISTENCE
  cPersistent_HEAD
#else
  PyObject_HEAD
#endif
  PyObject **data;
  PyObject *schema;
} Recordobject;

staticforward PyExtensionClass RecordType;

/* ---------------------------------------------------------------- */

static int
Record_init(Recordobject *self)
{
  int l;

  UNLESS(self->schema)
    UNLESS(self->schema=PyObject_GetAttr(OBJECT(self->ob_type),
					 py___record_schema__)) return -1;
  if((l=PyObject_Length(self->schema)) < 0) return -1;
  UNLESS(self->data) 
    {
      UNLESS(self->data=malloc(sizeof(PyObject*)*l))
	{
	  PyErr_NoMemory();
	  return -1;
	}
      memset(self->data, 0, sizeof(PyObject*)*l);
    }
  
  return l;
} 

static PyObject *
Record___setstate__(Recordobject *self, PyObject *args)
{
  PyObject *state=0, **d;
  int l, ls, i;

  if((l=Record_init(self)) < 0) return NULL;

  UNLESS(PyArg_ParseTuple(args, "|O", &state)) return NULL;

  if(state)
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

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
Record___getstate__( Recordobject *self, PyObject *args)
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
Record_deal(Recordobject *self)
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

#ifdef PERSISTENCE
static PyObject *
Record__p___reinit__(Recordobject *self, PyObject *args)
{
  Record_deal(self);
  self->schema=NULL;
  self->data=NULL;
  self->state=cPersistent_GHOST_STATE;
  Py_INCREF(Py_None);
  return Py_None;
}
#endif

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
#ifdef PERSISTENCE
  {"_p___reinit__",	(PyCFunction)Record__p___reinit__,	METH_VARARGS,
   "_p___reinit__() -- Reset the record's data"
  },
#endif
  {NULL,		NULL}		/* sentinel */
};

/* ---------- */

static void
Record_dealloc(Recordobject *self)
{
  Record_deal(self);
  PyMem_DEL(self);
}

static PyObject *
Record_getattr(Recordobject *self, PyObject *name)
{
  int l, i;
  PyObject *io;

  if((l=Record_init(self)) < 0) return NULL;
  if(io=PyObject_GetItem(self->schema, name))
    {
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
	  
  return Py_FindAttr((PyObject *)self, name);
}

static int
Record_setattr(Recordobject *self, PyObject *name, PyObject *v)
{
  int l, i;
  PyObject *io;

  if((l=Record_init(self)) < 0) return -1;
  if(io=PyObject_GetItem(self->schema, name))
    {
      i=PyInt_AsLong(io);
      Py_DECREF(io);
      if(i >= 0 && i < l)
	{
	  Py_INCREF(v);
	  ASSIGN(self->data[i],v);
	  return 0;
	}
    }
  else
    PyErr_Clear();
  PyErr_SetObject(PyExc_AttributeError, name);
  return -1;
}

#ifdef PERSISTENCE
static PyObject *
pRecord_getattr(Recordobject *self, PyObject *name)
{
  char *c;
  UNLESS(c=PyString_AsString(name)) return NULL;
  return cPersistenceCAPI->pergetattro(OBJECT(self),name,c,
				       Record_getattr);
}

static int
pRecord_setattr(Recordobject *self, PyObject *name, PyObject *v)
{
  return cPersistenceCAPI->persetattro(OBJECT(self),name,v,Record_setattr);
}
#endif


static int
Record_compare(Recordobject *v, Recordobject *w)
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
	    if(c=PyObject_Compare(*dv,*dw)) return c;
	  }
	else return 1;
      else if(*dw) return -1;
    }
  if(*dv) return 1;
  if(*dw) return -1;
  return 0;
}

static PyExtensionClass RecordType = {
  PyObject_HEAD_INIT(NULL)
  0,					/*ob_size*/
  "Record",				/*tp_name*/
  sizeof(Recordobject),			/*tp_basicsize*/
  0,					/*tp_itemsize*/
  /* methods */
  (destructor)Record_dealloc,		/*tp_dealloc*/
  (printfunc)0,				/*tp_print*/
  (getattrfunc)0,			/*obsolete tp_getattr*/
  (setattrfunc)0,			/*obsolete tp_setattr*/
  (cmpfunc)Record_compare,		/*tp_compare*/
  (reprfunc)0,				/*tp_repr*/
  0,					/*tp_as_number*/
  0,					/*tp_as_sequence*/
  0,					/*tp_as_mapping*/
  (hashfunc)0,				/*tp_hash*/
  (ternaryfunc)0,			/*tp_call*/
  (reprfunc)0,				/*tp_str*/
#ifdef PERSISTENCE
  (getattrofunc)pRecord_getattr,	/*tp_getattro*/
  (setattrofunc)pRecord_setattr,	/*tp_setattro*/
#else
  (getattrofunc)Record_getattr,			/*tp_getattro*/
  (setattrofunc)Record_setattr,			/*tp_setattro*/
#endif  
  /* Space for future expansion */
  0L,0L,
  "Simple Record Types", 		/* Documentation string */
  METHOD_CHAIN(Record_methods),
  EXTENSIONCLASS_NOINSTDICT_FLAG,
};

/* End of code for Record objects */
/* -------------------------------------------------------- */


/* List of methods defined in the module */

static struct PyMethodDef Module_Level__methods[] = {
  
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/* Initialization function for the module (*must* be called initRecord) */

void
initRecord()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.1 $";

  UNLESS(py___record_schema__=PyString_FromString("__record_schema__")) return;

  UNLESS(ExtensionClassImported) return;

#ifdef PERSISTENCE
  if(cPersistenceCAPI=PyCObject_Import("cPersistence","CAPI"))
    {
      static PyMethodChain m;
      m.methods=RecordType.methods.methods;
      RecordType.methods.methods=cPersistenceCAPI->methods->methods;
      RecordType.methods.link=&m;
    }
  else return;
#endif

  /* Create the module and add the functions */
  m = Py_InitModule4("Record", Module_Level__methods,
		     Record_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);

  PyExtensionClass_Export(d,"Record",RecordType);

  PyDict_SetItemString(d, "__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));
  
	
  /* Check for errors */
  if (PyErr_Occurred()) Py_FatalError("can't initialize module Record");
}

/*****************************************************************************
Revision Log:

  $Log: Record.c,v $
  Revision 1.1  1997/09/25 22:12:28  jim
  *** empty log message ***

  Revision 1.5  1997/07/16 20:17:45  jim
  *** empty log message ***

  Revision 1.4  1997/06/06 18:31:54  jim
  Fixed bug in __getstate__ that caused core dumps when some attributes
  were unset.

  Revision 1.3  1997/05/19 14:05:46  jim
  Fixed several bugs.

  Revision 1.2  1997/04/30 11:37:35  jim
  Fixed bug in reinitialization that probably explains the bug that
  Ellen reported where ad attributes were set to None.

  Revision 1.1  1997/04/27 09:18:42  jim
  *** empty log message ***

  $Revision 1.1  1997/02/24 23:25:42  jim
  $initial
  $

*****************************************************************************/
