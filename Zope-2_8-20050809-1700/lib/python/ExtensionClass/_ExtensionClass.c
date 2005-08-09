/*

 Copyright (c) 2003 Zope Corporation and Contributors.
 All Rights Reserved.

 This software is subject to the provisions of the Zope Public License,
 Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
 THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
 WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
 FOR A PARTICULAR PURPOSE.

*/
static char _extensionclass_module_documentation[] = 
"ExtensionClass\n"
"\n"
"$Id$\n"
;

#include "ExtensionClass.h"

#define EC PyTypeObject

static PyObject *str__of__, *str__get__, *str__class_init__, *str__init__;
static PyObject *str__bases__, *str__mro__, *str__new__;

#define OBJECT(O) ((PyObject *)(O))
#define TYPE(O) ((PyTypeObject *)(O))

static PyTypeObject ExtensionClassType;
static PyTypeObject BaseType;

static PyObject *
of_get(PyObject *self, PyObject *inst, PyObject *cls)
{
  /* Descriptor slot function that calls __of__ */
  if (inst && PyExtensionInstance_Check(inst))
    return PyObject_CallMethodObjArgs(self, str__of__, inst, NULL);

  Py_INCREF(self);
  return self;
}

PyObject *
Base_getattro(PyObject *obj, PyObject *name)
{
  /* This is a modified copy of PyObject_GenericGetAttr.
     See the change note below. */

	PyTypeObject *tp = obj->ob_type;
	PyObject *descr = NULL;
	PyObject *res = NULL;
	descrgetfunc f;
	long dictoffset;
	PyObject **dictptr;

	if (!PyString_Check(name)){
#ifdef Py_USING_UNICODE
		/* The Unicode to string conversion is done here because the
		   existing tp_setattro slots expect a string object as name
		   and we wouldn't want to break those. */
		if (PyUnicode_Check(name)) {
			name = PyUnicode_AsEncodedString(name, NULL, NULL);
			if (name == NULL)
				return NULL;
		}
		else
#endif
		{
			PyErr_SetString(PyExc_TypeError,
					"attribute name must be string");
			return NULL;
		}
	}
	else
		Py_INCREF(name);

	if (tp->tp_dict == NULL) {
		if (PyType_Ready(tp) < 0)
			goto done;
	}

	/* Inline _PyType_Lookup */
	{
		int i, n;
		PyObject *mro, *base, *dict;

		/* Look in tp_dict of types in MRO */
		mro = tp->tp_mro;
		assert(mro != NULL);
		assert(PyTuple_Check(mro));
		n = PyTuple_GET_SIZE(mro);
		for (i = 0; i < n; i++) {
			base = PyTuple_GET_ITEM(mro, i);
			if (PyClass_Check(base))
				dict = ((PyClassObject *)base)->cl_dict;
			else {
				assert(PyType_Check(base));
				dict = ((PyTypeObject *)base)->tp_dict;
			}
			assert(dict && PyDict_Check(dict));
			descr = PyDict_GetItem(dict, name);
			if (descr != NULL)
				break;
		}
	}

	f = NULL;
	if (descr != NULL &&
	    PyType_HasFeature(descr->ob_type, Py_TPFLAGS_HAVE_CLASS)) {
		f = descr->ob_type->tp_descr_get;
		if (f != NULL && PyDescr_IsData(descr)) {
			res = f(descr, obj, (PyObject *)obj->ob_type);
			goto done;
		}
	}

	/* Inline _PyObject_GetDictPtr */
	dictoffset = tp->tp_dictoffset;
	if (dictoffset != 0) {
		PyObject *dict;
		if (dictoffset < 0) {
			int tsize;
			size_t size;

			tsize = ((PyVarObject *)obj)->ob_size;
			if (tsize < 0)
				tsize = -tsize;
			size = _PyObject_VAR_SIZE(tp, tsize);

			dictoffset += (long)size;
			assert(dictoffset > 0);
			assert(dictoffset % SIZEOF_VOID_P == 0);
		}
		dictptr = (PyObject **) ((char *)obj + dictoffset);
		dict = *dictptr;
		if (dict != NULL) {
			res = PyDict_GetItem(dict, name);
			if (res != NULL) {

                          /* CHANGED!
                             If the tp_descr_get of res is of_get, 
                             then call it. */

                          if (PyObject_TypeCheck(res->ob_type,
                                                 &ExtensionClassType)
                              && res->ob_type->tp_descr_get != NULL)
                            res = res->ob_type->tp_descr_get(
                                                 res, obj, 
                                                 OBJECT(obj->ob_type));
                          else
                            Py_INCREF(res);
                          goto done;
			}
		}
	}

	if (f != NULL) {
		res = f(descr, obj, (PyObject *)obj->ob_type);
		goto done;
	}

	if (descr != NULL) {
		Py_INCREF(descr);
		res = descr;
		goto done;
	}

        /* CHANGED: Just use the name. Don't format. */
        PyErr_SetObject(PyExc_AttributeError, name);
  done:
	Py_DECREF(name);
	return res;
}

#include "pickle/pickle.c"

static struct PyMethodDef Base_methods[] = {
  PICKLE_METHODS
  {NULL,	 (PyCFunction)NULL, 0, NULL}		/* sentinel */
  };


static EC BaseType = {
	PyObject_HEAD_INIT(NULL)
	/* ob_size           */ 0,
	/* tp_name           */ "ExtensionClass."
                                "Base",
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
        /* tp_getattro       */ (getattrofunc)Base_getattro,
        0, 0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	"Standard ExtensionClass base type",
        0, 0, 0, 0, 0, 0, 
        Base_methods,
};

static EC NoInstanceDictionaryBaseType = {
	PyObject_HEAD_INIT(NULL)
	/* ob_size           */ 0,
	/* tp_name           */ "ExtensionClass."
                                "NoInstanceDictionaryBase",
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	"Base types for subclasses without instance dictionaries",
};

static PyObject *
EC_new(PyTypeObject *self, PyObject *args, PyObject *kw)
{
  PyObject *name, *bases=NULL, *dict=NULL;
  PyObject *new_bases=NULL, *new_args, *result;
  int have_base = 0, i;

  if (kw && PyObject_IsTrue(kw))
    {
      PyErr_SetString(PyExc_TypeError, 
                      "Keyword arguments are not supported");
        return NULL;
    }

  if (!PyArg_ParseTuple(args, "O|O!O!", &name,
                        &PyTuple_Type, &bases, &PyDict_Type, &dict))
    return NULL;

  /* Make sure Base is in bases */
  if (bases)
    {
      for (i = 0; i < PyTuple_GET_SIZE(bases); i++)
        {
          if (PyObject_TypeCheck(PyTuple_GET_ITEM(bases, i), 
                                 &ExtensionClassType))
            {
              have_base = 1;
              break;
            }
        }
      if (! have_base)
        {
          new_bases = PyTuple_New(PyTuple_GET_SIZE(bases) + 1);
          if (new_bases == NULL)
            return NULL;
          for (i = 0; i < PyTuple_GET_SIZE(bases); i++)
            {
              Py_XINCREF(PyTuple_GET_ITEM(bases, i));
              PyTuple_SET_ITEM(new_bases, i, PyTuple_GET_ITEM(bases, i));
            }
          Py_INCREF(OBJECT(&BaseType));
          PyTuple_SET_ITEM(new_bases, PyTuple_GET_SIZE(bases), 
                           OBJECT(&BaseType));
        }
    }
  else
    {
      new_bases = Py_BuildValue("(O)", &BaseType);
      if (new_bases == NULL)
        return NULL;
    }

  

  if (new_bases)
    {
      if (dict)
        new_args = Py_BuildValue("OOO", name, new_bases, dict);
      else
        new_args = Py_BuildValue("OO", name, new_bases);

      Py_DECREF(new_bases);

      if (new_args == NULL)
        return NULL;

      result = PyType_Type.tp_new(self, new_args, kw);
      Py_DECREF(new_args);
    }
  else
    {
      result = PyType_Type.tp_new(self, args, kw);

      /* We didn't have to add Base, so maybe NoInstanceDictionaryBase
         is in the bases. We need to check if it was. If it was, we
         need to suppress instance dictionary support. */
      for (i = 0; i < PyTuple_GET_SIZE(bases); i++)
        {
          if (
              PyObject_TypeCheck(PyTuple_GET_ITEM(bases, i), 
                                 &ExtensionClassType)
              &&
              PyType_IsSubtype(TYPE(PyTuple_GET_ITEM(bases, i)), 
                               &NoInstanceDictionaryBaseType)
              )
            {
              TYPE(result)->tp_dictoffset = 0;
              break;
            }
        }

    }

  return result;
}

/* set up __get__, if necessary */
static int
EC_init_of(PyTypeObject *self)
{
  PyObject *__of__;

  __of__ = PyObject_GetAttr(OBJECT(self), str__of__);
  if (__of__)
    {
      Py_DECREF(__of__);
      if (self->tp_descr_get)
        {
          if (self->tp_descr_get != of_get)
            {
              PyErr_SetString(PyExc_TypeError,
                              "Can't mix __of__ and descriptors");
              return -1;
            }
        }
      else
        self->tp_descr_get = of_get;
    }
  else
    {
      PyErr_Clear();
      if (self->tp_descr_get == of_get)
        self->tp_descr_get = NULL;
    }

  return 0;
}

static int
EC_init(PyTypeObject *self, PyObject *args, PyObject *kw)
{
  PyObject *__class_init__, *r;

  if (PyType_Type.tp_init(OBJECT(self), args, kw) < 0) 
    return -1; 

  if (self->tp_dict != NULL)
    {
      r = PyDict_GetItemString(self->tp_dict, "__doc__");
      if ((r == Py_None) && 
          (PyDict_DelItemString(self->tp_dict, "__doc__") < 0)
          )
        return -1;
    }

  if (EC_init_of(self) < 0)
    return -1;

  /* Call __class_init__ */
  __class_init__ = PyObject_GetAttr(OBJECT(self), str__class_init__);
  if (__class_init__ == NULL)
    {
      PyErr_Clear();
      return 0;
    }

  if (! (PyMethod_Check(__class_init__) 
         && PyMethod_GET_FUNCTION(__class_init__)
         )
      )
    {
      Py_DECREF(__class_init__);
      PyErr_SetString(PyExc_TypeError, "Invalid type for __class_init__");
      return -1;
    }

  r = PyObject_CallFunctionObjArgs(PyMethod_GET_FUNCTION(__class_init__),
                                   OBJECT(self), NULL);
  Py_DECREF(__class_init__);
  if (! r)
    return -1;
  Py_DECREF(r);
  
  return 0;
}

static int
EC_setattro(PyTypeObject *type, PyObject *name, PyObject *value)
{
  /* We want to allow setting attributes of builti-in types, because
     EC did in the past and there's code that relies on it.

     We can't really set slots though, but I don't think we need to.
     There's no good way to spot slots.  We could use a lame rule like
     names that begin and end with __s and have just 4 _s smell too
     much like slots.


  */
  if (! (type->tp_flags & Py_TPFLAGS_HEAPTYPE)) 
    {
      char *cname;
      int l;

      cname = PyString_AsString(name);
      if (cname == NULL)
        return -1;
      l = PyString_GET_SIZE(name);
      if (l > 4 
          && cname[0] == '_' && cname[1] == '_'
          && cname[l-1] == '_' && cname[l-2] == '_'
          )
        {
          char *c;
          
          c = strchr(cname+2, '_');
          if (c != NULL && (c - cname) >= (l-2))
            {
              PyErr_Format
                (PyExc_TypeError,
                 "can't set attributes of built-in/extension type '%s' if the "
                 "attribute name begins and ends with __ and contains only "
                 "4 _ characters",
                 type->tp_name
                 );
              return -1;
            }
        }
      
      return PyObject_GenericSetAttr(OBJECT(type), name, value);
    }
  return PyType_Type.tp_setattro(OBJECT(type), name, value);
}


static PyObject *
inheritedAttribute(PyTypeObject *self, PyObject *name)
{
  int i;
  PyObject *d, *cls;

  for (i = 1; i < PyTuple_GET_SIZE(self->tp_mro); i++)
    {
      cls = PyTuple_GET_ITEM(self->tp_mro, i);
      if (PyType_Check(cls))
        d = ((PyTypeObject *)cls)->tp_dict;
      else if (PyClass_Check(cls))
        d = ((PyClassObject *)cls)->cl_dict;
      else
        /* Unrecognized thing, punt */
        d = NULL;
      
      if ((d == NULL) || (PyDict_GetItem(d, name) == NULL))
        continue;
                    
      return PyObject_GetAttr(cls, name);
    }

  PyErr_SetObject(PyExc_AttributeError, name);
  return NULL;
}

static PyObject *
__basicnew__(PyObject *self)
{
  return PyObject_CallMethodObjArgs(self, str__new__, self, NULL);
}

static int
append_new(PyObject *result, PyObject *v)
{
  int contains;

  if (v == OBJECT(&BaseType) || v == OBJECT(&PyBaseObject_Type))
    return 0;                   /* Don't add these until end */
  contains = PySequence_Contains(result, v);
  if (contains != 0)
    return contains;
  return PyList_Append(result, v);
}

static int
copy_mro(PyObject *mro, PyObject *result)
{
  PyObject *base;
  int i, l;

  l = PyTuple_Size(mro);
  if (l < 0) 
    return -1;

  for (i=0; i < l; i++)
    {
      base = PyTuple_GET_ITEM(mro, i);
      if (append_new(result, base) < 0)
        return -1;
    }
  return 0;
}

static int 
copy_classic(PyObject *base, PyObject *result)
{
  PyObject *bases, *basebase;
  int i, l, err=-1;

  if (append_new(result, base) < 0)
    return -1;

  bases = PyObject_GetAttr(base, str__bases__);
  if (bases == NULL)
    return -1;

  l = PyTuple_Size(bases);
  if (l < 0) 
    goto end;

  for (i=0; i < l; i++)
    {
      basebase = PyTuple_GET_ITEM(bases, i);
      if (copy_classic(basebase, result) < 0)
        goto end;
    }

  err = 0;
 
 end:
  Py_DECREF(bases);
  return err;
}

static PyObject *
mro(PyTypeObject *self)
{
  /* Compute an MRO for a class */
  PyObject *result, *base, *basemro, *mro=NULL;
  int i, l, err;

  result = PyList_New(0);
  if (result == NULL)
    return NULL;
  if (PyList_Append(result, OBJECT(self)) < 0)
    goto end;
  l = PyTuple_Size(self->tp_bases);
  if (l < 0) 
    goto end;
  for (i=0; i < l; i++)
    {
      base = PyTuple_GET_ITEM(self->tp_bases, i);
      if (base == NULL)
        continue;
      basemro = PyObject_GetAttr(base, str__mro__);
      if (basemro != NULL)
        {
          /* Type */
          err = copy_mro(basemro, result);
          Py_DECREF(basemro);
          if (err < 0)
            goto end;
        }
      else
        {
          PyErr_Clear();
          if (copy_classic(base, result) < 0)
            goto end;
        }
    }

  if (self != &BaseType && PyList_Append(result, OBJECT(&BaseType)) < 0)
    goto end;

  if (PyList_Append(result, OBJECT(&PyBaseObject_Type)) < 0)
    goto end;

  l = PyList_GET_SIZE(result);
  mro = PyTuple_New(l);
  if (mro == NULL)
    goto end;

  for (i=0; i < l; i++)
    {
      Py_INCREF(PyList_GET_ITEM(result, i));
      PyTuple_SET_ITEM(mro, i, PyList_GET_ITEM(result, i));
    }
 
 end:
  Py_DECREF(result);
  return mro;
}

static struct PyMethodDef EC_methods[] = {
  {"__basicnew__", (PyCFunction)__basicnew__, METH_NOARGS, 
   "Create a new empty object"},
  {"inheritedAttribute", (PyCFunction)inheritedAttribute, METH_O, 
   "Look up an inherited attribute"},
  {"mro", (PyCFunction)mro, METH_NOARGS, 
   "Compute an mro using the 'encalsulated base' scheme"},
  {NULL,	 (PyCFunction)NULL, 0, NULL}		/* sentinel */
  };


static PyTypeObject ExtensionClassType = {
	PyObject_HEAD_INIT(NULL)
	/* ob_size           */ 0,
	/* tp_name           */ "ExtensionClass."
                                "ExtensionClass",
	/* tp_basicsize      */ 0,
	/* tp_itemsize       */ 0,
	/* tp_dealloc        */ (destructor)0,
	/* tp_print          */ (printfunc)0,
	/* tp_getattr        */ (getattrfunc)0,
	/* tp_setattr        */ (setattrfunc)0,
	/* tp_compare        */ (cmpfunc)0,
	/* tp_repr           */ (reprfunc)0,
	/* tp_as_number      */ 0,
	/* tp_as_sequence    */ 0,
	/* tp_as_mapping     */ 0,
	/* tp_hash           */ (hashfunc)0,
	/* tp_call           */ (ternaryfunc)0,
	/* tp_str            */ (reprfunc)0,
        /* tp_getattro       */ (getattrofunc)0,
        /* tp_setattro       */ (setattrofunc)EC_setattro,
        /* tp_as_buffer      */ 0,
        /* tp_flags          */ Py_TPFLAGS_DEFAULT
                                | Py_TPFLAGS_HAVE_GC
                                | Py_TPFLAGS_BASETYPE
                                ,
	/* tp_doc            */ "Meta-class for extension classes",
        /* tp_traverse       */ (traverseproc)0,
        /* tp_clear          */ (inquiry)0,
        /* tp_richcompare    */ (richcmpfunc)0,
        /* tp_weaklistoffset */ (long)0,
        /* tp_iter           */ (getiterfunc)0,
        /* tp_iternext       */ (iternextfunc)0,
        /* tp_methods        */ EC_methods,
        /* tp_members        */ 0,
        /* tp_getset         */ 0,
        /* tp_base           */ 0,
        /* tp_dict           */ 0, /* internal use */
        /* tp_descr_get      */ (descrgetfunc)0,
        /* tp_descr_set      */ (descrsetfunc)0,
        /* tp_dictoffset     */ 0,
        /* tp_init           */ (initproc)EC_init,
        /* tp_alloc          */ (allocfunc)0,
        /* tp_new            */ (newfunc)EC_new,
	/* tp_free           */ 0, /* Low-level free-mem routine */
	/* tp_is_gc          */ (inquiry)0, /* For PyObject_IS_GC */
};

static PyObject *
debug(PyObject *self, PyObject *o)
{
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
pmc_init_of(PyObject *self, PyObject *args)
{
  PyObject *o;

  if (! PyArg_ParseTuple(args, "O!", (PyObject *)&ExtensionClassType, &o))
    return NULL;

  if (EC_init_of((PyTypeObject *)o) < 0)
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}


/* List of methods defined in the module */

static struct PyMethodDef ec_methods[] = {
  {"debug", (PyCFunction)debug, METH_O, ""},
  {"pmc_init_of", (PyCFunction)pmc_init_of, METH_VARARGS, 
   "Initialize __get__ for classes that define __of__"},
  {NULL,	 (PyCFunction)NULL, 0, NULL}		/* sentinel */
  };


static PyObject *
EC_findiattrs_(PyObject *self, char *cname)
{
  PyObject *name, *r;
  
  name = PyString_FromString(cname);
  if (name == NULL)
    return NULL;
  r = ECBaseType->tp_getattro(self, name);
  Py_DECREF(name);
  return r;
}

static PyObject *
ec_new_for_custom_dealloc(PyTypeObject *type, PyObject *args, PyObject *kw)
{
  /* This is for EC's that have deallocs.  For these, we need to
     incref the type when we create an instance, because the deallocs
     will decref the type.
  */

  PyObject *r;

  r = PyType_GenericNew(type, args, kw);
  if (r)
    {
      Py_INCREF(type);
    }
  return r;
}

static int
ec_init(PyObject *self, PyObject *args, PyObject *kw)
{
  PyObject *r, *__init__;

  __init__ = PyObject_GetAttr(self, str__init__);
  if (__init__ == NULL)
    return -1;
    
  r = PyObject_Call(__init__, args, kw);
  Py_DECREF(__init__);
  if (r == NULL)
    return -1;

  Py_DECREF(r);
  return 0;
}

static int
PyExtensionClass_Export_(PyObject *dict, char *name, PyTypeObject *typ)
{
  int ecflags = 0;
  PyMethodDef *pure_methods = NULL, *mdef = NULL;
  PyObject *m;

  if (typ->tp_flags == 0) 
    { 
      /* Old-style EC */

      if (typ->tp_traverse) 
        { 
          /* ExtensionClasses stick there methods in the tp_traverse slot */
          mdef = (PyMethodDef *)typ->tp_traverse;

          if (typ->tp_basicsize <= sizeof(_emptyobject))
            /* Pure mixin. We want rebindable methods */
            pure_methods = mdef;
          else
            typ->tp_methods = mdef;

          typ->tp_traverse = NULL; 

          /* Look for __init__ method  */
          for (; mdef->ml_name; mdef++)
            {
              if (strcmp(mdef->ml_name, "__init__") == 0)
                {
                  /* we have an old-style __init__, install a special slot */
                  typ->tp_init = ec_init;
                  break;
                }
            }
        } 

      if (typ->tp_clear)
        {
          /* ExtensionClasses stick there flags in the tp_clear slot */
          ecflags = (int)(typ->tp_clear);

          /* Some old-style flags were set */

          if ((ecflags & EXTENSIONCLASS_BINDABLE_FLAG)
              && typ->tp_descr_get == NULL)
            /* We have __of__-style binding */
            typ->tp_descr_get = of_get; 
        }
      typ->tp_clear = NULL; 
      typ->tp_flags = Py_TPFLAGS_DEFAULT 
                    | Py_TPFLAGS_BASETYPE;

      if (typ->tp_dealloc != NULL)
          typ->tp_new = ec_new_for_custom_dealloc;
    }

  typ->ob_type = ECExtensionClassType; 

  if (ecflags & EXTENSIONCLASS_NOINSTDICT_FLAG)
    typ->tp_base = &NoInstanceDictionaryBaseType;
  else
    typ->tp_base = &BaseType;

  if (typ->tp_new == NULL)
    typ->tp_new = PyType_GenericNew; 

  if (PyType_Ready(typ) < 0) 
    return -1; 

  if (pure_methods)
    {
      /* We had pure methods. We want to be able to rebind these, so
         we'll make them ordinary method wrappers around method descrs
      */
      for (; pure_methods->ml_name; pure_methods++)
        {
          m = PyDescr_NewMethod(ECBaseType, pure_methods);
          if (! m)
            return -1;
          m = PyMethod_New((PyObject *)m, NULL, (PyObject *)ECBaseType);
          if (! m)
            return -1;
          if (PyDict_SetItemString(typ->tp_dict, pure_methods->ml_name, m) 
              < 0)
            return -1;
        }      
    }
  else if (mdef && mdef->ml_name)
    {
      /* Blast, we have to stick __init__ in the dict ourselves
         because PyType_Ready probably stuck a wrapper for ec_init in
         instead.
      */
      m = PyDescr_NewMethod(typ, mdef);
      if (! m)
        return -1;
      if (PyDict_SetItemString(typ->tp_dict, mdef->ml_name, m) < 0)
        return -1;
    }

  if (PyMapping_SetItemString(dict, name, (PyObject*)typ) < 0)  
    return -1; 

  return 0;
}

PyObject *
PyECMethod_New_(PyObject *callable, PyObject *inst)
{
  if (! PyExtensionInstance_Check(inst))
    {
      PyErr_SetString(PyExc_TypeError, 
                      "Can't bind non-ExtensionClass instance.");
      return NULL;
    }

  if (PyMethod_Check(callable))
    {
      if (callable->ob_refcnt == 1)
        {
          Py_XDECREF(((PyMethodObject*)callable)->im_self);
          Py_INCREF(inst);
          ((PyMethodObject*)callable)->im_self = inst;
          Py_INCREF(callable);
          return callable;
        }
      else
        return callable->ob_type->tp_descr_get(
                   callable, inst, 
                   ((PyMethodObject*)callable)->im_class);
    }
  else
    return PyMethod_New(callable, inst, (PyObject*)(ECBaseType));
}

static struct ExtensionClassCAPIstruct
TrueExtensionClassCAPI = {
  EC_findiattrs_,
  PyExtensionClass_Export_,
  PyECMethod_New_,
  &BaseType,
  &ExtensionClassType,
};

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
init_ExtensionClass(void)
{
  PyObject *m, *s;

  if (pickle_setup() < 0)
    return;

#define DEFINE_STRING(S) \
  if(! (str ## S = PyString_FromString(# S))) return

  DEFINE_STRING(__of__);
  DEFINE_STRING(__get__);
  DEFINE_STRING(__class_init__);
  DEFINE_STRING(__init__);
  DEFINE_STRING(__bases__);
  DEFINE_STRING(__mro__);
  DEFINE_STRING(__new__);
#undef DEFINE_STRING

  PyExtensionClassCAPI = &TrueExtensionClassCAPI;

  ExtensionClassType.ob_type = &PyType_Type;
  ExtensionClassType.tp_base = &PyType_Type;
  ExtensionClassType.tp_traverse = PyType_Type.tp_traverse;
  ExtensionClassType.tp_clear = PyType_Type.tp_clear;
  
  /* Initialize types: */
  if (PyType_Ready(&ExtensionClassType) < 0)
    return;
    
  BaseType.ob_type = &ExtensionClassType;
  BaseType.tp_base = &PyBaseObject_Type;
  BaseType.tp_new = PyType_GenericNew;
  
  if (PyType_Ready(&BaseType) < 0)
    return;
    
  NoInstanceDictionaryBaseType.ob_type = &ExtensionClassType;
  NoInstanceDictionaryBaseType.tp_base = &BaseType;
  NoInstanceDictionaryBaseType.tp_new = PyType_GenericNew;
  
  if (PyType_Ready(&NoInstanceDictionaryBaseType) < 0)
    return;
  
  /* Create the module and add the functions */
  m = Py_InitModule3("_ExtensionClass", ec_methods,
                     _extensionclass_module_documentation);

  if (m == NULL)
    return;

  s = PyCObject_FromVoidPtr(PyExtensionClassCAPI, NULL);
  if (PyModule_AddObject(m, "CAPI2", s) < 0)
    return;
        
  /* Add types: */
  if (PyModule_AddObject(m, "ExtensionClass", 
                         (PyObject *)&ExtensionClassType) < 0)
    return;
  if (PyModule_AddObject(m, "Base", (PyObject *)&BaseType) < 0)
    return;
  if (PyModule_AddObject(m, "NoInstanceDictionaryBase", 
                         (PyObject *)&NoInstanceDictionaryBaseType) < 0)
    return;
}

