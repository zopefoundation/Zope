/*****************************************************************************
  
  Zope Public License (ZPL) Version 1.0
  -------------------------------------
  
  Copyright (c) Digital Creations.  All rights reserved.
  
  This license has been certified as Open Source(tm).
  
  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are
  met:
  
  1. Redistributions in source code must retain the above copyright
     notice, this list of conditions, and the following disclaimer.
  
  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions, and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.
  
  3. Digital Creations requests that attribution be given to Zope
     in any manner possible. Zope includes a "Powered by Zope"
     button that is installed by default. While it is not a license
     violation to remove this button, it is requested that the
     attribution remain. A significant investment has been put
     into Zope, and this effort will continue if the Zope community
     continues to grow. This is one way to assure that growth.
  
  4. All advertising materials and documentation mentioning
     features derived from or use of this software must display
     the following acknowledgement:
  
       "This product includes software developed by Digital Creations
       for use in the Z Object Publishing Environment
       (http://www.zope.org/)."
  
     In the event that the product being advertised includes an
     intact Zope distribution (with copyright and license included)
     then this clause is waived.
  
  5. Names associated with Zope or Digital Creations must not be used to
     endorse or promote products derived from this software without
     prior written permission from Digital Creations.
  
  6. Modified redistributions of any form whatsoever must retain
     the following acknowledgment:
  
       "This product includes software developed by Digital Creations
       for use in the Z Object Publishing Environment
       (http://www.zope.org/)."
  
     Intact (re-)distributions of any official Zope release do not
     require an external acknowledgement.
  
  7. Modifications are encouraged but must be packaged separately as
     patches to official Zope releases.  Distributions that do not
     clearly separate the patches from the original work must be clearly
     labeled as unofficial distributions.  Modifications which do not
     carry the name Zope may be packaged in any form, as long as they
     conform to all of the clauses above.
  
  
  Disclaimer
  
    THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
    EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
    PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
    USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
    ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
    OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
    SUCH DAMAGE.
  
  
  This software consists of contributions made by Digital Creations and
  many individuals on behalf of Digital Creations.  Specific
  attributions are listed in the accompanying credits file.
  
 ****************************************************************************/
static char Record_module_documentation[] = 
""
"\n$Id: Record.c,v 1.8 1999/06/10 20:11:53 jim Exp $"
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
Record___setstate__(Record *self, PyObject *args)
{
  PyObject *state=0, *parent, **d;
  int l, ls, i;

  if((l=Record_init(self)) < 0) return NULL;

  UNLESS(PyArg_ParseTuple(args, "|OO", &state, &parent)) return NULL;

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

#ifdef PERSISTENCE
static PyObject *
Record__p_deactivate(Record *self, PyObject *args)
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
  {"_p_deactivate",	(PyCFunction)Record__p_deactivate,	METH_VARARGS,
   "_p_deactivate() -- Reset the record's data"
  },
#endif
  {NULL,		NULL}		/* sentinel */
};

/* ---------- */

static void
Record_dealloc(Record *self)
{
  Record_deal(self);
  Py_DECREF(self->ob_type);
  PyMem_DEL(self);
}

static PyObject *
Record_getattr(Record *self, PyObject *name)
{
  int l, i;
  PyObject *io;

  if((l=Record_init(self)) < 0) return NULL;

  if(io=Py_FindAttr((PyObject *)self, name)) return io;

  PyErr_Clear();

  if(io=PyObject_GetItem(self->schema, name))
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
  if(io=PyObject_GetItem(self->schema, name))
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

#ifdef PERSISTENCE
static PyObject *
pRecord_getattr(Record *self, PyObject *name)
{
  char *c;
  UNLESS(c=PyString_AsString(name)) return NULL;
  return cPersistenceCAPI->pergetattro(OBJECT(self),name,c,
				       Record_getattr);
}

static int
pRecord_setattr(Record *self, PyObject *name, PyObject *v)
{
  return cPersistenceCAPI->persetattro(OBJECT(self),name,v,Record_setattr);
}
#endif


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
	    if(c=PyObject_Compare(*dv,*dw)) return c;
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

  if(io=PyObject_GetItem(self->schema, key))
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
  if (io=PyObject_GetAttr(OBJECT(self), key)) return io;

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

  if(io=PyObject_GetItem(self->schema, key))
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
  char *rev="$Revision: 1.8 $";

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
  Revision 1.8  1999/06/10 20:11:53  jim
  Updated to use new ExtensionClass destructor protocol.

  Revision 1.7  1999/04/16 15:21:40  jim
  Added logic to fall back to getattr when getitem fails.
  This is needed to make computed attributes work in ZTables,
  but it might be better to expand the schema notion to accomidate
  computed attributes.

  Revision 1.6  1999/03/10 00:14:41  klm
  Committing with version 1.0 of the license.

  Revision 1.5  1998/12/04 20:15:24  jim
  Detabification and new copyright.

  Revision 1.4  1998/07/27 13:09:58  jim
  Changed _p___reinit__ to _p_deactivate.

  Revision 1.3  1998/01/16 21:13:28  jim
  Added extra ignored parent object argument to __init__ and
  __setstate__.

  Revision 1.2  1997/09/26 15:05:17  jim
  Added sequence and mapping behavior.

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
