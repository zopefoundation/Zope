"""Interface that a TALES engine provides to the METAL/TAL implementation."""

try:
    from Interface import Interface
    from Interface.Attribute import Attribute
except:
    # Before 2.7
    class Interface: pass
    def Attribute(*args): pass


class ITALESCompiler(Interface):
    """Compile-time interface provided by a TALES implementation.

    The TAL compiler needs an instance of this interface to support
    compilation of TALES expressions embedded in documents containing
    TAL and METAL constructs.
    """

    def getCompilerError():
        """Return the exception class raised for compilation errors.
        """

    def compile(expression):
        """Return a compiled form of 'expression' for later evaluation.

        'expression' is the source text of the expression.

        The return value may be passed to the various evaluate*()
        methods of the ITALESEngine interface.  No compatibility is
        required for the values of the compiled expression between
        different ITALESEngine implementations.
        """


class ITALESEngine(Interface):
    """Render-time interface provided by a TALES implementation.

    The TAL interpreter uses this interface to TALES to support
    evaluation of the compiled expressions returned by
    ITALESCompiler.compile().
    """

    def getCompiler():
        """Return an object that supports ITALESCompiler."""

    def getDefault():
        """Return the value of the 'default' TALES expression.

        Checking a value for a match with 'default' should be done
        using the 'is' operator in Python.
        """

    def setPosition((lineno, offset)):
        """Inform the engine of the current position in the source file.

        This is used to allow the evaluation engine to report
        execution errors so that site developers can more easily
        locate the offending expression.
        """

    def setSourceFile(filename):
        """Inform the engine of the name of the current source file.

        This is used to allow the evaluation engine to report
        execution errors so that site developers can more easily
        locate the offending expression.
        """

    def beginScope():
        """Push a new scope onto the stack of open scopes.
        """

    def endScope():
        """Pop one scope from the stack of open scopes.
        """

    def evaluate(compiled_expression):
        """Evaluate an arbitrary expression.

        No constraints are imposed on the return value.
        """

    def evaluateBoolean(compiled_expression):
        """Evaluate an expression that must return a Boolean value.
        """

    def evaluateMacro(compiled_expression):
        """Evaluate an expression that must return a macro program.
        """

    def evaluateStructure(compiled_expression):
        """Evaluate an expression that must return a structured
        document fragment.

        The result of evaluating 'compiled_expression' must be a
        string containing a parsable HTML or XML fragment.  Any TAL
        markup cnotained in the result string will be interpreted.
        """

    def evaluateText(compiled_expression):
        """Evaluate an expression that must return text.

        The returned text should be suitable for direct inclusion in
        the output: any HTML or XML escaping or quoting is the
        responsibility of the expression itself.
        """

    def evaluateValue(compiled_expression):
        """Evaluate an arbitrary expression.

        No constraints are imposed on the return value.
        """

    def createErrorInfo(exception, (lineno, offset)):
        """Returns an ITALESErrorInfo object.

        The returned object is used to provide information about the
        error condition for the on-error handler.
        """

    def setGlobal(name, value):
        """Set a global variable.

        The variable will be named 'name' and have the value 'value'.
        """

    def setLocal(name, value):
        """Set a local variable in the current scope.

        The variable will be named 'name' and have the value 'value'.
        """

    def setRepeat(name, compiled_expression):
        """
        """

    def translate(domain, msgid, mapping, default=None):
        """
        See ITranslationService.translate()
        """


class ITALESErrorInfo(Interface):

    type = Attribute("type",
                     "The exception class.")

    value = Attribute("value",
                      "The exception instance.")

    lineno = Attribute("lineno",
                       "The line number the error occurred on in the source.")

    offset = Attribute("offset",
                       "The character offset at which the error occurred.")
