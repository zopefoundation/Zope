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

#include "Python.h"

#define MAX_WORD 64		/* Words longer than MAX_WORD are stemmed */

#ifndef min
#define min(a,b) ((a)<(b)?(a):(b))
#endif

typedef struct
{
    PyObject_HEAD
    PyObject *list;
    PyObject *synstop;
}
Splitter;
static
PyUnicodeObject *prepareString(PyUnicodeObject *o);

static PyObject *checkSynword(Splitter *self, PyObject *word)
{
    /* Always returns a borrowed reference */
    PyObject *value;

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

static PyObject *
Splitter_pos(Splitter *self, PyObject *args)
{
    return Py_BuildValue("(ii)", 0,0);
}


static struct PyMethodDef Splitter_methods[] =
    {
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

    doc1 = prepareString(doc);
    if (doc1 == NULL)
      return -1;

    s=doc1->str;

    self->list = PyList_New(0);

    for (i = 0; i < len; s++, i++) {
        register Py_UNICODE ch;

        ch = *s;
#ifdef DEBUG
        printf("%d %c %d\n",i,ch,ch);
        fflush(stdout);
#endif
        if (!inside_word) {
            if (Py_UNICODE_ISALPHA(ch)) {
                inside_word=1;
                start = i;
            }
        } else {

            if (!(Py_UNICODE_ISALNUM(ch) || ch=='/' || ch=='_' || ch=='-')) {
                inside_word = 0;

                word = PySequence_GetSlice((PyObject *)doc1,start,
                                           min(i, start + MAX_WORD));
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
                                   min(len, start + MAX_WORD));
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
PyUnicodeObject *prepareString(PyUnicodeObject *o)

{
    PyUnicodeObject *u;

    u = (PyUnicodeObject*) PyUnicode_FromUnicode(o->str, o->length);
    if (u != NULL)
      fixlower(u);
    return  u;
}

static char *splitter_args[]={"doc","synstop","encoding",NULL};


static PyObject *
newSplitter(PyObject *modinfo, PyObject *args,PyObject *keywds)
{
    Splitter *self=NULL;
    PyObject *doc=NULL, *unicodedoc=NULL,*synstop=NULL;
    char *encoding = "latin1";

    if (! (self = PyObject_NEW(Splitter, &SplitterType))) return NULL;
    if (! (PyArg_ParseTupleAndKeywords(args,keywds,"O|Os",splitter_args,&doc,&synstop,&encoding))) return NULL;

#ifdef DEBUG
    puts("got text");
    PyObject_Print(doc,stdout,0);
    fflush(stdout);
#endif

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

    if (synstop) {
        self->synstop = synstop;
        Py_INCREF(synstop);
    } else  self->synstop=NULL;

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
        { "pos", (PyCFunction) Splitter_pos, 0,
          "pos(index) -- Return the starting and ending position of a token" },
        { "indexes", (PyCFunction) Splitter_indexes, METH_VARARGS,
          "indexes(word) -- Return a list of the indexes of word in sequence" },
   
        { "UnicodeSplitter", (PyCFunction)newSplitter,
          METH_VARARGS|METH_KEYWORDS,
          "UnicodeSplitter(doc[,synstop][,encoding='latin1']) "
          "-- Return a word splitter"
        },
        { NULL, NULL }
    };

static char Splitter_module_documentation[] =
    "Parse source (unicode) string into sequences of words\n"
    "\n"
    "for use in an inverted index\n"
    "\n"
    "$Id: UnicodeSplitter.c,v 1.11 2001/11/07 13:28:07 andreasjung Exp $\n"
    ;


void
initUnicodeSplitter(void)
{
    PyObject *m, *d;
    char *rev="$Revision: 1.11 $";

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
