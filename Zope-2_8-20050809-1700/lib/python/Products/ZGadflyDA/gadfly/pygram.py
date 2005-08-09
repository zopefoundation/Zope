# rules for python
# based on grammar given in Programming Python by Mark Lutz

# EDIT THIS: THE DIRECTORY IN WHICH TO MARSHAL THE
# GRAMMAR DATA STRUCTURES.
#
ARCHIVE = "."  

marshalfilename = ARCHIVE + "/pygram.mar"

pyrules = """

all ::

## input terminates with "fake" dedent (forces read of all file)

@R all1 :: all >> file_input DEDENT

## 1 term newline

##@R lead_blank :: file_input >> NEWLINE file_input

@R top_stmt :: file_input >> file_input stmt
@R file_input :: file_input >> stmt


## 2
@R simple :: stmt >> simple_stmt
@R compound :: stmt >> compound_stmt

## 3 punct ; term NEWLINE
@R one_small :: simple_stmt >> small_stmt NEWLINE
@R more_small :: simple_stmt >> small_stmt ; simple_stmt
@R small_semi :: simple_stmt >> small_stmt ; NEWLINE

## 4 kw pass
@R smexpr :: small_stmt >> expr_stmt
@R smassn :: small_stmt >> assn
@R smprint :: small_stmt >> print_stmt
@R smdel :: small_stmt >> del_stmt
@R smpass :: small_stmt >> pass
@R smflow :: small_stmt >> flow_stmt
@R smimport :: small_stmt >> import_stmt
@R smglobal :: small_stmt >> global_stmt
## access ignored
@R smexec :: small_stmt >> exec_stmt

## 5
@R cmif :: compound_stmt >> if_stmt
@R cmwhile :: compound_stmt >> while_stmt
@R cmfor :: compound_stmt >> for_stmt
@R cmtry :: compound_stmt >> try_stmt
@R cmdef :: compound_stmt >> funcdef
@R cmclass :: compound_stmt >> classdef

##6
@R exprlist :: expr_stmt >> testlist
##@R assignment :: expr_stmt >> assn
@R assn1 :: assn >> testlist = testlist

@R assnn :: assn >> testlist = assn

@R assn1c :: assn >> testlist , = testlist

@R assn1c2 :: assn >> testlist , = testlist ,

@R assnnc :: assn >> testlist , = assn

##testing @R exprassn :: expr_stmt >> expr_stmt = testlist 

@R exprlistc :: expr_stmt >> testlist ,

##testing @R exprassnc :: expr_stmt >> expr_stmt = testlist ,

##7 kw print
@R rprint0 :: print_stmt >> print
@R rprint :: print_stmt >> print testlist 
@R rprintc :: print_stmt >> print testlist ,

##8 kw del
@R rdel :: del_stmt >> del exprlist

##9 trivially handled in #4

##10 kw raise continue break return

## eliminates 11 12 13 14
@R rbreak  :: flow_stmt >> break
@R rcontinue :: flow_stmt >> continue
@R rreturn0 :: flow_stmt >> return
@R rreturn :: flow_stmt >> return testlist 
@R rreturnc :: flow_stmt >> return testlist ,
@R rraise1 :: flow_stmt >> raise test
@R rraise2 :: flow_stmt >> raise test , test
@R rraise3 :: flow_stmt >> raise test , test , test

## 11 12 13 14 skipped

## 15 kw import from
@R rimport :: import_stmt >> import dotted_name_list 
@R rimportc :: import_stmt >> import dotted_name_list ,
@R dnlist1 :: dotted_name_list >> dotted_name
@R dnlistn :: dotted_name_list >> dotted_name_list , dotted_name
@R rfrom :: import_stmt >> from dotted_name import name_list 
@R rfroms :: import_stmt >> from dotted_name import *
@R rfromc :: import_stmt >> from dotted_name import name_list ,
@R nlistn :: name_list >> name_list  , NAME
@R nlist1 :: name_list >> NAME

##16 nt NAME
@R dn1 :: dotted_name >> NAME
@R dnn :: dotted_name >> dotted_name . NAME

##17 kw global
@R global1 :: global_stmt >> global NAME 
@R globaln :: global_stmt >> global_stmt , NAME 

## 18 19 ignored

##20 kw exec in
@R exec1 :: exec_stmt >> exec expr
@R exec2 :: exec_stmt >> exec expr in test
@R exec3 :: exec_stmt >> exec expr in test , test

##21  kw if elif else punct :
@R ifr :: if_stmt >> if test : suite elifs
@R elifs0 :: elifs >>
@R relse :: elifs >> else : suite
@R elifsn :: elifs >> elif test : suite elifs

##22 kw while
@R while1 :: while_stmt >> 
while test : 
    suite
@R while2 :: while_stmt >> 
while test : 
   suite 
else : 
   suite

##23 kw for
@R for1 :: for_stmt >> 
for exprlist in testlist  : 
     suite
@R for2 :: for_stmt >> 
for exprlist in testlist  : 
     suite 
else : 
     suite

##24 kw try
@R tryr :: try_stmt >> try : suite excepts
@R excepts1 :: excepts >> except_clause : suite
@R excepts2 :: excepts >> except_clause : suite else : suite
@R exceptsn :: excepts >> except_clause : suite excepts
@R tryf :: try_stmt >> try : suite finally : suite

##25 kw except
@R except0 :: except_clause >> except 
@R except1 :: except_clause >> except test
@R except2 :: except_clause >> except test , test

##26
@R class1 :: classdef  >> class NAME : suite
@R class2 :: classdef  >> class NAME ( testlist ) : suite

##27 kw def
@R rdef :: funcdef >> def NAME parameters : suite

##28, 29 punct = * 

## (modified from grammar presented)
@R params1 :: parameters >> ( varargslist )
@R params1c :: parameters >> ( varargslist , )
@R params2 :: varargslist >> 

## this is way too permissive: fix at semantic level
@R params3 :: varargslist >> arg
@R params4 :: varargslist >> varargslist , arg
@R argd :: arg >> NAME = test
@R arg2 :: arg >> fpdef
@R arg3 :: arg >> * NAME
@R arg4 :: arg >> ** NAME

## 30
@R fpdef1 :: fpdef  >> NAME
@R fpdef2 :: fpdef  >>  ( fplist )
@R fpdef2c :: fpdef  >>  ( fplist , )

##31
@R fplist1 :: fplist >> fpdef
@R fplistn :: fplist >> fplist , fpdef

##32 t INDENT DEDENT
@R ssuite :: suite >> simple_stmt
@R csuite :: suite >> NEWLINE INDENT stmtseq DEDENT
@R stmtseq1 :: stmtseq >> stmt
@R stmtseqn :: stmtseq >> stmtseq stmt

##33 kw or cancels 53
@R testor :: test >> or_test
@R testand :: or_test >> and_test
@R testor1 :: or_test >> or_test or and_test
## @R testlambda0 :: test >> lambda : test REDUNDANT
@R testlambda1 :: test >> lambda varargslist : test

##34 kw and
@R andnot :: and_test >> not_test
@R andand :: and_test >> and_test and not_test

##35 kw not
@R notnot :: not_test >> not not_test
@R notcmp :: not_test >> comparison

##36 NOTE KWS == >= <= <> !=
@R cmpexpr :: comparison >> expr
@R cmplt :: comparison >> comparison < expr
@R cmpgt :: comparison >> comparison > expr
@R cmpeq :: comparison >> comparison == expr
@R cmpge :: comparison >> comparison >= expr
@R cmple :: comparison >> comparison <=  expr
@R cmpnep :: comparison >> comparison <> expr
@R cmpne :: comparison >> comparison != expr
@R cmpin :: comparison >> comparison in expr
@R cmpnotin :: comparison >> comparison not in expr
@R cmpis :: comparison >> comparison is expr
@R cmpisnot :: comparison >> comparison is not expr

##37 kw is not punct > < ! (eliminated)

##38 p |
@R expr_xor :: expr >> xor_expr
@R expr_lor :: expr >> expr | xor_expr

##39 p ^
@R xor_and :: xor_expr >> and_expr
@R xor_xor :: xor_expr >> xor_expr ^ and_expr

##40
@R and_shift :: and_expr >> shift_expr
@R and_and :: and_expr >> and_expr & shift_expr

##41 note kw's << >x> note goofy x to avoid confusing the grammar
@R shift_arith :: shift_expr >> arith_expr
@R shift_left :: shift_expr >> shift_expr << arith_expr
@R shift_right :: shift_expr >> shift_expr >x> arith_expr

##42
@R arith_term :: arith_expr >> term
@R arith_plus :: arith_expr >> arith_expr + term
@R arith_minus :: arith_expr >> arith_expr - term

##43 p */%
@R termfactor :: term >> factor
@R termmul :: term >> term * factor
@R termdiv :: term >> term / factor
@R termmod :: term >> term % factor

## stuff for power
@R factorpower :: factor >> power
@R factorexp :: factor >> factor ** power

##44 p ~
@R powera :: power >> atom trailerlist
@R trailerlist0 :: trailerlist >> 
@R trailerlistn :: trailerlist >> trailer trailerlist
@R powerp :: power >> + power
@R powerm :: power >> - power
@R poweri :: power >> ~ power

##45 t NUMBER STRING
@R nulltup :: atom >> ( )
@R parens :: atom >> ( testlist )
@R parensc :: atom >> ( testlist , )
@R nulllist :: atom >> [ ]
@R list :: atom >> [ testlist  ]
@R listc :: atom >> [ testlist , ]
@R nulldict :: atom >> { }
@R dict :: atom >> { dictmaker   }
@R dictc :: atom >> { dictmaker , }
@R repr :: atom >> ` testlist  `
## @R reprc :: atom >> ` testlist , ` doesn't work, apparently
@R aname :: atom >> NAME
## note number to be broken out into FLOAT OCTINT HEXINT INT
@R anumber :: atom >> NUMBER
@R astring :: atom >> stringseq
@R stringseq0 :: stringseq >> STRING
@R stringseqn :: stringseq >> stringseq STRING

##46 
@R nullcall :: trailer >> ( )
@R call :: trailer >> ( arglist  )
@R callc :: trailer >> ( arglist , )
@R index :: trailer >> [ subscriptdots ]
@R getattr :: trailer >> . NAME

##47
@R arg1 :: arglist >> argument
@R argn :: arglist >> arglist , argument
##@R argn1 :: arglist >> arglist , NAME = test

##48 ( !!!! is this wrong in PP?)

@R posarg :: argument >> test

## here the left test should be a NAME always, but parser doesn't like it
@R namearg :: argument >> test = test

##49 this IS wrong in PP (numeric ext)
@R nodots :: subscriptdots >> subscriptseq
@R yesdots :: subscriptdots >> subscriptseq , . . . , subscriptseq
@R subscript1 :: subscriptseq >> subscript
@R subscriptn :: subscriptseq >> subscriptseq , subscript
@R subscriptt :: subscript >> test
@R subscripts0 :: subscript >> :
@R subscriptsL :: subscript >> test :
@R subscriptsR :: subscript >> : test
@R subscripts :: subscript >> test : test

##50
@R exprlist1 :: exprlist >> expr
@R exprlistn :: exprlist >> exprlist , expr

##51
@R testlist0 :: testlist >> test
@R testlistn :: testlist >> testlist , test

##52
@R dictmaker1 :: dictmaker >> test : test
@R dictmaker2 :: dictmaker >> dictmaker , test : test

"""

nonterms = """
subscriptdots subscript arg
argument arglist subscriptseq params trailerlist
factor atom trailer dictmaker stringseq power
xor_expr and_expr shift_expr arith_expr term
and_test or_test not_test comparison comp_op expr
fplist stmtseq varargslist assn
expr elifs suite excepts parameters pbasic pdefault pspecial
testlist exprlist test dotted_name_list dotted_name name_list
if_stmt while_stmt for_stmt try_stmt funcdef classdef
expr_stmt print_stmt del_stmt flow_stmt import_stmt global_stmt
small_stmt compound_stmt stmt simple_stmt exec_stmt
file_input except_clause fpdef cmp_op
all
"""

import string
# python needs special handling for the lexical stuff
NAMEre = "[" + string.letters + "_][" + string.letters+string.digits +"]*"
NUMBERre = "[" + string.digits + "]+" # temporary!
STRINGre = '"[^"\n]*"' # to be overridden in lexdict
#NEWLINEre = "\n" # to be overridden in lexdict
INDENTre = "#" # a fake! to be overridden
DEDENTre = "#" # a fake! to be overridden

def echo(str):
    return str

def DeclareTerminals(Grammar):
    Grammar.Addterm("NAME", NAMEre, echo)
    Grammar.Addterm("NUMBER", NUMBERre, echo)
    Grammar.Addterm("STRING", STRINGre, echo)
    #Grammar.Addterm("NEWLINE", NEWLINEre, echo) # newline is kw!
    Grammar.Addterm("INDENT", INDENTre, echo)
    Grammar.Addterm("DEDENT", DEDENTre, echo)

# not >x> is a fake!
keywords = """
and break class continue def del elif else except exec
finally for from global if import in is lambda not or pass
print raise return try while == >= <= <> != >x> << NEWLINE
**
"""

import kjParser, string, re
from kjParser import KEYFLAG, ENDOFFILETERM

alphanumunder = string.letters+string.digits+"_"
alpha = string.letters + "_"

# components that are part of a identifier (cannot be next to kw).
id_letters = map(None, alphanumunder)

# terminator re for names
nametermre = "[^" + alphanumunder + "]"
nameterm = re.compile(nametermre)

# terminator re for numbers (same as above but allow "." in num).
numtermre =  "[^" + alphanumunder + "\.]"
numterm = re.compile(numtermre)

parseerror = "parseerror"

pycommentre = r"(#.*)"

# whitespace regex outside of brackets
#  white followed by (comment\n maybe repeated)
#  DON'T EAT NEWLINE!!
pywhiteoutre = r"([ \t\r\014]|[\]\n)*%s?" % pycommentre
pywhiteout = re.compile(pywhiteoutre)

# whitespace regex inside brackets
#  white or newline possibly followed by comment, all maybe repeated
pywhiteinre = pywhiteoutre #"[ \t\r]*(\\\\\n)*%s?" % pycommentre
pywhitein = re.compile(pywhiteinre)

# totally blank lines (only recognize if next char is newline)
#allblankre = "\n" + pywhiteinre
#allblank = re.compile(allblankre)

# re for indentation (might accept empty string)
indentp = re.compile(r"[\t ]*")

# two char kws and puncts
char2kw = ["if", "or", "in", "is"]
punct2 = ["<>", "<<", ">>", "<=", ">=", "!=", "**", "=="]

# >two char kws as map of first 3 chars to others
char3k_data = """
  and break class continue def del elif else except
  finally for from global import lambda not pass print
  raise return try while exec
"""

char3kw = string.split(char3k_data)
char3kwdict = {}
for x in char3kw:
    char3kwdict[x[:3]] = x

# NOTE: newline is treated same as a punctuation
# NOTE: "' ARE NOT PUNCTS
punct = "~!#%^&*()-+=|{}<>,.;:/[]{}\n`"
punctlist = map(None, punct)

kwmap = {}
for x in char2kw + punct2 + char3kw + map(None, punct):
    # everything parses as length 1 to the outer world.
    kwmap[x] = (((KEYFLAG, x), x), 1)

# special hack
kwmap[">>"] = (((KEYFLAG, ">x>"), ">x>"), 1)
newlineresult = kwmap["\n"] = (((KEYFLAG, "NEWLINE"), "NEWLINE"), 1)

#finaldedent = (((TERMFLAG, "DEDENT"), ""), 1)

# Python lexical dictionary.

### MUST HANDLE WHOLELY BLANK LINES CORRECTLY!

def RMATCH(re, key, start=0):
    group = re.match(key, start)
    if group is None: return -1
    return group.end() - group.start()

class pylexdict(kjParser.LexDictionary):
   def __init__(self):
       kjParser.LexDictionary.__init__(self)
       # need to add special map for >>
       self.brackets = 0 # count of active brackets
       self.realindex = 0 # where to start
       self.indents = [""] # stack of indents (start with a fake one)
       self.lineno = 0
       self.atdedent = 0
       ### handle multiple dedents correctly!!!
       ### translate tabs to 8 spaces...
       from kjParser import TERMFLAG
       self.NAMEflag = (TERMFLAG, "NAME")
       self.STRINGflag = (TERMFLAG, "STRING")
       self.NEWLINEflag = (TERMFLAG, "NEWLINE")
       self.INDENTflag = (TERMFLAG, "INDENT")
       self.DEDENTflag = (TERMFLAG, "DEDENT")
       self.NUMBERflag = (TERMFLAG, "NUMBER")

   def endoffile(self, String):
       # pop off all indentations!
       indents = self.indents
       #lastresult = self.lastresult
       self.realindex = len(String)
       if not indents:
          # pop indents
          #print "eof after dedent"
          result = self.lastresult = (ENDOFFILETERM, 0)
       else:
          #print "eof as dedent after", self.lastresult
          del indents[-1]
          if indents:
             dedent = indents[-1]
          else:
             dedent = ""
          result = self.lastresult = ((self.DEDENTflag, dedent), 1)
       #print "returning eof", result, "after", lastresult
       return result

   def Token(self, String, StartPosition):
       #print "Token", (StartPosition, 
       #  `String[self.realindex:self.realindex+20]`, self.lastresult)
       # HAVE TO FAKE OUT LEXER FOR DEDENTS
       # STARTPOSITION COUNTS # OF TOKEN, NOT STRING POSITION
       # STRING POSITION IS MAINTAINED IN LexDict object.
       lastindex = self.lastindex
       lastresult = self.lastresult
       if self.laststring is not String:
          #print "parsing new string"
          self.laststring = String
          # special hack: skip lead whitespace
          cursor = 0
          self.lineno = 1
          while 1:
             test = RMATCH(pywhitein,String, cursor)
             if test<0: break
             next = cursor + test
             #print "lead skip:", next, String[cursor:next]
             if String[next]!="\n": break
             #skipped = String[cursor:next]
             #if "\n" in skipped:
             #   self.lineno = (
             #    self.lineno + len(string.splitfields(skipped, "\n")))
             #self.lineno = self.lineno+1
             cursor = next + 1
          self.realindex = cursor
          self.saveindex = 0
          self.indents = [""] # stack of indents (start with a fake one)
          # pretend we saw a newline
          self.lastresult = newlineresult
          if StartPosition!=0:
             self.laststring = None
             raise ValueError, "python lexical parsing must start at zero"
          lastindex = self.lastindex
          lastresult = None
       elif lastindex == StartPosition:
          #print "returning lastresult ", lastresult
          return lastresult
       elif lastindex != StartPosition-1:
          raise ValueError, "python lexer can't skip tokens"

       #print "parsing", StartPosition, lastresult
       # do newline counting here!
       delta = String[self.saveindex: self.realindex]
       #print "delta", `delta`
       if "\n" in delta:
          #print self.lineno, self.saveindex, self.realindex, `delta`
          self.lineno = self.lineno + len(
            string.splitfields(delta, "\n")) - 1
       realindex = self.saveindex = self.realindex
       self.lastindex = StartPosition

       # skip whitespace (including comments)
       ### needs to be improved to parse blank lines, count line numbers...
       # skip all totally blank lines (don't eat last newline)
       atlineend = (String[realindex:realindex+1] == "\n"
                    or lastresult is newlineresult
                    or self.atdedent)
       skipnewlines = (lastresult is newlineresult or
                       self.atdedent or
                       self.brackets>0)
       if atlineend: #String[realindex:realindex+1]=="\n":
          #print "trying to skip blank lines", String[realindex:realindex+10]
          while 1:
             #if String[realindex:realindex+1]=="\n":
             #   start = realindex+1 # move past current newline
             #   self.lineno = self.lineno + 1
             #else:
             #   start = realindex
             start = realindex
             if skipnewlines:
                while String[start:start+1]=="\n":
                   start = start+1
                   #self.lineno = self.lineno+1
             #print "matching", `String[start:start+10]`
             skip = RMATCH(pywhitein,String, start)
             #print "skip=", skip
             if skip<0: break
             rs = skip + realindex + (start-realindex)
             if rs==realindex: break
             #print "at", rs, `String[rs]`
             if (rs<len(String) and 
                 (String[rs] == "\n" or 
                  (skipnewlines and String[rs-1:rs]=="\n"))):
                #print "skipping blank line"
                #if lastresult is newlineresult or self.brackets>0: 
                #   rs = rs + 1
                #skipped = String[start:rs]
                #if "\n" in skipped:
                   #self.lineno = self.lineno + len(
                   #   string.splitfields(skipped, "\n"))
                self.realindex = realindex = rs
                #self.lineno = self.lineno+1
             else:
                if skipnewlines: self.realindex = realindex = start
                break
       #print "after skipping blank lines", `String[realindex:realindex+20]`
       skipto = realindex
       skip = 0
       if self.brackets>0:
          while 1:
             #print "skipping white in brackets", skipto
             if realindex>len(String):
                break
             if String[skipto]=="\n":
                #self.lineno = self.lineno+1
                skipto = skipto + 1
                self.realindex = realindex = skipto
                continue
             skip = RMATCH(pywhiteout,String, skipto)
             nextskipto = skipto+skip
             #skipped = String[skipto:nextskipto]
             #if "\n" in skipped:
             #   self.lineno = self.lineno+len(
             #       string.splitfields(skipped, "\n"))
             if skip>0:
                skipto = nextskipto
             else: break
          skip = skipto - realindex
       elif not atlineend:
          skip = RMATCH(pywhitein,String, realindex)
       if skip<=0: 
          skip = 0
       else:
          #print "skipping", skip
          nextri = realindex + skip
          #skipped = String[realindex:nextri]
          #if "\n" in skipped:
          #   self.lineno = self.lineno + len(
          #    string.splitfields(skipped, "\n"))
          realindex = self.realindex = nextri
       if realindex>=len(String):
          return self.endoffile(String)
       # now look for a keyword, name, number, punctuation, 
       # INDENT, DEDENT, NEWLINE
       first = String[realindex]
       #if last parse was newline and not in brackets:
       #   look for indent/dedent
       if (self.brackets<=0 and (lastresult is newlineresult or self.atdedent)
           and first != "\n"):
          #print "looking for dent", realindex, `String[realindex:realindex+20]`
          match = RMATCH(indentp,String, realindex)
          if match>=0:
             dent = String[realindex: realindex+match]
             #print "dent match", match, `dent`
             oldindex = realindex
             self.realindex = realindex = realindex+match
             # replace tabs with 8 spaces
             dent = string.joinfields(string.splitfields(dent, "\t"),
                                      "        ")
             dents = self.indents
             lastdent = dents[-1]
             ldl = len(lastdent)
             dl = len(dent)
             #print "last", ldl, dents
             if ldl<dl:
                self.atdedent = 0
                result = self.lastresult = ((self.INDENTflag, dent), 1)
                dents.append(dent)
                #print "indent ", result, dents
                return result
             if ldl>dl:
                self.realindex = oldindex # back up, may have to see it again!
                self.atdedent = 1
                result = self.lastresult = ((self.DEDENTflag, dent), 1)
                del dents[-1]
                #print "dedent ", result, dl, dents
                return result
             # otherwise, indentation is same, keep looking
             # might be at eof now:
             if realindex>=len(String):
                #print "returning eof"
                return self.endoffile(String)
             first = String[realindex]
       self.atdedent = 0
       from string import digits #, letters
       if (first in punctlist and
           # special case for .123 numbers (yuck!)
           (first!="." or String[realindex+1] not in digits)):
          # is it a 2 char punct?
          first2 = String[realindex:realindex+2]
          if first2 in punct2:
             result = self.lastresult = kwmap[first2]
             self.realindex = realindex+2
             #print "2 digit punct", result
             return result
          # otherwise, just return normal punct
          result = self.lastresult = kwmap[first]
          self.realindex = self.realindex + 1
          ### special bookkeeping
          if first=="\n":
             result = newlineresult
             #print "newline!"
             #self.lineno = self.lineno+1
          elif first in "[{(":
             #print "bracket!"
             self.brackets = self.brackets + 1
          elif first in "]})":
             #print "close bracket!"
             self.brackets = self.brackets - 1
          #print "1 digit punct", result
          return result
       if first in digits or first==".":
          # parse a number...
          skip = numterm.search(String, realindex)
          if skip<=realindex:
             raise parseerror, "number length<1 (!)"
          thenumber = String[realindex:skip]
          self.realindex = skip
          ### note don't interpret number here!!
          result = self.lastresult = ((self.NUMBERflag, thenumber), 1)
          #print "number", result
          return result
       if first in alpha:
          # try keyword...
          first2 = String[realindex: realindex+2]
          if first2 in char2kw:
             if String[realindex+2:realindex+3] not in id_letters:
                # parse a 2 char kw first2
                result = self.lastresult = kwmap[first2]
                self.realindex = self.realindex+2
                #print "keyword 2", result
                return result
          first3 = String[realindex: realindex+3]
          if char3kwdict.has_key(first3):
             the_kw = char3kwdict[first3]
             the_end = realindex+len(the_kw)
             if ((the_end<len(String)) and 
                 (String[the_end] not in id_letters) and
                 (String[realindex:the_end]==the_kw)):
                # parse the_kw
                self.realindex = the_end
                result = self.lastresult = kwmap[the_kw]
                #print "keyword +", result
                return result
          #otherwise parse an identifier
          #print "looking for name:", `String[realindex:realindex+10]`
          skip = nameterm.search(String, realindex)
          if skip<=realindex:
             raise parseerror, "identifier length<1 (!)"
          theid = String[realindex:skip]
          self.realindex = skip
          ### note don't interpret number here!!
          result = self.lastresult = ((self.NAMEflag, theid), 1)
          #print "id", result
          return result
       if first in "\"'":
          # check for triplequotes
          first3 = first*3
          if String[realindex: realindex+3] == first3:
             # parse triple quotes
             start = place = realindex+3
             while 1:
                last = string.find(String, first3, place)
                if last<0:
                   raise parseerror, "failed to terminate triple quotes"
                if String[last-1:last]=="\\" and String[last-2:last-1]!="\\":
                   place = last+1
                else: break
             the_string = String[start: last]
             self.realindex = last+3
             result = self.lastresult = ((self.STRINGflag, the_string), 1)
             #print "3q string", result
             # count the newlines!
             #newlinecount = len(string.splitfields(the_string, "\n"))
             #self.lineno = self.lineno+newlinecount
             #print "triple quotes", result
             return result
          else:
             # parse single quotes
             sanity = start = place = realindex+1
             done = 0
             while 1:
                sanity = min(string.find(String, "\n", sanity), len(String))
                if sanity<start: 
                   sanity=len(String)
                   break
                if String[sanity-1]!="\\":
                   break
                else:
                   #self.lineno = self.lineno+1
                   sanity = sanity + 1
             while 1:
                last = string.find(String, first, place)
                if last<0 or last>sanity:
                   raise parseerror, "failed to terminate single quotes"
                if String[last-1:last]=="\\":
                   # are we at the end of an odd number of backslashes? (yuck!)
                   bplace = last-1
                   while String[bplace:bplace+1]=="\\":
                      bplace = bplace-1
                   if (last-bplace)%2==1: 
                      break # the end quote is real!
                   place = last+1
                else: break
             the_string = String[start:last]
             self.realindex = last+1
             result = self.lastresult = ((self.STRINGflag, the_string), 1)
             #print "1q string", result
             return result
       #print (String[realindex-20:realindex-1], String[realindex],
       #       String[realindex+1:realindex+20])
       raise parseerror, "invalid first: " + `first`

# use a modified lexstringwalker
class pylexstringwalker(kjParser.LexStringWalker):
   def DUMP(self):
       kjParser.DumpStringWindow(self.String, self.LexDict.realindex)

## a HORRIBLE HACK! of a hack: override the DoParse of Grammar
## to give Python line numbers.  RELIES ON GLOBAL pyg
##
def hackDoParse(String, Context=None, DoReductions=1):
    import sys, kjParser
    try:
        # construct the ParserObj
        # add a newline to front to avoid problem with leading comment
        #String = "\n%s\n" % String
        Stream = pylexstringwalker( String, pyg.LexD )
        Stack = [] # {-1:0} #Walkers.SimpleStack()
        ParseOb = kjParser.ParserObj( pyg.RuleL, Stream, pyg.DFA, Stack, \
                         DoReductions, Context )
        # do the parse
        ParseResult = ParseOb.GO()
        # return final result of reduction and the context
        return (ParseResult[1], Context)
        #return kjParser.Grammar.DoParse(pyg, String, Context, DoReductions)
    except: ### for testing!!
        t, v = sys.exc_type, sys.exc_value
        v = ("near line", pyg.LexD.lineno, v)
        raise t, v

buildinfo = """
Please edit the ARCHIVE parameter of this module (%s)
to place the python grammar archive in a standard
directory to prevent the module from rebuilding
the python grammar over and over and over...
""" % __name__

def GrammarBuild():
    global pyg
    import kjParseBuild
    pyg = kjParseBuild.NullCGrammar()
    pyg.DoParse = hackDoParse
    # override lexical dict here
    pyg.LexD = pylexdict()
    DeclareTerminals(pyg)
    pyg.Keywords(keywords)
    pyg.punct("~!#%^&*()-+=|{}'`<>,.;:/[]{}")
    pyg.Nonterms(nonterms)
    pyg.Declarerules(pyrules)
    print buildinfo
    print "compiling... this may take a while..."
    pyg.Compile()
    print "dumping"
    outfile = open(marshalfilename, "wb")
    pyg.MarshalDump(outfile)
    outfile.close()
    print "self testing the grammar"
    test(pyg)
    print "\n\ndone with regeneration"
    return pyg

def unMarshalpygram():
    global pyg
    import kjParser
    print "loading"
    try:
       infile = open(marshalfilename, "rb")
    except IOError:
       print marshalfilename, "not found, attempting creation"
       pyg = GrammarBuild()
    else:
       pyg = kjParser.UnMarshalGram(infile)
       infile.close()
    pyg.DoParse = hackDoParse
    # lexical override
    pyg.LexD = pylexdict()
    DeclareTerminals(pyg)
    # BindRules(pyg)
    if dotest: 
       print "self testing the grammar"
       test(pyg)
    return pyg


# not used, commented
#### interpretation rules/classes
#
#def zeroth(list, Context):
#    return list[0] # eg, for all1, ignore all but first
#
## file_input, stmt, simple_stmt, compound_stmt give list of statement_ob
#def append(list, Context):
#    "eg, for top_stmt, conjoin two smt lists"
#    return list[0] + list[1]
#
## file_input >zeroth
#
## simple, compound, one_small, small_semi: echol
#def echol(list, Context):
#    return list
#
## more_small > seq_sep
#def seq_sep(list, Context):
#    list[0].append(list[2])
#    return list[0]
#
## smexpr, smassn, smpring, smdel, smflow, smimport, smglobal, smexec
##  > zeroth
#
## cmif, cmwhile, cmfor, cmtry, cmdef, cmclass > zeroth
#
#
#def BindRules(pyg):
#    for name in string.split("""
#        all1 file_input cmif cmwhile cmfor cmtry cmdef cmclass
#        smexpr smassn smprint smdel smflow smimport smglobal smexec
#        """):
#        pyg.Bind(name, zeroth)
#    for name in string.split("""
#        simple compound one_small small_semi
#        """):
#        pyg.Bind(name, echol)
#    pyg.Bind("top_stmt", append)
#    pyg.Bind("more_small", seq_sep)

teststring = """#
#
# a test string
#
from string import join, split
'''
import re

for a in l:
    a.attr, a[x], b = c
else:
    d = b
'''
class zzz:
   ''' 
   #doc string 
   '''
   '''
   global re, join
   
   d = {} 
   for i in range(10): d[i] = i
   '''
   def test(c,s):
       return "this" 
       while not done:
             print done
             break
       list = [1,2,3]
         # comment
       return 5
   
   
   n,x = 89 >> 90 + 6 / 7 % x + z << 6 + 2 ** 8

if x==5:
   while y:
     for i in range(6):
         raise SystemError, "oops"


"""

#teststring ="""\
## comment
#if x in y: print z
#elif 1: print w
#"""

'''
teststring="""
exec "print 1"
"""
'''

def test(grammar, context=None, teststring=teststring):
       from time import time
       now = time()
       x = grammar.DoParse1(teststring, context)
       elapsed = time()-now
       print x
       print elapsed
       return x
   
regen = 0
dotest = 0
   
if __name__ == "__main__" : 
      if regen: GrammarBuild()
      unMarshalpygram()
