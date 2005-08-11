# Grammar generation 
# for lisp lists with strings, ints, vars, print, and setq

# set this variable to regenerate the grammar on each load
REGENERATEONLOAD = 1

import string
GRAMMARSTRING ="""
       Value ::  ## indicates Value is the root nonterminal for the grammar
         @R SetqRule :: Value >> ( setq var Value )
         @R ListRule :: Value >> ( ListTail
         @R TailFull :: ListTail >> Value ListTail
         @R TailEmpty :: ListTail >> )
         @R Varrule :: Value >> var
         @R Intrule :: Value >> int
         @R Strrule :: Value >> str
         @R PrintRule :: Value >> ( print Value )
"""
COMPILEDFILENAME = "TESTLispG.py"
MARSHALLEDFILENAME = "TESTLispG.mar"
LISPCOMMENTREGEX = ";.*"
INTREGEX = "["+string.digits+"]+"
STRREGEX = '"[^\n"]*"'
VARREGEX = "["+string.letters+"]["+string.letters+string.digits+"]*"

### declare interpretation functions and regex's for terminals
def intInterp( str ):
    return string.atoi(str)
def stripQuotes( str ):
    return str[1:len(str)-1]
def echo(string):
    return string
def DeclareTerminals(Grammar):
    Grammar.Addterm("int", INTREGEX, intInterp)
    Grammar.Addterm("str", STRREGEX, stripQuotes)
    Grammar.Addterm("var", VARREGEX, echo)

### declare the rule reduction interpretation functions.
def EchoValue( list, Context ):
    return list[0]
def VarValue( list, Context ):
    varName = list[0]
    if Context.has_key(varName):
       return Context[varName]
    else:
       raise NameError, "no such lisp variable in context "+varName
def NilTail( list, Context ):
    return []
def AddToList( list, Context ):
    return [ list[0] ] + list[1]
def MakeList( list, Context ):
    return list[1]
def DoSetq( list, Context):
    Context[ list[2] ] = list[3]
    return list[3]
def DoPrint( list, Context ):
    print list[2]
    return list[2]
def BindRules(Grammar):
    Grammar.Bind( "Intrule", EchoValue )
    Grammar.Bind( "Strrule", EchoValue )
    Grammar.Bind( "Varrule", VarValue )
    Grammar.Bind( "TailEmpty", NilTail )
    Grammar.Bind( "TailFull", AddToList )
    Grammar.Bind( "ListRule", MakeList )
    Grammar.Bind( "SetqRule", DoSetq )
    Grammar.Bind( "PrintRule", DoPrint )

# This function generates the grammar and dumps it to a file.  
def GrammarBuild():
    import kjParseBuild
    LispG = kjParseBuild.NullCGrammar()
    LispG.SetCaseSensitivity(0) # grammar is not case sensitive for keywords
    DeclareTerminals(LispG)
    LispG.Keywords("setq print")
    LispG.punct("().")
    LispG.Nonterms("Value ListTail")
    LispG.comments([LISPCOMMENTREGEX])
    LispG.Declarerules(GRAMMARSTRING)
    LispG.Compile()

    print "dumping as python to "+COMPILEDFILENAME
    outfile = open(COMPILEDFILENAME, "w")
    LispG.Reconstruct("LispG",outfile,"GRAMMAR")
    outfile.close()

    print "dumping as binary to "+MARSHALLEDFILENAME
    outfile = open(MARSHALLEDFILENAME, "w")
    LispG.MarshalDump(outfile)
    outfile.close()

    BindRules(LispG)
    return LispG

# this function initializes the compiled grammar from the generated file.  
def LoadLispG():
    import TESTLispG
    # reload to make sure we get the most recent version!
    # (only needed when debugging the grammar).
    reload(TESTLispG)
    LispG = TESTLispG.GRAMMAR()
    DeclareTerminals(LispG)
    BindRules(LispG)
    return LispG

def unMarshalLispG():
    import kjParser
    infile = open(MARSHALLEDFILENAME, "r")
    LispG = kjParser.UnMarshalGram(infile)
    infile.close()
    DeclareTerminals(LispG)
    BindRules(LispG)
    return LispG

########## test the grammar generation
if REGENERATEONLOAD:
   print "(re)generating the LispG grammar in file TESTLispG.py"
   Dummy = GrammarBuild()
   print "(re)generation done."

print "loading grammar as python"
LispG = LoadLispG()
### declare an initial context, and do some tests.
Context = { 'x':3 }
test1 = LispG.DoParse1( '()', Context)
test2 = LispG.DoParse1( '(123)', Context)
test3 = LispG.DoParse1( '(x)', Context)
test4 = LispG.DoParse1( '" a string "', Context)
test5 = LispG.DoParse1( '(setq y (1 2 3) )', Context )
test6 = LispG.DoParse1( '(SeTq x ("a string" "another" 0))', Context )
test7str = """
  ; this is a lisp comment
  (setq abc (("a" x)
             ("b" (setq d 12))
             ("c" y) ) ; another lisp comment
  )
"""
test7 = LispG.DoParse1( test7str, Context)
test8 = LispG.DoParse1( '(print (1 x d))', Context)

print "unmarshalling the grammar"
LispG2 = unMarshalLispG()
### declare an initial context, and do some tests.
Context = { 'x':3 }
test1 = LispG2.DoParse1( '()', Context)
test2 = LispG2.DoParse1( '(123)', Context)
test3 = LispG2.DoParse1( '(x)', Context)
test4 = LispG2.DoParse1( '" a string "', Context)
test5 = LispG2.DoParse1( '(setq y (1 2 3) )', Context )
test6 = LispG2.DoParse1( '(SeTq x ("a string" "another" 0))', Context )
test7str = """
  ; this is a lisp comment
  (setq abc (("a" x)
             ("b" (setq d 12))
             ("c" y) ) ; another lisp comment
  )
"""
test7 = LispG2.DoParse1( test7str, Context)
test8 = LispG2.DoParse1( '(print (1 x d))', Context)

