class standard_html: # Base class for using with ZTemplates
    def __init__(self, title):
        self.standard_html_header = """<HTML>
   <HEAD>
      <TITLE>
         %s
      </TITLE>
   </HEAD>

<BODY>""" % title

        self.standard_html_footer = """</BODY>
</HTML>"""

        self.title = title


def test(s):
    outfile = open("test.out", 'w')
    outfile.write(s)
    outfile.close()


def exception():
    import sys, traceback
    exc_type, exc_value, exc_tb = sys.exc_info()

    outfile = open("test.err", 'w')
    traceback.print_exception(exc_type, exc_value, exc_tb, None, outfile)
    outfile.close()


wordlist = [
   {"key": "aaa", "word": "AAA", "weight": 1},
   {"key": "bbb", "word": "BBB", "weight": 0},
   {"key": "ccc", "word": "CCC", "weight": 0},
   {"key": "ddd", "word": "DDD", "weight": 0},
   {"key": "eee", "word": "EEE", "weight": 1},
   {"key": "fff", "word": "FFF", "weight": 0},
   {"key": "ggg", "word": "GGG", "weight": 0},
   {"key": "hhh", "word": "HHH", "weight": 0},
   {"key": "iii", "word": "III", "weight": 1},
   {"key": "jjj", "word": "JJJ", "weight": -1},
   {"key": "kkk", "word": "KKK", "weight": 0},
   {"key": "lll", "word": "LLL", "weight": 0},
   {"key": "mmm", "word": "MMM", "weight": 0},
   {"key": "nnn", "word": "NNN", "weight": 0},
   {"key": "ooo", "word": "OOO", "weight": 1},
   {"key": "ppp", "word": "PPP", "weight": 0},
   {"key": "qqq", "word": "QQQ", "weight": -1},
   {"key": "rrr", "word": "RRR", "weight": 0},
   {"key": "sss", "word": "SSS", "weight": 0},
   {"key": "ttt", "word": "TTT", "weight": 0},
   {"key": "uuu", "word": "UUU", "weight": 1},
   {"key": "vvv", "word": "VVV", "weight": 0},
   {"key": "www", "word": "WWW", "weight": 0},
   {"key": "xxx", "word": "XXX", "weight": 0},
   {"key": "yyy", "word": "YYY", "weight": -1},
   {"key": "zzz", "word": "ZZZ", "weight": 0}
]
