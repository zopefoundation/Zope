# this was used for debugging null productions (a nearly full sql grammar
# is available on request).

#set this to automatically rebuild the grammar.
REBUILD = 1
MARSHALFILE = "SQLTEST.mar"

SELECTRULES = """
  ## highest level for select statement (not select for update)
  select-statement ::
  @R selectR :: select-statement >> 
                   SELECT 
                   from-clause
                   where-clause
                   group-by-clause
                   having-clause
  ## generalized to allow null from clause eg: select 2+2
  @R fromNull :: from-clause >>
  @R fromFull :: from-clause >> FROM 
  @R whereNull :: where-clause >>
  @R whereFull :: where-clause >> WHERE 
  @R groupNull :: group-by-clause >>
  @R groupFull :: group-by-clause >> GROUP BY 
  @R havingNull :: having-clause >> 
  @R havingFull :: having-clause >> HAVING
  @R unionNull :: union-clause >> 
  @R unionFull :: union-clause >> UNION 
"""

SELECTNONTERMS = """
  select-statement
  all-distinct select-list table-reference-list
  where-clause group-by-clause having-clause union-clause
  maybe-order-by
  search-condition column-list maybe-all order-by-clause
  column-name from-clause
"""
# of these the following need resolution
#   (select-list) (table-reference-list) 
#   (search-condition) order-by-clause (column-name) 

SELECTKEYWORDS = """
  SELECT FROM WHERE GROUP BY HAVING UNION DISTINCT ALL AS 
"""

# test generation of the grammar
def BuildSQLG():
   import kjParseBuild
   SQLG = kjParseBuild.NullCGrammar()
   SQLG.SetCaseSensitivity(0)
   SQLG.Keywords(SELECTKEYWORDS)
   SQLG.Nonterms(SELECTNONTERMS)
   # no comments yet
   SQLG.Declarerules(SELECTRULES)
   print "building"
   SQLG.Compile()
   print "marshaling"
   outfile = open( MARSHALFILE, "w")
   SQLG.MarshalDump(outfile)
   outfile.close()
   return SQLG

# load function
def LoadSQLG():
   import kjParser
   print "unmarshalling"
   infile = open(MARSHALFILE, "r")
   SQLG = kjParser.UnMarshalGram(infile)
   infile.close()
   return SQLG

#### for testing
if REBUILD:
   SQLG0 = BuildSQLG()
   print " rebuilt SQLG0 as compilable grammar"

SQLG = LoadSQLG()
print " build SQLG as reloaded grammar"