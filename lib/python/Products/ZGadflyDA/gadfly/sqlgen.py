"""grammar generation stuff for sql.

This module does not bind any rule semantics, it
just generates the parser data structures.
"""

### interpretation functions and regexen for terminals

MARSHALFILE = "sql.mar"

import string
alphanum = string.letters+string.digits + "_"
userdefre = "[%s][%s]*" % (string.letters +"_", alphanum)
commentre = "--.*"

def userdeffn(str):
    from string import upper
    return upper(str)
    
charstre = "'[^']*'"

def charstfn(str):
    return str[1:-1]
    
#numlitre = "[%s][%s\.]*" % (string.digits, alphanum) # not really...

digits = string.digits
# rely in python to filter out the good/bad/ugly
intre = "[%s][%s.jJ]*" % (digits,digits)
numlitre = "%s([Ee][+-]?%s)?" % (intre, intre)

def numlitfn(str):
    """Note: this is "safe" because regex
       filters out dangerous things."""
    return eval(str)

def DeclareTerminals(Grammar):
    Grammar.Addterm("user_defined_name", userdefre, userdeffn)
    Grammar.Addterm("character_string_literal", charstre, charstfn)
    Grammar.Addterm("numeric_literal", numlitre, numlitfn)
    
def BuildSQL(filename=MARSHALFILE):
    import kjParseBuild
    from sqlgram import sqlrules, nonterms, keywords, puncts
    SQLG = kjParseBuild.NullCGrammar()
    SQLG.SetCaseSensitivity(0)
    DeclareTerminals(SQLG)
    SQLG.Keywords(keywords)
    SQLG.punct(puncts)
    SQLG.Nonterms(nonterms)
    SQLG.comments([commentre])
    # should add comments
    SQLG.Declarerules(sqlrules)
    print "working..."
    SQLG.Compile()
    print "testing"
    from sqlgtest import test
    for x in test:
        print SQLG.DoParse1(x)
    print "dumping to", filename
    outfile = open(filename, "wb")
    SQLG.MarshalDump(outfile)
    outfile.close()
    return SQLG
    
def reloadSQLG(filename=MARSHALFILE):
    """does not bind any interpretation functions."""
    import kjParser
    infile = open(filename, "rb")
    SQLG = kjParser.UnMarshalGram(infile)
    infile.close()
    DeclareTerminals(SQLG)
    return SQLG
    
def getSQL():
    from sqlwhere import filename
    return reloadSQLG(filename)
    
    

    
