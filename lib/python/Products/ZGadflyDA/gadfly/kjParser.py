#
# python for parser interpretation
#  Copyright Aaron Robert Watters, 1994
#

# BUGS:
# Lexical error handling is not nice
# Parse error handling is not nice
#
# Lex analysis may be slow for big grammars
# Setting case sensitivity for keywords MUST happen BEFORE
#   declaration of keywords.

import kjSet
import string
import regex
import regsub
import string

# set this flag for regression testing at each load
RUNTESTS = 0

# set this flag to enable warning for default reductions
WARNONDEFAULTS = 0

# some local constants
TERMFLAG = -1 # FLAG FOR TERMINAL
NOMATCHFLAG = -2 # FLAG FOR NO MATCH IN FSM
MOVETOFLAG = -3 # FLAG FOR "SHIFT" IN SN FSM
REDUCEFLAG = -4 # FLAG FOR REDUCTION IN FSM
TRANSFLAG = -5 # FLAG FOR TRANSIENT STATE IN FSM
KEYFLAG = -6 # FLAG FOR KEYWORD
NONTERMFLAG = -7 # FLAG FOR NONTERMINAL
TERMFLAG = -8 # FLAG FOR TERMINAL
EOFFLAG = "*" # FLAG for End of file

# set this string to the Module name (filename)
# used for dumping reconstructable objects
THISMODULE = "kjParser"

# regular expression for matching whitespace
WHITERE = "["+string.whitespace+"]+"
WHITEREGEX = regex.compile(WHITERE)

# local errors
LexTokenError = "LexTokenError" # may happen on bad string
UnkTermError = "UnkTermError" # ditto
BadPunctError= "BadPunctError" # if try to make whitespace a punct
ParseInitError = "ParseInitError" # shouldn't happen?
#EOFError # may happen on bad string
FlowError = "FlowError" # shouldn't happen!!! (bug)
#SyntaxError # may happen on bad string
#TypeError
ReductError = "ReductError" # shouldn't happen?
NondetError = "NondetError" # shouldn't happen?

# the end of file is interpreted in the lexical stream as
# a terminal...
#  this should be appended to the lexical stream:
ENDOFFILETOKEN = (TERMFLAG, EOFFLAG)

# in FSM use the following terminal to indicate eof
ENDOFFILETERM = (ENDOFFILETOKEN, EOFFLAG)

# utility function for error diagnostics
def DumpStringWindow(Str, Pos, Offset=15):
    L = []
    L.append("near ::")
    start = Pos-Offset
    end = Pos+Offset
    if start<0: start = 0
    if end>len(Str): end = len(Str)
    L.append(`Str[start:Pos]`+"*"+`Str[Pos:end]`)
    from string import join
    return join(L, "\n")

# lexical dictionary class
#   this data structure is used by lexical parser below.
#
#   basic operations:
#      LD.punctuation(string)
#         registers a string as a punctuation
#           EG: LD.punctuation(":")
#      Punctuations are treated as a special kind of keyword
#      that is recognized even when not surrounded by whitespace.
#      IE, "xend" will not be recognized as "x end", but "x;" will be
#          recognized as "x ;" if "end" is a regular keyword but
#          ";" is a punctuation.  Only single character punctuations
#          are supported (now), ie, ":=" must be recognized as
#          ":" "=" above the lexical level.
#
#      LD.comment(compiled_reg_expression)
#         registers a comment pattern
#           EG LD.comment(regex.compile("--.*\n"))
#             asks to recognize ansi/sql comments like "-- correct?\n"
#
#      LD.keyword(keyword_string, canonicalstring)
#         specifies a keyword string that should map to the canonicalstring
#         when translated to the lexical stream.
#           EG: LD.keyword("begin","BEGIN"); LD.keyword("BEGIN","BEGIN")
#            will recognize upcase or downcase begins, not mixed case.
#            (automatic upcasing is allowed below at parser level).
#
#      LD[compiled_reg_expression] = (TerminalFlag, Function) # assignment!
#         specifies a regular expression that should be associated
#         with the lexical terminal marker TerminalFlag
#           EG: LD[regex.compile("[0-9]+")] = ("integer",string.atoi)
#         the Function should be a function on one string argument
#         that interprets the matching string as a value. if None is
#         given, just the string itself will be used as the
#         interpretation.  (a better choice above would be a function
#         which "tries" atoi first and uses atol on overflow).
#      NOTE: ambiguity among regular expressions will be decided
#         arbitrarily (fix?).
#
#      LD[string] # retrieval!
#         returns ((KEYFLAG, Keywordstring), Keywordstring)
#          if the (entire) string matches a keyword or a 
#          punctuation Keywordstring.
#         otherwise returns ((TERMFLAG, Terminalname), value)
#          if the (entire) string matches the regular expression for
#          a terminal flaged by Terminalname; value is the interpreted
#          value.  TerminalFlag better be something other than
#          KEYFLAG!
#         otherwise raises an error!
#         comments not filtered here!
#
# the following additional functions are used for autodocumentation
# in declaring rules, etcetera.
#     begin = LD.keyword("begin")
#        sets variable "begin" to (KEYFLAG, "BEGIN") if
#        "begin" maps to keyword "BEGIN" in LD
#     integer = LD.terminal("integer")
#        sets variable integer to ("integer", Function)
#        if  "integer" is a registered terminal Function is
#        its associated interpretation function.
#
class LexDictionary:

  def __init__(self):
    # commentpatterns is simply a list of compiled regular expressions
    # that represent comments
    self.commentpatterns = []
    # commentstrings is used for debugging/dumping/reconstruction etc.
    self.commentstrings = []
    # punctuationlist is a string of punctuations
    self.punctuationlist = ""
    # keywordmap is a dictionary mapping recognized keyword strings
    # and punctuations to their constant representations.
    self.keywordmap = KeywordDict()
    # regexprlist is a list of triples (regex,Flag,function) mapping
    # regular expressions to their flag and interpreter function.
    self.regexprlist = []

  def Dump(self):
    print "comments = ", self.commentstrings
    print "punctuations = ", self.punctuationlist
    print "keywordmap ="
    self.keywordmap.Dump()
    print "regexprlist =", self.regexprlist

  def __getitem__(self,key):
    # try to match string to a keyword
    try:
       return self.keywordmap[key]
    except KeyError:
       # try to match a regular expression
       found = 0 # so far not found
       length = len(key)
       for triple in self.regexprlist:
          (regexpr, Flag, Function) = triple
          index = regexpr.match(key)
          if index == length:
             found = 1
             # use the function to interpret the string, if given
             if Function != None:
                value = Function(key)
             else:
                value = key
             # NONLOCAL RETURN
             return (Flag, value)
       #endfor
       raise LexTokenError, "no match for string: " + `key`
  #enddef __getitem__

  # LD.keyword("this") will make a new keyword "this" if not found
  #
  def keyword(self,str):
    # upcase the string, if needed
    if self.keywordmap.caseInsensitive:
       str = string.upper(str)
    if not self.keywordmap.has_key(str):
       # redundancy for to avoid excess construction during parsing
       token = (KEYFLAG,str)
       self.keywordmap[str] = (token,str)
    else:
       (token, str2) = self.keywordmap[str]
    return token

  # LD.terminal("this") will just look for "this"
  # LD.terminal("this", RE, F) will register a new terminal
  #   RE must be a compiled regular expression or string reg ex
  #   F must be an interpretation function
  #
  def terminal(self, string, RegExpr=None, Function=None):
    if RegExpr != None and Function != None:
       if type(RegExpr) == type(""):
          RegExpr = regex.compile(RegExpr)
       self[ RegExpr ] = ( string, Function)
    for triple in self.regexprlist:
       (regexpr,token,Function) = triple
       if token[1] == string:
          # nonlocal exit
          return token
    #endfor
    # error if no exit by now
    raise UnkTermError, "no such terminal"

  def __setitem__(self,key,value):
    if type(key) == type(''):
       # if it's a string it must be a keyword
       if self.keywordmap.caseInsensitive:
          value = string.upper(value)
          key = string.upper(key)
       self.keywordmap[key] = ( (KEYFLAG, value), value)
    else:
       # otherwise it better be a compiled regular expression (not
       #verified)
       (Name, Function) = value
       Flag = (TERMFLAG, Name)
       regexpr = key
       self.regexprlist = self.regexprlist + \
                          [ (regexpr, Flag, Function) ]

  # register a regular expression as a comment
  def comment(self, string):
    # regexpr better be a uncompiled string regular expression! (not verified)
    regexpr = regex.compile(string)
    self.commentpatterns = self.commentpatterns + [ regexpr ]
    self.commentstrings = self.commentstrings + [ string ]

  # register a string as a punctuation
  def punctuation(self,Instring):
    if type(Instring) != type("") or len(Instring)!=1:
       raise BadPunctError, "punctuation must be string of length 1"
    if Instring in string.whitespace:
       raise BadPunctError, "punctuation may not be whitespace"
    self.punctuationlist = self.punctuationlist + Instring
    return self.keyword(Instring)

  # testing and altering case sensitivity behavior
  def isCaseSensitive(self):
    return not self.keywordmap.caseInsensitive

  # setting case sensitivity MUST happen before keyword
  # declarations!
  def SetCaseSensitivity(self, Boolean):
    self.keywordmap.caseInsensitive = not Boolean

  # function to do same as __getitem__ above but looking _inside_ a string
  # instead of at the whole string
  # returns (token,skip)
  # where token is one of
  #  ((KEYFLAG,name),name) or ((TERMFLAG,termname),value)
  # and skip is the length of substring of string that matches thetoken
  def Token(self, String, StartPosition):
     finished = 0 # dummy, exit should be nonlocal
     totalOffset = 0
     while not finished:
        # flag EOF if past end of string?
        if len(String) <= StartPosition:
           return (ENDOFFILETERM, 0)
        # skip whitespace
        whitespacefound = 0
        skip = WHITEREGEX.match(String, StartPosition)
        if skip > 0:
           StartPosition = StartPosition + skip
           totalOffset = totalOffset + skip
           whitespacefound = 1
        # try to find comment, keyword, term in that order:
        # looking for comment
        commentfound = 0
        for commentexpr in self.commentpatterns:
           offset = commentexpr.match(String,StartPosition)
           if offset != -1:
              if offset<1:
                 info = DumpStringWindow(String,StartPosition)
                 raise LexTokenError, "zero length comment "+info
              commentfound = 1
              StartPosition = StartPosition + offset
              totalOffset = totalOffset + offset
        # looking for a keyword
        keypair = self.keywordmap.hasPrefix(String,StartPosition,
                      self.punctuationlist)
        if keypair != 0:
           return ( keypair[0], keypair[1] + totalOffset)
        # looking for terminal
        for (regexpr, Flag, Function) in self.regexprlist:
           offset = regexpr.match(String,StartPosition)
           if offset != -1:
              matchstring = String[StartPosition : offset+StartPosition]
              if Function != None:
                 value = Function(matchstring)
              else:
                 value = matchstring
              return ((Flag, value) , offset + totalOffset)
        if not (commentfound or whitespacefound):
           info = DumpStringWindow(String,StartPosition)
           raise LexTokenError, "Lexical parse failure "+info
     #endwhile
  #enddef
#endclass LexDictionary

# alternate, experimental implementation

class lexdictionary:

   def __init__(self):
       self.skip = ""
       self.commentstrings = []
       self.punctuationlist = ""
       self.keywordmap = KeywordDict()
       self.termlist = [] # list of (term, regex, flag, interpret_fn)
       self.uncompiled = 1 # only compile after full initialization.
       self.laststring= self.lastindex= self.lastresult = None

   def Dump(self, *k):
       raise "sorry", "not implemented"
   __getitem__ = Dump

   def keyword(self, str):
       kwm = self.keywordmap
       if kwm.caseInsensitive:
          str = string.upper(str)
       try:
          (token, str2) = kwm[str]
       except:
          token = (KEYFLAG, str)
          self.keywordmap[str] = (token,str)
       return token

   def terminal(self, str, regexstr=None, Function=None):
       if regexstr is not None:
          flag = (TERMFLAG, str)
          self.termlist.append( (str, regexstr, flag, Function) )
          return flag
       else:
          for (s,fl,fn) in self.termlist:
              if fl[1]==str:
                 return fl
              else:
                 raise UnkTermError, "no such terminal"

   __setitem__ = Dump

   def comment(self, str):
       self.commentstrings.append(str)

   def punctuation(self, Instring):
       if type(Instring) != type("") or len(Instring)!=1:
         raise BadPunctError, "punctuation must be string of length 1"
       if Instring in string.whitespace:
         raise BadPunctError, "punctuation may not be whitespace"
       self.punctuationlist = self.punctuationlist + Instring
       return self.keyword(Instring)

   def SetCaseSensitivity(self, Boolean):
       self.keywordmap.caseInsensitive = not Boolean

   def Token(self, String, StartPosition):
       # shortcut for reductions.
       if self.laststring is String and self.lastindex == StartPosition:
          #print "lastresult", self.lastresult
          return self.lastresult
       self.lastindex = StartPosition
       self.laststring = String
       #print `String[StartPosition: StartPosition+60]`

       if self.uncompiled:
          self.compile()
          self.uncompiled = None
       finished = 0
       totalOffset = 0
       skipprog = self.skipprog
       keypairfn = self.keywordmap.hasPrefix
       punctlist = self.punctuationlist
       termregex = self.termregex
       while not finished:
          #print String[StartPosition:]
          if len(String) <= StartPosition:
             result = self.lastresult = (ENDOFFILETERM, 0)
             return result
          # skip ws and comments 
          skip = skipprog.match(String, StartPosition)
          if skip>0:
             if skip==0:
                info = DumpStringWindow(String, StartPosition)
                raise LexTokenError, \
                     "zero length whitespace or comment "+info
             #print "skipping", `String[StartPosition: StartPosition+skip]`
             StartPosition = StartPosition + skip
             totalOffset = totalOffset + skip
             continue
          # look for keyword
          keypair = keypairfn(String, StartPosition, punctlist)
          if keypair!=0:
             #print "keyword", keypair
             result = self.lastresult = (keypair[0], keypair[1]+totalOffset)
             return result
          # look for terminal
          offset = termregex.match(String, StartPosition)
          if (offset>0):
             g = termregex.group
             for (term, regex, flag, fn) in self.termlist:
                 test = g(term)
                 if test:
                    #print "terminal", test
                    if fn is not None:
                       value = fn(test)
                    else:
                       value = test
                    result = self.lastresult = (
                       (flag, value), offset + totalOffset)
                    return result
          # error if we get here
          info = DumpStringWindow(String, StartPosition)
          raise LexTokenError, "Lexical token not found "+info

   def isCaseSensitive(self):
       return not self.keywordmap.caseInsensitive

   def compile(self):
       from string import joinfields, whitespace
       import regex
       skipregexen = self.commentstrings + [WHITERE]
       skipregex = "\(" + joinfields(skipregexen, "\)\|\(") + "\)"
       #print skipregex; import sys; sys.exit(1)
       self.skipprog = regex.compile(skipregex)
       termregexen = []
       termnames = []
       for (term, rgex, flag, fn) in self.termlist:
           fragment = "\(<%s>%s\)" % (term, rgex)
           termregexen.append(fragment)
           termnames.append(term)
       termregex = joinfields(termregexen, "\|")
       self.termregex = regex.symcomp(termregex)
       self.termnames = termnames

LexDictionary = lexdictionary ##### test!

# a utility class: dictionary of prefixes
#  should be generalized to allow upcasing of keyword matches
class KeywordDict:

  def __init__(self, caseInsensitive = 0):
     self.FirstcharDict = {}
     self.KeyDict = {}
     self.caseInsensitive = caseInsensitive

  def Dump(self):
     if self.caseInsensitive:
        print "  case insensitive"
     else:
        print "  case sensitive"
     keys = self.KeyDict.keys()
     print "  keyDict has ", len(keys), " elts"
     for key in keys:
        print "     ", key," maps to ",self.KeyDict[key]
     firstchars = self.FirstcharDict.keys()
     print "  firstcharDict has ", len(firstchars), " elts"
     for char in firstchars:
        print "     ", char," maps to ",self.FirstcharDict[char]

  # set item assumes value has correct case already, if case sensitive
  def __setitem__(self, key, value):
     if len(key)<1:
        raise LexTokenError, "Keyword of length 0"
     if self.caseInsensitive:
        KEY = string.upper(key)
     else:
        KEY = key
     firstchar = KEY[0:1]
     if self.FirstcharDict.has_key(firstchar):
        self.FirstcharDict[firstchar] = \
          self.FirstcharDict[firstchar] + [(KEY, value)]
     else:
        self.FirstcharDict[firstchar] = [(KEY, value)]
     self.KeyDict[KEY] = value

  # if String has a registered keyword at start position
  #  return its canonical representation and offset, else 0
  # keywords that are not punctuations should be 
  # recognized only if followed
  # by a punctuation or whitespace char
  #
  def hasPrefix(self,String,StartPosition,punctuationlist):
     First = String[StartPosition:StartPosition+1]
     fcd = self.FirstcharDict
     caseins = self.caseInsensitive
     if caseins:
        First = string.upper(First)
     if fcd.has_key(First):
        Keylist = fcd[First]
     else:
        return 0
     for (key,value) in Keylist:
           offset = len(key)
           EndPosition = StartPosition+offset
           match = String[StartPosition : EndPosition]
           if caseins:
              match = string.upper(match)
           if key == match:
              if len(key)==1 and key in punctuationlist:
                 # punctuations are recognized regardless of nextchar
                 return (value,offset)
              else:
                 # nonpuncts must have punct or whitespace following
                 #(uses punct as single char convention)
                 if EndPosition == len(String):
                    return (value, offset)
                 else:
                    nextchar = String[EndPosition]
                    if nextchar in string.whitespace\
                     or nextchar in punctuationlist:
                       return (value, offset)
     return 0 # if no exit inside for loop, fail

  def __getitem__(self,key):
     if self.caseInsensitive:
        key = string.upper(key)
     return self.KeyDict[key]

  def has_key(self,key):
     if self.caseInsensitive:
        key = string.upper(key)
     return self.KeyDict.has_key(key)
#endclass KeywordDict:

# LexStringWalker walks through a string looking for
# substrings recognized by a lexical dictionary
#
#  ERROR REPORTING NEEDS IMPROVEMENT
class LexStringWalker:

  def __init__(self, String, LexDict):
    self.Position = 0
    self.NextPosition = 0
    self.String = String
    self.LexDict = LexDict
    self.PastEOF = 0
    self.Done = 0

  def DUMP(self):
    return DumpStringWindow(self.String,self.Position)

  #reset not defined

  def more(self):
    return not self.PastEOF

  def getmember(self):
    (Token,skip) = self.LexDict.Token(self.String, self.Position)
    self.NextPosition = self.Position + skip
    if Token == ENDOFFILETERM:
       self.PastEOF = 1
    return Token

  def next(self):
    if self.Done:
       data = self.DUMP()
       raise LexTokenError, "no next past end of file "+data
    elif self.PastEOF:
       self.Done=1
    elif self.NextPosition > self.Position:
       self.Position = self.NextPosition
    else:
       dummy = self.getmember()
       if self.NextPosition <= self.Position:
          data = self.DUMP()
          raise LexTokenError, "Lexical walker not advancing "+data
       self.Position = self.NextPosition

#endclass LexStringWalker

# the parse class:
#   Based loosely on Aho+Ullman, Principles of Compiler Design, Ch.6.
#    except that they don't describe how to handle boundary
#    conditions, I made them up myself.
#
#   Note: This could be implemented using just functions; it's implemented
#    as a class to facilitate diagnostics and debugging in case of
#    failures of various sorts.
#
# a parse accepts 
#   a rule list
#
#   a lexically analysed stream with methods
#     stream.getmember()  returns the current token on the stream
#     stream.next()  moves on to next token
#     stream.more()     returns false if current token is the last token
#
#   and a FSM (finite state machine) with methods
#     FSM.root_nonTerminal
#       the nonterminal at which to start parsing
#     FSM.initial_state
#       the initial state to start at
#     FSM.successful_final_state
#       the final state to go to upon successful parse
#     FSM.map(Current_State,Current_Token)
#       returns either
#          (TERMFLAG, 0)
#             if Current_State is terminal (final or reduction).
#          (NOMATCHFLAG, 0)
#             if Current_State is nonterminal, but the Current_Token
#             and Next_Token do not lead to a valid state in the FSM
#          (MOVETOFLAG, Next_State)
#             if Current_State is nonterminal and Current_Token,
#             Next_token map to Next_State from Current_State.
#          (REDUCEFLAG, Rulenum)
#             if Current_State indicates a reduction at Current_Token
#             for rule Rule number Rule
#
#    and a Stack with methods (replaced with dictionary)
#          (init: {-1:0} )
#       Stack.Top() returns top of stack (no pop)
#          ( Stack[Stack[-1]] )
#       Stack.Push(Object)
#          ( Stack[-1]=Stack[-1]+1; Stack[Stack[-1]]=Object )
#       Stack.MakeEmpty()
#          ( Stack[-1]=0 )
#       Stack.IsEmpty()
#          ( Stack[-1] == 0 )
#       Stack.Pop()
#          ( Stack[-1] = Stack[-1]-1 )
#       stack contents created by Parser will be of form (State,Value)
#       where Value was inserted at FSM state State.
#       Value of form either (KEYFLAG, Name)
#                            (NontermName, reductionvalue)
#                         or (TerminalName, value)
#
#    and an optional parameter Evaluate which if 0 indicates that
#       rules should be evaluated, otherwise indicates that rules
#       should just be reduced and the reduction structure should
#       be used as the result of the rule
#
# rule objects must support methods
#    Rule.reduce(Stack)
#       pops off the elements corresponding to the body of the Rule
#       from the stack and returns (NewStack,Red) where NewStack is
#       the stack minus the body and Red is the result of evaluating the
#       reduction function on this instance of the rule.
#    Rule.Nonterm
#       the nonterminal at the head of the rule

class ParserObj:

  # Evaluate determines whether rules should be evaluated
  # after reductions.  Context is an argument passed to the
  # list reduction function
  #
  def __init__(self, Rulelist, Stream, FSM, Stack, \
                Evaluate=1, \
                Context=None):
    self.Rules = Rulelist
    self.LexStream = Stream
    self.FSM = FSM
    self.Stack = Stack
    self.Context = Context

    # start with empty stack, initial_state, no nonterminal
    #self.Stack[-1] = 0#   self.Stack.MakeEmpty()
    self.Stack[:] = []
    self.State = FSM.initial_state
    self.currentNonterm = None
    self.Evaluate = Evaluate

  # DoOneReduction accepts tokens from the stream and pushes
  # them onto the stack until a reduction state is reached.
  #
  # Resolve the reduction
  #
  def DoOneReduction(self):
    current=self.State
    FSM=self.FSM
    Stack = self.Stack
    Context = self.Context
    Stream = self.LexStream
    # the internal FSM.StateTokenMap dictionary is used directly here.
    STMap = FSM.StateTokenMap
    #if FSM.final_state(current):
    #   raise ParseInitError, 'trying to reduce starting at final state'

    tokenVal = Stream.getmember()
    #print "tokenVal", tokenVal
    token = tokenVal[0]

    # push the token and traverse FSM until terminal state is reached
    #(flag, nextThing) = FSM.map(current, token)
    key = (current, token)
    try:
       (flag, nextThing) = STMap[key][0]
    except KeyError:
       flag = NOMATCHFLAG

    while flag == MOVETOFLAG:
       nextState = nextThing
       #print current, " shift ", token, 
       # no sanity check, possible infinite loop

       # push current token and next state
       ThingToPush = (nextState, tokenVal)
       #print "pushing ", ThingToPush
       #Stack[-1]=Stack[-1]+1; Stack[Stack[-1]]=ThingToPush
       Stack.append(ThingToPush)
       #Stack.Push( ThingToPush )

       # move to next token, next state
       Stream.next()
       # error if end of stream
       if not Stream.more(): # optimized Stream.PastEOF (?)
          data = Stream.DUMP()
          raise EOFError, 'end of stream during parse '+data

       current = nextState
       tokenVal = Stream.getmember()
       token = tokenVal[0]
       
       #MAP = FSM.map(current,token)
       key = (current, token)
       try:
          (flag, nextThing) = STMap[key][0]
       except KeyError:
          flag = NOMATCHFLAG

    # at end of while loop we should be at a reduction state

    if flag == REDUCEFLAG:
       rulenum = nextThing
       #print current, " reduce ", token, self.Rules[rulenum]
       # normal case
       # perform reduction
       rule = self.Rules[rulenum]
       Nonterm = rule.Nonterm
       self.currentNonterm = Nonterm
       (Stack, reduct) = rule.reduce( Stack , Context )
#       self.Stack = Stack #not needed, unless stack rep changes
       GotoState = self.GotoState(rule)
       # push the Gotostate and result of rule reduction on stack
       ThingToPush = (GotoState, (Nonterm, reduct) )
       # push the result of the reduction and exit normally
       #print "pushing ", ThingToPush
       #Stack[-1]=Stack[-1]+1; Stack[Stack[-1]]=ThingToPush
       Stack.append(ThingToPush)
       #Stack.Push(ThingToPush)
       self.State=GotoState
       return 1  # normal successful completion

    # some error cases
    elif flag == NOMATCHFLAG:
       self.ParseError(current,tokenVal, "nomatch1")
    #elif FSM.final_state(current):
    #   raise BadFinalError, 'unexpected final state reached in reduction'
    else:
       data = Stream.DUMP()
       s = """
           flag = %s
           map = %s """ % (flag, FSM.map(current,token))
       data = data + s
       raise FlowError, 'unexpected else '+data
  #enddef DoOneReduction

  # compute the state to goto after a reduction is performed
  # on a rule.
  # Algorithm: determine the state at beginning of reduction
  #  and the next state indicated by the head nonterminal of the rule.
  #  special case: empty stack and root nonterminal --> success.
  #
  def GotoState(self, rule):
     FSM = self.FSM
     Stack = self.Stack
     Head = rule.Nonterm
     if len(Stack)==0: #Stack[-1]==0: #Stack.IsEmpty():
        BeforeState = FSM.initial_state
     else:
        BeforeState = Stack[-1][0] #Stack[Stack[-1]][0] #Stack.Top()[0]
     # is this right? if the stack is empty and the Head
     # is the root nonterm, then goto is final state
     if len(Stack)==0 and Head == FSM.root_nonTerminal:#Stack.isEmpty()
        Result = FSM.successful_final_state
     else:
        # consider eliminating the call to .map here? (efficiency)
        (flag, Result) = FSM.map(BeforeState, Head)
        if flag != MOVETOFLAG:
           #FSM.DUMP()
           self.ParseError(BeforeState, Head, "notmoveto")
     return Result

  def ParseError( self, State, Token, *rest):
    # make this parse error nicer (add diagnostic methods?)
    L = [""]
    L.append("*******************************")
    L.append("current state = "+`State`)
    L.append("expects: ")
    expects = ""
    for (flag,name) in self.FSM.Expects(State):
       if flag in (TERMFLAG, KEYFLAG):
          expects = expects + `name`+ ", "
    L.append(expects)
    L.append(`rest`)
    L.append("current token = " + `Token`)
    #print "Stack =", 
    #self.StackDump(5)
    #print
    from string import join
    data = self.LexStream.DUMP() + join(L, "\n")
    raise SyntaxError, 'unexpected token sequence.' + data

  def StackDump(self, N):
    Stack = self.Stack
    Topkey = len(Stack)
    if Topkey>N:
       Start = Topkey - N
    else:
       Start = 1
    for i in range(Start,Topkey+1):
       print " :: ", Stack[i],

  # execute parsing until done:
  def GO(self):
    while self.State != self.FSM.successful_final_state:
              #self.FSM.final_state(self.State):
       self.DoOneReduction()
    # should I check that stack has only one elt here?
    # return result of last reduction
    return self.Stack[-1][1] #self.Stack.Top()[1]

#endclass ParserObj

# function for declaring a variable to represent a nonterminal:
# eg Program = nonterminal("program") 
#  included for convenient autodocumentation
#
def nonterminal(string):
   return (NONTERMFLAG, string)

# declaring a terminal WITHOUT INSTALLING IT IN A LexDict
def termrep(string):
   return (TERMFLAG, string)

# the rule class
#  a rule is defined by a goal nonterminal marker of form
#    (NONTERMFLAG, Name)
#  and a list defining the body which must contain elts of form
#    (KEYFLAG, Name) or (NONTERMFLAG, Name) of (TERMFLAG, Name)
#  and a reduction function which takes a list of the same size
#  as the BodyList (consisting of the results of the evaluations of
#  the previous reductions)
#  and returns an interpretation for the body

# the following function is used as a default reduction function
# for rules
def DefaultReductFun( RuleResultsList, Context ):
   if WARNONDEFAULTS:
      print "warn: default reduction."
      print "   ", RuleResultsList
   return RuleResultsList

class ParseRule:

  def __init__(self, goalNonTerm, BodyList, \
         ReductFunction = DefaultReductFun):
     #print BodyList
     # check some of the arguments (very limited!)
     if len(goalNonTerm) != 2 or goalNonTerm[0] != NONTERMFLAG:
        raise TypeError, "goal of rule must be nonterminal"
     for m in BodyList:
        #print m
        if len(m) != 2:
           raise TypeError, "invalid body form for rule"
     self.Nonterm = goalNonTerm
     self.Body = BodyList
     self.ReductFun = ReductFunction

  # for dumping/reconstruction: LOSES THE INTERPRETATION FUNCTION!
  def __repr__(self):
     return THISMODULE + ".ParseRule" + `self.components()`

  # marshal-able components of a rule
  def components(self):
     return (self.Nonterm, self.Body)

  # rule.reduce(Stack) pops of the stack elements corresponding
  # to the body of the rule and prepares the appropriate reduction
  # object for evaluation (or not) at higher levels
  #
  def reduce(self, Stack, Context=None):
     #print "reducing", Stack
     Blength = len(self.Body)
     #print Blength, len(self.Body)
     # pop off previous results from stack corresponding to body
     BodyResults = [None] * Blength
     #BodyNames = [None] * Blength # for debug
     #print "popping: "
     for i in range(1,Blength+1):
        Bindex = Blength - i  # stack contents pop off in reverse order

        # get and destructure the rule body entry
        RuleEntry = self.Body[Bindex]
        ( REkind , REname ) = RuleEntry

        # get and destructure the stack entry
        PoppedValue = Stack[-i] #Stack.Top()
        #print PoppedValue,
        #del Stack[-1]# = Stack[-1]-1 #Stack.Pop()
        SETokVal = PoppedValue[1]
        SEvalue = SETokVal[1]
        SEname = SETokVal[0][1]

        # the names from rule and stack must match (?)
        if SEname != REname:
           print SEname, REname
           print self
           raise ReductError, " token names don't match"

        # store the values for the reduction
        BodyResults[Bindex] = SEvalue
        #BodyNames[Bindex] = SEname # debug
     #endfor
     del Stack[len(Stack)-Blength:]
     #print "reduced", Stack
     #print
     # evaluate the reduction, in context
     reduct = self.ReductFun(BodyResults, Context)
     if WARNONDEFAULTS and self.ReductFun is DefaultReductFun:
        # should check whether name is defined before this...
        print "  default used on ", self.Name
     #Reduction( self.ReductFun, BodyResults, BodyNames )
     return (Stack, reduct)
  #enddef ParseRule.reduce

#endclass ParseRule

# for debugging: look through a rule list
#  and print names of rules that have default binding
#
def PrintDefaultBindings(rulelist):
    for r in rulelist:
        if r.ReductFun is DefaultReductFun:
           print r.Name

# the FSM class
#
class FSMachine:

  def __init__(self, rootNonTerm):

    # start and success state conventions
    startState=1
    successState=0

    self.root_nonTerminal = rootNonTerm
    self.initial_state = startState
    self.successful_final_state = successState

    # the list of states of the FSM, implemented as a dictionary
    #  entries are identified by their index
    #  content is 
    #  a list whose first elt is either TRANSFLAG, or TERMFLAG
    #  other list elts may be added by other layers (parse generator)
    #  indicating the kind of the state.
    self.States = {}

    # allocate start and success states
    self.States[startState]=[TRANSFLAG]
    self.States[successState]=[TERMFLAG]

    # the most recently allocated state
    self.maxState= startState

    # the map of current token+state number to next state
    #with entries of form (tokenname,state):nextstate_sequence
    #
    self.StateTokenMap = {}
  #enddef FSM()

  # ForbiddenMark is for filtering out maps to an error state
  def DUMP(self, DumpMapData=1, DumpStateData=1, ForbiddenMark={}):
    print "root nonterminal is ", self.root_nonTerminal
    print "start at ", self.initial_state
    print "end at ", self.successful_final_state
    print "number of states: ", self.maxState
    if DumpStateData:
       print
       for State in range(0,self.maxState+1):
          Data = self.States[State]
          print State, ": ", Data
    if DumpMapData:
       print
       for key in self.StateTokenMap.keys():
          map = self.StateTokenMap[key]
          if map[0][0] == MOVETOFLAG:
             ToStateData = self.States[map[0][1]]
             if len(ToStateData) < 2:
                Mark = None
             else:
                Mark = ToStateData[1]
             if Mark != ForbiddenMark:
                print key, " --> ", map, " = ", ToStateData
          else:
             print key, " --> reduction to rule number ", map[0][1]

  # what tokens does a state expect?
  def Expects(self, State):
    keys = self.StateTokenMap.keys()
    Tokens = kjSet.NewSet( [] )
    for (state1,token) in keys:
       if State == state1:
          kjSet.addMember(token,Tokens)
    return kjSet.get_elts(Tokens)

  # "allocate" a new state of specified kind
  #   kind must either be TRANSFLAG, TERMFLAG or a rule object
  # returns the number of the new state
  def NewState(self, kind, AdditionalInfo = []):
    if not kind in (TRANSFLAG,TERMFLAG,REDUCEFLAG):
       raise TypeError, "unknown state kind"
    available = self.maxState+1

    self.States[available] = [kind] + AdditionalInfo
    self.maxState = available
    return available

  # Install a reduction transition in the FSM:
  # a reduction is represented by mapping to a rule index
  # no nondeterminism is allowed.
  def SetReduction(self, fromState, TokenRep, Rulenum):
    key = (fromState, TokenRep)
    if not self.StateTokenMap.has_key(key):
       self.StateTokenMap[ key ] = ((REDUCEFLAG, Rulenum),)
    else:
       raise ReductError, "attempt to set ambiguous reduction"

  # Install a "shift" or "goto transition in the FSM:
  # supports nondeterminism by storing a sequence of possible transitions
  #
  def SetMap(self, fromState, TokenRep, toState): 
    key = (fromState, TokenRep)
    if self.StateTokenMap.has_key(key):
       Old = self.StateTokenMap[key]
       if Old[0][0] != MOVETOFLAG:
          # if the old value was not an integer, not a "normal state":
          # complain:
          raise NondetError, \
            "attempt to make inappropriate transition ambiguous"
       self.StateTokenMap[ key ] = Old + ((MOVETOFLAG,toState),)
    else:
       self.StateTokenMap[ key ] = ((MOVETOFLAG,toState),)

  # Find the action indicated by fsm on 
  #  (current_state, current_token) input.
  #
  # note: in the event of nondeterministic choice this chooses
  #   the first possibility listed.
  # ParseObj.DoOneReduction() currently uses the internal structure
  #  of StateTokenMap directly, rather than using this function.
  #
  def map(self, current_state, current_token):
    StateEntry = self.States[current_state][0]
    if StateEntry == TERMFLAG:
       return (TERMFLAG, 0)
    elif StateEntry == TRANSFLAG:
       # try to find a transition for this token and state
       key = (current_state, current_token)
       try:
          TMap = self.StateTokenMap[key]
          #print "TMap ", TMap
          #print "key ", key
          #print
          return TMap[0]
       except KeyError:
          return (NOMATCHFLAG, 0)
    else:
       raise FlowError, "unexpected else (2)"
  #enddef map

#endclass FSMachine

# the grammar class:
#   a grammar consists of 
#     - a LexDict lexical dictionary;
#     - a deterministic FSMachine;
#     - a Rulelist
#   and optionally a dictionary that maps Rulenames
#   to Rulelist indices (used for dumping and externally)
#   
class Grammar:

   def __init__(self, LexD, DFA, RuleL, RuleNameDict = None):
      # for auto initialization set LexD,DFA,RuleL to None
      if LexD == None and DFA == None and RuleL == None:
         self.LexD = LexDictionary()
         # use a dummy root nonterminal -- must fix elsewhere!
         self.DFA = FSMachine("ERROR")
         self.RuleL = []
      else:
         self.LexD = LexD
         self.DFA = DFA
         self.RuleL = RuleL
      if RuleNameDict != None:
         self.AddNameDict(RuleNameDict)
      self.CleanUp()
   #enddef __init__

   # look for default bindings
   def PrintDefaults(self):
       print "Default bindings on:"
       PrintDefaultBindings(self.RuleL)

   # setting case sensitivity: must happen before keyword installation
   # in LexD.
   def SetCaseSensitivity( self, Boolean ):
      self.LexD.SetCaseSensitivity( Boolean )

   # this may be silly, but to save some space in construction
   # a token dictionary may be used that facilitates sharing of
   # token representations.  This method either initializes
   # the dictionary or disposes of it if it exists
   def CleanUp(self):
      self.IndexToToken = {}
      # this dictionary is used by automatically
      # generated grammars to determine whether
      # a string represents a nonterminal
      self.NonTermDict = {}
      # similarly for terminals
      self.TermDict = {}
      # this string may be used to keep a printable
      # representation of the rules of the grammar
      # (usually in automatic grammar generation
      self.RuleString = ""

   # to associate a token to an integer use
   # self.IndexToToken[int] = tokenrep

   # this method associates rules to names using a
   # RuleNameDict dictionary which maps names to rule indices.
   # after invocation
   #   self.RuleNameToIndex[ name ] gives the index
   #     in self.RuleL for the rule associated with name, and
   #   self.RuleL[index].Name gives the name associated
   #     with the rule self.RuleL[index]
   #
   def AddNameDict(self, RuleNameDict):
     self.RuleNameToIndex = RuleNameDict
     # add a Name attribute to the rules of the rule list
     for ruleName in RuleNameDict.keys():
        index = RuleNameDict[ ruleName ]
        self.RuleL[ index ].Name = ruleName

   # parse a string using the grammar, return result and context
   def DoParse( self, String, Context = None, DoReductions = 1 ):
     # construct the ParserObj
     Stream = LexStringWalker( String, self.LexD )
     Stack = [] # {-1:0} #Walkers.SimpleStack()
     ParseOb = ParserObj( self.RuleL, Stream, self.DFA, Stack, \
                         DoReductions, Context )
     # do the parse
     ParseResult = ParseOb.GO()
     # return final result of reduction and the context
     return (ParseResult[1], Context)
   #enddef DoParse

   # parse a string using the grammar, but only return
   # the result of the last reduction, without the context
   def DoParse1( self, String, Context=None, DoReductions=1 ):
       return self.DoParse(String, Context, DoReductions)[0]

   # if the Name dictionary has been initialized
   # this method will (re)bind a reduction function to
   # a rule associated with Rulename	
   #
   def Bind( self, Rulename, NewFunction ):
     ruleindex = self.RuleNameToIndex[ Rulename ]
     rule = self.RuleL[ ruleindex ]
     rule.ReductFun = NewFunction
   #enddef Bind

   # bind a terminal to a regular expression and interp function
   # in the lexical dictionary (convenience)
   def Addterm( self, termname, regexpstr, funct ):
     self.TermDict[ termname ] =\
         self.LexD.terminal( termname, regexpstr, funct )
#endclass Grammar

# function to create a "null grammar"
def NullGrammar():
   return Grammar(None,None,None,{})

# unmarshalling a marshalled grammar created by
#   buildmodule.CGrammar.MarshalDump(Tofile)
#   tightly coupled with buildmodule code...
# file should be open and "pointing to" the marshalled rep.
#
# warning: doesn't bind semantics!
#
def UnMarshalGram(file):
    Grammar = NullGrammar()
    UnMarshal = UnMarshaller(file, Grammar)
    UnMarshal.MakeLex()
    UnMarshal.MakeRules()
    UnMarshal.MakeTransitions()
    UnMarshal.Cleanup()
    return UnMarshal.Gram

# unmarshalling object for unmarshalling grammar from a file
#
class UnMarshaller:

   def __init__(self, file, Grammar):
      import marshal
      self.Gram = Grammar
      BigList = marshal.load(file)
      if type(BigList) != type([]):
         raise FlowError, "bad type for unmarshalled list"
      if len(BigList) != 9:
         raise FlowError, "unmarshalled list of wrong size"
      self.tokens = BigList[0]
      self.punct = BigList[1]
      self.comments = BigList[2]
      self.RuleTups = BigList[3]
      self.MaxStates = BigList[4]
      self.reducts = BigList[5]
      self.moveTos = BigList[6]
      self.Root = BigList[7]
      self.CaseSensitivity = BigList[8]
      
      Grammar.SetCaseSensitivity( self.CaseSensitivity )

   def MakeLex(self):
      Grammar=self.Gram
      LexD = Grammar.LexD
      # punctuations
      LexD.punctuationlist = self.punct
      # comments
      for commentregex in self.comments:
          LexD.comment(commentregex)
      #LexD.commentstring = self.comments
      # keywords, terminals, nonterms
      #   rewrite the tokens list for sharing and extra safety
      LexTokens = {}
      tokens = self.tokens
      for tokenindex in range(len(tokens)):
          (kind,name) = tokens[tokenindex]
          if kind == KEYFLAG:
             tokens[tokenindex] = LexD.keyword(name)
          elif not kind in [TERMFLAG, NONTERMFLAG]:
             raise FlowError, "unknown token type"
      # not needed
      self.tokens = tokens

   def MakeRules(self):
      Grammar = self.Gram
      Grammar.DFA.root_nonTerminal = self.Root
      NameIndex = Grammar.RuleNameToIndex
      RuleTuples = self.RuleTups
      nRules = len(RuleTuples)
      RuleList = [None] * nRules
      for index in range(nRules):
         (Name, Components) = RuleTuples[index]
         rule = apply(ParseRule, Components)
         rule.Name = Name
         RuleList[index] = rule
         NameIndex[Name] = index
      Grammar.RuleL = RuleList

   def MakeTransitions(self):
      Grammar = self.Gram
      DFA = Grammar.DFA
      StateTokenMap = DFA.StateTokenMap
      tokens = self.tokens
      # record the state number
      DFA.maxState = self.MaxStates
      # this is historical, unfortunately...  CLEAN IT UP SOMEDAY!
      # THE DFA.States DICT IS NOT NEEDED (?) (here)
      for state in range(1, self.MaxStates+1):
         DFA.States[state] = [TRANSFLAG]
      # record the reductions
      for (fromState, TokenIndex, rulenum) in self.reducts:
         DFA.SetReduction(fromState, tokens[TokenIndex], rulenum)
      # record the transitions
      for (fromState, TokenIndex, ToState) in self.moveTos:
         DFA.SetMap(fromState, tokens[TokenIndex], ToState)

   def Cleanup(self):
      Grammar = self.Gram
      Grammar.CleanUp()

################# FOLLOWING CODE IS FOR REGRESSION TESTING ONLY
################# DELETE IT IF YOU WANT/NEED
#### All tests for this module deleted, since
#### ParseBuild module tests are sufficient.  
