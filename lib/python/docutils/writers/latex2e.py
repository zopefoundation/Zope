"""
:Author: Engelbert Gruber
:Contact: grubert@users.sourceforge.net
:Revision: $Revision: 1.1 $
:Date: $Date: 2003/07/10 15:50:05 $
:Copyright: This module has been placed in the public domain.

LaTeX2e document tree Writer.
"""

__docformat__ = 'reStructuredText'

# code contributions from several people included, thanks too all.
# some named: David Abrahams, Julien Letessier, who is missing.
#
# convention deactivate code by two # e.g. ##.

import sys
import time
import re
import string
from types import ListType
from docutils import writers, nodes, languages

class Writer(writers.Writer):

    supported = ('latex','latex2e')
    """Formats this writer supports."""

    settings_spec = (
        'LaTeX-Specific Options',
        'The LaTeX "--output-encoding" default is "latin-1:strict".',
        (('Specify documentclass.  Default is "article".',
          ['--documentclass'],
          {'default': 'article', }),
         ('Format for footnote references: one of "superscript" or '
          '"brackets".  Default is "brackets".',
          ['--footnote-references'],
          {'choices': ['superscript', 'brackets'], 'default': 'brackets',
           'metavar': '<format>'}),
         ('Format for block quote attributions: one of "dash" (em-dash '
          'prefix), "parentheses"/"parens", or "none".  Default is "dash".',
          ['--attribution'],
          {'choices': ['dash', 'parentheses', 'parens', 'none'],
           'default': 'dash', 'metavar': '<format>'}),
         ('Specify a stylesheet file. The file will be "input" by latex '
          'in the document header. Default is "style.tex". '
          'If this is set to "" disables input.'
          'Overridden by --stylesheet-path.',
          ['--stylesheet'],
          {'default': 'style.tex', 'metavar': '<file>'}),
         ('Specify a stylesheet file, relative to the current working '
          'directory.'
          'Overrides --stylesheet.',
          ['--stylesheet-path'],
          {'metavar': '<file>'}),
         ('Link to the stylesheet in the output LaTeX file.  This is the '
          'default.',
          ['--link-stylesheet'],
          {'dest': 'embed_stylesheet', 'action': 'store_false'}),
         ('Embed the stylesheet in the output LaTeX file.  The stylesheet '
          'file must be accessible during processing (--stylesheet-path is '
          'recommended).',
          ['--embed-stylesheet'],
          {'action': 'store_true'}),
         ('Table of contents by docutils (default) or latex. Latex(writer) '
          'supports only one ToC per document, but docutils does not write '
          'pagenumbers.',
          ['--use-latex-toc'], {'default': 0}),
         ('Color of any hyperlinks embedded in text '
          '(default: "blue", "0" to disable).',
          ['--hyperlink-color'], {'default': 'blue'}),))

    settings_defaults = {'output_encoding': 'latin-1'}

    output = None
    """Final translated form of `document`."""

    def translate(self):
        visitor = LaTeXTranslator(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()
        self.head_prefix = visitor.head_prefix
        self.head = visitor.head
        self.body_prefix = visitor.body_prefix
        self.body = visitor.body
        self.body_suffix = visitor.body_suffix

"""
Notes on LaTeX
--------------

* latex does not support multiple tocs in one document.
  (might be no limitation except for docutils documentation)

* width 

  * linewidth - width of a line in the local environment
  * textwidth - the width of text on the page

  Maybe always use linewidth ?
"""    

class Babel:
    """Language specifics for LaTeX."""
    # country code by a.schlock.
    # partly manually converted from iso and babel stuff, dialects and some
    _ISO639_TO_BABEL = {
        'no': 'norsk',     #XXX added by hand ( forget about nynorsk?)
        'gd': 'scottish',  #XXX added by hand
        'hu': 'magyar',    #XXX added by hand
        'pt': 'portuguese',#XXX added by hand
        'sl': 'slovenian',
        'af': 'afrikaans',
        'bg': 'bulgarian',
        'br': 'breton',
        'ca': 'catalan',
        'cs': 'czech',
        'cy': 'welsh',
        'da': 'danish',
        'fr': 'french',
        # french, francais, canadien, acadian
        'de': 'ngerman',  #XXX rather than german
        # ngerman, naustrian, german, germanb, austrian
        'el': 'greek',
        'en': 'english',
        # english, USenglish, american, UKenglish, british, canadian
        'eo': 'esperanto',
        'es': 'spanish',
        'et': 'estonian',
        'eu': 'basque',
        'fi': 'finnish',
        'ga': 'irish',
        'gl': 'galician',
        'he': 'hebrew',
        'hr': 'croatian',
        'hu': 'hungarian',
        'is': 'icelandic',
        'it': 'italian',
        'la': 'latin',
        'nl': 'dutch',
        'pl': 'polish',
        'pt': 'portuguese',
        'ro': 'romanian',
        'ru': 'russian',
        'sk': 'slovak',
        'sr': 'serbian',
        'sv': 'swedish',
        'tr': 'turkish',
        'uk': 'ukrainian'
    }

    def __init__(self,lang):
        self.language = lang
        # pdflatex does not produce double quotes for ngerman in tt.
        self.double_quote_replacment = None
        if re.search('^de',self.language):
            # maybe use: {\glqq} {\grqq}.
            self.quotes = ("\"`", "\"'")
            self.double_quote_replacment = "{\\dq}"
        else:    
            self.quotes = ("``", "''")
        self.quote_index = 0
        
    def next_quote(self):
        q = self.quotes[self.quote_index]
        self.quote_index = (self.quote_index+1)%2
        return q

    def quote_quotes(self,text):
        t = None
        for part in text.split('"'):
            if t == None:
                t = part
            else:
                t += self.next_quote() + part
        return t

    def double_quotes_in_tt (self,text):
        if not self.double_quote_replacment:
            return text
        return text.replace('"', self.double_quote_replacment)

    def get_language(self):
        if self._ISO639_TO_BABEL.has_key(self.language):
            return self._ISO639_TO_BABEL[self.language]
        else:
            # support dialects.
            l = self.language.split("_")[0]
            if self._ISO639_TO_BABEL.has_key(l):
                return self._ISO639_TO_BABEL[l]
        return None


latex_headings = {
        'optionlist_environment' : [
              '\\newcommand{\\optionlistlabel}[1]{\\bf #1 \\hfill}\n'
              '\\newenvironment{optionlist}[1]\n'
              '{\\begin{list}{}\n'
              '  {\\setlength{\\labelwidth}{#1}\n'
              '   \\setlength{\\rightmargin}{1cm}\n'
              '   \\setlength{\\leftmargin}{\\rightmargin}\n'
              '   \\addtolength{\\leftmargin}{\\labelwidth}\n'
              '   \\addtolength{\\leftmargin}{\\labelsep}\n'
              '   \\renewcommand{\\makelabel}{\\optionlistlabel}}\n'
              '}{\\end{list}}\n',
              ],
        'footnote_floats' : [
            '% begin: floats for footnotes tweaking.\n',
            '\\setlength{\\floatsep}{0.5em}\n',
            '\\setlength{\\textfloatsep}{\\fill}\n',
            '\\addtolength{\\textfloatsep}{3em}\n',
            '\\renewcommand{\\textfraction}{0.5}\n',
            '\\renewcommand{\\topfraction}{0.5}\n',
            '\\renewcommand{\\bottomfraction}{0.5}\n',
            '\\setcounter{totalnumber}{50}\n',
            '\\setcounter{topnumber}{50}\n',
            '\\setcounter{bottomnumber}{50}\n',
            '% end floats for footnotes\n',
            ],
         'some_commands' : [
            '% some commands, that could be overwritten in the style file.\n'
            '\\newcommand{\\rubric}[1]'
            '{\\subsection*{~\\hfill {\\it #1} \\hfill ~}}\n'
            '% end of "some commands"\n',
         ]
        }


class LaTeXTranslator(nodes.NodeVisitor):
    # When options are given to the documentclass, latex will pass them
    # to other packages, as done with babel. 
    # Dummy settings might be taken from document settings

    d_options = '10pt'  # papersize, fontsize
    d_paper = 'a4paper'
    d_margins = '2cm'

    latex_head = '\\documentclass[%s]{%s}\n'
    encoding = '\\usepackage[%s]{inputenc}\n'
    linking = '\\usepackage[colorlinks=%s,linkcolor=%s,urlcolor=%s]{hyperref}\n'
    geometry = '\\usepackage[%s,margin=%s,nohead]{geometry}\n'
    stylesheet = '\\input{%s}\n'
    # add a generated on day , machine by user using docutils version.
    generator = '%% generator Docutils: http://docutils.sourceforge.net/\n'

    # use latex tableofcontents or let docutils do it.
    use_latex_toc = 0
    # table kind: if 0 tabularx (single page), 1 longtable
    # maybe should be decided on row count.
    use_longtable = 1
    # TODO: use mixins for different implementations.
    # list environment for option-list. else tabularx
    use_optionlist_for_option_list = 1
    # list environment for docinfo. else tabularx
    use_optionlist_for_docinfo = 0 # NOT YET IN USE

    # default link color
    hyperlink_color = "blue"

    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self.settings = settings = document.settings
        self.use_latex_toc = settings.use_latex_toc
        self.hyperlink_color = settings.hyperlink_color
        if self.hyperlink_color == '0':
            self.hyperlink_color = 'black'
            self.colorlinks = 'false'
        else:
            self.colorlinks = 'true'
            
        # language: labels, bibliographic_fields, and author_separators.
        # to allow writing labes for specific languages.
        self.language = languages.get_language(settings.language_code)
        self.babel = Babel(settings.language_code)
        self.author_separator = self.language.author_separators[0]
        if self.babel.get_language():
            self.d_options += ',%s' % \
                    self.babel.get_language()
        self.head_prefix = [
              self.latex_head % (self.d_options,self.settings.documentclass),
              '\\usepackage{babel}\n',     # language is in documents settings.
              '\\usepackage{shortvrb}\n',  # allows verb in footnotes.
              self.encoding % self.to_latex_encoding(settings.output_encoding),
              # * tabularx: for docinfo, automatic width of columns, always on one page.
              '\\usepackage{tabularx}\n',
              '\\usepackage{longtable}\n',
              # possible other packages.
              # * fancyhdr
              # * ltxtable is a combination of tabularx and longtable (pagebreaks).
              #   but ??
              #
              # extra space between text in tables and the line above them
              '\\setlength{\\extrarowheight}{2pt}\n',
              '\\usepackage{amsmath}\n',   # what fore amsmath. 
              '\\usepackage{graphicx}\n',
              '\\usepackage{color}\n',
              '\\usepackage{multirow}\n',
              self.linking % (self.colorlinks, self.hyperlink_color, self.hyperlink_color),
              # geometry and fonts might go into style.tex.
              self.geometry % (self.d_paper, self.d_margins),
              #
              self.generator,
              # latex lengths
              '\\newlength{\\admonitionwidth}\n',
              '\\setlength{\\admonitionwidth}{0.9\\textwidth}\n' 
              # width for docinfo tablewidth
              '\\newlength{\\docinfowidth}\n',
              '\\setlength{\\docinfowidth}{0.9\\textwidth}\n' 
              ]
        self.head_prefix.extend( latex_headings['optionlist_environment'] )
        self.head_prefix.extend( latex_headings['footnote_floats'] )
        self.head_prefix.extend( latex_headings['some_commands'] )
        ## stylesheet is last: so it might be possible to overwrite defaults.
        stylesheet = self.get_stylesheet_reference()
        if stylesheet:
            self.head_prefix.append(self.stylesheet % (stylesheet))

        if self.linking: # and maybe check for pdf
            self.pdfinfo = [ ]
            self.pdfauthor = None
            # pdftitle, pdfsubject, pdfauthor, pdfkeywords, pdfcreator, pdfproducer
        else:
            self.pdfinfo = None
        # NOTE: Latex wants a date and an author, rst puts this into
        #   docinfo, so normally we donot want latex author/date handling.
        # latex article has its own handling of date and author, deactivate.
        self.latex_docinfo = 0
        self.head = [ ]
        if not self.latex_docinfo:
            self.head.extend( [ '\\author{}\n', '\\date{}\n' ] )
        self.body_prefix = ['\\raggedbottom\n']
        # separate title, so we can appen subtitle.
        self.title = ""
        self.body = []
        self.body_suffix = ['\n']
        self.section_level = 0
        self.context = []
        self.topic_class = ''
        # column specification for tables
        self.colspecs = []
        # Flags to encode
        # ---------------
        # verbatim: to tell encode not to encode.
        self.verbatim = 0
        # insert_newline: to tell encode to replace blanks by "~".
        self.insert_none_breaking_blanks = 0
        # insert_newline: to tell encode to add latex newline.
        self.insert_newline = 0
        # mbox_newline: to tell encode to add mbox and newline.
        self.mbox_newline = 0

        # enumeration is done by list environment.
        self._enum_cnt = 0
        # docinfo. 
        self.docinfo = None
        # inside literal block: no quote mangling.
        self.literal_block = 0
        self.literal = 0

    def get_stylesheet_reference(self):
        if self.settings.stylesheet_path:
            return self.settings.stylesheet_path
        else:
            return self.settings.stylesheet

    def to_latex_encoding(self,docutils_encoding):
        """
        Translate docutils encoding name into latex's.

        Default fallback method is remove "-" and "_" chars from docutils_encoding.

        """
        tr = {  "iso-8859-1": "latin1",     # west european
                "iso-8859-2": "latin2",     # east european
                "iso-8859-3": "latin3",     # esperanto, maltese
                "iso-8859-4": "latin4",     # north european,scandinavian, baltic
                "iso-8859-5": "iso88595",   # cyrillic (ISO)
                "iso-8859-9": "latin5",     # turkish
                "iso-8859-15": "latin9",    # latin9, update to latin1.
                "mac_cyrillic": "maccyr",   # cyrillic (on Mac)
                "windows-1251": "cp1251",   # cyrillic (on Windows)
                "koi8-r": "koi8-r",         # cyrillic (Russian)
                "koi8-u": "koi8-u",         # cyrillic (Ukrainian)
                "windows-1250": "cp1250",   # 
                "windows-1252": "cp1252",   # 
                "us-ascii": "ascii",        # ASCII (US) 
                # unmatched encodings
                #"": "applemac",
                #"": "ansinew",  # windows 3.1 ansi
                #"": "ascii",    # ASCII encoding for the range 32--127.
                #"": "cp437",    # dos latine us
                #"": "cp850",    # dos latin 1
                #"": "cp852",    # dos latin 2
                #"": "decmulti",
                #"": "latin10",
                #"iso-8859-6": ""   # arabic
                #"iso-8859-7": ""   # greek
                #"iso-8859-8": ""   # hebrew
                #"iso-8859-10": ""   # latin6, more complete iso-8859-4
             }
        if tr.has_key(docutils_encoding.lower()):
            return tr[docutils_encoding.lower()]
        return docutils_encoding.translate(string.maketrans("",""),"_-").lower()

    def language_label(self, docutil_label):
        return self.language.labels[docutil_label]

    def encode(self, text):
        """
        Encode special characters in `text` & return.
            # $ % & ~ _ ^ \ { }
        Escaping with a backslash does not help with backslashes, ~ and ^.

            < > are only available in math-mode (really ?)
            $ starts math- mode.
        AND quotes:
        
        """
        if self.verbatim:
            return text
        # compile the regexps once. do it here so one can see them.
        #
        # first the braces.
        if not self.__dict__.has_key('encode_re_braces'):
            self.encode_re_braces = re.compile(r'([{}])')
        text = self.encode_re_braces.sub(r'{\\\1}',text)
        if not self.__dict__.has_key('encode_re_bslash'):
            # find backslash: except in the form '{\{}' or '{\}}'.
            self.encode_re_bslash = re.compile(r'(?<!{)(\\)(?![{}]})')
        # then the backslash: except in the form from line above:
        # either '{\{}' or '{\}}'.
        text = self.encode_re_bslash.sub(r'{\\textbackslash}', text)

        # then dollar
        text = text.replace("$", '{\\$}')
        # then all that needs math mode
        text = text.replace("<", '{$<$}')
        text = text.replace(">", '{$>$}')
        # then
        text = text.replace("&", '{\\&}')
        text = text.replace("_", '{\\_}')
        # the ^:
        # * verb|^| does not work in mbox.
        # * mathmode has wedge. hat{~} would also work.
        text = text.replace("^", '{\\ensuremath{^\\wedge}}')
        text = text.replace("%", '{\\%}')
        text = text.replace("#", '{\\#}')
        text = text.replace("~", '{\\~{ }}')
        if self.literal_block or self.literal:
            # pdflatex does not produce doublequotes for ngerman.
            text = self.babel.double_quotes_in_tt(text)
        else:
            text = self.babel.quote_quotes(text)
        if self.insert_newline:
            # HACK: insert a blank before the newline, to avoid 
            # ! LaTeX Error: There's no line here to end.
            text = text.replace("\n", '~\\\\\n')
        elif self.mbox_newline:
            text = text.replace("\n", '}\\\\\n\\mbox{')
        if self.insert_none_breaking_blanks:
            text = text.replace(' ', '~')
        # unicode !!! 
        text = text.replace(u'\u2020', '{$\\dagger$}')
        return text

    def attval(self, text,
               whitespace=re.compile('[\n\r\t\v\f]')):
        """Cleanse, encode, and return attribute value text."""
        return self.encode(whitespace.sub(' ', text))

    def astext(self):
        if self.pdfinfo:
            if self.pdfauthor:
                self.pdfinfo.append('pdfauthor={%s}' % self.pdfauthor)
            pdfinfo = '\\hypersetup{\n' + ',\n'.join(self.pdfinfo) + '\n}\n'
        else:
            pdfinfo = ''
        title = '\\title{%s}\n' % self.title
        return ''.join(self.head_prefix + [title]  
                        + self.head + [pdfinfo]
                        + self.body_prefix  + self.body + self.body_suffix)

    def visit_Text(self, node):
        self.body.append(self.encode(node.astext()))

    def depart_Text(self, node):
        pass

    def visit_address(self, node):
        self.visit_docinfo_item(node, 'address')

    def depart_address(self, node):
        self.depart_docinfo_item(node)

    def visit_admonition(self, node, name):
        self.body.append('\\begin{center}\\begin{sffamily}\n')
        self.body.append('\\fbox{\\parbox{\\admonitionwidth}{\n')
        self.body.append('\\textbf{\\large '+ self.language.labels[name] + '}\n');
        self.body.append('\\vspace{2mm}\n')


    def depart_admonition(self):
        self.body.append('}}\n') # end parbox fbox
        self.body.append('\\end{sffamily}\n\\end{center}\n');

    def visit_attention(self, node):
        self.visit_admonition(node, 'attention')

    def depart_attention(self, node):
        self.depart_admonition()

    def visit_author(self, node):
        self.visit_docinfo_item(node, 'author')

    def depart_author(self, node):
        self.depart_docinfo_item(node)

    def visit_authors(self, node):
        # ignore. visit_author is called for each one
        # self.visit_docinfo_item(node, 'author')
        pass

    def depart_authors(self, node):
        # self.depart_docinfo_item(node)
        pass

    def visit_block_quote(self, node):
        self.body.append( '\\begin{quote}\n')

    def depart_block_quote(self, node):
        self.body.append( '\\end{quote}\n')

    def visit_bullet_list(self, node):
        if not self.use_latex_toc and self.topic_class == 'contents':
            self.body.append( '\\begin{list}{}{}\n' )
        else:
            self.body.append( '\\begin{itemize}\n' )

    def depart_bullet_list(self, node):
        if not self.use_latex_toc and self.topic_class == 'contents':
            self.body.append( '\\end{list}\n' )
        else:
            self.body.append( '\\end{itemize}\n' )

    def visit_caption(self, node):
        self.body.append( '\\caption{' )

    def depart_caption(self, node):
        self.body.append('}')

    def visit_caution(self, node):
        self.visit_admonition(node, 'caution')

    def depart_caution(self, node):
        self.depart_admonition()

    def visit_citation(self, node):
        self.visit_footnote(node)

    def depart_citation(self, node):
        self.depart_footnote(node)

    def visit_title_reference(self, node):
        # BUG title-references are what?
        pass

    def depart_title_reference(self, node):
        pass

    def visit_citation_reference(self, node):
        href = ''
        if node.has_key('refid'):
            href = node['refid']
        elif node.has_key('refname'):
            href = self.document.nameids[node['refname']]
        self.body.append('[\\hyperlink{%s}{' % href)

    def depart_citation_reference(self, node):
        self.body.append('}]')

    def visit_classifier(self, node):
        self.body.append( '(\\textbf{' )

    def depart_classifier(self, node):
        self.body.append( '})\n' )

    def visit_colspec(self, node):
        if self.use_longtable:
            self.colspecs.append(node)
        else:    
            self.context[-1] += 1

    def depart_colspec(self, node):
        pass

    def visit_comment(self, node,
                      sub=re.compile('\n').sub):
        """Escape end of line by a ne comment start in comment text."""
        self.body.append('%% %s \n' % sub('\n% ', node.astext()))
        raise nodes.SkipNode

    def visit_contact(self, node):
        self.visit_docinfo_item(node, 'contact')

    def depart_contact(self, node):
        self.depart_docinfo_item(node)

    def visit_copyright(self, node):
        self.visit_docinfo_item(node, 'copyright')

    def depart_copyright(self, node):
        self.depart_docinfo_item(node)

    def visit_danger(self, node):
        self.visit_admonition(node, 'danger')

    def depart_danger(self, node):
        self.depart_admonition()

    def visit_date(self, node):
        self.visit_docinfo_item(node, 'date')

    def depart_date(self, node):
        self.depart_docinfo_item(node)

    def visit_decoration(self, node):
        pass

    def depart_decoration(self, node):
        pass

    def visit_definition(self, node):
        self.body.append('%[visit_definition]\n')

    def depart_definition(self, node):
        self.body.append('\n')
        self.body.append('%[depart_definition]\n')

    def visit_definition_list(self, node):
        self.body.append( '\\begin{description}\n' )

    def depart_definition_list(self, node):
        self.body.append( '\\end{description}\n' )

    def visit_definition_list_item(self, node):
        self.body.append('%[visit_definition_list_item]\n')

    def depart_definition_list_item(self, node):
        self.body.append('%[depart_definition_list_item]\n')

    def visit_description(self, node):
        if self.use_optionlist_for_option_list:
            self.body.append( ' ' )
        else:    
            self.body.append( ' & ' )

    def depart_description(self, node):
        pass

    def visit_docinfo(self, node):
        self.docinfo = []
        self.docinfo.append('%' + '_'*75 + '\n')
        self.docinfo.append('\\begin{center}\n')
        self.docinfo.append('\\begin{tabularx}{\\docinfowidth}{lX}\n')

    def depart_docinfo(self, node):
        self.docinfo.append('\\end{tabularx}\n')
        self.docinfo.append('\\end{center}\n')
        self.body = self.docinfo + self.body
        # clear docinfo, so field names are no longer appended.
        self.docinfo = None
        if self.use_latex_toc:
            self.body.append('\\tableofcontents\n\n\\bigskip\n')

    def visit_docinfo_item(self, node, name):
        if not self.latex_docinfo:
            self.docinfo.append('\\textbf{%s}: &\n\t' % self.language_label(name))
        if name == 'author':
            if not self.pdfinfo == None:
                if not self.pdfauthor:
                    self.pdfauthor = self.attval(node.astext())
                else:
                    self.pdfauthor += self.author_separator + self.attval(node.astext())
            if self.latex_docinfo:
                self.head.append('\\author{%s}\n' % self.attval(node.astext()))
                raise nodes.SkipNode
        elif name == 'date':
            if self.latex_docinfo:
                self.head.append('\\date{%s}\n' % self.attval(node.astext()))
                raise nodes.SkipNode
        if name == 'address':
            # BUG will fail if latex_docinfo is set.
            self.insert_newline = 1 
            self.docinfo.append('{\\raggedright\n')
            self.context.append(' } \\\\\n')
        else:    
            self.context.append(' \\\\\n')
        self.context.append(self.docinfo)
        self.context.append(len(self.body))

    def depart_docinfo_item(self, node):
        size = self.context.pop()
        dest = self.context.pop()
        tail = self.context.pop()
        tail = self.body[size:] + [tail]
        del self.body[size:]
        dest.extend(tail)
        # for address we did set insert_newline
        self.insert_newline = 0

    def visit_doctest_block(self, node):
        self.body.append( '\\begin{verbatim}' )
        self.verbatim = 1

    def depart_doctest_block(self, node):
        self.body.append( '\\end{verbatim}\n' )
        self.verbatim = 0

    def visit_document(self, node):
        self.body_prefix.append('\\begin{document}\n')
        self.body_prefix.append('\\maketitle\n\n')
        # alternative use titlepage environment.
        # \begin{titlepage}

    def depart_document(self, node):
        self.body_suffix.append('\\end{document}\n')

    def visit_emphasis(self, node):
        self.body.append('\\emph{')

    def depart_emphasis(self, node):
        self.body.append('}')

    def visit_entry(self, node):
        # cell separation
        column_one = 1
        if self.context[-1] > 0:
            column_one = 0
        if not column_one:
            self.body.append(' & ')

        # multi{row,column}
        if node.has_key('morerows') and node.has_key('morecols'):
            raise NotImplementedError('LaTeX can\'t handle cells that'
            'span multiple rows *and* columns, sorry.')
        atts = {}
        if node.has_key('morerows'):
            count = node['morerows'] + 1
            self.body.append('\\multirow{%d}*{' % count)
            self.context.append('}')
        elif node.has_key('morecols'):
            # the vertical bar before column is missing if it is the first column.
            # the one after always.
            if column_one:
                bar = '|'
            else:
                bar = ''
            count = node['morecols'] + 1
            self.body.append('\\multicolumn{%d}{%sl|}{' % (count, bar))
            self.context.append('}')
        else:
            self.context.append('')

        # header / not header
        if isinstance(node.parent.parent, nodes.thead):
            self.body.append('\\textbf{')
            self.context.append('}')
        else:
            self.context.append('')

    def depart_entry(self, node):
        self.body.append(self.context.pop()) # header / not header
        self.body.append(self.context.pop()) # multirow/column
        self.context[-1] += 1

    def visit_enumerated_list(self, node):
        # We create our own enumeration list environment.
        # This allows to set the style and starting value
        # and unlimited nesting.
        self._enum_cnt += 1

        enum_style = {'arabic':'arabic',
                'loweralpha':'alph',
                'upperalpha':'Alph', 
                'lowerroman':'roman',
                'upperroman':'Roman' }
        enum_suffix = ""
        if node.has_key('suffix'):
            enum_suffix = node['suffix']
        enum_prefix = ""
        if node.has_key('prefix'):
            enum_prefix = node['prefix']
        
        enum_type = "arabic"
        if node.has_key('enumtype'):
            enum_type = node['enumtype']
        if enum_style.has_key(enum_type):
            enum_type = enum_style[enum_type]
        counter_name = "listcnt%d" % self._enum_cnt;
        self.body.append('\\newcounter{%s}\n' % counter_name)
        self.body.append('\\begin{list}{%s\\%s{%s}%s}\n' % \
            (enum_prefix,enum_type,counter_name,enum_suffix))
        self.body.append('{\n')
        self.body.append('\\usecounter{%s}\n' % counter_name)
        # set start after usecounter, because it initializes to zero.
        if node.has_key('start'):
            self.body.append('\\addtocounter{%s}{%d}\n' \
                    % (counter_name,node['start']-1))
        ## set rightmargin equal to leftmargin
        self.body.append('\\setlength{\\rightmargin}{\\leftmargin}\n')
        self.body.append('}\n')

    def depart_enumerated_list(self, node):
        self.body.append('\\end{list}\n')

    def visit_error(self, node):
        self.visit_admonition(node, 'error')

    def depart_error(self, node):
        self.depart_admonition()

    def visit_field(self, node):
        # real output is done in siblings: _argument, _body, _name
        pass

    def depart_field(self, node):
        self.body.append('\n')
        ##self.body.append('%[depart_field]\n')

    def visit_field_argument(self, node):
        self.body.append('%[visit_field_argument]\n')

    def depart_field_argument(self, node):
        self.body.append('%[depart_field_argument]\n')

    def visit_field_body(self, node):
        # BUG by attach as text we loose references.
        if self.docinfo:
            self.docinfo.append('%s \\\\\n' % node.astext())
            raise nodes.SkipNode
        # BUG: what happens if not docinfo

    def depart_field_body(self, node):
        self.body.append( '\n' )

    def visit_field_list(self, node):
        if not self.docinfo:
            self.body.append('\\begin{quote}\n')
            self.body.append('\\begin{description}\n')

    def depart_field_list(self, node):
        if not self.docinfo:
            self.body.append('\\end{description}\n')
            self.body.append('\\end{quote}\n')

    def visit_field_name(self, node):
        # BUG this duplicates docinfo_item
        if self.docinfo:
            self.docinfo.append('\\textbf{%s}: &\n\t' % node.astext())
            raise nodes.SkipNode
        else:
            self.body.append('\\item [')

    def depart_field_name(self, node):
        if not self.docinfo:
            self.body.append(':]')

    def visit_figure(self, node):
        self.body.append( '\\begin{figure}\n' )

    def depart_figure(self, node):
        self.body.append( '\\end{figure}\n' )

    def visit_footer(self, node):
        self.context.append(len(self.body))

    def depart_footer(self, node):
        start = self.context.pop()
        footer = (['\n\\begin{center}\small\n']
                  + self.body[start:] + ['\n\\end{center}\n'])
        self.body_suffix[:0] = footer
        del self.body[start:]

    def visit_footnote(self, node):
        notename = node['id']
        self.body.append('\\begin{figure}[b]')
        self.body.append('\\hypertarget{%s}' % notename)

    def depart_footnote(self, node):
        self.body.append('\\end{figure}\n')

    def visit_footnote_reference(self, node):
        href = ''
        if node.has_key('refid'):
            href = node['refid']
        elif node.has_key('refname'):
            href = self.document.nameids[node['refname']]
        format = self.settings.footnote_references
        if format == 'brackets':
            suffix = '['
            self.context.append(']')
        elif format == 'superscript':
            suffix = '\\raisebox{.5em}[0em]{\\scriptsize'
            self.context.append('}')
        else:                           # shouldn't happen
            raise AssertionError('Illegal footnote reference format.')
        self.body.append('%s\\hyperlink{%s}{' % (suffix,href))

    def depart_footnote_reference(self, node):
        self.body.append('}%s' % self.context.pop())

    def visit_generated(self, node):
        pass

    def depart_generated(self, node):
        pass

    def visit_header(self, node):
        self.context.append(len(self.body))

    def depart_header(self, node):
        start = self.context.pop()
        self.body_prefix.append('\n\\verb|begin_header|\n')
        self.body_prefix.extend(self.body[start:])
        self.body_prefix.append('\n\\verb|end_header|\n')
        del self.body[start:]

    def visit_hint(self, node):
        self.visit_admonition(node, 'hint')

    def depart_hint(self, node):
        self.depart_admonition()

    def visit_image(self, node):
        atts = node.attributes.copy()
        href = atts['uri']
        ##self.body.append('\\begin{center}\n')
        self.body.append('\n\\includegraphics{%s}\n' % href)
        ##self.body.append('\\end{center}\n')

    def depart_image(self, node):
        pass

    def visit_important(self, node):
        self.visit_admonition(node, 'important')

    def depart_important(self, node):
        self.depart_admonition()

    def visit_interpreted(self, node):
        # @@@ Incomplete, pending a proper implementation on the
        # Parser/Reader end.
        self.visit_literal(node)

    def depart_interpreted(self, node):
        self.depart_literal(node)

    def visit_label(self, node):
        # footnote/citation label
        self.body.append('[')

    def depart_label(self, node):
        self.body.append(']')

    def visit_legend(self, node):
        self.body.append('{\\small ')

    def depart_legend(self, node):
        self.body.append('}')

    def visit_line_block(self, node):
        """line-block: 
        * whitespace (including linebreaks) is significant 
        * inline markup is supported. 
        * serif typeface
        """
        self.body.append('\\begin{flushleft}\n')
        self.insert_none_breaking_blanks = 1
        self.line_block_without_mbox = 1
        if self.line_block_without_mbox:
            self.insert_newline = 1
        else:
            self.mbox_newline = 1
            self.body.append('\\mbox{')

    def depart_line_block(self, node):
        if self.line_block_without_mbox:
            self.insert_newline = 0
        else:
            self.body.append('}')
            self.mbox_newline = 0
        self.insert_none_breaking_blanks = 0
        self.body.append('\n\\end{flushleft}\n')

    def visit_list_item(self, node):
        self.body.append('\\item ')

    def depart_list_item(self, node):
        self.body.append('\n')

    def visit_literal(self, node):
        self.literal = 1
        self.body.append('\\texttt{')

    def depart_literal(self, node):
        self.body.append('}')
        self.literal = 0

    def visit_literal_block(self, node):
        """
        .. parsed-literal::
        """
        # typically in a typewriter/monospaced typeface.
        # care must be taken with the text, because inline markup is recognized.
        # 
        # possibilities:
        # * verbatim: is no possibility, as inline markup does not work.
        # * obey..: is from julien and never worked for me (grubert).
        self.use_for_literal_block = "mbox"
        self.literal_block = 1
        if (self.use_for_literal_block == "mbox"):
            self.mbox_newline = 1
            self.insert_none_breaking_blanks = 1
            self.body.append('\\begin{ttfamily}\\begin{flushleft}\n\\mbox{')
        else:
            self.body.append('{\\obeylines\\obeyspaces\\ttfamily\n')

    def depart_literal_block(self, node):
        if (self.use_for_literal_block == "mbox"):
            self.body.append('}\n\\end{flushleft}\\end{ttfamily}\n')
            self.insert_none_breaking_blanks = 0
            self.mbox_newline = 0
        else:
            self.body.append('}\n')
        self.literal_block = 0

    def visit_meta(self, node):
        self.body.append('[visit_meta]\n')
        # BUG maybe set keywords for pdf
        ##self.head.append(self.starttag(node, 'meta', **node.attributes))

    def depart_meta(self, node):
        self.body.append('[depart_meta]\n')

    def visit_note(self, node):
        self.visit_admonition(node, 'note')

    def depart_note(self, node):
        self.depart_admonition()

    def visit_option(self, node):
        if self.context[-1]:
            # this is not the first option
            self.body.append(', ')

    def depart_option(self, node):
        # flag tha the first option is done.
        self.context[-1] += 1

    def visit_option_argument(self, node):
        """The delimiter betweeen an option and its argument."""
        self.body.append(node.get('delimiter', ' '))

    def depart_option_argument(self, node):
        pass

    def visit_option_group(self, node):
        if self.use_optionlist_for_option_list:
            self.body.append('\\item [')
        else:
            atts = {}
            if len(node.astext()) > 14:
                self.body.append('\\multicolumn{2}{l}{')
                self.context.append('} \\\\\n  ')
            else:
                self.context.append('')
            self.body.append('\\texttt{')
        # flag for first option    
        self.context.append(0)

    def depart_option_group(self, node):
        self.context.pop() # the flag
        if self.use_optionlist_for_option_list:
            self.body.append('] ')
        else:
            self.body.append('}')
            self.body.append(self.context.pop())

    def visit_option_list(self, node):
        self.body.append('% [option list]\n')
        if self.use_optionlist_for_option_list:
            self.body.append('\\begin{optionlist}{3cm}\n')
        else:
            self.body.append('\\begin{center}\n')
            # BUG: use admwidth or make it relative to textwidth ?
            self.body.append('\\begin{tabularx}{.9\\linewidth}{lX}\n')

    def depart_option_list(self, node):
        if self.use_optionlist_for_option_list:
            self.body.append('\\end{optionlist}\n')
        else:
            self.body.append('\\end{tabularx}\n')
            self.body.append('\\end{center}\n')

    def visit_option_list_item(self, node):
        pass

    def depart_option_list_item(self, node):
        if not self.use_optionlist_for_option_list:
            self.body.append('\\\\\n')

    def visit_option_string(self, node):
        ##self.body.append(self.starttag(node, 'span', '', CLASS='option'))
        pass

    def depart_option_string(self, node):
        ##self.body.append('</span>')
        pass

    def visit_organization(self, node):
        self.visit_docinfo_item(node, 'organization')

    def depart_organization(self, node):
        self.depart_docinfo_item(node)

    def visit_paragraph(self, node):
        if not self.topic_class == 'contents':
            self.body.append('\n')

    def depart_paragraph(self, node):
        if self.topic_class == 'contents':
            self.body.append('\n')
        else:
            self.body.append('\n')

    def visit_problematic(self, node):
        self.body.append('{\\color{red}\\bfseries{}')

    def depart_problematic(self, node):
        self.body.append('}')

    def visit_raw(self, node):
        if node.has_key('format') and node['format'].lower() == 'latex':
            self.body.append(node.astext())
        raise nodes.SkipNode

    def visit_reference(self, node):
        # for pdflatex hyperrefs might be supported
        if node.has_key('refuri'):
            href = node['refuri']
        elif node.has_key('refid'):
            href = '#' + node['refid']
        elif node.has_key('refname'):
            href = '#' + self.document.nameids[node['refname']]
        ##self.body.append('[visit_reference]')
        self.body.append('\\href{%s}{' % href)

    def depart_reference(self, node):
        self.body.append('}')
        ##self.body.append('[depart_reference]')

    def visit_revision(self, node):
        self.visit_docinfo_item(node, 'revision')

    def depart_revision(self, node):
        self.depart_docinfo_item(node)

    def visit_row(self, node):
        self.context.append(0)

    def depart_row(self, node):
        self.context.pop()  # remove cell counter
        self.body.append(' \\\\ \\hline\n')

    def visit_section(self, node):
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1

    def visit_sidebar(self, node):
        # BUG:  this is just a hack to make sidebars render something 
        self.body.append('\\begin{center}\\begin{sffamily}\n')
        self.body.append('\\fbox{\\colorbox[gray]{0.80}{\\parbox{\\admonitionwidth}{\n')

    def depart_sidebar(self, node):
        self.body.append('}}}\n') # end parbox colorbox fbox
        self.body.append('\\end{sffamily}\n\\end{center}\n');


    attribution_formats = {'dash': ('---', ''),
                           'parentheses': ('(', ')'),
                           'parens': ('(', ')'),
                           'none': ('', '')}

    def visit_attribution(self, node):
        prefix, suffix = self.attribution_formats[self.settings.attribution]
        self.body.append('\n\\begin{flushright}\n')
        self.body.append(prefix)
        self.context.append(suffix)

    def depart_attribution(self, node):
        self.body.append(self.context.pop() + '\n')
        self.body.append('\\end{flushright}\n')

    def visit_status(self, node):
        self.visit_docinfo_item(node, 'status')

    def depart_status(self, node):
        self.depart_docinfo_item(node)

    def visit_strong(self, node):
        self.body.append('\\textbf{')

    def depart_strong(self, node):
        self.body.append('}')

    def visit_substitution_definition(self, node):
        raise nodes.SkipNode

    def visit_substitution_reference(self, node):
        self.unimplemented_visit(node)

    def visit_subtitle(self, node):
        if isinstance(node.parent, nodes.sidebar):
            self.body.append('~\\\\\n\\textbf{')
            self.context.append('}\n\\smallskip\n')
        else:
            self.title = self.title + \
                '\\\\\n\\large{%s}\n' % self.encode(node.astext()) 
            raise nodes.SkipNode

    def depart_subtitle(self, node):
        if isinstance(node.parent, nodes.sidebar):
            self.body.append(self.context.pop())

    def visit_system_message(self, node):
        if node['level'] < self.document.reporter['writer'].report_level:
            raise nodes.SkipNode


    def depart_system_message(self, node):
        self.body.append('\n')

    def get_colspecs(self):
        """
        Return column specification for longtable.

        Assumes reST line length being 80 characters.
        """
        width = 80
        
        total_width = 0.0
        # first see if we get too wide.
        for node in self.colspecs:
            colwidth = float(node['colwidth']) / width 
            total_width += colwidth
        # donot make it full linewidth
        factor = 0.93
        if total_width > 1.0:
            factor /= total_width
            
        latex_table_spec = ""
        for node in self.colspecs:
            colwidth = factor * float(node['colwidth']) / width 
            latex_table_spec += "|p{%.2f\\linewidth}" % colwidth
        self.colspecs = []
        return latex_table_spec+"|"

    def visit_table(self, node):
        if self.use_longtable:
            self.body.append('\n\\begin{longtable}[c]')
        else:
            self.body.append('\n\\begin{tabularx}{\\linewidth}')
            self.context.append('table_sentinel') # sentinel
            self.context.append(0) # column counter

    def depart_table(self, node):
        if self.use_longtable:
            self.body.append('\\end{longtable}\n')
        else:    
            self.body.append('\\end{tabularx}\n')
            sentinel = self.context.pop()
            if sentinel != 'table_sentinel':
                print 'context:', self.context + [sentinel]
                raise AssertionError

    def table_preamble(self):
        if self.use_longtable:
            self.body.append('{%s}\n' % self.get_colspecs())
        else:
            if self.context[-1] != 'table_sentinel':
                self.body.append('{%s}' % ('|X' * self.context.pop() + '|'))
                self.body.append('\n\\hline')

    def visit_target(self, node):
        if not (node.has_key('refuri') or node.has_key('refid')
                or node.has_key('refname')):
            self.body.append('\\hypertarget{%s}{' % node['name'])
            self.context.append('}')
        else:
            self.context.append('')

    def depart_target(self, node):
        self.body.append(self.context.pop())

    def visit_tbody(self, node):
        # BUG write preamble if not yet done (colspecs not [])
        # for tables without heads.
        if self.colspecs:
            self.visit_thead(None)
            self.depart_thead(None)
        self.body.append('%[visit_tbody]\n')

    def depart_tbody(self, node):
        self.body.append('%[depart_tbody]\n')

    def visit_term(self, node):
        self.body.append('\\item[')

    def depart_term(self, node):
        # definition list term.
        self.body.append(':]\n')

    def visit_tgroup(self, node):
        #self.body.append(self.starttag(node, 'colgroup'))
        #self.context.append('</colgroup>\n')
        pass

    def depart_tgroup(self, node):
        pass

    def visit_thead(self, node):
        # number_of_columns will be zero after get_colspecs.
        # BUG ! push onto context for depart to pop it.
        number_of_columns = len(self.colspecs)
        self.table_preamble()
        #BUG longtable needs firstpage and lastfooter too.
        self.body.append('\\hline\n')

    def depart_thead(self, node):
        if self.use_longtable:
            # the table header written should be on every page
            # => \endhead
            self.body.append('\\endhead\n')
            # and the firsthead => \endfirsthead
            # BUG i want a "continued from previous page" on every not
            # firsthead, but then we need the header twice.
            #
            # there is a \endfoot and \endlastfoot too.
            # but we need the number of columns to 
            # self.body.append('\\multicolumn{%d}{c}{"..."}\n' % number_of_columns)
            # self.body.append('\\hline\n\\endfoot\n')
            # self.body.append('\\hline\n')
            # self.body.append('\\endlastfoot\n')
            

    def visit_tip(self, node):
        self.visit_admonition(node, 'tip')

    def depart_tip(self, node):
        self.depart_admonition()

    def visit_title(self, node):
        """Only 3 section levels are supported by LaTeX article (AFAIR)."""
        if isinstance(node.parent, nodes.topic):
            # section titles before the table of contents.
            if node.parent.hasattr('id'):
                self.body.append('\\hypertarget{%s}{}' % node.parent['id'])
            # BUG: latex chokes on center environment with "perhaps a missing item".
            # so we use hfill.
            self.body.append('\\subsection*{~\\hfill ')
            # the closing brace for subsection.
            self.context.append('\\hfill ~}\n')
        elif isinstance(node.parent, nodes.sidebar):
            self.body.append('\\textbf{\\large ')
            self.context.append('}\n\\smallskip\n')
        elif self.section_level == 0:
            # document title
            self.title = self.encode(node.astext())
            if not self.pdfinfo == None:
                self.pdfinfo.append( 'pdftitle={%s}' % self.encode(node.astext()) )
            raise nodes.SkipNode
        else:
            self.body.append('\n\n')
            self.body.append('%' + '_' * 75)
            self.body.append('\n\n')
            if node.parent.hasattr('id'):
                self.body.append('\\hypertarget{%s}{}\n' % node.parent['id'])
            # section_level 0 is title and handled above.    
            # BUG: latex has no deeper sections (actually paragrah is no section either).
            if self.use_latex_toc:
                section_star = ""
            else:
                section_star = "*"
            if (self.section_level<=3):  # 1,2,3    
                self.body.append('\\%ssection%s{' % ('sub'*(self.section_level-1),section_star))
            elif (self.section_level==4):      
                #self.body.append('\\paragraph*{')
                self.body.append('\\subsubsection%s{' % (section_star))
            else:
                #self.body.append('\\subparagraph*{')
                self.body.append('\\subsubsection%s{' % (section_star))
            # BUG: self.body.append( '\\label{%s}\n' % name)
            self.context.append('}\n')

    def depart_title(self, node):
        self.body.append(self.context.pop())
        if isinstance(node.parent, nodes.sidebar):
            return
        # BUG level depends on style.
        elif node.parent.hasattr('id') and not self.use_latex_toc:
            # pdflatex allows level 0 to 3
            # ToC would be the only on level 0 so i choose to decrement the rest.
            # "Table of contents" bookmark to see the ToC. To avoid this
            # we set all zeroes to one.
            l = self.section_level
            if l>0:
                l = l-1
            self.body.append('\\pdfbookmark[%d]{%s}{%s}\n' % \
                (l,node.astext(),node.parent['id']))

    def visit_topic(self, node):
        self.topic_class = node.get('class')
        if self.use_latex_toc:
            self.topic_class = ''
            raise nodes.SkipNode

    def depart_topic(self, node):
        self.topic_class = ''
        self.body.append('\n')

    def visit_rubric(self, node):
#        self.body.append('\\hfill {\\color{red}\\bfseries{}')
#        self.context.append('} \\hfill ~\n')
        self.body.append('\\rubric{')
        self.context.append('}\n')

    def depart_rubric(self, node):
        self.body.append(self.context.pop())

    def visit_transition(self, node):
        self.body.append('\n\n')
        self.body.append('%' + '_' * 75)
        self.body.append('\n\\hspace*{\\fill}\\hrulefill\\hspace*{\\fill}')
        self.body.append('\n\n')

    def depart_transition(self, node):
        #self.body.append('[depart_transition]')
        pass

    def visit_version(self, node):
        self.visit_docinfo_item(node, 'version')

    def depart_version(self, node):
        self.depart_docinfo_item(node)

    def visit_warning(self, node):
        self.visit_admonition(node, 'warning')

    def depart_warning(self, node):
        self.depart_admonition()

    def unimplemented_visit(self, node):
        raise NotImplementedError('visiting unimplemented node type: %s'
                                  % node.__class__.__name__)

#    def unknown_visit(self, node):
#    def default_visit(self, node):
    
# vim: set ts=4 et ai :
