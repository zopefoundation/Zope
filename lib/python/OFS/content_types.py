
src="""
htm, html: text/html
gif: image/gif
jpg, jpe, jpeg: image/jpeg
pdf: application/pdf
aiff, aif, aifc: audio/aiff
au, snd: audio/basic
xbm: application/x-bitmap
ra, ram: audio/x-pn-realaudio
txt, py, c, h, pl, bat, sh, ksh: text/plain
avi: video/avi
wav: audio/wav
tar: application/x-tar
zip: application/x-zip
"""

from string import split, strip
import regex

content_type={}
for l in filter(lambda s: s and s[:1] != '#', map(strip, split(src,'\n'))):
    [e, t]=split(l, ':')
    t=strip(t)
    for e in map(strip, split(e, ',')):
	content_type[e]=t
    
find_binary=regex.compile('[\0-\6\177-\277]').search
html_re=regex.compile('<html>', regex.casefold)
def text_type(s):
    return "text/" + (html_re.search(s) >= 0 and 'html' or 'plain')
    

if __name__=='__main__':
    items=content_type.items()
    items.sort()
    for item in items: print "%s:\t%s" % item

