/***********************************************************
     Copyright 

       Copyright 1997 Digital Creations, L.L.C., 910 Princess Anne
       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
       rights reserved. 

******************************************************************/


static char cDocumentTemplate_module_documentation[] = 
""
"\n$Id: cDocumentTemplate.c,v 1.6 1997/11/07 17:09:40 jim Exp $"
;

#include "ExtensionClass.h"

static PyObject *py_isDocTemp=0, *py_blocks=0, *py_=0, *join=0, *py_acquire;
static PyObject *py___call__;

/* ----------------------------------------------------- */

static void PyVar_Assign(PyObject **v, PyObject *e) { Py_XDECREF(*v); *v=e;}
#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)

typedef struct {
  PyObject_HEAD
  PyObject *inst;
  PyObject *cache;
  PyObject *namespace;
  PyObject *validate;
} InstanceDictobject;

staticforward PyExtensionClass InstanceDictType;

static PyObject *
InstanceDict___init__( InstanceDictobject *self, PyObject *args)
{
  UNLESS(PyArg_ParseTuple(args, "OOO",
			  &(self->inst),
			  &(self->namespace),
			  &(self->validate)))
    return NULL;
  Py_INCREF(self->inst);
  Py_INCREF(self->namespace);
  Py_INCREF(self->validate);
  UNLESS(self->cache=PyDict_New()) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static struct PyMethodDef InstanceDict_methods[] = {
  {"__init__",	(PyCFunction)InstanceDict___init__, 1,
   ""},
  
  {NULL,		NULL}		/* sentinel */
};

/* ---------- */

static void
InstanceDict_dealloc(InstanceDictobject *self)
{
  Py_XDECREF(self->inst);
  Py_XDECREF(self->cache);
  Py_XDECREF(self->namespace);
  Py_XDECREF(self->validate);
  PyMem_DEL(self);
}

static PyObject *
InstanceDict_getattr(InstanceDictobject *self, PyObject *name)
{
  return Py_FindAttr((PyObject *)self, name);
}

static PyObject *
InstanceDict_repr(InstanceDictobject *self)
{
  return PyObject_Repr(self->inst);
}

/* Code to access InstanceDict objects as mappings */

static int
InstanceDict_length( InstanceDictobject *self)
{
  return 1;
}

static PyObject *
InstanceDict_subscript( InstanceDictobject *self, PyObject *key)
{
  PyObject *r, *v;
  char *name;
  
  /* Try to get value from the cache */
  if(r=PyObject_GetItem(self->cache, key)) return r;
  PyErr_Clear();
  
  /* Check for __str__ */
  UNLESS(name=PyString_AsString(key)) return NULL;
  if(*name=='_')
    {
      UNLESS(strcmp(name,"__str__")==0) goto KeyError;
      return PyObject_Str(self->inst);
    }
  
  /* Do explicit acquisition with "roles" rule */
  if(r=PyObject_GetAttr(self->inst, py_acquire))
    {
      if(self->validate != Py_None)
	{
	  UNLESS_ASSIGN(r,PyObject_CallFunction(
		 r, "OOO", key, self->validate, self->namespace))
	    goto KeyError;
	}
      else
	UNLESS(r=PyObject_GetAttr(self->inst, key)) goto KeyError;
    }  
  else
    {
      /* OK, use getattr */
      UNLESS(r=PyObject_GetAttr(self->inst, key)) goto KeyError;

      if(self->validate != Py_None)
	{
	  UNLESS(v=PyObject_CallFunction(
	    self->validate,"OOOO",
	    self->inst, self->inst, key, r, self->namespace))
	    return NULL;
	  Py_DECREF(v);
	}
    }
  
  if(r && PyObject_SetItem(self->cache, key, r) < 0) PyErr_Clear();
  
  return r;
  
KeyError:
  PyErr_SetObject(PyExc_KeyError, key);
  return NULL;
}

static int
InstanceDict_ass_sub( InstanceDictobject *self, PyObject *v, PyObject *w)
{
  PyErr_SetString(PyExc_TypeError,
		  "InstanceDict objects do not support item assignment");
  return -1;
}

static PyMappingMethods InstanceDict_as_mapping = {
  (inquiry)InstanceDict_length,		/*mp_length*/
  (binaryfunc)InstanceDict_subscript,		/*mp_subscript*/
  (objobjargproc)InstanceDict_ass_sub,	/*mp_ass_subscript*/
};

/* -------------------------------------------------------- */


static char InstanceDicttype__doc__[] = 
""
;

static PyExtensionClass InstanceDictType = {
  PyObject_HEAD_INIT(NULL)
  0,				/*ob_size*/
  "InstanceDict",			/*tp_name*/
  sizeof(InstanceDictobject),	/*tp_basicsize*/
  0,				/*tp_itemsize*/
  /* methods */
  (destructor)InstanceDict_dealloc,	/*tp_dealloc*/
  (printfunc)0,	/*tp_print*/
  (getattrfunc)0,		/*obsolete tp_getattr*/
  (setattrfunc)0,		/*obsolete tp_setattr*/
  (cmpfunc)0,	/*tp_compare*/
  (reprfunc)InstanceDict_repr,		/*tp_repr*/
  0,		/*tp_as_number*/
  0,		/*tp_as_sequence*/
  &InstanceDict_as_mapping,		/*tp_as_mapping*/
  (hashfunc)0,		/*tp_hash*/
  (ternaryfunc)0,	/*tp_call*/
  (reprfunc)0,		/*tp_str*/
  (getattrofunc)InstanceDict_getattr,			/*tp_getattro*/
  0,			/*tp_setattro*/
  
  /* Space for future expansion */
  0L,0L,
  InstanceDicttype__doc__, /* Documentation string */
  METHOD_CHAIN(InstanceDict_methods)
};

typedef struct {
  PyObject_HEAD
  int level;
  PyObject *dict;
  PyObject *data;
} MM;

staticforward PyExtensionClass MMtype;

static PyObject *
MM_push(self, args)
	MM *self;
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
	MM *self;
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
     MM *self;
     PyObject *args;
{
  UNLESS(PyArg_Parse(args, "")) return NULL;
  UNLESS(self->data=PyList_New(0)) return NULL;
  self->dict=NULL;
  self->level=0;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
MM_cget(MM *self, PyObject *key, int call)
{
  long i;
  int dt=0;
  PyObject *e, *t, *rr, *tb;

  UNLESS(-1 != (i=PyList_Size(self->data))) return NULL;
  while(--i >= 0)
    {
      e=PyList_GetItem(self->data,i);
      if(e=PyObject_GetItem(e,key))
	{
	  dt=0;

	  if(PyCallable_Check(e))
	    {
	      /* Decide whether we have a document template */
	      if(rr=PyObject_GetAttr(e,py_isDocTemp))
		{
		  if(PyObject_IsTrue(rr)) dt=1;
		  Py_DECREF(rr);
		}
	      else PyErr_Clear();

	      /* Try calling the object */
	      if(call)
		{
		  if(dt)
		    {
		      ASSIGN(e,PyObject_CallFunction(e,"OO", Py_None, self));
		      UNLESS(e) return NULL;
		    }
		  else
		    {
		      rr=PyObject_CallObject(e,NULL);
		      if(rr) ASSIGN(e,rr);
		      else
			{
			  PyErr_Fetch(&t, &rr, &tb);
			  if(t!=PyExc_AttributeError ||
			     PyObject_Compare(rr,py___call__) != 0)
			    {
			      PyErr_Restore(t,rr,tb);
			      Py_DECREF(e);
			      return NULL;
			    }

		      if((rr=PyObject_CallObject(e,NULL))) ASSIGN(e,rr);
			}
		    }
		}
	    }

	  return e;
	}
      PyErr_Fetch(&e, &rr, &tb);
      if(dt || e != PyExc_KeyError)
	{
	  PyErr_Restore(e,rr,tb);
	  return NULL;
	}
      Py_XDECREF(e);
      Py_XDECREF(rr);
      Py_XDECREF(tb);
    }
  PyErr_SetObject(PyExc_KeyError,key);
  return NULL;
}

static PyObject *
MM_get(MM *self, PyObject *args)
{
  PyObject *key, *call=Py_None;

  UNLESS(PyArg_ParseTuple(args,"O|O",&key,&call)) return NULL;
  return MM_cget(self, key, PyObject_IsTrue(call));
}

static PyObject *
MM_has_key(MM *self, PyObject *args)
{
  PyObject *key;

  UNLESS(PyArg_ParseTuple(args,"O",&key)) return NULL;
  if((key=MM_cget(self, key, 0)))
    {
      Py_DECREF(key);
      return PyInt_FromLong(1);
    }
  PyErr_Clear();
  return PyInt_FromLong(0);
}

static struct PyMethodDef MM_methods[] = {
  {"__init__", (PyCFunction)MM__init__, 0,
   "__init__() -- Create a new empty multi-mapping"},
  {"push", (PyCFunction) MM_push, 0,
   "push(mapping_object) -- Add a data source"},
  {"pop",  (PyCFunction) MM_pop,  0,
   "pop() -- Remove and return the last data source added"}, 
  {"getitem",  (PyCFunction) MM_get,  METH_VARARGS,
   "getitem(key[,call]) -- Get a value\n\n"
   "Normally, callable objects that can be called without arguments are\n"
   "called during retrieval. This can be suppressed by providing a\n"
   "second argument that is false.\n"
  }, 
  {"has_key",  (PyCFunction) MM_has_key,  METH_VARARGS,
   "has_key(key) -- Test whether the mapping has the given key"
  }, 
  {NULL,		NULL}		/* sentinel */
};

static void
MM_dealloc(self)
     MM *self;
{
  Py_XDECREF(self->data);
  Py_XDECREF(self->dict);
  PyMem_DEL(self);
}

static PyObject *
MM_getattro(MM *self, PyObject *name)
{
  if(PyString_Check(name))
    {
      if(strcmp(PyString_AsString(name),"level")==0)
	return PyInt_FromLong(self->level);
    }
  
  if(self->dict)
    {
      PyObject *v;

      if(v=PyDict_GetItem(self->dict, name))
	{
	  Py_INCREF(v);
	  return v;
	}
    }
  
  return Py_FindAttr((PyObject *)self, name);
}

static int
MM_setattro(MM *self, PyObject *name, PyObject *v)
{
  if(v && PyString_Check(name))
    {
      if(strcmp(PyString_AsString(name),"level")==0)
	{
	  self->level=PyInt_AsLong(v);
	  if(PyErr_Occurred()) return -1;
	  return 0;
	}
    }

  if(! self->dict && ! (self->dict=PyDict_New())) return -1;
  
  if(v) return PyDict_SetItem(self->dict, name, v);
  else  return PyDict_DelItem(self->dict, name);
}

static int
MM_length(self)
	MM *self;
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
MM_subscript(MM *self, PyObject *key)
{
  return MM_cget(self, key, 1);
}

static PyMappingMethods MM_as_mapping = {
	(inquiry)MM_length,		/*mp_length*/
	(binaryfunc)MM_subscript,      	/*mp_subscript*/
	(objobjargproc)NULL,		/*mp_ass_subscript*/
};

/* -------------------------------------------------------- */

static char MMtype__doc__[] = 
"TemplateDict -- Combine multiple mapping objects for lookup"
;

static PyExtensionClass MMtype = {
	PyObject_HEAD_INIT(NULL)
	0,				/*ob_size*/
	"TemplateDict",			/*tp_name*/
	sizeof(MM),			/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)MM_dealloc,		/*tp_dealloc*/
	(printfunc)0,			/*tp_print*/
	(getattrfunc)0,			/*tp_getattr*/
	(setattrfunc)0,			/*tp_setattr*/
	(cmpfunc)0,			/*tp_compare*/
	(reprfunc)0,			/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	&MM_as_mapping,			/*tp_as_mapping*/
	(hashfunc)0,			/*tp_hash*/
	(ternaryfunc)0,			/*tp_call*/
	(reprfunc)0,			/*tp_str*/
	(getattrofunc)MM_getattro,	/*tp_getattro*/
	(setattrofunc)MM_setattro,	/*tp_setattro*/

	/* Space for future expansion */
	0L,0L,
	MMtype__doc__, /* Documentation string */
	METHOD_CHAIN(MM_methods)
};

static struct PyMethodDef TemplateDict_methods[] = {
  {NULL,		NULL}		/* sentinel */
};



/* List of methods defined in the module */

static PyObject *
render_blocks(PyObject *self, PyObject *args)
{
  PyObject *md, *blocks, *rendered, *block;
  int l, i, k;

  UNLESS(PyArg_ParseTuple(args,"OO", &self, &md)) return NULL;
  UNLESS(md=Py_BuildValue("(O)",md)) return NULL;
  UNLESS(rendered=PyList_New(0)) goto err;
  UNLESS(blocks=PyObject_GetAttr(self,py_blocks)) goto err;
  if((l=PyList_Size(blocks)) < 0) goto err;
  for(i=0; i < l; i++)
    {
      block=PyList_GET_ITEM(((PyListObject*)blocks), i);
      if(PyString_Check(block))
	{
	  if(PyList_Append(rendered,block) < 0) goto err;
	}
      else
	{
	  UNLESS(block=PyObject_CallObject(block,md)) goto err;
	  k=PyList_Append(rendered,block);
	  Py_DECREF(block);
	  if(k < 0) goto err;
	}
    }
  Py_DECREF(md);
  Py_DECREF(blocks);
  ASSIGN(rendered,PyObject_CallFunction(join,"OO",rendered,py_));
  return rendered;

err:
  Py_DECREF(md);
  Py_XDECREF(rendered);
  Py_XDECREF(blocks);
  return NULL;
}

static struct PyMethodDef Module_Level__methods[] = {
  {"render_blocks", (PyCFunction)render_blocks,	METH_VARARGS,
   ""},
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/* Initialization function for the module (*must* be called initcDocumentTemplate) */

void
initcDocumentTemplate()
{
  PyObject *m, *d;
  char *rev="$Revision: 1.6 $";

  UNLESS(py_isDocTemp=PyString_FromString("isDocTemp")) return;
  UNLESS(py_blocks=PyString_FromString("blocks")) return;
  UNLESS(py_acquire=PyString_FromString("aq_acquire")) return;
  UNLESS(py___call__=PyString_FromString("__call__")) return;
  UNLESS(py_=PyString_FromString("")) return;
  UNLESS(join=PyImport_ImportModule("string")) return;
  ASSIGN(join,PyObject_GetAttrString(join,"join"));
  UNLESS(join) return;
  UNLESS(ExtensionClassImported) return;

  m = Py_InitModule4("cDocumentTemplate", Module_Level__methods,
		     cDocumentTemplate_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

  d = PyModule_GetDict(m);

  PyExtensionClass_Export(d,"InstanceDict",InstanceDictType);
  PyExtensionClass_Export(d,"TemplateDict",MMtype);

  PyDict_SetItemString(d, "__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));
  
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module cDocumentTemplate");
}

/*****************************************************************************
Revision Log:

  $Log: cDocumentTemplate.c,v $
  Revision 1.6  1997/11/07 17:09:40  jim
  Changed so exception is raised if a callable object raises an
  exception when called and the exception type and value are not
  AttributeError and '__call__'.

  Revision 1.5  1997/10/29 16:58:53  jim
  Changed name of get to getitem.

  Revision 1.4  1997/10/28 21:57:31  jim
  Changed to use aq_acquire.

  Revision 1.3  1997/10/28 21:52:58  jim
  Fixed bug in get.
  Added latest validation rules.

  Revision 1.2  1997/10/27 17:43:28  jim
  Added some new experimental validation machinery.
  This is, still a work in progress.

  Added level attribute used in preventing excessive recursion.

  Added get method.

  Revision 1.1  1997/08/27 18:55:47  jim
  initial

  Revision 1.4  1997/08/07 12:26:52  jim
  - InstanceDicts no longer try to evaluate results.  This is defered to
    the TemplateDict.
  - Fixed bug in the way TemplateDicts were evaluating
    document templates.
  - TemplateDicts now use PyCallable_Check before trying to call
    returned values.  This should speed common cases.

  Revision 1.3  1997/08/05 21:56:20  jim
  Changed the way InstanceDicts call template attributes to avoid
  problem with instance attributes overriding kw arguments.

  Revision 1.2  1997/04/11 19:53:36  jim
  Forgot NULL return on error in render_blocks.

  Revision 1.1  1997/04/09 22:24:23  jim
  *** empty log message ***

  $Revision 1.1  1997/02/24 23:25:42  jim
  $initial
  $

*****************************************************************************/
