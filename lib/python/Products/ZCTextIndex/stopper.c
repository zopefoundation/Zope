/*****************************************************************************

  Copyright (c) 2002 Zope Corporation and Contributors.
  All Rights Reserved.
  
  This software is subject to the provisions of the Zope Public License,
  Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE
  
 ****************************************************************************/

/*  stopper.c
 *
 *  Fast version of the StopWordRemover object.
 */

#include "Python.h"
#include "structmember.h"

typedef struct {
    PyObject_HEAD
    PyObject *swr_dict;
} StopWordRemover;

static PyObject *
swr_process(StopWordRemover *self, PyObject *args)
{
    PyObject *result = NULL;
    PyObject *seq;
    int len, i;

    if (!PyArg_ParseTuple(args, "O:process", &seq))
        return NULL;
    seq = PySequence_Fast(seq,
                          "process() requires a sequence as the argument");
    if (seq == NULL)
        return NULL;
    result = PyList_New(0);
    if (result == NULL)
        goto finally;
#if PY_VERSION_HEX >= 0x02020000
    /* Only available in Python 2.2 and newer. */
    len = PySequence_Fast_GET_SIZE(seq);
#else
    len = PyObject_Length(seq);
#endif
    for (i = 0; i < len; ++i) {
        PyObject *s = PySequence_Fast_GET_ITEM(seq, i);
        /*
         * PyDict_GetItem() returns NULL if there isn't a matching
         * item, but without setting an exception, so this does what
         * we want.
         */
        if (PyDict_GetItem(self->swr_dict, s) == NULL)
            if (PyList_Append(result, s) < 0) {
                Py_DECREF(result);
                result = NULL;
                goto finally;
            }
    }
 finally:
    Py_XDECREF(seq);
    return result;
}

static struct memberlist swr_members[] = {
    {"dict",  T_OBJECT,  offsetof(StopWordRemover, swr_dict),  READONLY},
    {NULL}
};

static PyMethodDef swr_methods[] = {
    {"process", (PyCFunction)swr_process, METH_VARARGS,
     "process([str, ...]) --> [str, ...]\n"
     "Remove stop words from the input list of strings to create a new list."},
    {NULL}
};

static PyObject *
swr_getattr(PyObject *self, char *name)
{
    PyObject *res;

    res = Py_FindMethod(swr_methods, self, name);
    if (res != NULL)
        return res;
    PyErr_Clear();
    return PyMember_Get((char *)self, swr_members, name);
}

static void
swr_dealloc(StopWordRemover *self)
{
    Py_XDECREF(self->swr_dict);
    PyObject_Del(self);
}

static PyTypeObject StopWordRemover_Type = {
    PyObject_HEAD_INIT(NULL)    /* ob_type      */
    0,                          /* ob_size      */
    "stopper.StopWordRemover",  /* tp_name      */
    sizeof(StopWordRemover),    /* tp_basicsize */
    0,                          /* tp_itemsize  */
    (destructor)swr_dealloc,    /* tp_dealloc   */
    0,                          /* tp_print     */
    (getattrfunc)swr_getattr,   /* tp_getattr   */
    0,                          /* tp_setattr   */
};

static PyObject *
swr_new(PyObject *notused, PyObject *args)
{
    StopWordRemover *swr = NULL;
    PyObject *dict = NULL;

    if (PyArg_ParseTuple(args, "|O!:new", &PyDict_Type, &dict)) {
        swr = PyObject_New(StopWordRemover, &StopWordRemover_Type);
        if (swr != NULL) {
            if (dict != NULL) {
                Py_INCREF(dict);
                swr->swr_dict = dict;
            }
            else {
                swr->swr_dict = PyDict_New();
                if (swr->swr_dict == NULL) {
                    Py_DECREF(swr);
                    swr = NULL;
                }
            }
        }
    }
    return (PyObject *) swr;
}

static PyObject*
pickle_constructor = NULL;

PyObject *
swr_pickler(PyObject *unused, PyObject *args)
{
    StopWordRemover *swr;
    PyObject *result = NULL;

    if (PyArg_ParseTuple(args, "O!:_pickler", &StopWordRemover_Type, &swr)) {
        result = Py_BuildValue("O(O)", pickle_constructor, swr->swr_dict);
    }
    return result;
}

static PyMethodDef stopper_functions[] = {
    {"new",      swr_new,     METH_VARARGS,
     "new() -> StopWordRemover instance\n"
     "Create & return a new stop-word remover."},
    {"_pickler", swr_pickler, METH_VARARGS,
     "_pickler(StopWordRemover instance) -> pickle magic\n"
     "Internal magic used to make stop-word removers picklable."},
    {NULL}
};

void
initstopper(void)
{
    PyObject *m, *copy_reg;

    StopWordRemover_Type.ob_type = &PyType_Type;
    m = Py_InitModule3("stopper", stopper_functions,
                       "Fast StopWordRemover implementation.");
    if (m == NULL)
        return;
    if (PyObject_SetAttrString(m, "StopWordRemoverType",
                               (PyObject *) &StopWordRemover_Type) < 0)
        return;

    /* register to support pickling */
    copy_reg = PyImport_ImportModule("copy_reg");
    if (copy_reg != NULL) {
        PyObject *pickler;

        if (pickle_constructor == NULL) {
            pickle_constructor = PyObject_GetAttrString(m, "new");
            Py_XINCREF(pickle_constructor);
        }
        pickler = PyObject_GetAttrString(m, "_pickler");
        if ((pickle_constructor != NULL) && (pickler != NULL)) {
            PyObject *res;

            res = PyObject_CallMethod(
                    copy_reg, "pickle", "OOO", &StopWordRemover_Type,
                    pickler, pickle_constructor);
            Py_XDECREF(res);
        }
        Py_DECREF(copy_reg);
    }
}
