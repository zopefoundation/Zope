
#
# sets implemented using mappings
#  Copyright Aaron Robert Watters, 1994
#
# these only work for "immutable" elements.
# probably not terribly efficient, but easy to implement
# and not as slow as concievably possible.

def NewSet(Sequence):
    Result = {}
    for Elt in Sequence:
        Result[Elt] = 1
    return Result

def Empty(Set):
    if Set == {}:
       return 1
    else:
       return 0

def get_elts(Set):
    return Set.keys()

def member(Elt,Set):
    return Set.has_key(Elt)

# in place mutators:
# returns if no change otherwise 1

def addMember(Elt,Set):
    change = 0
    if not Set.has_key(Elt):
       Set[Elt] = 1
       change = 1
    return change

def Augment(Set, OtherSet):
    change = 0
    for Elt in OtherSet.keys():
        if not Set.has_key(Elt):
           Set[Elt] = 1
           change = 1
    return change


def Mask(Set, OtherSet):
    change = 0
    for Elt in OtherSet.keys():
        if Set.has_key(Elt):
           del Set[Elt]
           change = 1
    return change

# side effect free functions

def Intersection(Set1, Set2):
    Result = {}
    for Elt in Set1.keys():
        if Set2.has_key(Elt):
           Result[Elt] = 1
    return Result

def Difference(Set1, Set2):
    Result = {}
    for Elt in Set1.keys():
        if not Set2.has_key(Elt):
           Result[Elt] = 1
    return Result

def Union(Set1,Set2):
    Result = {}
    Augment(Result,Set1)
    Augment(Result,Set2)
    return Result

def Subset(Set1,Set2):
    Result = 1
    for Elt in Set1.keys():
        if not Set2.has_key(Elt):
           Result = 0
           return Result # nonlocal
    return Result

def Same(Set1,Set2):
    if Subset(Set1,Set2) and Subset(Set2,Set1):
       return 1
    else:
       return 0

# directed graphs as Dictionaries of Sets
#   also only works for immutable nodes

def NewDG(pairlist):
    Result = {}
    for (source,dest) in pairlist:
        AddArc(Result, source, dest)
    return Result

def GetPairs(Graph):
    result = []
    Sources = Graph.keys()
    for S in Sources:
        Dests = get_elts( Graph[S] )
        ThesePairs = [None] * len(Dests)
        for i in range(0,len(Dests)):
            D = Dests[i]
            ThesePairs[i] = (S, D)
        result = result + ThesePairs
    return result

def AddArc(Graph, Source, Dest):
    change = 0
    if Graph.has_key(Source):
       Adjacent = Graph[Source]
       if not member(Dest,Adjacent):
          addMember(Dest,Adjacent)
          change = 1
    else:
       Graph[Source] = NewSet( [ Dest ] )
       change = 1
    return change

def Neighbors(Graph,Source):
    if Graph.has_key(Source):
       return get_elts(Graph[Source])
    else:
       return []

def HasArc(Graph, Source, Dest):
    result = 0
    if Graph.has_key(Source) and member(Dest, Graph[Source]):
       result = 1
    return result

def Sources(Graph):
    return Graph.keys()

# when G1, G2 and G3 are different graphs this results in
#   G1 = G1 U ( G2 o G3 )
# If G1 is identical to one of G2,G3 the result is somewhat
# nondeterministic (depends on dictionary implementation).
# However, guaranteed that AddComposition(G,G,G) returns
#    G1 U (G1 o G1) <= G <= TC(G1)
# where G1 is G's original value and TC(G1) is its transitive closure
# hence this function can be used for brute force transitive closure
#
def AddComposition(G1, G2, G3):
    change = 0
    for G2Source in Sources(G2):
        for Middle in Neighbors(G2,G2Source):
            for G3Dest in Neighbors(G3, Middle):
                if not HasArc(G1, G2Source, G3Dest):
                   change = 1
                   AddArc(G1, G2Source, G3Dest)
    return change

# in place transitive closure of a graph
def TransClose(Graph):
    change = AddComposition(Graph, Graph, Graph)
    somechange = change
    while change:
       change = AddComposition(Graph, Graph, Graph)
       if not somechange:
          somechange = change
    return somechange

########### SQueue stuff
#
#  A GrabBag should be used to hold objects temporarily for future
#  use.  You can put things in and take them out, with autodelete
#  that's all!

# make a new baggy with nothing in it
#   BG[0] is insert cursor BG[1] is delete cursor, others are elts
#
OLD = 1
NEW = 0
START = 2
def NewBG():
    B = [None]*8 #default size
    B[OLD] = START
    B[NEW] = START
    return B

def BGempty(B):
    # other ops must maintain this: old == new iff empty
    return B[OLD] == B[NEW]

# may return new, larger structure
# must be used with assignment...  B = BGadd(e,B)
def BGadd(elt, B):
    cursor = B[NEW]
    oldlen = len(B)
    # look for an available position
    while B[cursor] != None:
       cursor = cursor+1
       if cursor >= oldlen: cursor = START
       if cursor == B[NEW]: #back to beginning
          break
    # resize if wrapped
    if B[cursor] != None:
       B = B + [None] * oldlen
       cursor = oldlen
       B[OLD] = START
    if B[cursor] != None:
       raise IndexError, "can't insert?"
    # add the elt
    B[cursor] = (elt,)
    B[NEW] = cursor
    # B nonempty so OLD and NEW should differ.
    if B[OLD] == cursor:
       B[NEW] = cursor + 1
       if B[NEW]<=len(B): B[NEW] = START
    return B

def BGgetdel(B):
    # find something to delete:
    cursor = B[OLD]
    blen = len(B)
    while B[cursor]==None:
       cursor = cursor+1
       if cursor>=blen: cursor = START
       if cursor == B[OLD]: break # wrapped
    if B[cursor] == None:
       raise IndexError, "delete from empty grabbag(?)"
    # test to see if bag is empty (position cursor2 at nonempty slot)
    cursor2 = cursor+1
    if cursor2>=blen: cursor2 = START
    while B[cursor2]==None:
       cursor2 = cursor2+1
       if cursor2>=blen: cursor2 = START
       # since B[cursor] not yet deleted while will terminate
    # get and delete the elt
    (result,) = B[cursor]
    B[cursor] = None
    # cursor == cursor2 iff bag is empty
    B[OLD] = cursor2
    if B[NEW] == cursor2: B[NEW] = cursor
    return result

def BGtest(n):
    B = NewBG()
    rn = range(n)
    rn2 = range(n-2)
    for i in rn:
        for j in rn:
            B = BGadd( (i,j), B)
            B = BGadd( (j,i), B)
            x = BGgetdel(B)
        for j in rn2:
            y = BGgetdel(B)
        print (i, x, y)
    return B
