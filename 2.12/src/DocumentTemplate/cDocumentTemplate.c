/*****************************************************************************

  Copyright (c) 2002 Zope Foundation and Contributors.
  
  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE
  
 ****************************************************************************/
static char cDocumentTemplate_module_documentation[] = 
""
"\n$Id$"
;

#include "ExtensionClass/ExtensionClass.h"

static PyObject *py_isDocTemp=0, *py_blocks=0, *py_=0, *join=0, *py_acquire;
static PyObject *py___call__, *py___roles__, *py_AUTHENTICATED_USER;
static PyObject *py_hasRole, *py__proxy_roles, *py_Unauthorized;
static PyObject *py_Unauthorized_fmt, *py_guarded_getattr;
static PyObject *py__push, *py__pop, *py_aq_base, *py_renderNS;
static PyObject *py___class__, *html_quote, *ustr, *untaint_name;

/* ----------------------------------------------------- */

static void PyVar_Assign(PyObject **v, PyObject *e) { Py_XDECREF(*v); *v=e;}
#define ASSIGN(V,E) PyVar_Assign(&(V),(E))
#define UNLESS(E) if (!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E); UNLESS(V)
#define OBJECT(O)(((PyObject*)O))

typedef struct {
  PyObject_HEAD
  PyObject *inst;
  PyObject *cache;
  PyObject *namespace;
  PyObject *guarded_getattr;
} InstanceDictobject;

staticforward PyExtensionClass InstanceDictType;

staticforward PyObject *_join_unicode(PyObject *prejoin);

static PyObject *
InstanceDict___init__(InstanceDictobject *self, PyObject *args)
{
  self->guarded_getattr=NULL;
  UNLESS(PyArg_ParseTuple(args, "OO|O",
			  &(self->inst),
			  &(self->namespace),
			  &(self->guarded_getattr)))
    return NULL;
  Py_INCREF(self->inst);
  Py_INCREF(self->namespace);
  if (self->guarded_getattr)
    Py_INCREF(self->guarded_getattr);
  else
    UNLESS(self->guarded_getattr=PyObject_GetAttr(self->namespace,
                                                  py_guarded_getattr))
       return NULL;
    
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
  Py_XDECREF(self->guarded_getattr);
  Py_DECREF(self->ob_type);
  PyObject_DEL(self);
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
  if ((r=PyObject_GetItem(self->cache, key))) return r;
  PyErr_Clear();
  
  /* Check for __str__ */
  UNLESS(name=PyString_AsString(key)) return NULL;
  if (*name=='_')
    {
      UNLESS(strcmp(name,"__str__")==0) goto KeyError;
      return PyObject_Str(self->inst);
    }
  
  if (self->guarded_getattr != Py_None) {
    r = PyObject_CallFunction(self->guarded_getattr, "OO", self->inst, key);
  }
  else {
    r = PyObject_GetAttr(self->inst, key);
  }

  if (!r) {
    PyObject *tb;

    PyErr_Fetch(&r, &v, &tb);
    if (r != PyExc_AttributeError) /* || PyObject_Compare(v,key)) */
      {
	PyErr_Restore(r,v,tb);
	return NULL;
      }
    Py_XDECREF(r);
    Py_XDECREF(v);
    Py_XDECREF(tb);

    goto KeyError;
  }
  
  if (r && PyObject_SetItem(self->cache, key, r) < 0) PyErr_Clear();
  
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
MM_push(MM *self, PyObject *args)
{
  PyObject *src;
  UNLESS(PyArg_Parse(args, "O", &src)) return NULL;
  UNLESS(-1 != PyList_Append(self->data,src)) return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
MM_pop(MM *self, PyObject *args)
{
  int i=1, l;
  PyObject *r;

  if (args) UNLESS(PyArg_Parse(args, "i", &i)) return NULL;
  if ((l=PyList_Size(self->data)) < 0) return NULL;
  i=l-i;
  UNLESS(r=PySequence_GetItem(self->data,l-1)) return NULL;
  if (PyList_SetSlice(self->data,i,l,NULL) < 0) goto err;
  return r;
err:
  Py_DECREF(r);
  return NULL;
}

static PyObject *
MM__init__(MM *self, PyObject *args)
{
  UNLESS(PyArg_Parse(args, "")) return NULL;
  UNLESS(self->data=PyList_New(0)) return NULL;
  self->dict=NULL;
  self->level=0;
  Py_INCREF(Py_None);
  return Py_None;
}

static int
safe_PyCallable_Check(PyObject *x)
{
  PyObject *klass;

  if (x == NULL)
    return 0;
  klass = PyObject_GetAttr(x, py___class__);
  if (klass) {
    PyObject *call = PyObject_GetAttr(x, py___call__);
    if (call) {
      Py_DECREF(klass);
      Py_DECREF(call);
      return 1;
    }
    else {
      PyErr_Clear();
      Py_DECREF(klass);
      if (PyClass_Check(x) || PyExtensionClass_Check(x))
        return 1;
      else
        return 0;
    }
  }
  else {
    PyErr_Clear();
    return PyCallable_Check(x);
  }
}

static int 
dtObjectIsCallable(PyObject *ob) {
  PyObject *base=0;
  int result=0;

  /* Ensure that an object is really callable by unwrapping it */
  UNLESS(base=PyObject_GetAttr(ob, py_aq_base)) {
    PyErr_Clear();
    return safe_PyCallable_Check(ob);
  }
  result=safe_PyCallable_Check(base);
  Py_DECREF(base);
  return result;
}

static int
dtObjectIsDocTemp(PyObject *ob) {
  PyObject *base=0;
  PyObject *value=0;
  int result=0;

  /* Ensure that 'isDocTemp' is not acquired */
  UNLESS(base=PyObject_GetAttr(ob, py_aq_base)) {
    PyErr_Clear();
    base = ob;
    Py_INCREF(base);
  }

  if ( (value = PyObject_GetAttr(base, py_isDocTemp)) ) {
    if (PyObject_IsTrue(value)) {
      result = 1;
    }
    Py_DECREF(value);
  }
  else PyErr_Clear();

  Py_DECREF(base);
  return result;
}


static PyObject *
MM_cget(MM *self, PyObject *key, int call)
{
  long i;
  PyObject *e, *rr;

  UNLESS(-1 != (i=PyList_Size(self->data))) return NULL;
  while (--i >= 0)
    {
      e=PyList_GET_ITEM(self->data,i);
      if (PyDict_Check(e))
        {
          e=PyDict_GetItem(e, key);
          Py_XINCREF(e);
        }
      else
        {
          UNLESS (e=PyObject_GetItem(e,key)) 
            {
              if (PyErr_Occurred() == PyExc_KeyError)
                PyErr_Clear();
              else
                return NULL;
            }
        }

      if (e)
	{
          if (!call) return e;

          /* Try calling __render_with_namespace__ */
          if ((rr = PyObject_GetAttr(e, py_renderNS))) 
            {
              Py_DECREF(e);
              UNLESS_ASSIGN(rr, PyObject_CallFunction(rr, "O", self))
                return NULL;
              return rr;
            }
          else PyErr_Clear();

	  if (dtObjectIsCallable(e))
	    {
	      /* Try calling the object */
              if (dtObjectIsDocTemp(e))
                {
                  ASSIGN(e,PyObject_CallFunction(e,"OO", Py_None, self));
                  UNLESS(e) return NULL;
                  return e;
                }

              rr=PyObject_CallObject(e,NULL);
              if (rr) ASSIGN(e,rr);
              else {
                Py_DECREF(e);
                return NULL;
              }
            }
	  return e;
	}
    }
  PyErr_SetObject(PyExc_KeyError, key);
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
  if ((key=MM_cget(self, key, 0)))
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
  {"_push", (PyCFunction) MM_push, 0,
   "_push(mapping_object) -- Add a data source"},
  {"_pop",  (PyCFunction) MM_pop,  0,
   "_pop() -- Remove and return the last data source added"}, 
  {"getitem",  (PyCFunction) MM_get,  METH_VARARGS,
   "getitem(key[,call]) -- Get a value from the MultiDict\n\n"
   "If call is true, callable objects that can be called without arguments are\n"
   "called during retrieval.\n"
   "If call is false, the object will be returns without any attempt to call it.\n"
   "If not specified, call is false by default.\n"
  }, 
  {"has_key",  (PyCFunction) MM_has_key,  METH_VARARGS,
   "has_key(key) -- Test whether the mapping has the given key"
  }, 
  {NULL,		NULL}		/* sentinel */
};

static void
MM_dealloc(MM *self)
{
  Py_XDECREF(self->data);
  Py_XDECREF(self->dict);
  Py_DECREF(self->ob_type);
  PyObject_DEL(self);
}

static PyObject *
MM_getattro(MM *self, PyObject *name)
{
  if (PyString_Check(name))
    {
      if (strcmp(PyString_AsString(name),"level")==0)
	return PyInt_FromLong(self->level);
    }
  
  if (self->dict)
    {
      PyObject *v;

      if ((v=PyDict_GetItem(self->dict, name)))
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
  if (v && PyString_Check(name))
    {
      if (strcmp(PyString_AsString(name),"level")==0)
	{
	  self->level=PyInt_AsLong(v);
	  if (PyErr_Occurred()) return -1;
	  return 0;
	}
    }

  if (! self->dict && ! (self->dict=PyDict_New())) return -1;
  
  if (v) return PyDict_SetItem(self->dict, name, v);
  else  return PyDict_DelItem(self->dict, name);
}

static int
MM_length(MM *self)
{
  long l=0, el, i;
  PyObject *e=0;

  UNLESS(-1 != (i=PyList_Size(self->data))) return -1;
  while (--i >= 0)
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

typedef struct {
  PyObject_HEAD
  PyObject *data;
} DictInstance;

static void
DictInstance_dealloc(DictInstance *self)
{
  Py_DECREF(self->data);
  PyObject_DEL(self);
}

static PyObject *
DictInstance_getattr(DictInstance *self, PyObject *name)
{
  PyObject *r;

  if ((r=PyObject_GetItem(self->data, name))) return r;
  PyErr_SetObject(PyExc_AttributeError, name);
  return NULL;
}

static PyTypeObject DictInstanceType = {
  PyObject_HEAD_INIT(NULL)
  0,				/*ob_size*/
  "DictInstance",			/*tp_name*/
  sizeof(DictInstance),		/*tp_basicsize*/
  0,				/*tp_itemsize*/
  (destructor)DictInstance_dealloc,
  (printfunc)0,
  (getattrfunc)0,
  (setattrfunc)0,
  (cmpfunc)0,
  (reprfunc)0,
  0, 0, 0,
  (hashfunc)0,
  (ternaryfunc)0,
  (reprfunc)0,
  (getattrofunc)DictInstance_getattr,
  (setattrofunc)0,
  0L,0L,
  "Wrap a mapping object to look like an instance"
};

static DictInstance *
newDictInstance(PyObject *data)
{
  DictInstance *self;
	
  UNLESS(self = PyObject_NEW(DictInstance, &DictInstanceType)) return NULL;
  self->data=data;
  Py_INCREF(data);
  return self;
}

static PyObject *
MM_call(MM *self, PyObject *args, PyObject *kw)
{
  PyObject *r, *t;
  int i, l=0;

  if (args && (l=PyTuple_Size(args)) < 0) return NULL;
  if (l)
    {
      UNLESS(r=PyObject_CallObject(OBJECT(self->ob_type), NULL)) return NULL;
      for (i=0; i < l; i++) 
	if (PyList_Append(((MM*)r)->data, PyTuple_GET_ITEM(args, i)) < 0) 
	  goto err;
      if (kw && PyList_Append(((MM*)r)->data, kw) < 0) goto err;
    }
  else
    {
      if (!kw) 
	{
	  Py_INCREF(Py_None);
	  return Py_None;
	}
      r=kw;
      Py_INCREF(r);
    }

  ASSIGN(r, OBJECT(newDictInstance(r)));
  UNLESS(t=PyTuple_New(1)) goto err;
  PyTuple_SET_ITEM(t, 0, r);
  return t;

err:
  Py_XDECREF(r);
  return NULL;
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
	(ternaryfunc)MM_call,		/*tp_call*/
	(reprfunc)0,			/*tp_str*/
	(getattrofunc)MM_getattro,	/*tp_getattro*/
	(setattrofunc)MM_setattro,	/*tp_setattro*/

	/* Space for future expansion */
	0L,0L,
	MMtype__doc__, /* Documentation string */
	METHOD_CHAIN(MM_methods)
};


/* List of methods defined in the module */

static int
if_finally(PyObject *md, int err)
{
  PyObject *t, *v, *tb;

  if (err) PyErr_Fetch(&t, &v, &tb);

  md=PyObject_GetAttr(md,py__pop);
  if (md) ASSIGN(md, PyObject_CallObject(md,NULL));
  
  if (err) PyErr_Restore(t,v,tb);
  
  if (md)
    {
      Py_DECREF(md);
      return -1;
    }
  else 
    return -2;
}

static int
render_blocks_(PyObject *blocks, PyObject *rendered,
	       PyObject *md, PyObject *mda)
{
  PyObject *block, *t, *args;
  int l, i, k=0, append;
  int skip_html_quote;

  if ((l=PyList_Size(blocks)) < 0) return -1;
  for (i=0; i < l; i++)
    {
      block=PyList_GET_ITEM(((PyListObject*)blocks), i);
      append=1;

      if (PyTuple_Check(block) 
          && PyTuple_GET_SIZE(block) > 1 
          && PyTuple_GET_ITEM(block, 0)
          && PyString_Check(PyTuple_GET_ITEM(block, 0)))
	{
          switch (PyString_AS_STRING(PyTuple_GET_ITEM(block, 0))[0])
            {
            case 'v': /* var  */
	      t=PyTuple_GET_ITEM(block,1);

	      if (t == NULL) return -1;

	      if (PyString_Check(t)) t=PyObject_GetItem(md, t);
	      else t=PyObject_CallObject(t, mda);

              if (t == NULL) return -1;

	      skip_html_quote = 0;
	      if (! ( PyString_Check(t) || PyUnicode_Check(t) ) )
	        {
		  /* This might be a TaintedString object */
		  PyObject *untaintmethod = NULL;

		  untaintmethod = PyObject_GetAttr(t, untaint_name);
		  if (untaintmethod) {
		     /* Quote it */
		     UNLESS_ASSIGN(t,
		   	    PyObject_CallObject(untaintmethod, NULL)) return -1;
		     skip_html_quote = 1;

		  } else PyErr_Clear();

		  Py_XDECREF(untaintmethod);
	        }

              if (! ( PyString_Check(t) || PyUnicode_Check(t) ) )
                {
                  args = PyTuple_New(1);
                  if(!args) return -1;
                  PyTuple_SET_ITEM(args,0,t);
                  t = PyObject_CallObject(ustr, args);
                  Py_DECREF(args);
                  args = NULL;
                  UNLESS(t) return -1;
                }

              if (skip_html_quote == 0 && PyTuple_GET_SIZE(block) == 3)
		       /* html_quote */
                {
                  if (PyString_Check(t))
                    {
                      if (strchr(PyString_AS_STRING(t), '&') ||
                          strchr(PyString_AS_STRING(t), '<') ||
                          strchr(PyString_AS_STRING(t), '>') ||
                          strchr(PyString_AS_STRING(t), '"')     )
                        {
                          /* string includes html problem characters, so
                             we cant skip the quoting process */
                          skip_html_quote = 0;
                        }
                      else
                        {
                          skip_html_quote = 1;
                        }
                    }
                  else
                    {
                      /* never skip the quoting for unicode strings */
                      skip_html_quote = 0;
                    }
                  if (!skip_html_quote)
                    {
                      ASSIGN(t, PyObject_CallFunction(html_quote, "O", t));
                      if (t == NULL) return -1;
                    }
                }
                  
              block = t;
              break;
            case 'i': /* if */
              {
                int icond, m, bs;
                PyObject *cond, *n, *cache;

                bs = PyTuple_GET_SIZE(block) - 1; /* subtract code */

                UNLESS(cache=PyDict_New()) return -1;
                cond=PyObject_GetAttr(md,py__push);
                if (cond) ASSIGN(cond, PyObject_CallFunction(cond,"O",cache));
                Py_DECREF(cache);
                if (cond) Py_DECREF(cond);
                else return -1;
	      
                append=0;
                m=bs-1;
                for (icond=0; icond < m; icond += 2)
                  {
                    cond=PyTuple_GET_ITEM(block,icond+1);
                    if (PyString_Check(cond))
                      {
                        /* We have to be careful to handle key errors here */
                        n=cond;
                        if ((cond=PyObject_GetItem(md,cond)))
                          {
                            if (PyDict_SetItem(cache, n, cond) < 0)
                              {
                                Py_DECREF(cond);
                                return if_finally(md,1);
                              }
                          }
                        else
                          {
                            PyObject *t, *v, *tb;
                            
                            PyErr_Fetch(&t, &v, &tb);
                            if (t != PyExc_KeyError || PyObject_Compare(v,n))
                              {
                                PyErr_Restore(t,v,tb);
                                return if_finally(md,1);
                              }
                            Py_XDECREF(t);
                            Py_XDECREF(v);
                            Py_XDECREF(tb);
                            cond=Py_None;
                            Py_INCREF(cond);
                          }
                      }
                    else
                      UNLESS(cond=PyObject_CallObject(cond,mda))
                        return if_finally(md,1);
                    
                    if (PyObject_IsTrue(cond))
                      {
                        Py_DECREF(cond);
                        block=PyTuple_GET_ITEM(block,icond+1+1);
                        if (block!=Py_None &&
                            render_blocks_(block, rendered, md, mda) < 0)
                          return if_finally(md,1);
                        m=-1;
                        break;
                      }
                    else Py_DECREF(cond);
                  }
		if (icond==m)
		  {
		    block=PyTuple_GET_ITEM(block,icond+1);
		    if (block!=Py_None &&
                        render_blocks_(block, rendered, md, mda) < 0)
		      return if_finally(md,1);
		  }
                
		if (if_finally(md,0) == -2) return -1;
              }
              break;
            default:
              PyErr_Format(PyExc_ValueError,
                           "Invalid DTML command code, %s",
                           PyString_AS_STRING(PyTuple_GET_ITEM(block, 0)));
              return -1;
            }
        }
      else if (PyString_Check(block) || PyUnicode_Check(block))
	{
	  Py_INCREF(block);
	}
      else
	{
	  UNLESS(block=PyObject_CallObject(block,mda)) return -1;
	}

      if (append && PyObject_IsTrue(block))
	{
	  k=PyList_Append(rendered,block);
	  Py_DECREF(block);
	  if (k < 0) return -1;
	}
    }

  return 0;
}

static PyObject *
render_blocks(PyObject *self, PyObject *args)
{
  PyObject *md, *blocks, *mda=0, *rendered=0;
  int l;

  UNLESS(PyArg_ParseTuple(args,"OO", &blocks, &md)) return NULL;
  UNLESS(rendered=PyList_New(0)) goto err;
  UNLESS(mda=Py_BuildValue("(O)",md)) goto err;
  
  if (render_blocks_(blocks, rendered, md, mda) < 0) goto err;

  Py_DECREF(mda);

  l=PyList_Size(rendered);
  if (l==0)
    {
      Py_INCREF(py_);
      ASSIGN(rendered, py_);
    }
  else if (l==1)
    ASSIGN(rendered, PySequence_GetItem(rendered,0));
  else
    ASSIGN(rendered, _join_unicode(rendered));

  return rendered;

err:
  Py_XDECREF(mda);
  Py_XDECREF(rendered);
  return NULL;
}  
  
static PyObject *
safe_callable(PyObject *self, PyObject *args)
{
  PyObject *ob;
  int res;

  UNLESS(PyArg_ParseTuple(args,"O", &ob)) return NULL;
  res = safe_PyCallable_Check(ob);
  if (res)
    return PyInt_FromLong(1);
  else
    return PyInt_FromLong(0);
}

static PyObject *
_join_unicode(PyObject *prejoin)
{
    PyObject *joined;
    joined = PyObject_CallFunction(join,"OO",prejoin,py_);
    if(!joined && PyErr_ExceptionMatches(PyExc_UnicodeError))
    {
        int i,l;
        PyObject *list;
        PyErr_Clear();
        list = PySequence_List(prejoin);
        if(!list)
        {
            return NULL;
        }
        l = PyList_Size(list);
        for(i=0;i<l;++i)
        {
            PyObject *item = PyList_GetItem(list,i);
            if(PyString_Check(item))
            {
                PyObject *unicode = PyUnicode_DecodeLatin1(PyString_AsString(item),PyString_Size(item),NULL);
                if(unicode)
                {
                    PyList_SetItem(list,i,unicode);
                }
                else
                {
                    Py_DECREF(list);
                    return NULL;
                }
           }
       }
       joined = PyObject_CallFunction(join,"OO",list,py_);
       Py_DECREF(list);
    }
    return joined;
}

static PyObject *
join_unicode(PyObject *self, PyObject *args)
{
  PyObject *ob;

  UNLESS(PyArg_ParseTuple(args,"O", &ob)) return NULL;
  return _join_unicode(ob);
}


static struct PyMethodDef Module_Level__methods[] = {
  {"render_blocks", (PyCFunction)render_blocks,	METH_VARARGS,
   ""},
  {"join_unicode", (PyCFunction)join_unicode,	METH_VARARGS,
   "join a list of plain strings into a single plain string,\n"
   "a list of unicode strings into a single unicode strings,\n"
   "or a list containing a mix into a single unicode string with\n"
   "the plain strings converted from latin-1"},
  {"safe_callable", (PyCFunction)safe_callable,	METH_VARARGS,
   "callable() with a workaround for a problem with ExtensionClasses\n"
   "and __call__()."},
  {NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

void
initcDocumentTemplate(void)
{
  PyObject *m, *d;

  DictInstanceType.ob_type=&PyType_Type;

  UNLESS (html_quote = PyImport_ImportModule("DocumentTemplate.html_quote")) return;
  ASSIGN(ustr, PyObject_GetAttrString(html_quote, "ustr"));
  UNLESS (ustr) return;
  ASSIGN(html_quote, PyObject_GetAttrString(html_quote, "html_quote"));
  UNLESS (html_quote) return;

  UNLESS(py_isDocTemp=PyString_FromString("isDocTemp")) return;
  UNLESS(py_renderNS=PyString_FromString("__render_with_namespace__")) return;
  UNLESS(py_blocks=PyString_FromString("blocks")) return;
  UNLESS(untaint_name=PyString_FromString("__untaint__")) return;
  UNLESS(py_acquire=PyString_FromString("aq_acquire")) return;
  UNLESS(py___call__=PyString_FromString("__call__")) return;
  UNLESS(py___roles__=PyString_FromString("__roles__")) return;
  UNLESS(py__proxy_roles=PyString_FromString("_proxy_roles")) return;
  UNLESS(py_hasRole=PyString_FromString("hasRole")) return;
  UNLESS(py_guarded_getattr=PyString_FromString("guarded_getattr")) return;
  UNLESS(py__push=PyString_FromString("_push")) return;
  UNLESS(py__pop=PyString_FromString("_pop")) return;
  UNLESS(py_aq_base=PyString_FromString("aq_base")) return;
  UNLESS(py_Unauthorized=PyString_FromString("Unauthorized")) return;
  UNLESS(py_Unauthorized_fmt=PyString_FromString(
	 "You are not authorized to access <em>%s</em>.")) return;
  UNLESS(py___class__=PyString_FromString("__class__")) return;

  UNLESS(py_AUTHENTICATED_USER=PyString_FromString("AUTHENTICATED_USER"))
    return;

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

}
