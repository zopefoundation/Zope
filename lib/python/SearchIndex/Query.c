#include "Python.h"

#define UNLESS(E) if(!(E))
#define ASSIGN(V,E) { PyObject *__e; __e = (E); Py_XDECREF(V); (V) = __e; }
#define UNLESS_ASSIGN(V,E) ASSIGN(V, E) if (!(V))

static PyTypeObject *RegexType;
static PyObject *string_lower;

#define Regex_Check(ob) (ob->ob_type == RegexType)

typedef struct
{
    PyObject_HEAD
    PyObject *key;
    PyObject *tests;
} FieldTestobject;

staticforward PyTypeObject AttrTesttype, CompAttrTesttype, MethodTesttype;
staticforward PyTypeObject ItemTesttype;

typedef struct
{
    PyObject_HEAD
    PyObject *tests;
} Testobject;

staticforward PyTypeObject Andtype, Ortype, Cmptype, Regextype, Stringtype;

typedef struct
{
    PyObject_HEAD
    PyObject *low;
    PyObject *high;
} Rangeobject;

staticforward PyTypeObject Rangetype;

FieldTestobject *
new_FieldTestobject(PyObject *key, PyObject *tests, PyTypeObject *type)
{
    FieldTestobject *self;

    if (!(self = PyObject_NEW(FieldTestobject, type)))
        return NULL;

    Py_INCREF(self->key = key);
    Py_INCREF(self->tests = tests);
  
    return self;
}

static void
FieldTest_dealloc(FieldTestobject *self)
{
    Py_XDECREF(self->key);
    Py_XDECREF(self->tests);
    PyMem_DEL(self);
}

Testobject *
new_Testobject(PyObject *tests, PyTypeObject *type)
{
    Testobject *self;

    if (!(self = PyObject_NEW(Testobject, type)))
        return NULL;

    Py_INCREF(self->tests = tests);
  
    return self;
}

static void
Test_dealloc(Testobject *self)
{
    Py_XDECREF(self->tests);
    PyMem_DEL(self);
}

Rangeobject *
new_Rangeobject(PyObject *low, PyObject *high)
{
    Rangeobject *self;

    if (!(self = PyObject_NEW(Rangeobject, &Rangetype)))
        return NULL;

    Py_INCREF(self->high = high);
    Py_INCREF(self->low = low);
  
    return self;
}

static void
Range_dealloc(Rangeobject *self)
{
    Py_XDECREF(self->high);
    Py_XDECREF(self->low);
    PyMem_DEL(self);
}

static PyObject *
Query__call__(PyObject *self, PyObject *args, PyObject *kw)
{
  PyObject *arg;

  if (!(PyArg_ParseTuple(args, "O", &arg)))
    return NULL;

  return PyObject_GetItem(self, arg);
}

static PyObject *
AttrTest__getitem__(FieldTestobject *self, PyObject *key)
{
    PyObject *ob;

    UNLESS(ob=PyObject_GetAttr(key, self->key)) return NULL;
    ASSIGN(ob, PyObject_GetItem(self->tests, ob));
    return ob;
}

static PyObject *
CompAttrTest__getitem__(FieldTestobject *self, PyObject *key)
{
    PyObject *ob;

    UNLESS(ob=PyObject_GetAttr(key, self->key)) return NULL;
    UNLESS_ASSIGN(ob, PyObject_CallObject(ob, NULL)) return NULL;
    ASSIGN(ob, PyObject_GetItem(self->tests, ob));
    return ob;
}

static PyObject *
MethodTest__getitem__(FieldTestobject *self, PyObject *key)
{
    PyObject *ob;

    UNLESS(ob=PyObject_GetAttr(key, self->key)) return NULL;
    ASSIGN(ob,PyObject_CallObject(ob, self->tests));
    return ob;
}

static PyObject *
meaningless_len(PyObject *self)
{
  return PyInt_FromLong(1);	/* Use one so we are considered "true" */
}

static PyMappingMethods AttrTest_as_mapping = {
    (inquiry)meaningless_len,         /*mp_length*/
    (binaryfunc)AttrTest__getitem__,  /*mp_subscript*/
    (objobjargproc)0,                 /*mp_ass_subscript*/
};

static PyMappingMethods CompAttrTest_as_mapping = {
    (inquiry)meaningless_len,         /*mp_length*/
    (binaryfunc)CompAttrTest__getitem__,  /*mp_subscript*/
    (objobjargproc)0,                 /*mp_ass_subscript*/
};

static PyMappingMethods MethodTest_as_mapping = {
    (inquiry)meaningless_len,         /*mp_length*/
    (binaryfunc)MethodTest__getitem__,  /*mp_subscript*/
    (objobjargproc)0,                 /*mp_ass_subscript*/
};

static PyObject *
AttrTest(PyObject *self, PyObject *args)
{
    PyObject *key, *test;

    if (!PyArg_ParseTuple(args, "OO", &key, &test))
        return NULL;

    return (PyObject *)new_FieldTestobject(key, test, &AttrTesttype);
}

static PyObject *
CompAttrTest(PyObject *self, PyObject *args)
{
    PyObject *key, *test;

    if (!PyArg_ParseTuple(args, "OO", &key, &test))
        return NULL;

    return (PyObject *)new_FieldTestobject(key, test, &CompAttrTesttype);
}

static PyObject *
MethodTest(PyObject *self, PyObject *args)
{
    PyObject *key, *test;

    if (!PyArg_ParseTuple(args, "OO", &key, &test))
        return NULL;

    UNLESS(PyTuple_Check(test))
      {
	PyErr_SetString(PyExc_TypeError,
			"second argument to MethodTest must be an "
			"argument tuple");
	return NULL;
      }

    self=(PyObject *)new_FieldTestobject(key, test, &MethodTesttype);
    return self;
}

static PyTypeObject AttrTesttype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "AttrTest",		/*tp_name*/
    sizeof(FieldTestobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)FieldTest_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &AttrTest_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    "Test objects that apply sub-tests to attribute values",
};

static PyTypeObject CompAttrTesttype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "CompAttrTest",		/*tp_name*/
    sizeof(FieldTestobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)FieldTest_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &CompAttrTest_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    "Test objects that apply sub-tests to computed attribute values",
};

static PyTypeObject MethodTesttype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "MethodTest",		/*tp_name*/
    sizeof(FieldTestobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)FieldTest_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &MethodTest_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    "Test objects that call test methods",
};

static PyObject *
ItemTest__getitem__(FieldTestobject *self, PyObject *key)
{
    PyObject *ob;

    UNLESS(ob=PyObject_GetItem(key, self->key)) return NULL;

    UNLESS_ASSIGN(ob, PyObject_GetItem(self->tests, ob)) return NULL;

    return ob;
}

static PyMappingMethods ItemTest_as_mapping = {
    (inquiry)meaningless_len,         /*mp_length*/
    (binaryfunc)ItemTest__getitem__,  /*mp_subscript*/
    (objobjargproc)0,                 /*mp_ass_subscript*/
};

static PyObject *
ItemTest(PyObject *self, PyObject *args)
{
    PyObject *key, *test;

    if (!PyArg_ParseTuple(args, "OO", &key, &test)) return NULL;

    return (PyObject *)new_FieldTestobject(key, test, &ItemTesttype);
}

static char ItemTesttype__doc__[] = "";

static PyTypeObject ItemTesttype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "ItemTest",		/*tp_name*/
    sizeof(FieldTestobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)FieldTest_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &ItemTest_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    ItemTesttype__doc__ /* Documentation string */
};

static PyObject *
FieldTest(PyObject *self, PyObject *args)
{
    PyObject *key, *test;

    if (!PyArg_ParseTuple(args, "OO", &key, &test))
        return NULL;

    return (PyObject *)new_FieldTestobject(key, test, 
        (PyString_Check(key) ? &AttrTesttype : &ItemTesttype));
}

static PyObject *
And__getitem__(Testobject *self, PyObject *key)
{
    int len, i;
    PyObject *val=0;

    if ((len = PySequence_Length(self->tests)) < 0)
        return NULL;

    for (i = 0; i < len; i++)
    {
        UNLESS_ASSIGN(val,PySequence_GetItem(self->tests, i)) return NULL;

        UNLESS_ASSIGN(val, PyObject_GetItem(val, key)) return NULL;

        if (!PyObject_IsTrue(val)) return val; /* No need to convert to 0 */
    }

    if(val) return val;
    else    return PyInt_FromLong(1);
}

static PyMappingMethods And_as_mapping = {
    (inquiry)meaningless_len,    /* mp_length        */
    (binaryfunc)And__getitem__,  /* mp_subscript     */
    (objobjargproc)0,            /* mp_ass_subscript */
};

static PyObject *
And(PyObject *self, PyObject *args)
{
    return (PyObject *)new_Testobject(args, &Andtype);
}

static char Andtype__doc__[] = "";

static PyTypeObject Andtype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "And",		/*tp_name*/
    sizeof(Testobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)Test_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &And_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Andtype__doc__ /* Documentation string */
};

static PyObject *
Or__getitem__(Testobject *self, PyObject *key)
{
    int len, i;
    PyObject *val=0;

    if ((len = PySequence_Length(self->tests)) < 0)
        return NULL;

    for (i = 0; i < len; i++)
    {
        UNLESS_ASSIGN(val, PySequence_GetItem(self->tests, i)) return NULL;

        UNLESS_ASSIGN(val, PyObject_GetItem(val, key)) return NULL;

        if (PyObject_IsTrue(val)) return val;
    }

    if(val) return val;
    else    return PyInt_FromLong(0);
}

static PyMappingMethods Or_as_mapping = {
    (inquiry)meaningless_len,   /*mp_length*/
    (binaryfunc)Or__getitem__,  /*mp_subscript*/
    (objobjargproc)0,           /*mp_ass_subscript*/
};

static PyObject *
Or(PyObject *self, PyObject *args)
{
    return (PyObject *)new_Testobject(args, &Ortype);
}

static char Ortype__doc__[] = "";

static PyTypeObject Ortype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "Or",		/*tp_name*/
    sizeof(Testobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)Test_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &Or_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Ortype__doc__ /* Documentation string */
};

static PyObject *
Range__getitem__(Rangeobject *self, PyObject *key)
{
    if ((self->low ==Py_None || PyObject_Compare(key, self->low)  >= 0) &&
        (self->high==Py_None || PyObject_Compare(key, self->high) <= 0))
    {
        return PyInt_FromLong(1);
    }

    return PyInt_FromLong(0);
}

static PyMappingMethods Range_as_mapping = {
    (inquiry)meaningless_len,      /*mp_length*/
    (binaryfunc)Range__getitem__,  /*mp_subscript*/
    (objobjargproc)0,              /*mp_ass_subscript*/
};

static PyObject *
Range(PyObject *self, PyObject *args)
{
    PyObject *high, *low;

    if (!PyArg_ParseTuple(args, "OO", &low, &high))
        return NULL;

    return (PyObject *)new_Rangeobject(low, high);
}

static char Rangetype__doc__[] = "";

static PyTypeObject Rangetype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "Or",		/*tp_name*/
    sizeof(Rangeobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)Range_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &Range_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Rangetype__doc__ /* Documentation string */
};

static PyObject *
Cmp__getitem__(Testobject *self, PyObject *key)
{
    if (PyObject_Compare(self->tests, key) == 0)
    {    
        return PyInt_FromLong(1);
    }

    return PyInt_FromLong(0);
}

static PyMappingMethods Cmp_as_mapping = {
    (inquiry)meaningless_len,    /*mp_length*/
    (binaryfunc)Cmp__getitem__,  /*mp_subscript*/
    (objobjargproc)0,            /*mp_ass_subscript*/
};

static PyObject *
Cmp(PyObject *self, PyObject *args)
{
    return (PyObject *)new_Testobject(args, &Cmptype);
}

static char Cmptype__doc__[] = "";

static PyTypeObject Cmptype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "Cmp",		/*tp_name*/
    sizeof(Testobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)Test_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &Cmp_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Cmptype__doc__ /* Documentation string */
};

static PyObject *
Regex__getitem__(Testobject *self, PyObject *key)
{
    PyObject *t, *search_res, *ret = NULL;

    if (!(t = PyTuple_New(1)))
        return NULL;

    PyTuple_SET_ITEM(t, 0, key);
    Py_INCREF(key);

    if (!(search_res = PyObject_CallObject(self->tests, t)))
        goto finally;

    if (!PyInt_Check(search_res))
    {
        PyErr_SetString(PyExc_TypeError, "search method of regular "
            "expression must return an integer");
        goto finally;
    }

    if (PyInt_AS_LONG((PyIntObject *)search_res) >= 0)
    {    
        ret = PyInt_FromLong(1);
        goto finally;
    }

    ret = PyInt_FromLong(0);

finally:
    Py_XDECREF(t);
    Py_XDECREF(search_res);

    return ret;
}

static PyMappingMethods Regex_as_mapping = {
    (inquiry)meaningless_len,      /*mp_length*/
    (binaryfunc)Regex__getitem__,  /*mp_subscript*/
    (objobjargproc)0,              /*mp_ass_subscript*/
};

static PyObject *
Regex(PyObject *self, PyObject *args)
{
    PyObject *search, *r;

    static PyObject *search_str = 0;

    if (!search_str)
        if (!(search_str = PyString_FromString("search")))
            return NULL;

    if (!Regex_Check(args))
    {
        PyErr_SetString(PyExc_TypeError, "argument must be compiled regular"
            " expression");
        return NULL;
    }

    if (!(search = PyObject_GetAttr(args, search_str)))
        return NULL;

    r = (PyObject *)new_Testobject(search, &Regextype);

    Py_DECREF(search);

    return r;
}

static char Regextype__doc__[] = "";

static PyTypeObject Regextype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "RegexMatch",		/*tp_name*/
    sizeof(Testobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)Test_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &Regex_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Regextype__doc__ /* Documentation string */
};

static PyObject *
String__getitem__(Testobject *self, PyObject *key)
{
    char *ckey, *ctests;
    int lkey, ltests, k;

    if (!PyString_Check(key))
    {
        PyErr_SetString(PyExc_TypeError, "argument must be string");
        return NULL;
    }

    UNLESS(ckey=PyString_AsString(key)) return NULL;
    if((lkey=PyString_Size(key)) < 0) return NULL;

    UNLESS(ctests=PyString_AsString(self->tests)) return NULL;
    if((ltests=PyString_Size(self->tests)) < 0) return NULL;

    if(lkey != ltests) return PyInt_FromLong(0);

    while(lkey--)
      {
	k=*ckey++;
	if(tolower(k) != *ctests++) return PyInt_FromLong(0);
      }
    return PyInt_FromLong(1);
}

static PyMappingMethods String_as_mapping = {
    (inquiry)meaningless_len,       /*mp_length*/
    (binaryfunc)String__getitem__,  /*mp_subscript*/
    (objobjargproc)0,               /*mp_ass_subscript*/
};

static PyObject *
String(PyObject *self, PyObject *args)
{
  UNLESS(args=PyObject_CallObject(string_lower,args)) return NULL;
  UNLESS_ASSIGN(args,(PyObject *)new_Testobject(args, &Stringtype));
  return args;
}

static char Stringtype__doc__[] = "";

static PyTypeObject Stringtype = {
    PyObject_HEAD_INIT(NULL)
    0,				/*ob_size*/
    "StringMatch",		/*tp_name*/
    sizeof(Testobject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)Test_dealloc,	/*tp_dealloc*/
    (printfunc)0,		/*tp_print*/
    (getattrfunc)0,	/*tp_getattr*/
    (setattrfunc)0,	/*tp_setattr*/
    (cmpfunc)0,		/*tp_compare*/
    (reprfunc)0,		/*tp_repr*/
    0,			/*tp_as_number*/
    0,		/*tp_as_sequence*/
    &String_as_mapping,		/*tp_as_mapping*/
    (hashfunc)0,		/*tp_hash*/
    (ternaryfunc)Query__call__,		/*tp_call*/
    (reprfunc)0,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Stringtype__doc__ /* Documentation string */
};

static struct PyMethodDef Query_methods[] = {
  {"AttrTest",    (PyCFunction)AttrTest,  1,
   "AttrTest(name,subtest) -- Define a test on an attribute."},
  {"CompAttrTest",    (PyCFunction)CompAttrTest,  1,
   "CompAttrTest(name,subtest) -- Define a test on a computed attribute."},
  {"MethodTest",    (PyCFunction)MethodTest,  1,
   "MethodTest(method,arg) -- Define a test on method and argument.\n\n"
   "Matches occur for those objects for which: o.method(arg)\n"
   "is true."
  },
  {"ItemTest",    (PyCFunction)ItemTest,  1,
   "ItemTest(key,subtest) -- Define a test on an item."},
  {"FieldTest",   (PyCFunction)FieldTest, 1,
   "FieldTest(index,subtest) -- Define a test on an item or attribute.\n"
   "\n"
   "If 'index' is an integer, then an item test will be done, otherwise\n"
   "an attribute test will be done."
  },
  {"And",         (PyCFunction)And,       1,
   "And(*subtests) -- Create a test that is an and of several sub-tests"},
  {"Or",          (PyCFunction)Or,        1,
   "Or(*subtests) -- Create a test that is an or of several sub-tests"},
  {"Range",       (PyCFunction)Range,     1,
   "Range(min,max) -- Create a range test"},
  {"Cmp",         (PyCFunction)Cmp,       0,
   "Cmp(value) -- Define a straight comparison test with the given value"},
  {"Regex",       (PyCFunction)Regex,     0,
   "Regex(compiled_regex) -- Define a Regular-expression test"},
  {"String",      (PyCFunction)String,    1,
   "String(str) -- Define a case-insensitive test"},
  {NULL,		NULL}		/* sentinel */
};


static char Query_module_documentation[] = 
"Query blocks for composing complex queries without execing Python code\n"
"\n"
"This module provides a number of simple types that can be used to\n"
"compose complex queries that execute in a reasonable effiecient manner\n"
"against objects.  Each object type define objects that can be called\n"
"with a single argument or with 'getitem' to check whether an object,\n"
"such as a database record or a collection item satisfies a query.\n"
;

void
initQuery()
{
    PyObject *m, *d, *regex, *string;

    AttrTesttype.ob_type  =&PyType_Type;
    ItemTesttype.ob_type  =&PyType_Type;
    Andtype.ob_type       =&PyType_Type;
    Ortype.ob_type        =&PyType_Type;
    Rangetype.ob_type     =&PyType_Type;
    Cmptype.ob_type       =&PyType_Type;
    Regextype.ob_type     =&PyType_Type;
    Stringtype.ob_type    =&PyType_Type;

    /* Create the module and add the functions */
    m = Py_InitModule4("Query", Query_methods,
		     Query_module_documentation,
		     (PyObject*)NULL,PYTHON_API_VERSION);

    /* Add some symbolic constants to the module */
    d = PyModule_GetDict(m);

    if (!(regex = PyImport_ImportModule("regex")))
        Py_FatalError("can't initialize module qbe:  "
            "failed to import regex module");

    UNLESS_ASSIGN(regex, PyObject_CallMethod(regex, 
            "compile", "s", "a"))
        Py_FatalError("can't initialize module qbe:  "
            "failed to compile regular expression");

    RegexType = regex->ob_type;
    Py_DECREF(regex);

    if (!(string = PyImport_ImportModule("string")))
        Py_FatalError("can't initialize module qbe:  "
            "failed to import string module");

    if (!(string_lower = PyObject_GetAttrString(string, "lower")))
        Py_FatalError("can't initalize module qbe:  "
            "failed to import function lower() from string module");

    Py_DECREF(string);

    /* Check for errors */
    if (PyErr_Occurred())
        Py_FatalError("can't initialize module qbe");
}
