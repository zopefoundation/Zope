import os
import pprint
from hotshot.log import LogReader

prevloc = None
byline = {}
log = LogReader('profile.dat')

for what, place, tdelta in log:
    byline[prevloc] = tdelta + byline.get(prevloc, 0)
    byline.setdefault(place,0)
    prevloc = place

# Sort
results = [(v, k) for k, v in byline.items()]
results.sort()

for usecs, place in results:
    if not place:
        print 'Bad unpack:', usecs, place
        continue
    filename, line, funcname = place
    print '%08d' % usecs, os.path.split(filename)[1], line
