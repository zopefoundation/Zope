static char cPickle_module_documentation[] = 
""
;

#include <errno.h>

#include "Python.h"
#include "import.h"

static PyObject *ErrorObject;

#ifdef DEBUG_ON
#define DEBUG(x) printf("%s\n", x);
#else
#define DEBUG(x)
#endif

#define UNLESS(E) if(!(E))
#define ASSIGN(V,E) {PyObject *__e; __e=(E); Py_XDECREF(V); (V)=__e;}
#define UNLESS_ASSIGN(V,E) ASSIGN(V,E) UNLESS(V)

#define APPEND  'a'
#define BUILD   'b'
#define DUP     '2'
#define GET     'g'
#define INST    'i'
#define MARK    '('
#define PUT     'p'
#define POP     '0'
#define SETITEM 's'
#define STOP    '.'
#define CLASS   'c'
#define DICT    'd'
#define LIST    'l'
#define TUPLE   't'
#define NONE    'N'
#define INT     'I'
#define LONG    'L'
#define FLOAT   'F'
#define STRING  'S'
#define PERSID  'P'


#define FMT_STR(ob)  (PyTuple_Check(ob) ? "(O)" : "O")

#define DEL_SLICE(list, from, to) \
        (PySequence_SetSlice(list, from, to, empty_list) != -1)

#define ID(id_ob, ob) \
        (id_ob = PyObject_CallFunction(id_func, FMT_STR(ob), ob))


/* the sys module */
static PyObject *sys_module;

/* functions from __builtin__ module */
static PyObject *apply_func;
static PyObject *id_func;
static PyObject *eval_func;

/* the pickle module */
static PyObject *pickle_module;

/* functions from pickle module */
static PyObject *whichmodule_func;

static PyObject *empty_list;

static PyObject *py_string_save, *py_string_write, *py_string_stack,
                *py_string_memo;
static PyObject *mark;

static int
save_repr(self, ob, type)
    PyObject *self;
    PyObject *ob;
    char type;
{
  PyObject *arg = 0, *s = 0;

  UNLESS(s = PyString_FromStringAndSize(&type, 1))  return -1;

  UNLESS(arg = PyObject_Repr(ob))  goto err;

  UNLESS_ASSIGN(s, PySequence_Concat(s, arg))  goto err;

  UNLESS_ASSIGN(arg, PyTuple_New(1))  goto err;
  UNLESS(-1 != PyTuple_SetItem(arg, 0, s))  goto err;

  UNLESS(s = PyObject_GetAttr(self, py_string_write))  goto err;

  UNLESS_ASSIGN(s, PyObject_CallObject(s, arg))  goto err;
  
  Py_DECREF(arg);
  Py_DECREF(s);
  return 1;

err:
  Py_XDECREF(arg);
  Py_XDECREF(s);
  return -1;
}


static int
safe(ob)
    PyObject *ob;
{
  PyObject *this_item;
  int len, res, i;
  
  if (PyInt_Check(ob) || PyFloat_Check(ob) || 
      PyString_Check(ob) || ob == Py_None)
  {
    return 1;
  }

  if (PyTuple_Check(ob))
  {
    len = PyObject_Length(ob);
    for (i = 0; i < len; i++)
    {
      UNLESS(this_item = PySequence_GetItem(ob, i))
        return -1;
    
      if ((res = safe(this_item)) == 1)
        continue;

      return res;
    }

    return 1;
  }

  return 0;
}


static PyObject *
save_none(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *junk, *write;
  static PyObject *none;

  DEBUG("save_none");

  UNLESS(none)
    UNLESS(none = Py_BuildValue("(c)", NONE))
      return NULL;
  
  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;

  UNLESS(write = PyObject_GetAttr(self, py_string_write))  return NULL;

  UNLESS(junk = PyObject_CallObject(write, none))  
  {
    Py_DECREF(write);
    return NULL;
  }
  
  Py_DECREF(write);
  Py_DECREF(junk);

  Py_INCREF(Py_None);
  return Py_None;
}

      
static PyObject *
save_int(self, args)
    PyObject *self;
    PyObject *args;
{
  DEBUG("save_int");

  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;
  UNLESS(save_repr(self, args, INT) != -1)  return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
save_long(self, args)
    PyObject *self;
    PyObject *args;
{
  DEBUG("save_long");

  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;
  UNLESS(save_repr(self, args, LONG) != -1)  return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
save_float(self, args)
    PyObject *self;
    PyObject *args;
{
  DEBUG("save_long");

  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;
  UNLESS(save_repr(self, args, FLOAT) != -1)  return NULL;
  
  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
save_string(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *memo = 0, *ob_id = 0;

  DEBUG("save_string");

  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;

  UNLESS(save_repr(self, args, STRING) != -1)  return NULL;

  UNLESS(ID(ob_id, args))  return NULL;

  UNLESS(save_repr(self, ob_id, PUT) != -1)  goto err;

  UNLESS(memo = PyObject_GetAttr(self, py_string_memo))  goto err;
  
  UNLESS(PyObject_SetItem(memo, ob_id, args) != -1)  goto err;

  Py_DECREF(memo);
  Py_DECREF(ob_id);
  
  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(ob_id);
  Py_XDECREF(memo);

  return NULL;
}


static PyObject *
save_tuple(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *ob_id = 0, *element = 0, *memo = 0, *id_repr = 0, *junk = 0,
           *write = 0, *save = 0;
  static PyObject *pop;
  int len, i;
  char *id_repr_string, *s;

  DEBUG("save_tuple");

  UNLESS(pop)
    UNLESS(pop = Py_BuildValue("(c)", POP))
      return NULL;

  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;

  UNLESS(write = PyObject_GetAttr(self, py_string_write))  return NULL;

  UNLESS(save = PyObject_GetAttr(self, py_string_save))  goto err;

  UNLESS(junk = PyObject_CallObject(write, mark))  goto err;
  
  Py_DECREF(junk);

  UNLESS(ID(ob_id, args))  goto err;

  UNLESS(id_repr = PyObject_Repr(ob_id))  goto err;

  id_repr_string = PyString_AsString(id_repr);

  UNLESS(memo = PyObject_GetAttr(self, py_string_memo))  goto err;

  UNLESS((len = PyObject_Length(args)) != -1)  goto err;

  UNLESS(s = (char *)malloc((strlen(id_repr_string) + 3) * sizeof(char)))
  {
    PyErr_SetString(PyExc_MemoryError, "out of memory");
    goto err;
  }

  for (i = 0; i < len; i++)
  {
    UNLESS(element = PySequence_GetItem(args, i))  
    {
      free(s);
      goto err;
    }
    
    UNLESS(junk = PyObject_CallFunction(save, FMT_STR(element), element))
    {
      free(s);
      goto err;
    }
  
    Py_DECREF(junk);

    if (PyMapping_HasKey(memo, ob_id))
    {
      while (i-- >= 0)  
      {
        UNLESS(junk = PyObject_CallObject(write, pop))  
        {
          free(s);
          goto err;    
        }

        Py_DECREF(junk);        
      }

      sprintf(s, "%c%s\n", GET, id_repr_string);

      UNLESS(junk = PyObject_CallFunction(write, "s", s))
      {
        free(s); 
        goto err;
      }

      Py_DECREF(junk);

      break;
    }
  }

  UNLESS(i < len)
  {
    UNLESS(s = (char *)malloc((strlen(id_repr_string) + 3) * sizeof(char)))
    {
      PyErr_SetString(PyExc_MemoryError, "out of memory");
      goto err;
    }
  
    sprintf(s, "%c%c%s\n", TUPLE, PUT, id_repr_string);

    UNLESS(junk = PyObject_CallFunction(write, "s", s))
    {
      free(s);
      goto err;
    }

    Py_DECREF(junk);

    UNLESS(PyObject_SetItem(memo, ob_id, args) != -1)  
    {
      free(s);
      goto err;
    }
  }

  free(s);

  Py_DECREF(write);
  Py_DECREF(save);
  Py_DECREF(memo);
  Py_DECREF(ob_id);
  Py_DECREF(id_repr);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(write);
  Py_XDECREF(save);
  Py_XDECREF(memo);
  Py_XDECREF(ob_id);
  Py_XDECREF(id_repr);

  return NULL;
}


static PyObject *
save_list(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *ob_id = 0, *memo = 0, *element = 0, *junk = 0,
           *write = 0, *save = 0, *arg=0;
  static PyObject *list=0, *append=0;
  int len, i, safe_val;  

  DEBUG("save_list");

  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;

  UNLESS(write = PyObject_GetAttr(self, py_string_write))  return NULL;

  UNLESS(save = PyObject_GetAttr(self, py_string_save))  goto err;

  UNLESS(junk = PyObject_CallObject(write, mark))  goto err;
  
  Py_DECREF(junk);

  UNLESS(arg=PyTuple_New(1)) goto err;

  len = PyObject_Length(args);
  for (i = 0; i < len; i++)
  {
    UNLESS(element = PySequence_GetItem(args, i))  goto err;

    UNLESS((safe_val = safe(self, element)) != -1)  goto err;

    UNLESS(safe_val)
    {
      break;
    }

    UNLESS(junk = PyObject_CallObject(save, arg)) goto err;

    Py_DECREF(junk);
  }
  if(! list) UNLESS(list=Py_BuildValue("(c)",LIST)) return NULL;
  if(! append) UNLESS(append=Py_BuildValue("(c)",APPEND)) return NULL;
  UNLESS(junk = PyObject_CallObject(write, list))  return NULL;

  UNLESS(-1 != (PyTuple_SetItem(arg, 0, args))) goto err;
  Py_INCREF(args);
  UNLESS(ob_id = PyObject_CallObject(id_func, arg)) goto err;

  UNLESS(save_repr(self, ob_id, PUT) != -1)  goto err;

  UNLESS(memo = PyObject_GetAttr(self, py_string_memo))  goto err;

  UNLESS(PyObject_SetItem(memo, ob_id, args) != -1)  goto err;

  for (; i < len; i++)
  {
    UNLESS(element = PySequence_GetItem(args, i))  goto err;

    UNLESS(-1 != PyTuple_SetItem(arg, 0, element)) goto err;

    UNLESS(junk = PyObject_CallObject(save, arg)) goto err;

    UNLESS(junk = PyObject_CallObject(write, append))  goto err;
    
    Py_DECREF(junk);
  }
  Py_DECREF(arg);

  Py_DECREF(write);
  Py_DECREF(save);
  Py_DECREF(memo);
  Py_DECREF(ob_id);
  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(arg);
  Py_XDECREF(write);
  Py_XDECREF(save);
  Py_XDECREF(memo);
  Py_XDECREF(ob_id);

  return NULL;
}


static PyObject *
save_dict(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *items = 0, *element = 0, *key = 0, *value = 0, *junk = 0,
           *ob_id = 0, *memo = 0, *write = 0, *save = 0;
  int len, i, safe_key, safe_value;

  DEBUG("save_dict");

  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;

  UNLESS(write = PyObject_GetAttr(self, py_string_write))  return NULL;
  
  UNLESS(save = PyObject_GetAttr(self, py_string_save))  goto err;

  UNLESS(junk = PyObject_CallObject(write, mark))  goto err;
  
  Py_DECREF(junk);

  UNLESS(items = PyDict_Items(args))  goto err;

  len = PyObject_Length(items);
  for (i = 0; i < len; i++)
  {
    UNLESS(element = PySequence_GetItem(items, i))  goto err;
 
    UNLESS(key = PySequence_GetItem(element, 0))  goto err;

    UNLESS(value = PySequence_GetItem(element, 1))  goto err;

    UNLESS((safe_key = safe(key)) != -1)  goto err;

    UNLESS(safe_key)  break;
   
    UNLESS((safe_value = safe(value)) != -1)  goto err;
   
    UNLESS(safe_value)  break;

    UNLESS(junk = PyObject_CallFunction(save, FMT_STR(key), key))
      goto err;

    Py_DECREF(junk);

    UNLESS(junk = PyObject_CallFunction(save, FMT_STR(value), value))
      goto err;

    Py_DECREF(junk);
  }

  UNLESS(junk = PyObject_CallFunction(write, "c", DICT))  goto err;
  
  Py_DECREF(junk);

  UNLESS(ID(ob_id, args))  goto err;

  UNLESS(save_repr(self, ob_id, PUT) != -1)  goto err;

  UNLESS(memo = PyObject_GetAttr(self, py_string_memo))  goto err;

  UNLESS(PyObject_SetItem(memo, ob_id, args) != -1)  goto err;

  for (; i < len; i++)
  {
    UNLESS(element = PySequence_GetItem(items, i))  goto err;

    UNLESS(key = PySequence_GetItem(element, 0))  goto err;

    UNLESS(value = PySequence_GetItem(element, 1))  goto err;

    UNLESS(junk = PyObject_CallFunction(save, FMT_STR(key), key))
      goto err;

    Py_DECREF(junk);

    UNLESS(junk = PyObject_CallFunction(save, FMT_STR(value), value))
      goto err;

    Py_DECREF(junk);

    UNLESS(junk = PyObject_CallFunction(write, "c", SETITEM))
      goto err;
  
    Py_DECREF(junk);
  }

  Py_DECREF(write);
  Py_DECREF(save);
  Py_DECREF(items);
  Py_DECREF(ob_id);
  Py_DECREF(memo);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(write);
  Py_XDECREF(save);
  Py_XDECREF(items);
  Py_XDECREF(ob_id);
  Py_XDECREF(memo);

  return NULL;
}

  
static PyObject *
save_inst(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *class = 0, *module = 0, *name = 0, *ob_id = 0, *init_args = 0, 
           *memo = 0, *junk = 0, *id_repr = 0, *state = 0, *class_args = 0, 
           *element = 0, *write = 0, *save = 0;
  static PyObject *py_string__name__, *py_string__class__,
                  *py_string__dict__;

  char *s, *id_repr_string, *module_string, *name_string;
  int i, len;

  DEBUG("save_inst");

  UNLESS(py_string__name__)
    UNLESS(py_string__name__ = PyString_FromString("__name__"))
      return NULL;

  UNLESS(py_string__class__)
    UNLESS(py_string__class__ = PyString_FromString("__class__"))
      return NULL;

  UNLESS(py_string__dict__)
    UNLESS(py_string__dict__ = PyString_FromString("__dict__"))
      return NULL;

  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;

  UNLESS(write = PyObject_GetAttr(self, py_string_write))  return NULL;

  UNLESS(save = PyObject_GetAttr(self, py_string_save))  goto err;

  UNLESS(junk = PyObject_CallObject(write, mark))  goto err;
  
  Py_DECREF(junk);

  UNLESS(class = PyObject_GetAttr(args, py_string__class__))  goto err;

  UNLESS(module = PyObject_CallFunction(whichmodule_func, "O", class))
    goto err;

  UNLESS(name = PyObject_GetAttr(class, py_string__name__))  goto err;

  if (PyObject_HasAttrString(args, "__getinitargs__"))
  {
    UNLESS(class_args = PyObject_CallMethod(args, "__getinitargs__", NULL))
      goto err;

    UNLESS((len = PyObject_Length(class_args)) != -1)  goto err;

    for (i = 0; i < len; i++)
    {
      UNLESS(element = PySequence_GetItem(class_args, i))  goto err;

      UNLESS(junk = PyObject_CallFunction(save, FMT_STR(element), element))
        goto err;

      Py_DECREF(junk);
    }
  }

  UNLESS(ID(ob_id, args))  goto err;

  UNLESS(id_repr = PyObject_Repr(ob_id))  goto err;

  id_repr_string = PyString_AsString(id_repr);
  module_string  = PyString_AsString(module);
  name_string    = PyString_AsString(name);

  UNLESS(s = (char *)malloc((strlen(id_repr_string) + strlen(module_string) +
                      strlen(name_string) + 6) * sizeof(char)))
  {
    PyErr_SetString(PyExc_MemoryError, "out of memory");
    goto err;
  }

  sprintf(s, "%c%s\n%s\n%c%s\n", INST, module_string, name_string,
      PUT, id_repr_string);

  UNLESS(junk = PyObject_CallFunction(write, "s", s))
  {
    free(s);
    goto err;
  }

  Py_DECREF(junk);

  free(s);

  UNLESS(memo = PyObject_GetAttr(self, py_string_memo))  goto err;

  UNLESS(PyObject_SetItem(memo, ob_id, args) != -1)  goto err;

  if (PyObject_HasAttrString(args, "__getstate__"))
  {
    UNLESS(state = PyObject_CallMethod(args, "__getstate__", NULL))  
      goto err;
  }
  else
  {
    UNLESS(state = PyObject_GetAttr(args, py_string__dict__))  goto err;
  }

  UNLESS(junk = PyObject_CallFunction(save, FMT_STR(state), state))
    goto err;

  Py_DECREF(junk);

  Py_DECREF(write);
  Py_DECREF(save);
  Py_DECREF(class);
  Py_DECREF(module);
  Py_XDECREF(class_args);
  Py_DECREF(ob_id);
  Py_DECREF(id_repr);
  Py_DECREF(memo);
  Py_DECREF(state);

  UNLESS(junk = PyObject_CallMethod(self, "write", "c", BUILD))  return NULL;
  
  Py_DECREF(junk);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(write);
  Py_XDECREF(save);
  Py_XDECREF(class);
  Py_XDECREF(module);
  Py_XDECREF(name);
  Py_XDECREF(class_args);
  Py_XDECREF(ob_id);
  Py_XDECREF(id_repr);
  Py_XDECREF(memo);
  Py_XDECREF(state);

  return NULL;
}


static PyObject *
save_class(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *ob_id = 0, *id_repr = 0, *module = 0, *name = 0, *junk = 0;
  static PyObject *py_string__name__;
  char *id_repr_string, *module_string, *name_string, *s;

  DEBUG("save_class");

  UNLESS(py_string__name__)
    UNLESS(py_string__name__ = PyString_FromString("__name__"))
      return NULL;

  UNLESS(PyArg_Parse(args, "(OO)", &self, &args))  return NULL;

  UNLESS(module = PyObject_CallFunction(whichmodule_func, "O", args))  
    return NULL;

  UNLESS(name = PyObject_GetAttr(args, py_string__name__))  goto err;

  UNLESS(ID(ob_id, args))  goto err;

  UNLESS(id_repr = PyObject_Repr(ob_id))  goto err;

  id_repr_string = PyString_AsString(id_repr);
  module_string  = PyString_AsString(module);
  name_string    = PyString_AsString(name);

  UNLESS(s = malloc((strlen(id_repr_string) + strlen(module_string) +
              strlen(name_string) + 6) * sizeof(char)))
  {
    PyErr_SetString(PyExc_MemoryError, "out of memory");
    goto err;
  }

  sprintf(s, "%c%s\n%s\n%c%s\n", CLASS, module_string, name_string,
      PUT, id_repr_string);

  UNLESS(junk = PyObject_CallMethod(self, "write", "s", s))
  {
    free(s);
    goto err;
  }

  Py_DECREF(junk);

  free(s);

  Py_DECREF(module);
  Py_DECREF(name);
  Py_DECREF(ob_id);
  Py_DECREF(id_repr);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(module);
  Py_XDECREF(name);
  Py_XDECREF(ob_id);
  Py_XDECREF(id_repr);

  return NULL;
}

static PyObject *
persistent_id(self, args)
    PyObject *self;
    PyObject *args;
{
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
load_none(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *junk;

  DEBUG("load_none");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(junk = PyObject_CallMethod(self, "append", "O", Py_None))  
    return NULL;

  Py_DECREF(junk);
  Py_INCREF(Py_None);

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
load_int(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *str, *line, *junk;
  char *c_str, *endptr;
  long i;

  DEBUG("load_int");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  return NULL; 

  UNLESS(str = PySequence_GetSlice(line, 0, -1))
  {
    Py_DECREF(line);
    return NULL;
  }

  Py_DECREF(line);

  c_str = PyString_AsString(str);
  
  errno = 0;
  i = strtol(c_str, &endptr, 0);
  
  if (!errno && !strlen(endptr))
  {
    UNLESS(junk = PyObject_CallMethod(self, "append", "l", i))  
    {
      Py_DECREF(str);
      return NULL;
    }

    Py_DECREF(junk);
  }
  else
  {
    Py_DECREF(str);
    PyErr_SetString(PyExc_ValueError, "could not convert string to int");
    return NULL;
  }

  Py_DECREF(str);

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
load_long(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *str, *line, *py_long, *junk;
  char *c_str, *endptr;
  long i;

  DEBUG("load_long");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  return NULL;

  UNLESS(str = PySequence_GetSlice(line, 0, -1))
  {  
    Py_DECREF(line);
    return NULL;
  }

  Py_DECREF(line);

  c_str = PyString_AsString(str);

  errno = 0;
  i = strtol(c_str, &endptr, 0);
  
  if (!errno && (!strlen(endptr) || 
      ((strlen(endptr) == 1) && ((*endptr == 'l') || (*endptr == 'L')))))
  {
    py_long = PyLong_FromLong(i);
    UNLESS(junk = PyObject_CallMethod(self, "append", "O", py_long))  
    {
      Py_DECREF(py_long); Py_DECREF(str);
      return NULL;
    }

    Py_DECREF(junk);

    Py_DECREF(py_long);
  }
  else
  {
    Py_DECREF(str);
    PyErr_SetString(PyExc_ValueError, "could not convert string to long");
    return NULL;
  }

  Py_DECREF(str);

  Py_INCREF(Py_None);
  return Py_None;  
}

 
static PyObject *
load_float(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *str, *line, *junk;
  char *c_str, *endptr;
  double f;

  DEBUG("load_float");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  return NULL;

  UNLESS(str = PySequence_GetSlice(line, 0, -1))
  {  
    Py_DECREF(line);
    return NULL;
  }

  Py_DECREF(line);

  c_str = PyString_AsString(str);

  errno = 0;
  f = strtod(c_str, &endptr);
  
  if (!errno && !strlen(endptr))
  {
    UNLESS(junk = PyObject_CallMethod(self, "append", "d", f))  
    {
      Py_DECREF(str);
      return NULL;
    }

    Py_DECREF(junk);
  }
  else
  {
    Py_DECREF(str);
    PyErr_SetString(PyExc_ValueError, "could not convert string to float");
    return NULL;
  }

  Py_DECREF(str);

  Py_INCREF(Py_None);
  return Py_None;  
}


static PyObject *
load_string(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *str = 0, *line = 0, *new_str = 0, *junk = 0;
  static PyObject *empty_dict;

  DEBUG("load_string");

  UNLESS(empty_dict)
    UNLESS(empty_dict = PyDict_New())
      return NULL;

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  return NULL;

  UNLESS(str = PySequence_GetSlice(line, 0, -1))  goto err;

  UNLESS(new_str = PyObject_CallFunction(eval_func, "O{sO}", 
         str, "__builtins__", empty_dict))
    goto err;

  UNLESS(junk = PyObject_CallMethod(self, "append", "O", new_str))  goto err;

  Py_DECREF(junk);

  Py_DECREF(str);
  Py_DECREF(line);
  Py_DECREF(new_str);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(str);
  Py_XDECREF(line);
  Py_XDECREF(new_str);

  return NULL;
}


static PyObject *
load_tuple(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *marker = 0, *tup = 0, *stack = 0, *slice = 0, *list = 0;
  int i, j;

  DEBUG("load_tuple");
  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(marker = PyObject_CallMethod(self, "marker", NULL))  return NULL;

  i = (int)PyInt_AsLong(marker);
  Py_DECREF(marker);
  
  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  return NULL;

  UNLESS((j = PyObject_Length(stack)) != -1)  goto err;

  UNLESS(slice = PySequence_GetSlice(stack, i + 1, j))  goto err;
  
  UNLESS(tup = PySequence_Tuple(slice))  goto err;

  UNLESS(list = Py_BuildValue("[O]", tup))  goto err;

  UNLESS(PySequence_SetSlice(stack, i, j, list) != -1)  goto err;

  Py_DECREF(stack);
  Py_DECREF(tup);
  Py_DECREF(list);
  Py_DECREF(slice);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(stack);
  Py_XDECREF(tup);
  Py_XDECREF(list);
  Py_XDECREF(slice);

  return NULL;
}


static PyObject *
load_list(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *marker, *list, *stack;
  int i, j;

  DEBUG("load_list");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(marker = PyObject_CallMethod(self, "marker", NULL))  return NULL;

  i = (int)PyInt_AsLong(marker);
  Py_DECREF(marker);  

  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  return NULL;

  UNLESS((j = PyObject_Length(stack)) != -1)  goto err;

  UNLESS(list = PySequence_GetSlice(stack, i + 1, j))  goto err;

  UNLESS(list = Py_BuildValue("[O]", list))  goto err;

  UNLESS(PySequence_SetSlice(stack, i, j, list) != -1)  goto err;

  Py_DECREF(stack);
  Py_DECREF(list);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(stack);
  Py_XDECREF(list);

  return NULL;
}


static PyObject *
load_dict(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *marker = 0, *list = 0, *dict = 0, *stack = 0, *key = 0, *value = 0;
  int i, j, k;

  DEBUG("load_dict");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(marker = PyObject_CallMethod(self, "marker", NULL))  return NULL;

  i = (int)PyInt_AsLong(marker);
  
  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  goto err;

  UNLESS((j = PyObject_Length(stack)) != -1)  goto err;

  UNLESS(dict = PyDict_New())  goto err;

  for (k = i + 1; k < j; k += 2)
  {
    UNLESS(key = PySequence_GetItem(stack, k))  goto err;

    UNLESS(value = PySequence_GetItem(stack, k + 1))  goto err;

    UNLESS(PyObject_SetItem(dict, key, value) != -1)  goto err;
  }

  UNLESS(list = Py_BuildValue("[O]", dict))  goto err;

  UNLESS(PySequence_SetSlice(stack, i, j, list) != -1)  goto err;

  Py_DECREF(stack);
  Py_DECREF(list);
  Py_DECREF(dict);
  Py_DECREF(marker);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(stack);
  Py_XDECREF(dict);
  Py_XDECREF(list);
  Py_XDECREF(marker);

  return NULL;
}


static PyObject *
load_inst(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *marker = 0, *stack = 0, *arg_tup = 0, *module = 0, *name = 0, 
           *arg_slice = 0, *line = 0, *class = 0, *value = 0, 
           *ApplicationError = 0, *err_tup = 0, *exc_type = 0,
           *exc_value = 0, *exc_value_repr = 0, *class__name__ = 0, 
           *error_str = 0, *junk = 0;
  int i, j;
  char *module_str, *class__name__str, *exc_value_str, *s; 

  DEBUG("load_inst");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  return NULL;

  UNLESS(module = PySequence_GetSlice(line, 0, -1))
  {  
    Py_DECREF(line);  
    return NULL; 
  }

  Py_DECREF(line);

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  goto err;

  UNLESS(name = PySequence_GetSlice(line, 0, -1))
  {  
    Py_DECREF(line);
    goto err;
  } 

  Py_DECREF(line);

  UNLESS(marker = PyObject_CallMethod(self, "marker", NULL))  goto err;

  i = (int)PyInt_AsLong(marker);
  Py_DECREF(marker);

  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  goto err;

  UNLESS((j = PyObject_Length(stack)) != -1)  goto err;

  UNLESS(arg_slice = PySequence_GetSlice(stack, i + 1, j))  goto err;

  UNLESS(arg_tup = PySequence_Tuple(arg_slice))  goto err;

  UNLESS(DEL_SLICE(stack, i, j))  goto err;

  UNLESS(class = PyObject_CallMethod(self, "find_class", "OO", module, name))
    goto err;

  UNLESS(value = PyObject_CallFunction(apply_func, "OO", class, arg_tup))
  {
    UNLESS(ApplicationError = PyObject_GetAttrString(self, "ApplicationError"))
      goto err;

    UNLESS(exc_type = PyObject_GetAttrString(sys_module, "exc_type"))
      goto err;

    UNLESS(exc_value = PyObject_GetAttrString(sys_module, "exc_value"))
      goto err;

    UNLESS(class__name__ = PyObject_GetAttrString(class, "__name__"))
      goto err;

    /***************   FIX THIS!!!!!!!!!!!  *************************/
    UNLESS(exc_value_repr = PyObject_Str(exc_value))  goto err;

    module_str = PyString_AsString(module);
    class__name__str = PyString_AsString(class__name__);
    exc_value_str = PyString_AsString(exc_value_repr);

    UNLESS(s = (char *)malloc((strlen(module_str) + strlen(class__name__str) +
                        strlen(exc_value_str) + 13) * sizeof(char)))
    {
      PyErr_SetString(PyExc_MemoryError, "out of memory");
      goto err;
    }

    sprintf(s, "In class %s.%s: %s", module_str, class__name__str,
        exc_value_str);

    UNLESS(error_str = PyString_FromString(s)) 
    {
      free(s);
      goto err;
    }

    free(s);

    UNLESS(err_tup = Py_BuildValue("(OO)", exc_type, error_str))  goto err;

    PyErr_SetObject(ApplicationError, err_tup);

    Py_DECREF(module);
    Py_DECREF(name);
    Py_DECREF(stack);
    Py_DECREF(arg_slice);
    Py_DECREF(arg_tup);
    Py_DECREF(class);
    Py_DECREF(value);
    Py_DECREF(ApplicationError);
    Py_DECREF(exc_type);
    Py_DECREF(exc_value);
    Py_DECREF(class__name__);
    Py_DECREF(exc_value_repr);
    Py_DECREF(error_str);
    Py_DECREF(err_tup);

    return NULL;
  }

  UNLESS(junk = PyObject_CallMethod(self, "append", "O", value))  
    goto err;

  Py_DECREF(junk);

  Py_DECREF(module);
  Py_DECREF(name);  
  Py_DECREF(stack);
  Py_DECREF(arg_slice);
  Py_DECREF(arg_tup);
  Py_DECREF(class);
  Py_DECREF(value);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(module);
  Py_XDECREF(name);
  Py_XDECREF(stack);
  Py_XDECREF(arg_slice);
  Py_XDECREF(arg_tup);
  Py_XDECREF(class);
  Py_XDECREF(value);
  Py_XDECREF(ApplicationError);
  Py_XDECREF(exc_type);
  Py_XDECREF(exc_value);
  Py_XDECREF(class__name__);
  Py_XDECREF(exc_value_repr);
  Py_XDECREF(error_str);
  Py_XDECREF(err_tup);

  return NULL;
}


static PyObject *
load_class(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *line = 0, *module = 0, *name = 0, *class = 0, *junk = 0;

  DEBUG("load_class");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  return NULL;

  UNLESS(module = PySequence_GetSlice(line, 0, -1))
  {
    Py_DECREF(line);
    return NULL;
  }

  Py_DECREF(line);

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  goto err;

  UNLESS(name = PySequence_GetSlice(line, 0, -1))
  {
    Py_DECREF(line);
    goto err;
  }

  Py_DECREF(line);

  UNLESS(class = PyObject_CallMethod(self, "find_class", "OO", module, name))
    goto err;

  UNLESS(junk = PyObject_CallMethod(self, "append", "O", class))  goto err;
  
  Py_DECREF(junk);

  Py_DECREF(module);
  Py_DECREF(name);
  Py_DECREF(class);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(module);
  Py_XDECREF(name);
  Py_XDECREF(class);

  return NULL;
}


static PyObject *
load_persid(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *line = 0, *pid = 0, *pers_load_val = 0, *junk = 0;

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  return NULL;

  UNLESS(pid = PySequence_GetSlice(line, 0, -1))
  {
    Py_DECREF(line);
    return NULL;
  }

  Py_DECREF(line);

  UNLESS(pers_load_val = PyObject_CallMethod(self, "persistent_load","O", pid))
    goto err;

  UNLESS(junk = PyObject_CallMethod(self, "append", "O", pers_load_val))
    goto err;

  Py_DECREF(junk);
  Py_DECREF(pid);
  Py_DECREF(pers_load_val);
  
  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(pid);
  Py_XDECREF(pers_load_val);

  return NULL;
}


static PyObject *
load_pop(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *stack;
  int len;

  DEBUG("load_pop");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  return NULL;

  UNLESS((len = PyObject_Length(stack)) != -1)  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(DEL_SLICE(stack, -1, len))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  Py_DECREF(stack);

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
load_dup(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *stack, *last, *junk;

  DEBUG("load_dup");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;
  
  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  return NULL;

  UNLESS(last = PySequence_GetItem(stack, -1))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(junk = PyObject_CallMethod(self, "append", "O", last))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  Py_DECREF(junk);
  Py_DECREF(stack);

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
load_get(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *line = 0, *str = 0, *memo = 0, *value = 0;

  DEBUG("load_get");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  return NULL;

  UNLESS(str = PySequence_GetSlice(line, 0, -1))
  {
    Py_DECREF(line);
    return NULL;
  }

  Py_DECREF(line);

  UNLESS(memo = PyObject_GetAttr(self, py_string_memo))  goto err;

  UNLESS(value = PyObject_GetItem(memo, str))  goto err;

  UNLESS(PyObject_CallMethod(self, "append", "O", value))  goto err;

  Py_DECREF(str);
  Py_DECREF(memo);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(str);
  Py_XDECREF(memo);

  return NULL;
}


static PyObject *
load_put(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *line = 0, *str = 0, *memo = 0, *stack = 0, *value = 0;

  DEBUG("load_put");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(line = PyObject_CallMethod(self, "readline", NULL))  return NULL;

  UNLESS(str = PySequence_GetSlice(line, 0, -1))
  {
    Py_DECREF(line);
    return NULL;
  }

  Py_DECREF(line);

  UNLESS(memo = PyObject_GetAttr(self, py_string_memo))  goto err;
  
  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  goto err;

  UNLESS(value = PySequence_GetItem(stack, -1))  goto err;

  UNLESS(PyObject_SetItem(memo, str, value) != -1)  goto err;

  Py_DECREF(str);
  Py_DECREF(memo);
  Py_DECREF(stack);

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(str);
  Py_XDECREF(memo);
  Py_XDECREF(stack);

  return NULL;
}


static PyObject *
load_append(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *stack, *value, *list, *junk;
  int len;

  DEBUG("load_append");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  return NULL;

  UNLESS(value = PySequence_GetItem(stack, -1))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS((len = PyObject_Length(stack)) != -1)  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(DEL_SLICE(stack, -1, len))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(list = PySequence_GetItem(stack, -1))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(junk = PyObject_CallMethod(list, "append", "O", value)) 
  {
    Py_DECREF(stack);    
    return NULL;
  }

  Py_DECREF(junk);
  Py_DECREF(stack);

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
load_setitem(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *stack, *value, *key, *dict;
  int len;

  DEBUG("load_setitem");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  return NULL;

  UNLESS(value = PySequence_GetItem(stack, -1))
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(key = PySequence_GetItem(stack, -2))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS((len = PyObject_Length(stack)) != -1)  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(DEL_SLICE(stack, -2, len))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(dict = PySequence_GetItem(stack, -1))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(PyObject_SetItem(dict, key, value) != -1)  
  {
    Py_DECREF(stack);
    return NULL;
  }

  Py_DECREF(stack);

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
load_build(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *stack = 0, *value = 0, *inst = 0, *instdict = 0, *keys = 0, 
           *this_key = 0, *this_value = 0, *ApplicationError = 0, 
           *exc_type = 0, *exc_value = 0, *class = 0, *class__name__ = 0,
           *ob_id = 0, *exc_value_repr = 0, *err_tup = 0, *exc_traceback = 0,
           *ob_id_repr = 0, *junk = 0;
  static PyObject *py_string__dict__;
  char *class__name__str, *exc_value_str, *s, *ob_id_str;
  int len, i;

  DEBUG("load_build");

  UNLESS(py_string__dict__)
    UNLESS(py_string__dict__ = PyString_FromString("__dict__"))
      return NULL;


  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  return NULL;

  UNLESS(value = PySequence_GetItem(stack, -1))  goto err; 

  UNLESS((len = PyObject_Length(stack)) != -1)  goto err;

  UNLESS(DEL_SLICE(stack, -1, len))  goto err;

  UNLESS(inst = PySequence_GetItem(stack, -1))  goto err;

  UNLESS(PyObject_HasAttrString(inst, "__setstate__"))
  {
    UNLESS(instdict = PyObject_GetAttr(inst, py_string__dict__))  goto err;

    UNLESS(keys = PyDict_Keys(value))  goto err;

    UNLESS((len = PyObject_Length(keys)) != -1)  goto err;

    for (i = 0; i < len; i++)
    {
      UNLESS(this_key = PySequence_GetItem(keys, i))  goto err;
  
      UNLESS(this_value = PyObject_GetItem(value, this_key))  goto err;

      UNLESS(PyObject_SetItem(instdict, this_key, this_value) != -1)  goto err;
    }
  }
  else
  {
    UNLESS(junk = PyObject_CallMethod(inst, "__setstate__", "O", value))
    {
      UNLESS(ApplicationError = PyObject_GetAttrString(self, 
          "ApplicationError"))
        goto err;

      UNLESS(exc_type = PyObject_GetAttrString(sys_module, "exc_type"))
        goto err;

      UNLESS(exc_value = PyObject_GetAttrString(sys_module, "exc_value"))
        goto err;

      UNLESS(exc_traceback = PyObject_GetAttrString(sys_module, 
          "exc_traceback"))
        goto err;

      UNLESS(class = PyObject_GetAttrString(inst, "__class__"))  goto err;

      UNLESS(class__name__ = PyObject_GetAttrString(class, "__name__"))
        goto err;

      UNLESS(ob_id = PyObject_CallFunction(id_func, "O", inst))  
        goto err;

      /***************   FIX THIS!!!!!!!!!!!  *************************/
      UNLESS(exc_value_repr = PyObject_Str(exc_value))  goto err;

      UNLESS(ob_id_repr = PyObject_Repr(ob_id))  goto err;

      class__name__str = PyString_AsString(class__name__);
      exc_value_str = PyString_AsString(exc_value_repr);
      ob_id_str = PyString_AsString(ob_id_repr);

      UNLESS(s = (char *)malloc((strlen(ob_id_str) + strlen(class__name__str) +
                          strlen(exc_value_str) + 18) * sizeof(char)))
      {
        PyErr_SetString(PyExc_MemoryError, "out of memory");
        goto err;
      }
      
      sprintf(s, "%s(%s).__setstate__: %s", class__name__str, ob_id_str,
          exc_value_str);

      UNLESS(err_tup = Py_BuildValue("(OsO)", 
             exc_type, s, exc_traceback))
      {
        free(s);
        goto err;
      }

      free(s);

      PyErr_SetObject(ApplicationError, err_tup);
      goto err;
    }

    Py_DECREF(junk);
    Py_XDECREF(stack);
    Py_XDECREF(instdict);
    Py_XDECREF(keys);
  }

  Py_INCREF(Py_None);
  return Py_None;

err:
  Py_XDECREF(stack);
  Py_XDECREF(instdict);
  Py_XDECREF(keys);
  Py_XDECREF(ApplicationError);
  Py_XDECREF(exc_type);
  Py_XDECREF(exc_value);
  Py_XDECREF(exc_traceback);
  Py_XDECREF(class);
  Py_XDECREF(class__name__);
  Py_XDECREF(ob_id);
  Py_XDECREF(exc_value_repr);
  Py_XDECREF(ob_id_repr);
  Py_XDECREF(err_tup);
  
  return NULL;
}


static PyObject *
load_mark(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *junk;
  static PyObject *m;

  DEBUG("load_mark");

  UNLESS(m)
    UNLESS(m = PyObject_GetAttrString(self, "mark"))
      return NULL;

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(junk = PyObject_CallMethod(self, "append", "O", m))  
  {
    Py_DECREF(m);
    return NULL;
  }

  Py_DECREF(junk);
  Py_DECREF(m);

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
load_stop(self, args)
    PyObject *self;
    PyObject *args;
{
  PyObject *stack, *value, *stop;
  static PyObject *py_string_STOP;
  int len;

  DEBUG("load_stop");

  UNLESS(py_string_STOP)
    UNLESS(py_string_STOP = PyString_FromString("STOP"))
      return NULL;

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  UNLESS(stack = PyObject_GetAttr(self, py_string_stack))  return NULL;

  UNLESS(value = PySequence_GetItem(stack, -1))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS((len = PyObject_Length(stack)) != -1)  
  {
    Py_DECREF(stack);
    return NULL;
  }

  UNLESS(DEL_SLICE(stack, -1, len))  
  {
    Py_DECREF(stack);
    return NULL;
  }

  Py_DECREF(stack);

  UNLESS(stop = PyObject_GetAttr(pickle_module, py_string_STOP))
  {
    return NULL;
  }

  PyErr_SetObject(stop, value);
  
  Py_DECREF(stop);

  return NULL;
}


static PyObject *  
load_eof(self, args)
    PyObject *self;
    PyObject *args;
{
  DEBUG("load_eof");

  UNLESS(PyArg_Parse(args, "O", &self))  return NULL;

  PyErr_SetNone(PyExc_EOFError);
  return NULL;
}


/* List of methods defined in the module */
static struct PyMethodDef cPickle_methods[] = {
  {"save_none",    save_none,    0, ""},
  {"save_int",     save_int,     0, ""},
  {"save_long",    save_long,    0, ""},
  {"save_float",   save_float,   0, ""},
  {"save_string",  save_string,  0, ""},
  {"save_tuple",   save_tuple,   0, ""},
  {"save_list",    save_list,    0, ""},
  {"save_dict",    save_dict,    0, ""},
  {"save_inst",    save_inst,    0, ""},
  {"save_class",   save_class,   0, ""},
  {"persistent_id",   persistent_id,   0, ""},
  {"load_none",    load_none,    0, ""},
  {"load_int",     load_int,     0, ""},
  {"load_long",    load_long,    0, ""},
  {"load_float",   load_float,   0, ""},
  {"load_string",  load_string,  0, ""},
  {"load_tuple",   load_tuple,   0, ""},
  {"load_list",    load_list,    0, ""},
  {"load_dict",    load_dict,    0, ""},
  {"load_inst",    load_inst,    0, ""},
  {"load_class",   load_class,   0, ""},
  {"load_persid",  load_persid,  0, ""},
  {"load_pop",     load_pop,     0, ""},
  {"load_dup",     load_dup,     0, ""},
  {"load_get",     load_get,     0, ""},
  {"load_put",     load_put,     0, ""},
  {"load_append",  load_append,  0, ""},
  {"load_setitem", load_setitem, 0, ""},
  {"load_build",   load_build,   0, ""},
  {"load_mark",    load_mark,    0, ""},
  {"load_stop",    load_stop,    0, ""},
  {"load_eof",     load_eof,     0, ""},
  {NULL,		NULL}		/* sentinel */
};


/* Initialization function for the module (*must* be called initcPickle) */


static int
replace_pickle(pickle, cPickle)
    PyObject *pickle;
    PyObject *cPickle;
{
  PyObject *key, *value, *pickler, *unpickler, 
           *replacement, *dispatch, *dispatch_keys, *dispatch_values, 
           *value_str;
  int len, i;

  UNLESS(pickler = PyObject_GetAttrString(pickle, "Pickler"))
    return NULL;

  UNLESS(dispatch = PyObject_GetAttrString(pickler, "dispatch"))
    return NULL;

  UNLESS(dispatch_keys = PyDict_Keys(dispatch))
    return NULL;

  UNLESS(dispatch_values = PyDict_Values(dispatch))
    return NULL;

  len = PyObject_Length(dispatch_keys);
  for (i = 0; i < len; i++)
  {
    UNLESS(key = PySequence_GetItem(dispatch_keys, i))
      return NULL;

    UNLESS(value = PySequence_GetItem(dispatch_values, i))
      return NULL;

    UNLESS(value_str = PyObject_GetAttrString(value, "__name__"))
      return NULL;

    UNLESS(replacement = PyObject_GetAttr(cPickle, value_str))
      return NULL;

    UNLESS(PyObject_SetItem(dispatch, key, replacement) != -1)
      return NULL;

    Py_DECREF(value_str);  
    Py_DECREF(replacement);
  }


  UNLESS(replacement = PyObject_GetAttrString(cPickle, "persistent_id"))
    return NULL;
  UNLESS(-1 != PyObject_SetAttrString(pickler,"persistent_id",replacement))
    return NULL;
  Py_DECREF(replacement);


  Py_DECREF(dispatch_keys);
  Py_DECREF(dispatch_values);
  Py_DECREF(pickler);
  Py_DECREF(dispatch);

  UNLESS(unpickler = PyObject_GetAttrString(pickle, "Unpickler"))
    return NULL;

  UNLESS(dispatch = PyObject_GetAttrString(unpickler, "dispatch"))
    return NULL;

  UNLESS(dispatch_keys = PyDict_Keys(dispatch))
    return NULL;

  UNLESS(dispatch_values = PyDict_Values(dispatch))
    return NULL;

  len = PyObject_Length(dispatch_keys);
  for (i = 0; i < len; i++)
  {
    UNLESS(key = PySequence_GetItem(dispatch_keys, i))
      return NULL;

    UNLESS(value = PySequence_GetItem(dispatch_values, i))
      return NULL;

    UNLESS(value_str = PyObject_GetAttrString(value, "__name__"))
      return NULL;

    UNLESS(replacement = PyObject_GetAttr(cPickle, value_str))
      return NULL;

    UNLESS(PyObject_SetItem(dispatch, key, replacement) != -1)
      return NULL;
  
    Py_DECREF(value_str);
    Py_DECREF(replacement);
  }

  Py_DECREF(unpickler);
  Py_DECREF(dispatch);
  Py_DECREF(dispatch_keys);
  Py_DECREF(dispatch_values);
}


static int
init_stuff()
{
  PyObject *builtins;

  UNLESS(pickle_module = PyImport_ImportModule("newpickle"))
    return NULL;
 
  UNLESS(whichmodule_func = 
      PyObject_GetAttrString(pickle_module, "whichmodule"))
    return NULL;

  UNLESS(sys_module = PyImport_ImportModule("sys"))
    return NULL;

  UNLESS(builtins = PyImport_ImportModule("__builtin__"))
    return NULL;

  UNLESS(id_func = PyObject_GetAttrString(builtins, "id"))
    return NULL;

  UNLESS(apply_func = PyObject_GetAttrString(builtins, "apply"))
    return NULL;

  UNLESS(eval_func = PyObject_GetAttrString(builtins, "eval"))
    return NULL;

  Py_DECREF(builtins);

  UNLESS(empty_list = PyList_New(0))
    return NULL;

  UNLESS((py_string_save  = PyString_FromString("save")) &&
         (py_string_write = PyString_FromString("write")) &&
         (py_string_stack = PyString_FromString("stack")) &&
         (py_string_memo  = PyString_FromString("memo")))
    return NULL;

  UNLESS(mark = Py_BuildValue("(c)", MARK))
    return NULL;
}
  
#define CHECK_FOR_ERRORS(MESS) \
if(PyErr_Occurred()) { \
  PyObject *__sys_exc_type, *__sys_exc_value, *__sys_exc_traceback; \
  PyErr_Fetch( &__sys_exc_type, &__sys_exc_value, &__sys_exc_traceback); \
  fprintf(stderr, # MESS ":\n\t"); \
  PyObject_Print(__sys_exc_type, stderr,0); \
  fprintf(stderr,", "); \
  PyObject_Print(__sys_exc_value, stderr,0); \
  fprintf(stderr,"\n"); \
  fflush(stderr); \
  Py_FatalError(# MESS); \
}

void
initcPickle()
{
  PyObject *m, *d;

  /* Create the module and add the functions */
  m = Py_InitModule4("cPickle", cPickle_methods,
      cPickle_module_documentation,
      (PyObject*)NULL,PYTHON_API_VERSION);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  ErrorObject = PyString_FromString("cPickle.error");
  PyDict_SetItemString(d, "error", ErrorObject);

  /* XXXX Add constants here */
  init_stuff();

  CHECK_FOR_ERRORS("can't initialize module cPickle");

  replace_pickle(pickle_module, m);

  CHECK_FOR_ERRORS("can't initialize module cPickle:  cannot replace Pickler and Unpickler methods");
}
