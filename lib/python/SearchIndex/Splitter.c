#include "Python.h"

#define ASSIGN(V,E) {PyObject *__e; __e=(E); Py_XDECREF(V); (V)=__e;}
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E) UNLESS(V)

static PyObject *next_word();

typedef struct 
{
    PyObject_HEAD
    PyObject *text, *synstop;
    char *here, *end;
    int index;
} Splitter;
 
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
    PyMem_DEL(self);
}

static int
Splitter_length(Splitter *self)
{
    PyObject *res=0;

    Splitter_reset(self);
    while(1)
      {
	UNLESS_ASSIGN(res,next_word(self,NULL,NULL)) return -1;
	UNLESS(PyString_Check(res))
	  {
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
    
    cword = PyString_AsString(word);
    len = PyString_Size(word) - 1;

    len = PyString_Size(word);
    if(len < 2)	/* Single-letter words are stop words! */
    {
      Py_INCREF(Py_None);
      return Py_None;
    }

    /*************************************************************
      Test whether a word has any letters.                       *
                                                                 */    
    for (; --len >= 0 && ! isalpha(cword[len]); );
    if (len < 0)
    {
        Py_INCREF(Py_None);
        return Py_None;
    }
    /*
     * If no letters, treat it as a stop word.
     *************************************************************/

    Py_INCREF(word);

    if (self->synstop == NULL) return word;

    while ((value = PyObject_GetItem(self->synstop, word)) &&
	   PyString_Check(value))
    {
        ASSIGN(word,value);
	if(len++ > 100) break;	/* Avoid infinite recurssion */
    }

    if (value == NULL)
    {
        PyErr_Clear();
        return word;
    }

    return value;		/* Which must be None! */
}
 
#define MAX_WORD 64		/* Words longer than MAX_WORD are stemmed */
   
static PyObject *
next_word(Splitter *self, char **startpos, char **endpos)
{
  char wbuf[MAX_WORD];
  char *p, *end, *here, *b;
  int i = 0, c;
  PyObject *pyword, *res;

  here=self->here;
  end=self->end;
  b=wbuf;
  while (here < end)
    {
      /* skip hyphens */ 
      if ((i > 0) && (*here == '-'))
        {
	  here++;
	  while (isspace(here) && (here < end)) here++;
	  continue;
	}

      c=tolower(*here);
      
      /* Check to see if this character is part of a word */
      if(isalnum(c) || c=='/')
        { /* Found a word character */
	  if(startpos && i==0) *startpos=here;
	  if(i++ < MAX_WORD) *b++ = c;
        }
      else if (i != 0)
        { /* We've found the end of a word */
	  if(i >= MAX_WORD) i=MAX_WORD; /* "stem" the long word */

	  UNLESS(pyword = PyString_FromStringAndSize(wbuf, i))
            {
	      self->here=here;
	      return NULL;
	    }
	  
	  UNLESS(res = check_synstop(self, pyword))
            {
	      self->here=here;
	      Py_DECREF(pyword);
	      return NULL;
	    }
	  
	  if (res != Py_None)
            {
	      if(endpos) *endpos=here;
	      self->here=here;
	      Py_DECREF(pyword);
	      self->index++;
	      return res;
	    }

	  /* The word is a stopword, so ignore it */ 

	  Py_DECREF(res);          
	  Py_DECREF(pyword);
	  i = 0;
	  b=wbuf;
        }
      
      here++;
    }

  self->here=here;

  /* We've reached the end of the string */

  if(i >= MAX_WORD) i=MAX_WORD; /* "stem" the long word */
  if (i == 0)
    { 
      /* No words */
      self->here=here;
      Py_INCREF(Py_None);
      return Py_None;
    }
  
  UNLESS(pyword = PyString_FromStringAndSize(wbuf, i)) return NULL;
  
  if(endpos) *endpos=here;
  res = check_synstop(self, pyword);
  Py_DECREF(pyword);
  if(PyString_Check(res)) self->index++;
  return res;
}

static PyObject *
Splitter_item(Splitter *self, int i)
{
    PyObject *word = NULL;

    if (i <= self->index) Splitter_reset(self);

    while(self->index < i)
    {
        Py_XDECREF(word);

        UNLESS(word = next_word(self,NULL,NULL)) return NULL; 
        if (word == Py_None)
        {
            Py_DECREF(word);
            PyErr_SetString(PyExc_IndexError,
			    "Splitter index out of range");
            return NULL;
        }
    }

    return word;
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

    if (i <= self->index) Splitter_reset(self);

    while(self->index < i)
    {
	UNLESS(res=next_word(self, &start, &end)) return NULL;
	if(PyString_Check(res))
	  {
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
  while(1)
    {
      UNLESS_ASSIGN(w,next_word(self, NULL, NULL)) goto err;
      UNLESS(PyString_Check(w)) break;
      if(PyObject_Compare(word,w)==0)
	{
	  UNLESS_ASSIGN(index,PyInt_FromLong(i)) goto err;
	  if(PyList_Append(r,index) < 0) goto err;
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

static struct PyMethodDef Splitter_methods[] = {
    { "pos", (PyCFunction)Splitter_pos, 0,
      "pos(index) -- Return the starting and ending position of a token" },
    { "indexes", (PyCFunction)Splitter_indexes, METH_VARARGS,
      "indexes(word) -- Return al list of the indexes of word in the sequence",
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

static PyObject *
get_Splitter(PyObject *modinfo, PyObject *args)
{
    Splitter *self;
    PyObject *doc, *synstop = NULL;

    UNLESS(PyArg_ParseTuple(args,"O|O",&doc,&synstop)) return NULL;

    UNLESS(self = PyObject_NEW(Splitter, &SplitterType)) return NULL;

    if(synstop)
      {
	self->synstop=synstop;
	Py_INCREF(synstop);
      }
    else self->synstop=NULL;

    UNLESS(self->text = PyObject_Str(doc)) goto err;
    UNLESS(self->here=PyString_AsString(self->text)) goto err;
    self->end = self->here + PyString_Size(self->text);
    self->index = -1;
    return (PyObject*)self;
err:
    Py_DECREF(self);
    return NULL;
}

static struct PyMethodDef Splitter_module_methods[] = {
    { "Splitter", (PyCFunction)get_Splitter, METH_VARARGS,
      "Splitter(doc[,synstop]) -- Return a word splitter" },
    { NULL, NULL }
};

static char Splitter_module_documentation[] = 
"Parse source strings into sequences of words\n"
"\n"
"for use in an inverted index\n"
"\n"
"$Id: Splitter.c,v 1.6 1997/12/10 20:55:11 jim Exp $\n"
;


void
initSplitter() 
{
  PyObject *m, *d;
  char *rev="$Revision: 1.6 $";
  
  /* Create the module and add the functions */
  m = Py_InitModule4("Splitter", Splitter_module_methods,
                     Splitter_module_documentation,
                     (PyObject*)NULL,PYTHON_API_VERSION);
  
  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  PyDict_SetItemString(d, "__version__",
		       PyString_FromStringAndSize(rev+11,strlen(rev+11)-2));

#include "dcprotect.h"

  if (PyErr_Occurred()) Py_FatalError("can't initialize module Splitter");
}
