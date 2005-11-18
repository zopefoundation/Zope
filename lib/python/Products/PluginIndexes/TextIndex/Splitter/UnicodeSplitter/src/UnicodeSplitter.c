/*****************************************************************************

  Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
  
  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE
  
 ****************************************************************************/

#include "Python.h"

#ifndef min
#define min(a,b) ((a)<(b)?(a):(b))
#endif

typedef struct
{
    PyObject_HEAD
    PyObject *list;
    PyObject *synstop;
    int max_len;
    int allow_single_chars;
    int index_numbers;
    int casefolding;
}
Splitter;

static
PyUnicodeObject *prepareString(Splitter *self, PyUnicodeObject *o);

static PyObject *checkSynword(Splitter *self, PyObject *word)
{
    /* Always returns a borrowed reference */
    PyObject *value;

    if (PyUnicode_GetSize(word)==1 && ! self->allow_single_chars) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    if (self->synstop) {
        value = PyDict_GetItem(self->synstop,word);
        if (value != NULL) {
          return value;
        }
    }
    return word;
}

static void
Splitter_dealloc(Splitter *self)
{
    Py_XDECREF(self->list);
    Py_XDECREF(self->synstop);
    PyMem_DEL(self);
}

static int
Splitter_length(Splitter *self)
{
    return PyList_Size(self->list);
}

static PyObject *
Splitter_concat(Splitter *self, PyObject *other)
{
    PyErr_SetString(PyExc_TypeError, "Cannot concatenate Splitters.");
    return NULL;
}

static PyObject *
Splitter_repeat(Splitter *self, long n)
{
    PyErr_SetString(PyExc_TypeError, "Cannot repeat Splitters.");
    return NULL;
}



static PyObject *
Splitter_item(Splitter *self, int i)
{
  PyObject *item;
  item = PyList_GetItem(self->list, i);
  Py_XINCREF(item);  /* Promote borrowed ref unless exception */
  return item;
}

static PyObject * 
Splitter_split(Splitter *self) {

    Py_INCREF(self->list);

    return self->list;
}


static PyObject *
Splitter_indexes(Splitter *self, PyObject *args)
{
    int i=0, size;
    PyObject *word=NULL,*item=NULL,*r=NULL,*index=NULL;

    if (! (PyArg_ParseTuple(args,"O",&word))) return NULL;
    if (! (r=PyList_New(0))) return NULL;

    size = PyList_Size(self->list);
    for (i=0;i<size;i++) {
        item=PyList_GET_ITEM(self->list,i);

        if (PyUnicode_Compare(word,item)==0) {
            index=PyInt_FromLong(i);
            if(!index) return NULL;
            PyList_Append(r,index);
        }
    }

    return r;
}


static PyObject *
Splitter_slice(Splitter *self, int i, int j)
{
    PyErr_SetString(PyExc_TypeError, "Cannot slice Splitters.");
    return NULL;
}

static PySequenceMethods Splitter_as_sequence = {
    (inquiry)Splitter_length,        /*sq_length*/
    (binaryfunc)Splitter_concat,     /*sq_concat*/
    (intargfunc)Splitter_repeat,     /*sq_repeat*/
    (intargfunc)Splitter_item,       /*sq_item*/
    (intintargfunc)Splitter_slice,   /*sq_slice*/
    (intobjargproc)0,                    /*sq_ass_item*/
    (intintobjargproc)0,                 /*sq_ass_slice*/
};

static struct PyMethodDef Splitter_methods[] =
    {
        { "split", (PyCFunction) Splitter_split, 0,
          "split() -- Split string in one run" },
        { "indexes", (PyCFunction)Splitter_indexes, METH_VARARGS,
          "indexes(word) -- Return a list of the indexes of word in the sequence",
        },
        { NULL, NULL }		/* sentinel */
    };


static PyObject *
Splitter_getattr(Splitter *self, char *name)
{
    return Py_FindMethod(Splitter_methods, (PyObject *)self, name);
}

static char SplitterType__doc__[] = "";

static PyTypeObject SplitterType = {
    PyObject_HEAD_INIT(NULL)
    0,                                 /*ob_size*/
    "Splitter",                    /*tp_name*/
    sizeof(Splitter),              /*tp_basicsize*/
    0,                                 /*tp_itemsize*/
    /* methods */
    (destructor)Splitter_dealloc,  /*tp_dealloc*/
    (printfunc)0,                      /*tp_print*/
    (getattrfunc)Splitter_getattr, /*tp_getattr*/
    (setattrfunc)0,                    /*tp_setattr*/
    (cmpfunc)0,                        /*tp_compare*/
    (reprfunc)0,                       /*tp_repr*/
    0,                                 /*tp_as_number*/
    &Splitter_as_sequence,         /*tp_as_sequence*/
    0,                                 /*tp_as_mapping*/
    (hashfunc)0,                       /*tp_hash*/
    (ternaryfunc)0,                    /*tp_call*/
    (reprfunc)0,                       /*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    SplitterType__doc__ /* Documentation string */
};


static int splitUnicodeString(Splitter *self,PyUnicodeObject *doc)
{

    PyObject *word,*synword;
    PyUnicodeObject * doc1;
    Py_UNICODE *s;

    int len = doc->length;
    int inside_word=0;
    int i=0;
    int start=0;

    doc1 = prepareString(self,doc);
    if (doc1 == NULL)
      return -1;

    s=doc1->str;

    self->list = PyList_New(0);

    for (i = 0; i < len; s++, i++) {
        register Py_UNICODE ch;

        ch = *s;

        if (!inside_word) {
            if (self->index_numbers) {
                if (Py_UNICODE_ISALNUM(ch)) {
                    inside_word=1;
                    start = i;
                }

            } else {
                if (Py_UNICODE_ISALPHA(ch)) {
                    inside_word=1;
                    start = i;
                }
            }
        } else {

            if (!(Py_UNICODE_ISALNUM(ch) || ch=='/' || ch=='_' || ch=='-')) {
                inside_word = 0;

                word = PySequence_GetSlice((PyObject *)doc1,start,
                                           min(i, start + self->max_len));
                if (word==NULL)
                  goto err;

                synword = checkSynword(self,word);
                if (synword != Py_None) {
                  PyList_Append(self->list,synword);
                }

                start =  0;
#ifdef DEBUG
                PyObject_Print(word,stdout,0);
                fflush(stdout);
#endif
                Py_DECREF(word);
            }
        }
    }

    if (inside_word) {
        word = PySequence_GetSlice((PyObject *)doc1,start,
                                   min(len, start + self->max_len));
        if (word==NULL)
          goto err;

        synword = checkSynword(self,word);
        if (synword != Py_None) {
          PyList_Append(self->list,synword);
        }

        Py_DECREF(word);
    }

#ifdef DEBUG
    PyObject_Print(self->list,stdout,0);
    fflush(stdout);
#endif

    Py_DECREF(doc1);
    return 1;

 err:
    Py_DECREF(doc1);
    return -1;
}


static
void fixlower(PyUnicodeObject *self)
{
    int len = self->length;
    Py_UNICODE *s = self->str;

    while (len-- > 0) {
        register Py_UNICODE ch;

        ch = Py_UNICODE_TOLOWER(*s);
        if (ch != *s) *s = ch;
        s++;
    }
}


static
PyUnicodeObject *prepareString(Splitter *self,PyUnicodeObject *o)

{
    PyUnicodeObject *u;

    u = (PyUnicodeObject*) PyUnicode_FromUnicode(o->str, o->length);
    if (u != NULL){
        if (self->casefolding)
          fixlower(u);
    }
    return  u;
}

static char *splitter_args[]={"doc","synstop","encoding","indexnumbers","singlechar","maxlen","casefolding",NULL};


static PyObject *
newSplitter(PyObject *modinfo, PyObject *args,PyObject *keywds)
{
    Splitter *self=NULL;
    PyObject *doc=NULL, *unicodedoc=NULL,*synstop=NULL;
    char *encoding = "latin1";
    int index_numbers = 0;
    int max_len=64;
    int single_char = 0;
    int casefolding=1;

    if (! (PyArg_ParseTupleAndKeywords(args,keywds,"O|Osiiii",splitter_args,&doc,&synstop,&encoding,&index_numbers,&single_char,&max_len,&casefolding))) return NULL;

#ifdef DEBUG
    puts("got text");
    PyObject_Print(doc,stdout,0);
    fflush(stdout);
#endif

    if (index_numbers<0 || index_numbers>1) {
        PyErr_SetString(PyExc_ValueError,"indexnumbers must be 0 or 1");
        return NULL;
    }

    if (casefolding<0 || casefolding>1) {
        PyErr_SetString(PyExc_ValueError,"casefolding must be 0 or 1");
        return NULL;
    }

    if (single_char<0 || single_char>1) {
        PyErr_SetString(PyExc_ValueError,"singlechar must be 0 or 1");
        return NULL;
    }

    if (max_len<1 || max_len>128) {
        PyErr_SetString(PyExc_ValueError,"maxlen must be between 1 and 128");
        return NULL;
    }

    if (PyString_Check(doc)) {

        unicodedoc = PyUnicode_FromEncodedObject(doc,encoding,"strict");
        if (unicodedoc ==NULL) {
            PyErr_SetString(PyExc_UnicodeError, "Problem converting encoded string");
            return NULL;
        }

    } else if( PyUnicode_Check(doc)) {
        unicodedoc = doc;
        Py_INCREF(unicodedoc);

    } else {
        PyErr_SetString(PyExc_TypeError, "first argument is neither string nor unicode.");
        return NULL;
    }

    if (! (self = PyObject_NEW(Splitter, &SplitterType))) return NULL;

    if (synstop) {
        self->synstop = synstop;
        Py_INCREF(synstop);
    } else  self->synstop=NULL;

    self->index_numbers      = index_numbers;
    self->max_len            = max_len;
    self->allow_single_chars = single_char;
    self->casefolding        = casefolding;

    if ((splitUnicodeString(self,(PyUnicodeObject *)unicodedoc)) < 0)
      goto err;

    Py_DECREF(unicodedoc);
    return (PyObject*)self;

err:
    Py_DECREF(self);
    Py_DECREF(unicodedoc);

    return NULL;
}

static struct PyMethodDef Splitter_module_methods[] =
    {
        { "UnicodeSplitter", (PyCFunction)newSplitter,
          METH_VARARGS|METH_KEYWORDS,
          "UnicodeSplitter(doc[,synstop][,encoding='latin1'][,indexnumbers][,maxlen][,singlechar][,casefolding]) "
          "-- Return a word splitter"
        },
        { NULL, NULL }
    };

static char Splitter_module_documentation[] =
    "Parse source (unicode) string into sequences of words\n"
    "\n"
    "for use in an inverted index\n"
    "\n"
    "$Id$\n"
    ;


void
initUnicodeSplitter(void)
{
    PyObject *m, *d;
    char *rev="$Revision: 1.16 $";

    /* Create the module and add the functions */
    m = Py_InitModule4("UnicodeSplitter", Splitter_module_methods,
                       Splitter_module_documentation,
                       (PyObject*)NULL,PYTHON_API_VERSION);

    /* Add some symbolic constants to the module */
    d = PyModule_GetDict(m);
    PyDict_SetItemString(d, "__version__",
                         PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));

    if (PyErr_Occurred()) Py_FatalError("can't initialize module Splitter");
}
