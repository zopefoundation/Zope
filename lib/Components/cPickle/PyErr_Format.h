/*
  PyErr_Format -- Raise an exception from C using format strings

  Arguments:

     ErrType -- The type of error to be raised

     string_format -- A Python format-string-style format used to
       create a string return value.  This argument may be NULL, in
       which case the error value will be a value built with
       Py_BuildValue using the build-format argument.

     build_format -- A PyBuild_Value format string for building a
       Python values from C objects.  If this argument is NULL, and
       string_format is not NULL, then PyErr_Format is equivalent to
       PyErr_SetString, except that a NULL value is returned.

     If both build_format and string_format are ommitted, then
     PyErr_Format uses None as the error return value. 

     The remaining arguments will be passed to PyBuildValue.

  Return

     This function always returns a NULL pointer.  This allows the
     function to be used in simple return statements.  For example, in
     a function that returns a PyObject pointer, an error may be
     raised like this::

       if(some_error_condition)
         return PyErr_Format("Something bad happened with %s at index %s",
	                     "si", some_c_string, some_int)

  
 */
PyObject *
PyErr_Format(PyObject *ErrType, char *string_format, char *build_format, ...);

/*
  PyErr_Format -- Raise an exception from C using a C format string

  Arguments:

     ErrType -- The type of error to be raised

     format -- A C format string

     The remaining arguments will be used with the C format string.

  Limitation

     The size of the formatted string must not exceed 500 characters.

  Return

     This function always returns a NULL pointer.  This allows the
     function to be used in simple return statements.  For example, in
     a function that returns a PyObject pointer, an error may be
     raised like this::

       if(some_error_condition)
         return PyErr_CFormat("Something bad happened with %s at index %d",
	                     some_c_string, some_int)

  
 */
PyObject *
PyErr_CFormat(PyObject *ErrType, char *format, ...);

