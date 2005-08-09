
#
# test for kjParseBuild module automatic parser generation
#
# lisp lists with strings, ints, vars, and setq

import string

### The string representation for the grammar.
### Since this is used only by GrammarBuild()
### it could be put in a separate file with GrammarBuild()
### to save space/load time after Grammar compilation.
###
GRAMMARSTRING ="""
       Value ::  ## indicates Value is the root nonterminal for the grammar
         @R SetqRule :: Value >> ( setq var Value )
         @R ListRule :: Value >> ( ListTail
         @R TailFull :: ListTail >> Value ListTail
         @R TailEmpty :: ListTail >> )
         @R Varrule :: Value >> var
         @R Intrule :: Value >> int
         @R Strrule :: Value >> str
"""

### the name of the file in which to create the compiled
### grammar declarations
COMPILEDFILENAME = "TESTLispG2.py"

### declare comment form(s) as regular expressions 
LISPCOMMENTREGEX = ";.*"

### declare regular expression string constants for terminals

#integer terminal::::::: 
INTREGEX = "["+string.digits+"]+"

#string terminal:::::::: 
STRREGEX = '"[^\n"]*"'

#var terminal:::::::: 
VARREGEX = "["+string.letters+"]["+string.letters+string.digits+"]*"

### declare interpretation functions for terminals

# int interpretation function: translates string to int: 
# Could use string.atoi without the extra level of indirection 
# but for demo purposes here it is.  
# 
def intInterp( str ):
   return string.atoi(str)

# interpretation function for strings strips off the surrounding quotes.  
def stripQuotes( str ):
   if len(str)<2:
      TypeError, "string too short?"
   return str[1:len(str)-1]

# interpretation function for vars just returns the recognized string
def echo(string):
   return string

# This function declares the nonterminals both in the 
# "grammar generation phase" and in loading the compiled 
# grammar after generation 
# 
def DeclareTerminals(Grammar):
   Grammar.Addterm("int", INTREGEX, intInterp)
   Grammar.Addterm("str", STRREGEX, stripQuotes)
   Grammar.Addterm("var", VARREGEX, echo)

### declare the rule reduction interpretation functions.

# EchoValue() serves for Intrule and Strrule, since 
# we just want to echo the value returned by the 
# respective terminal interpretation functions.  
# 
# Parser delivers list of form [ interpreted_value ] 
def EchoValue( list, Context ):
   if len(list)!=1:
      raise TypeError, "this shouldn't happen! (1)"
   return list[0]

# for Varrule interpreter must try to look up the value 
# in the Context dictionary 
# 
# Parser delivers list of form [ var_name ] 
def VarValue( list, Context ):
   if len(list)!=1:
      raise TypeError, "Huh? (2)"
   varName = list[0]
   if Context.has_key(varName):
      return Context[varName]
   else:
      raise NameError, "no such lisp variable in context "+varName

# for an empty tail, return the empty list 
# 
# Parser delivers list of form [")"] 
def NilTail( list, Context ):
   if len(list) != 1 or list[0] != ")":
      return TypeError, "Bad reduction?"
   return []

# For a full tail, add the new element to the front of the list 
# 
# Parser delivers list of form [Value, TailValue] 
def AddToList( list, Context ):
   if len(list) !=2:
      return TypeError, "Bad reduction?"
   return [ list[0] ] + list[1]

# For a list, simply return the list determined by the tail 
# 
# Parser delivers list of form ["(", TailValue ] 
def MakeList( list, Context ):
   if len(list)!=2 or list[0]!="(":
      raise TypeError, "Bad reduction? (3)"
   return list[1]

# For a setq, declare a new variable in the Context dictionary 
# 
# Parser delivers list of form # ["(", "setq", varName, Value, ")"] 
def DoSetq( list, Context):
   if len(list) != 5\
     or list[0] != "("\
     or list[1] != "setq"\
     or list[4] != ")":
      print list
      raise TypeError, "Bad reduction? (4)"
   VarName = list[2]
   if type(VarName) != type(''):
      raise TypeError, "Bad var name? (5)"
   Value = list[3]
   # add or set the variable in the Context dictionary
   Context[ VarName ] = Value
   return Value

# This function Binds the named rules of the Grammar string to their 
# interpretation functions in a Grammar.  
# 
def BindRules(Grammar):
    Grammar.Bind( "Intrule", EchoValue )
    Grammar.Bind( "Strrule", EchoValue )
    Grammar.Bind( "Varrule", VarValue )
    Grammar.Bind( "TailEmpty", NilTail )
    Grammar.Bind( "TailFull", AddToList )
    Grammar.Bind( "ListRule", MakeList )
    Grammar.Bind( "SetqRule", DoSetq )

# This function generates the grammar and dumps it to a file.  
# Since it will be used only once (after debugging), 
# it probably should be put in another file save memory/load-time.  
#
# the result returned is a Grammar Object that can be used 
# for testing/debugging purposes.  
#
# (maybe this should be made into a generic function?)  
def GrammarBuild():
    import kjParseBuild

    # initialize a Null compilable grammar to define
    LispG = kjParseBuild.NullCGrammar()
    
    # declare terminals for the grammar
    DeclareTerminals(LispG)

    # declare the keywords for the grammar
    # defun is not used, included here for demo purposes only
    LispG.Keywords("setq defun")

    # Declare punctuations
    # dot is not used here
    LispG.punct("().")

    # Declare Nonterms
    LispG.Nonterms("Value ListTail")

    # Declare comment forms
    LispG.comments([LISPCOMMENTREGEX])

    # Declare rules
    LispG.Declarerules(GRAMMARSTRING)

    # Compile the grammar
    LispG.Compile()

    # Write the grammar to a file except for
    # the function bindings (which must be rebound)
    outfile = open(COMPILEDFILENAME, "w")
    LispG.Reconstruct("LispG",outfile,"GRAMMAR")
    outfile.close()

    # for debugging purposes only, bind the rules
    # in the generated grammar
    BindRules(LispG)

    # return the generated Grammar
    return LispG

# this function initializes the compiled grammar from 
# generated file.  
def LoadLispG():
    import TESTLispG2
    # make sure we have most recent version (during debugging)
    reload(TESTLispG2)
    # evaluate the grammar function from generated file
    LispG = TESTLispG2.GRAMMAR()
    # bind the semantics functions
    DeclareTerminals(LispG)
    BindRules(LispG)
    return LispG

########## test grammar generation

# do generation
Dummy = GrammarBuild()

# load the grammar from the file as LispG
LispG = LoadLispG()

# declare an initial context, and do some tests.
Context = { "x":3 }
test1 = LispG.DoParse1( "()", Context)
test2 = LispG.DoParse1( "(123)", Context)
test3 = LispG.DoParse1( "(x)", Context)
test4 = LispG.DoParse1( '" a string "', Context)
test5 = LispG.DoParse1( "(setq y (1 2 3) )", Context )
test6 = LispG.DoParse1( '(setq x ("a string" "another" 0))', Context )
test7str = """
  ; this is a lisp comment
  (setq abc (("a" x)
             ("b" (setq d 12))
             ("c" y) ) ; another lisp comment
  )
"""
test7 = LispG.DoParse1( test7str, Context)
