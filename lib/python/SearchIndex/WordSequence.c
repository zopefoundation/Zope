#include "Python.h"

#define ASSIGN(V,E) {PyObject *__e; __e=(E); Py_XDECREF(V); (V)=__e;}
#define UNLESS(E) if(!(E))
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E) UNLESS(V)


static PyObject *next_word();
static void WordSequence_reset();
static PyObject *default_wordletters;

static PyObject *string_lower;

typedef struct 
{
    PyObject_HEAD
    PyObject *text, *synstop, *wordletters;
    char *ctext, *here, *end, *cwordletters;
    int index;
} WordSequence;

staticforward PyTypeObject WordSequenceType;

static WordSequence *
newWordSequence(PyObject *text, PyObject *synstop, PyObject *wordletters)
{
    WordSequence *self;
    PyObject *t;

    UNLESS(self = PyObject_NEW(WordSequence, &WordSequenceType))
    {
        return NULL;
    }

    self->text = text;
    Py_INCREF(self->text);

    if ((synstop == NULL) || PyDict_Size(synstop) == 0)
    {
        self->synstop = NULL;
    }
    else
    {
        self->synstop = synstop;
        Py_INCREF(self->synstop);
    }

    if (wordletters == NULL) wordletters=default_wordletters;
    Py_INCREF(wordletters);
    self->wordletters = wordletters;
    self->cwordletters = PyString_AsString(self->wordletters);

    UNLESS(t = PyTuple_New(1))
    {
        return NULL;
    }

    Py_INCREF(text);
    PyTuple_SET_ITEM((PyTupleObject *)t, 0, text);

    UNLESS_ASSIGN(text, PyObject_CallObject(string_lower, t))
    {
        Py_DECREF(t);
        return NULL;
    }

    Py_DECREF(t);

    self->ctext = self->here = PyString_AsString(text);

    self->end = self->here + PyString_Size(text);

    self->index = -1;

    return self;
}

static void
WordSequence_dealloc(WordSequence *self) 
{
    Py_XDECREF(self->text);
    Py_XDECREF(self->synstop);
    Py_XDECREF(self->wordletters);

    PyMem_DEL(self);
}

static int
WordSequence_length(WordSequence *self)
{
    PyObject *res;

    WordSequence_reset(self);

    while (PyString_Check(res = next_word(self)))
    {
        Py_DECREF(res);
        self->index++;
    }

    if (res == NULL)
    {
        return NULL;
    }

    return self->index + 1;
}

static PyObject *
WordSequence_concat(WordSequence *self, PyObject *other)
{
    PyErr_SetString(PyExc_TypeError, "Cannot concatenate WordSequences.");
    return NULL;
}

static PyObject *
WordSequence_repeat(WordSequence *self, long n)
{
    PyErr_SetString(PyExc_TypeError, "Cannot repeat WordSequences.");
    return NULL;
}

static PyObject *
check_synstop(WordSequence *self, PyObject *word)
{
    PyObject *value;
    PyObject *t;

    if (self->synstop == NULL)
    {
        UNLESS(t = PyTuple_New(1))
        {
            return NULL;
	}

        Py_INCREF(word);
        PyTuple_SET_ITEM((PyTupleObject *)t, 0, word);

        UNLESS_ASSIGN(word, PyObject_CallObject(string_lower, t))
        {
            Py_DECREF(t);
  	    return NULL;
	}

        Py_DECREF(t);

        Py_INCREF(word);
        return word;
    }

    while ((value = PyDict_GetItem(self->synstop, word)) && 
        PyString_Check(value))
    {
        word = value;
    }

    if (value == NULL)
    {
        PyErr_Clear();

        UNLESS(t = PyTuple_New(1))
        {
            return NULL;
	}

        Py_INCREF(word);
        PyTuple_SET_ITEM((PyTupleObject *)t, 0, word);

        UNLESS_ASSIGN(word, PyObject_CallObject(string_lower, t))
        {
            Py_DECREF(t);
  	    return NULL;
	}

        Py_DECREF(t);

        Py_INCREF(word);
        return word;
    }

    Py_INCREF(Py_None);
    return Py_None;
}
    
static PyObject *
next_word(WordSequence *self)
{
    char wbuf[256];
    char *tmp_ptr;
    int size = PyString_Size(self->wordletters), i = 0;
    PyObject *pyword, *res;

    while (self->here < self->end)
    {
        /* skip hyphens */ 
        if ((i > 0) && (*self->here == '-'))
        {
            tmp_ptr = self->here;
            while ((*(++tmp_ptr) <= ' ') && (tmp_ptr < self->end));

            if ((tmp_ptr < self->end) && (tmp_ptr - self->here) > 1)
            {
                self->here = tmp_ptr;
	    }
	}
               
        /* Check to see if this character is part of a word */
        if (memchr(self->cwordletters, *self->here, size))
        {
            wbuf[i++] = *self->here;
        }
        else if (i != 0)
        {
            UNLESS(pyword = PyString_FromStringAndSize(wbuf, i))
            {
                return NULL;
	    }

	    /* We've found the end of a word */

            UNLESS(res = check_synstop(self, pyword))
            {
                Py_DECREF(pyword);
                return NULL;
	    }

            if (res != Py_None)
            {
                Py_DECREF(pyword);
                return res;
	    }

	    /* The word is a stopword, so ignore it */ 

            Py_DECREF(res);          
            Py_DECREF(pyword);
            i = 0;
        }            

        self->here++;
    }

    /* We've reached the end of the string */

    if (i == 0)
    { 
        /* No words */
        Py_INCREF(Py_None);
        return Py_None;
    }

    UNLESS(pyword = PyString_FromStringAndSize(wbuf, i))
    {
        return NULL;
    }

    res = check_synstop(self, pyword);
    Py_DECREF(pyword);
    return res;
}
 
static void
WordSequence_reset(WordSequence *self)
{
    self->here = self->ctext;
    self->index = -1;
}

static PyObject *
WordSequence_item(WordSequence *self, int i)
{
    PyObject *word = NULL;

    if (i <= self->index)
    {
        WordSequence_reset(self);
    }

    while(self->index < i)
    {
        Py_XDECREF(word);

        UNLESS(word = next_word(self))
        {
            return NULL;
	}
 
        if (word == Py_None)
        {
            Py_DECREF(word);
            PyErr_SetString(PyExc_IndexError, "WordSequence index out of range");
            return NULL;
        }

        self->index++;
    }

    return word;
}

static PyObject *
WordSequence_slice(WordSequence *self, int i, int j)
{
    PyErr_SetString(PyExc_TypeError, "Cannot slice WordSequences.");
    return NULL;
}

static PySequenceMethods WordSequence_as_sequence = {
    (inquiry)WordSequence_length,        /*sq_length*/
    (binaryfunc)WordSequence_concat,     /*sq_concat*/
    (intargfunc)WordSequence_repeat,     /*sq_repeat*/
    (intargfunc)WordSequence_item,       /*sq_item*/
    (intintargfunc)WordSequence_slice,   /*sq_slice*/
    (intobjargproc)0,                    /*sq_ass_item*/
    (intintobjargproc)0,                 /*sq_ass_slice*/
};

static int
next_word_pos(WordSequence *self, char **start, char **end)
{
    int size = PyString_Size(self->wordletters), res = -1;
    PyObject *pyword = NULL, *synstop = NULL;
    char *tmp_ptr;

    *start = *end = NULL;

    while (self->here < self->end)
    {
        /* skip hyphens */ 
        if ((*start != NULL) && (*self->here == '-'))
        {
	    /* If this isn't a valid hyphenated region, we'll want
             * to know where the end of the word is later.
             */ 
            *end = self->here;

            tmp_ptr = *end = self->here;
            while ((*(++tmp_ptr) <= ' ') && (tmp_ptr < self->end));

            if ((tmp_ptr < self->end) && (tmp_ptr - self->here) > 1)
            {
                self->here = tmp_ptr;
	    }
	}

        /* Check to see if this character is part of a word */
        if (memchr(self->cwordletters, *self->here, size))
        {
	    /* The character is part of a word.  If we don't have
             * a start position for the word, this must be the
             * first character; save a pointer to it if so.
             */
            if (*start == NULL)
            {    
                *start = self->here;
            }

            if (*end != NULL)
            {
	        /* This must be valid hyphenated word, so reset the end */
                *end = NULL;
	    }
        }
        else if (*start != NULL)
        {
	    /* We've found the end of a word */

	    /* See if we already have an end for the word */ 
            if (*end == NULL)
            {
                *end = self->here;
	    }

            UNLESS(pyword = PyString_FromStringAndSize(*start, *end - *start))
            {
                return -1;
	    }

            UNLESS(synstop = check_synstop(self, pyword))
            {
                res = -1;
                goto finally;
	    }

            if (synstop != Py_None)
            {
		/* We've found a word.  Set the end and return */
		*end = self->here;

                res = 1;
                goto finally;
	    }

	    /* The word is a stopword, so ignore it */ 
            *start = NULL;

            Py_DECREF(synstop);
            Py_DECREF(pyword);
        }            

        self->here++;
    }

    /* We've reached the end of the string */

    if (*start == NULL)
    { 
        /* No words */
        res = 0;
        goto finally;
    }

    *end = self->here;

    UNLESS(pyword = PyString_FromStringAndSize(*start, *end - *start))
    {
        goto finally;
    }

    UNLESS(synstop = check_synstop(self, pyword))
    {
        res = -1;
        goto finally;
    }

    if (synstop != Py_None)
    {
        res = 1;
        goto finally;
    }

    res = 0;

finally:
    Py_XDECREF(pyword);
    Py_XDECREF(synstop);

    return res;
}

static PyObject *
WordSequence_pos(WordSequence *self, PyObject *args)
{
    char *start, *end;
    int res, i;

    UNLESS(PyArg_Parse(args, "i", &i))
    {
        return NULL;
    }

    if (i <= self->index)
    {
        WordSequence_reset(self);
    }

    while(self->index < i)
    {
	res = next_word_pos(self, &start, &end);
    
	if (res > 0)
	{ 
            self->index++;
            continue;
	}
    
	if (res == 0)
	{
	    PyErr_SetString(PyExc_IndexError, "WordSequence index out of range");
	}
    
	return NULL;
    }

    return Py_BuildValue("(ii)", start - self->ctext, end - self->ctext);
}

static struct PyMethodDef WordSequence_methods[] = {
    { "pos", (PyCFunction)WordSequence_pos, 0, "" },
    { NULL, NULL }		/* sentinel */
};

static PyObject *
WordSequence_getattr(WordSequence *self, char *name) 
{
    return Py_FindMethod(WordSequence_methods, (PyObject *)self, name);
}

static char WordSequenceType__doc__[] = "";

static PyTypeObject WordSequenceType = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,                                 /*ob_size*/
    "WordSequence",                    /*tp_name*/
    sizeof(WordSequence),              /*tp_basicsize*/
    0,                                 /*tp_itemsize*/
    /* methods */
    (destructor)WordSequence_dealloc,  /*tp_dealloc*/
    (printfunc)0,                      /*tp_print*/
    (getattrfunc)WordSequence_getattr, /*tp_getattr*/
    (setattrfunc)0,                    /*tp_setattr*/
    (cmpfunc)0,                        /*tp_compare*/
    (reprfunc)0,                       /*tp_repr*/
    0,                                 /*tp_as_number*/
    &WordSequence_as_sequence,         /*tp_as_sequence*/
    0,                                 /*tp_as_mapping*/
    (hashfunc)0,                       /*tp_hash*/
    (ternaryfunc)0,                    /*tp_call*/
    (reprfunc)0,                       /*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    WordSequenceType__doc__ /* Documentation string */
};

static PyObject *
get_WordSequence(PyObject *self, PyObject *args)
{
    PyObject *text = NULL, *doc, *synstop = NULL, *wordletters = NULL,
             *res = NULL;

    UNLESS(PyArg_ParseTuple(args, "O|OO", &doc, &synstop, &wordletters))
    {
        goto finally;
    }

    UNLESS(text = PyObject_Str(doc))
    {
        goto finally;
    }

    if (synstop && !PyDict_Check(synstop))
    {
        PyErr_SetString(PyExc_TypeError, "Second argument to WordSequence "
            "must be dictionary");
        goto finally;
    }

    if (wordletters && !PyString_Check(wordletters))
    {
        PyErr_SetString(PyExc_TypeError, "Thirst argument to WordSequence "
            "must be string");
        goto finally;
    }

    res = (PyObject *)newWordSequence(text, synstop, wordletters);

finally:
    Py_XDECREF(text);
    return res;
}

static struct PyMethodDef WordSequence_module_methods[] = {
    { "WordSequence", (PyCFunction)get_WordSequence, 1, "" },
    { NULL, NULL }
};

static char WordSequence_module_documentation[] = "";

void
initWordSequence() 
{
    PyObject *m, *string;

    UNLESS(default_wordletters=
	   PyString_FromString("abcdefghijklmnopqrstuvwxyz0123456789"
			       "ABCDEFGHIJKLMNOPQRSTUVWXYZ")) return;

    /* Create the module and add the functions */
    m = Py_InitModule4("WordSequence", WordSequence_module_methods,
                     WordSequence_module_documentation,
                     (PyObject*)NULL,PYTHON_API_VERSION);

    string = PyImport_ImportModule("string");

    string_lower = PyObject_GetAttrString(string, "lower");
    Py_INCREF(string_lower);

    Py_DECREF(string);

    if (PyErr_Occurred())
    {
        Py_FatalError("can't initialize module WordSequence");
    }
}
