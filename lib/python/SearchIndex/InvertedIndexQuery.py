
__doc__='''\
Simple query parser for InvertedIndex.

Usage:
  
  InvertedIndexQuery.query(query_string, InvertedIndex_Index_instance)


Query strings should be of the form 

  "keyword1 [and | or | and not] [keyword2 [and | or | and not] ... keywordN]"

Parentheses may be used to alter association rules.

A series of keywords may be surrounded by quotes to perform a proximity
search (InvertedIndex.ResultList.near)

$Id: InvertedIndexQuery.py,v 1.1 1997/09/15 17:25:47 jim Exp $'''
  
import string, regsub, regex

from types import *

QueryError = 'InvertedIndexQuery.QueryError'

AndNot    = 'andnot'
And       = 'and'
Or        = 'or'
Proximity = 'proximity'

operator_dict = {
                   AndNot    : AndNot,
                   And       : And,
                   Or        : Or,
                   Proximity : Proximity
                }
                  
ws = (string.whitespace,)


class Word:
    '''Holds a parsed word in a query'''
    def __init__(self, word):
        self._word = word

    def word(self):
        return self._word

    def __repr__(self):
        return 'Word(%s)' % repr(self._word)


parens_regex = regex.compile("(\|)")

def parens(s):
    '''Find the beginning and end of the first set of parentheses in string, s'''

    if (parens_regex.search(s) < 0):
        return None

    if (parens_regex.group(0) == ")"):
        raise QueryError, "Mismatched parentheses"

    open = parens_regex.regs[0][0] + 1
    start = parens_regex.regs[0][1]
    p = 1

    while (parens_regex.search(s, start) >= 0):
	if (parens_regex.group(0) == ")"):
            p = p - 1
        else:
            p = p + 1

	start = parens_regex.regs[0][1]
  
        if (p == 0):
            return (open, parens_regex.regs[0][0])

    raise QueryError, "Mismatched parentheses"    


def parse2(q, default_operator):
    '''Find operators and operands'''
    i = 0
    while (i < len(q)):
        if (type(q[i]) is ListType):
            q[i] = parse2(q[i], default_operator)

        # every other item, starting with the first, should be an operand
        if ((i % 2) == 0):
            if (type(q[i]) is StringType):
                q[i] = Word(q[i])
        else:
            # This word should be an operator; if it is not, splice in
            # the default operator.
            try:
                q[i] = operator_dict[q[i]]
            except:
                q[i : i] = [ default_operator ]

        i = i + 1

    return q
             

def quotes(s):
     # split up quoted regions
     split = regsub.split(s, '[%s]*\"[%s]*' % (ws * 2))

     if (len(split) > 1):
         if ((len(split) % 2) == 0):
             raise QueryError, "Mismatched quotes"
    
         for i in range(1, len(split), 2):
             # split the quoted region into words and make Word instances out of them
             split[i] = map(Word, filter(None, regsub.split(split[i], '[%s]+' % ws)))

             # put the Proxmity operator in between quoted words
             for j in range(1, len(split[i])):
                 split[i][j : j] = [ Proximity ]

         split = filter(None, split)
     else:
         # No quotes, so just split the string into words
         split = filter(None, regsub.split(s, '[%s]+' % ws))

     return split
    

def parse(s):
    '''Parse parentheses and quotes'''
    l = []
    tmp = string.lower(s)

    while (1):
        p = parens(tmp)

        if (p is None):
            # No parentheses found.  Look for quotes then exit.
            l = l + quotes(tmp)
            break
        else:
            # Look for quotes in the section of the string before
            # the parentheses, then parse the string inside the parens
            l = l + quotes(tmp[:(p[0] - 1)])
            l.append(parse(tmp[p[0] : p[1]]))

            # continue looking through the rest of the string
            tmp = tmp[(p[1] + 1):]

    return l


def get_operands(q, i, index):
    '''Evaluate and return the left and right operands for an operator'''
    try:
        left  = q[i - 1]
        right = q[i + 1]
    except IndexError:
        raise QueryError, "Malformed query"

    # A list is a parenthesized section, so evaluate those
    # before anything else

    if (type(left) is ListType):
        left = evaluate(left, index)
    
    if (type(right) is ListType):
        right = evaluate(right, index)

    # Do a search on each Word

    try:
        left = left.word()
    except AttributeError:
        pass
    else:
        left = index[left]

    try:
        right = right.word()
    except AttributeError:
        pass
    else:
        right = index[right]

    # Return a pair of ResultLists
 
    return (left, right)


def evaluate(q, index):
    '''Evaluate a parsed query'''

    if (len(q) == 1):
	if (type(q[0]) is ListType):
	    return evaluate(q[0], index)

        return index[q[0].word()]
      
    i = 0
    while (i < len(q)):
        if q[i] is AndNot:
            left, right = get_operands(q, i, index)
            val = left.and_not(right)
            q[(i - 1) : (i + 2)] = [ val ]
        else:
            i = i + 1

    i = 0
    while (i < len(q)):
        if q[i] is And:
	    left, right = get_operands(q, i, index)
	    val = left & right
	    q[(i - 1) : (i + 2)] = [ val ]
        else:
            i = i + 1

    i = 0
    while (i < len(q)):
        if q[i] is Or:
	    left, right = get_operands(q, i, index)
	    val = left | right
	    q[(i - 1) : (i + 2)] = [ val ]
	else:
	    i = i + 1

    i = 0
    while (i < len(q)):
        if q[i] is Proximity:
	    left, right = get_operands(q, i, index)
	    val = left.near(right)
	    q[(i - 1) : (i + 2)] = [ val ]
        else:
            i = i + 1

    if (len(q) != 1):
        raise QueryError, "Malformed query"

    return q[0]


def query(s, index, default_operator = Or):
    # First replace any occurences of " and not " with " andnot "
    s = regsub.gsub('[%s]+and[%s]*not[%s]+' % (ws * 3), ' andnot ', s)

    q = parse(s)
    q = parse2(q, default_operator)

    return evaluate(q, index)


# $Log: InvertedIndexQuery.py,v $
# Revision 1.1  1997/09/15 17:25:47  jim
# *** empty log message ***
#
# Revision 1.8  1997/05/15 14:10:46  jim
# Fixed bug in handling of or.
# Also added some quote escapes to make hilit19 happier.
#
# Revision 1.7  1997/04/30 16:27:39  jim
# Changed default operator to Or.
#
# Revision 1.6  1997/04/10 19:11:52  chris
# Added some documentation
#
