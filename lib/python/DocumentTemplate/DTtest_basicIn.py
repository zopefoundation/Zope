from DocumentTemplate import HTML, HTMLFile, String, File

def d(**kw): return kw

class D:
    def __init__(self, **kw):
	for k, v in kw.items(): self.__dict__[k]=v

    def __repr__(self): return "D(%s)" % `self.__dict__`

xxx=(D(name=1), D(name=2), D(name=3))
data=(
    d(name='jim', age=39),
    d(name='kak', age=29),
    d(name='will', age=8),
    d(name='andrew', age=5),
    d(name='chessie',age=2),
    )

html="""
<!--#in data mapping-->
  <!--#var name-->, <!--#var age-->
<!--#else-->
  <!--#in xxx    -->
    <!--#var name-->
  <!--#/in-->
  Sorry, no data
<!--#/in-->
"""

print '='*74
print HTML(html)(data=data, xxx=xxx)
print '='*74
print HTML(html)(xxx=xxx)
print '='*74

s="""
%(in data mapping)[
  %(name)s, %(age)s
%(else)[
  %(in xxx)[
    %(name)s
  %(in)]
  Sorry, no data
%(in)]
"""

print '='*74
print String(s)(data=data, xxx=xxx)
print '='*74
print String(s)(xxx=xxx)
print '='*74
