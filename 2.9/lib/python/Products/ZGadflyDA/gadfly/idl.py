
# idl grammar
#
# Note, this grammar requires a special hack at the lexical
# level in order to parse the fragment
#
# ...
#  case abc::def: jjj::www: whatever...
#
# (Yuck!)
# Some would argue this is a language design flaw, but whatever...
# It causes a shift/reduce problem without special handling for ::
# below coloncolon is a 'fake' keyword that parses as two colons.

idlgramstring = """

specification ::

## 1
@R r1a :: specification >> definition speclist
@R r1b :: speclist >> specification
@R r1c :: speclist >>

## 2 punct ;
@R r2a :: definition >> type_dcl ;
@R r2b :: definition >> const_dcl ;
@R r2c :: definition >> except_dcl ;
@R r2d :: definition >> interface_nt ;
@R r2e :: definition >> module_nt ;

## 3 identifier=term, module=kw puncts {}
@R r3 :: module_nt >> module identifier { specification }

## 4
@R r4a :: interface_nt >> interface_dcl
@R r4b :: interface_nt >> forward_dcl

## 5
@R r5 :: interface_dcl >> interface_header { interface_body }

## 6 interface=kw
@R r6 :: forward_dcl >> interface identifier

## 7 puncts []
@R r7 :: interface_header >> interface identifier [ inheritance_spec ]

## 8 
@R r8a :: interface_body >> 
@R r8b :: interface_body >> export interface_body

## 9
@R r9a :: export >> type_dcl
@R r9b :: export >> const_dcl
@R r9c :: export >> except_dcl
@R r9d :: export >> attr_dcl
@R r9e :: export >> op_dcl

## 10 punct ,:
@R r10a :: inheritance_spec >> : scoped_name_list
@R r10b :: scoped_name_list >> scoped_name
@R r10c :: scoped_name_list >> scoped_name_list , scoped_name

## 11
@R r11a :: scoped_name >> identifier
@R r11b :: scoped_name >> colon_colon identifier
@R r11d :: scoped_name >> scoped_name coloncolon identifier

## 12 const=kw punct =
@R r12 :: const_dcl >> const const_type identifier = const_expr

## 13
@R r13a :: const_type >> integer_type
@R r13b :: const_type >> char_type
@R r13c :: const_type >> boolean_type
@R r13d :: const_type >> floating_type
@R r13e :: const_type >> string_type
@R r13f :: const_type >> scoped_name

## 14
@R r14 :: const_expr >> or_expr

##15 punct |
@R r15a :: or_expr >> xor_expr
@R r15b :: or_expr >> or_expr | xor_expr

##16 punct ^
@R r16a :: xor_expr >> and_expr
@R r16b :: xor_expr >> xor_expr ^ and_expr

##17 punct &
@R r17a :: and_expr >> shift_expr
@R r17b :: and_expr >> and_expr & shift_expr

##18 punct > <
@R r18a :: shift_expr >> add_expr
@R r18b :: shift_expr >> shift_expr > > add_expr
@R r18c :: shift_expr >> shift_expr < < add_expr

##19 punct +-
@R r19a :: add_expr >> mult_expr
@R r19b :: add_expr >> add_expr + mult_expr
@R r19c :: add_expr >> add_expr - mult_expr

##20 punct */%
@R r20a :: mult_expr >> unary_expr
@R r20b :: mult_expr >> mult_expr * unary_expr
@R r20c :: mult_expr >> mult_expr / unary_expr
@R r20d :: mult_expr >> mult_expr % unary_expr

##21
@R r21a :: unary_expr >> unary_operator primary_expr
@R r21b :: unary_expr >> primary_expr

##22
@R r22a :: unary_operator >> -
@R r22b :: unary_operator >> +
@R r22c :: unary_operator >> ~

##23 punct ()
@R r23a :: primary_expr >> scoped_name
@R r23b :: primary_expr >> literal
@R r23c :: primary_expr >> ( const_expr )

##24 terms = *_literal (?) except boolean
@R r24a :: literal >> integer_literal
@R r24b :: literal >> string_literal
@R r24c :: literal >> character_literal
@R r24d :: literal >> floating_pt_literal
@R r24e :: literal >> boolean_literal

##25 kw TRUE FALSE
@R r25a :: boolean_literal >> TRUE
@R r25b :: boolean_literal >> FALSE

##26 
@R r26 :: positive_int_literal >> const_expr

##27 kw typedef
@R r27a :: type_dcl >> typedef type_declarator
@R r27b :: type_dcl >> struct_type
@R r27c :: type_dcl >> union_type
@R r27d :: type_dcl >> enum_type

##28
@R r28 :: type_declarator >> type_spec declarators

##29
@R r29a :: type_spec >> simple_type_spec
@R r29b :: type_spec >> constr_type_spec

##30
@R r30a :: simple_type_spec >> base_type_spec
@R r30b :: simple_type_spec >> template_type_spec
@R r30c :: simple_type_spec >> scoped_name

##31
@R r31a :: base_type_spec >> floating_pt_type
@R r31b :: base_type_spec >> integer_type
@R r31c :: base_type_spec >> char_type
@R r31d :: base_type_spec >> boolean_type
@R r31e :: base_type_spec >> octet_type
@R r31f :: base_type_spec >> any_type

## 32
@R r32a :: template_type_spec >> sequence_type
@R r32b :: template_type_spec >> string_type

##33
@R r33a :: constr_type_spec >> struct_type
@R r33b :: constr_type_spec >> union_type
@R r33c :: constr_type_spec >> enum_type

##34
@R r34a :: declarators >> declarator
@R r34b :: declarators >> declarators , declarator

##35
@R r35a :: declarator >> simple_declarator
@R r35b :: declarator >> complex_declarator

##36
@R r36 :: simple_declarator >> identifier

##37
@R r37 :: complex_declarator >> array_declarator

##38 kw float double
@R r38a :: floating_pt_type >> float
@R r38b :: floating_pt_type >> double

##39 
@R r39a :: integer_type >> signed_int
@R r39b :: integer_type >> unsigned_int

##40
@R r40 :: signed_int >> signed_long_int
@R r40 :: signed_int >> signed_short_int

##41 kw long
@R r41 :: signed_long_int >> long

##42 kw short
@R r42 :: signed_short_int >> short

##43
@R r43 :: unsigned_int >> unsigned_long_int
@R r43 :: unsigned_int >> unsigned_short_int

##44 kw unsigned
@R r44 :: unsigned_long_int >> unsigned long

##45 
@R r45 :: unsigned_short_int >> unsigned short

##46 kw char
@R r46 :: char_type >> char

##47 kw boolean
@R r47 :: boolean_type >> boolean

##48 kw octet
@R r48 :: octet_type >> octet

##49 kw any
@R r49 :: any_type >> any

##50 kw struct
@R r50 :: struct_type >> struct identifier { member_list }

##51
@R r51a :: member_list >> member
@R r51b :: member_list >> member_list member

##52
@R r52 :: member >> type_spec declarators ;

##53 kw union switch
@R r53 :: union_type >> 
    union identifier switch ( switch_type_spec ) { switch_body }

##54
@R r54a :: switch_type_spec >> integer_type
@R r54b :: switch_type_spec >> char_type
@R r54c :: switch_type_spec >> boolean_type
@R r54d :: switch_type_spec >> enum_type
@R r54e :: switch_type_spec >> scoped_name

##55
@R r55a :: switch_body >> case_nt
@R r55b :: switch_body >> switch_body case_nt

##56
@R r56a :: case_nt >> case_labels element_spec ;
@R r56b :: case_labels >> case_label
@R r56c :: case_labels >> case_labels case_label


##57 kw default case
@R r57a :: case_label >> case const_expr : 
@R r57b :: case_label >> default :

##58
@R r58 :: element_spec >> type_spec declarator

##59 kw enum
@R r59a :: enum_type >> enum identifier { enumerators }
@R r59b :: enumerators >> enumerator
@R r59c :: enumerators >> enumerators , enumerator

##60
@R r60 :: enumerator >> identifier

##61 kw sequence
@R r61 :: sequence_type >> sequence < simple_type_spec , positive_int_const >

##62 kw string
@R r62a :: string_type >> string < positive_int_const >
@R r62b :: string_type >> string

##63
@R r63a :: array_declarator >> identifier fixed_array_sizes
@R r63b :: fixed_array_sizes >> fixed_array_size
@R r63c :: fixed_array_sizes >> fixed_array_sizes fixed_array_size

##64
@R r64 :: fixed_array_size >> [ positive_int_const ]

##65 kw attribute readonly
@R r65a :: attr_dcl >> maybe_readonly attribute param_type_spec simple_declarators
@R r65b :: maybe_readonly >> readonly
@R r65c :: maybe_readonly >>
@R r65d :: simple_declarators >> simple_declarator
@R r65e :: simple_declarators >> simple_declarators , simple_declarator

##66 kw exception
@R r66a :: except_dcl >> exception identifier { members }
@R r66b :: members >>
@R r66c :: members >> member_list

##67
@R r67a :: op_dcl >> 
   maybe_op_attribute op_type_spec identifier parameter_dcls
   maybe_raises_expr maybe_context_expr
@R r67b :: maybe_op_attribute >> 
@R r67c :: maybe_op_attribute >> op_attribute
@R r67d :: maybe_raises_expr >>
@R r67e :: maybe_raises_expr >> raises_expr
@R r67f :: maybe_context_expr >>
@R r67g :: maybe_context_expr >> context_expr

##68 kw oneway
@R r68a :: op_attribute >> oneway

##69 kw void
@R r69a :: op_type_spec >> param_type_spec
@R r69b :: op_type_spec >> void

##70
@R r70a :: parameter_dcls >> ( parameterlist )
@R r70b :: parameter_dcls >> (  )
@R r70c :: parameterlist >> param_dcl
@R r70d :: parameterlist >> parameterlist , param_dcl

##71
@R r71 :: param_dcl >> param_attribute param_type_spec simple_declarator

##72 kw in out inout
@R r72 :: param_attribute >> in
@R r72 :: param_attribute >> out
@R r72 :: param_attribute >> inout

##73 kw raises
@R r73 :: raises_expr >> raises ( scoped_name_list )

##74 kw context
@R r74 :: context_expr >> context ( string_literal_list )
@R r74b :: string_literal_list >> string_literal
@R r74c :: string_literal_list >> string_literal_list , string_literal

@R r75 :: param_type_spec >> base_type_spec
@R r75 :: param_type_spec >> string_type
@R r75 :: param_type_spec >> scoped_name

"""

nonterms = """
colon_colon
param_attribute
unsigned_long_int unsigned_short_int param_dcl
parameterlist string_literal_list
members maybe_op_attribute maybe_raises_expr maybe_context_expr
op_type_spec parameter_dcls op_attribute raises_expr context_expr
maybe_readonly param_type_spec simple_declarators simple_declarator
fixed_array_sizes fixed_array_size
element_spec enumerator enumerators
switch_type_spec switch_body case_nt case_labels case_label
member_list member
signed_int unsigned_int signed_long_int signed_short_int
simple_declarator complex_declarator array_declarator
declarator 
sequence_type string_type
floating_pt_type integer_type char_type boolean_type
octet_type any_type
base_type_spec template_type_spec
simple_type_spec constr_type_spec
type_spec declarators
type_declarator struct_type union_type enum_type
literal boolean_literal positive_int_literal
mult_expr unary_expr unary_operator primary_expr
or_expr xor_expr and_expr shift_expr add_expr
integer_type char_type boolean_type floating_type string_type
const_type const_expr
scoped_name_list scoped_name
attr_dcl op_dcl
inheritance_spec export
interface_header interface_body
interface_dcl forward_dcl
type_dcl const_dcl except_dcl interface_nt module_nt
specification definition speclist
"""

keywords = """
exception oneway void in out inout raises context
interface module const TRUE FALSE typedef float double long
unsigned short char boolean octet any struct union switch
enum string attribute readonly default case sequence ::
""" 
# NOTE: FOR NECESSARY HACKERY REASONS :: IS A KEYWORD!

punctuations = ";{}()[],:|^&<>+-*/%~="

# dummy regexen
identifierre = "identifier"
integer_literalre = "123"
positive_int_constre = "999"
string_literalre = "'string'"
character_literalre= "'c'"
floating_pt_literalre = "1.23"


# dummy interp fun for all terminals
def echo (str):
    return str

def DeclareTerminals(Grammar):
    Grammar.Addterm("identifier", identifierre, echo)
    Grammar.Addterm("integer_literal", integer_literalre, echo)
    Grammar.Addterm("string_literal", string_literalre, echo)
    Grammar.Addterm("character_literal", character_literalre, echo)
    Grammar.Addterm("floating_pt_literal", floating_pt_literalre, echo)
    Grammar.Addterm("positive_int_const", positive_int_constre, echo)

## we need to override LexDictionary to recognize :: as a SINGLE punctuation.
## (not possible using standard kjParsing, requires a special override)
import kjParser
class myLexDictionary(kjParser.LexDictionary):
   def __init__(self):
       kjParser.LexDictionary.__init__(self)
       map = ((kjParser.KEYFLAG, "coloncolon"), "coloncolon")
       self.keywordmap["::"] = map
       self.keywordmap["coloncolon"] = map
       
   def Token(self, String, StartPosition):
       if String[StartPosition:StartPosition+2] == "::":
          tok = self.keywordmap["::"]
          return (tok, 2)
       # default:
       return kjParseBuild.LexDictionary.Token(self, String, StartPosition)

# default bind all rules

def GrammarBuild():
    import kjParseBuild
    idl = kjParseBuild.NullCGrammar()
    idl.LexD = myLexDictionary()
    #idl.SetCaseSensitivity(0) # grammar is not case sensitive for keywords
    DeclareTerminals(idl)
    idl.Keywords(keywords)
    idl.punct(punctuations)
    idl.Nonterms(nonterms)
    #idl.comments([LISPCOMMENTREGEX])
    idl.Declarerules(idlgramstring)
    print "now compiling"
    idl.Compile()
    return idl

if __name__=="__main__": GrammarBuild()