#include <Python.h>

/* This helper only works for Python 2.2.  If using an older version, crap
 * out now so we don't leave a broken, but compiled and importable module
 * laying about.
 */
#if PY_VERSION_HEX < 0x020200F0
#error "Must be using at least Python 2.2"
#endif

static PyObject*
helper_incr(PyObject* self, PyObject* args)
{
    PyObject *pylong, *incr, *sum;
    char *s, x[8];
    int len, res;

    if (!PyArg_ParseTuple(args, "s#O:incr", &s, &len, &incr))
        return NULL;

    assert(len == 8);

    /* there seems to be no direct route from byte array to long long, so
     * first convert it to a PyLongObject*, then convert /that/ thing to a
     * long long
     */
    pylong = _PyLong_FromByteArray(s, len,
                                   0 /* big endian */, 0 /* unsigned */);
    
    if (!pylong)
        return NULL;

    sum = PyNumber_Add(pylong, incr);
    if (!sum)
        return NULL;

    res = _PyLong_AsByteArray((PyLongObject*)sum, x, 8,
                              0 /* big endian */, 0 /* unsigned */);
    if (res < 0)
        return NULL;

    return PyString_FromStringAndSize(x, 8);
}


static PyMethodDef helper_methods[] = {
    {"incr", helper_incr, METH_VARARGS},
    {NULL, NULL}                             /* sentinel */
};


DL_EXPORT(void)
init_helper(void)
{
    (void)Py_InitModule("_helper", helper_methods);
}
