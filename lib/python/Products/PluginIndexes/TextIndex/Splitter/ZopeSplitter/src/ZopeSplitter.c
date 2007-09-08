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
#include <ctype.h>

#define ASSIGN(V,E) {PyObject *__e; __e=(E); Py_XDECREF(V); (V)=__e;}
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E) UNLESS(V)

typedef struct
{
    PyObject_HEAD
    PyObject *text, *synstop;
    char *here, *end;
    int index;
    int allow_single_chars;
    int index_numbers;
    int max_len;
    int casefolding;
}

Splitter;

static PyObject *next_word(Splitter *, char **, char **);

static void
Splitter_reset(Splitter *self)
{
    self->here = PyString_AsString(self->text);
    self->index = -1;
}

static void
Splitter_dealloc(Splitter *self)
{
    Py_XDECREF(self->text);
    Py_XDECREF(self->synstop);
    PyObject_DEL(self);
}

static int
Splitter_length(Splitter *self)
{
    PyObject *res=0;

    Splitter_reset(self);

    while(1) {
        UNLESS_ASSIGN(res,next_word(self,NULL,NULL)) return -1;
        UNLESS(PyString_Check(res)) {
            Py_DECREF(res);
            break;
        }
    }

    return self->index+1;
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

/*
  Map an input word to an output word by applying standard
  filtering/mapping words, including synonyms/stop words.
 
  Input is a word.
  
  Output is:
 
     None -- The word is a stop word
 
     sometext -- A replacement for the word
 */
static PyObject *
check_synstop(Splitter *self, PyObject *word)
{
    PyObject *value;
    char *cword;
    int len;

    cword = PyString_AS_STRING(word);
    len = PyString_GET_SIZE(word);

    if (len < 2 && !self->allow_single_chars)	
    /* Single-letter words are stop words! */
    {
        Py_INCREF(Py_None);
        return Py_None;
    }

    /*************************************************************
      Test whether a word has any letters.                       *
                                                                 */
    for (; --len >= 0 && ! isalpha((unsigned char)cword[len]); )
        ;
    if (len < 0 && ! self->index_numbers) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    /*
     * If no letters, treat it as a stop word.
     *************************************************************/

    Py_INCREF(word);

    if (self->synstop == NULL)
        return word;

    len = 0;
    while ((value = PyObject_GetItem(self->synstop, word)) &&
            PyString_Check(value)) {
	Py_DECREF(word);
	word = value;

        if (len++ > 100)
            break;	/* Avoid infinite recurssion */
    }

    if (value == NULL) {
        PyErr_Clear();
        return word;
    }

    return value;		/* Which must be None! */
}


static PyObject *
next_word(Splitter *self, char **startpos, char **endpos)
{
    char wbuf[256];
    char *end, *here, *b;
    int i = 0, c;
    PyObject *pyword, *res;

    here=self->here;
    end=self->end;
    b=wbuf;

    while (here < end) {
        /* skip hyphens */

        if ((i > 0) && (*here == '-')) {
            here++;

            while (isspace((unsigned char) *here) && (here < end))
                here++;

            continue;
        }

        if (self->casefolding) 
            c = tolower((unsigned char) *here);
        else
            c = (unsigned char) *here;

        /* Check to see if this character is part of a word */
        if (isalnum((unsigned char)c) || c == '/' || c == '_') { 
            /* Found a word character */

            if (startpos && i == 0)
                *startpos = here;

            if (i++ < self->max_len)
                *b++ = c;
        } else if (i != 0) { /* We've found the end of a word */
            if (i >= self->max_len)
                i =self->max_len; /* "stem" the long word */

            UNLESS(pyword = PyString_FromStringAndSize(wbuf, i)) {
                self->here = here;
                return NULL;
            }

            UNLESS(res = check_synstop(self, pyword)) {
                self->here = here;
                Py_DECREF(pyword);
                return NULL;
            }

            if (res != Py_None) {
                if (endpos)
                    *endpos = here;
                self->here = here;
                Py_DECREF(pyword);
                self->index++;
                return res;
            }

            /* The word is a stopword, so ignore it */
            Py_DECREF(res);
            Py_DECREF(pyword);
            i = 0;
            b = wbuf;
        }
        here++;
    }
    self->here=here;

    /* We've reached the end of the string */

    if (i >= self->max_len)
        i = self->max_len; /* "stem" the long word */

    if (i == 0) {
        /* No words */
        self->here=here;
        Py_INCREF(Py_None);
        return Py_None;
    }

    UNLESS(pyword = PyString_FromStringAndSize(wbuf, i)) return NULL;

    if(endpos)
        *endpos=here;

    res = check_synstop(self, pyword);
    Py_DECREF(pyword);

    if (PyString_Check(res))
        self->index++;

    return res;
}

static PyObject *
Splitter_item(Splitter *self, int i)
{
    PyObject *word = NULL;

    if (i <= self->index)
        Splitter_reset(self);

    while(self->index < i) {
        Py_XDECREF(word);

        UNLESS(word = next_word(self,NULL,NULL)) return NULL;

        if (word == Py_None) {
            Py_DECREF(word);
            PyErr_SetString(PyExc_IndexError,
                            "Splitter index out of range");
            return NULL;
        }
    }

    return word;
}


static PyObject *
Splitter_split(Splitter*self)
{
    PyObject *list=NULL,*word=NULL;

    UNLESS(list = PyList_New(0)) return NULL;

    Splitter_reset(self);

    while (1) {
        Py_XDECREF(word);

        UNLESS(word = next_word(self, NULL, NULL)) return NULL;

        if (word == Py_None) {
            return list;
        }

        PyList_Append(list,word);
    }

    return list;
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
    char *start, *end, *ctext;
    PyObject *res;
    int i;

    UNLESS(PyArg_Parse(args, "i", &i)) return NULL;

    if (i <= self->index)
        Splitter_reset(self);

    while(self->index < i) {
        UNLESS(res=next_word(self, &start, &end)) return NULL;

        if(PyString_Check(res)) {
            self->index++;
            Py_DECREF(res);
            continue;
        }

        Py_DECREF(res);
        PyErr_SetString(PyExc_IndexError, "Splitter index out of range");
        return NULL;
    }

    ctext=PyString_AsString(self->text);
    return Py_BuildValue("(ii)", start - ctext, end - ctext);
}

static PyObject *
Splitter_indexes(Splitter *self, PyObject *args)
{
    PyObject *word, *r, *w=0, *index=0;
    int i=0;

    UNLESS(PyArg_ParseTuple(args,"O",&word)) return NULL;
    UNLESS(r=PyList_New(0)) return NULL;
    UNLESS(word=check_synstop(self, word)) goto err;

    Splitter_reset(self);

    while(1) {
        UNLESS_ASSIGN(w,next_word(self, NULL, NULL)) goto err;
        UNLESS(PyString_Check(w)) break;

        if(PyObject_Compare(word,w)==0) {
            UNLESS_ASSIGN(index,PyInt_FromLong(i)) goto err;

            if(PyList_Append(r,index) < 0)
                goto err;
        }

        i++;
    }

    Py_XDECREF(w);
    Py_XDECREF(index);
    return r;

err:
    Py_DECREF(r);
    Py_XDECREF(index);
    return NULL;
}

static struct PyMethodDef Splitter_methods[] =
    {
        { "split", (PyCFunction)Splitter_split, 0,
            "split() -- Split complete string in one run"
        },

        { "pos", (PyCFunction)Splitter_pos, 0,
          "pos(index) -- Return the starting and ending position of a token"
        },

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

static char *splitter_args[]={"doc","synstop","encoding","singlechar","indexnumbers","maxlen","casefolding",NULL};


static PyObject *
get_Splitter(PyObject *modinfo, PyObject *args,PyObject * keywds)
{
    Splitter *self;
    PyObject *doc, *synstop = NULL;
    char *encoding = "latin1";
    int single_char = 0;
    int index_numbers = 0;
    int max_len= 64;
    int casefolding = 1;

    UNLESS(PyArg_ParseTupleAndKeywords(args,keywds,"O|Osiiii",splitter_args,
                                       &doc,
                                       &synstop,
                                       &encoding,
                                       &single_char,
                                       &index_numbers,
                                       &max_len,
                                       &casefolding
                                    )) return NULL;


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

    UNLESS(self = PyObject_NEW(Splitter, &SplitterType)) return NULL;

    if(synstop) {
        self->synstop=synstop;
        Py_INCREF(synstop);

    } else
        self->synstop=NULL;

    UNLESS(self->text = PyObject_Str(doc)) goto err;

    UNLESS(self->here = PyString_AS_STRING(self->text)) goto err;

    self->end = self->here + PyString_GET_SIZE(self->text);

    self->index = -1;
    self->allow_single_chars = single_char;
    self->index_numbers      = index_numbers;
    self->max_len            = max_len;
    self->casefolding        = casefolding;

    return (PyObject*)self;

err:
    Py_DECREF(self);

    return NULL;
}

static struct PyMethodDef Splitter_module_methods[] =
    {
        { "ZopeSplitter", (PyCFunction)get_Splitter, METH_VARARGS|METH_KEYWORDS,
            "ZopeSplitter(doc[,synstop][,encoding][,singlechar][,indexnumbers][,maxlen][,casefolding]) -- Return a word splitter"
        },

        { NULL, NULL }
    };

static char Splitter_module_documentation[] =
    "Parse source strings into sequences of words\n"
    "\n"
    "for use in an inverted index\n"
    "\n"
    "$Id$\n"
    ;


void
initZopeSplitter(void)
{
    /* Create the module and add the functions */
    Py_InitModule4("ZopeSplitter", Splitter_module_methods,
		   Splitter_module_documentation, NULL, PYTHON_API_VERSION);
}
