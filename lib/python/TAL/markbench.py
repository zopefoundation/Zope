#! /usr/bin/env python

# This software is subject to the provisions of the Zope Public License,
# Version 1.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.


'''Run benchmarks of TAL vs. DTML'''

try:
    import warnings
except ImportError:
    pass
else:
    warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
os.environ['NO_SECURITY'] = 'true'

import sys, time

if __name__ == "__main__":
    import setpath

from DocumentTemplate.DT_HTML import HTMLFile
from HTMLTALParser import HTMLTALParser
from TALInterpreter import TALInterpreter
from DummyEngine import DummyEngine
from cStringIO import StringIO

def time_apply(f, args, kwargs, count):
    for i in range(4):
        f(*args, **kwargs)
    r = [None] * count
    t0 = time.clock()
    for i in r:
        pass
    t1 = time.clock()
    for i in r:
        f(*args, **kwargs)
    t = time.clock() - t1 - (t1 - t0)
    return t / count

def time_zpt(fn, count):
    from Products.PageTemplates.PageTemplate import PageTemplate
    pt = PageTemplate()
    pt.write(open(fn).read())
    return time_apply(pt.pt_render, (), {'extra_context': data}, count)

def time_tal(fn, count):
    p = HTMLTALParser()
    p.parseFile(fn)
    program, macros = p.getCode()
    engine = DummyEngine(macros)
    engine.globals = data
    tal = TALInterpreter(program, macros, engine, StringIO(), wrap=0,
                         tal=1, strictinsert=0)
    return time_apply(tal, (), {}, count)

def time_dtml(fn, count):
    html = HTMLFile(fn)
    return time_apply(html, (), data, count)

def profile_zpt(fn, count, profiler):
    from Products.PageTemplates.PageTemplate import PageTemplate
    pt = PageTemplate()
    pt.write(open(fn).read())
    for i in range(4):
        pt.pt_render(extra_context=data)
    r = [None] * count
    for i in r:
        profiler.runcall(pt.pt_render, 0, data)

def profile_tal(fn, count, profiler):
    p = HTMLTALParser()
    p.parseFile(fn)
    program, macros = p.getCode()
    engine = DummyEngine(macros)
    engine.globals = data
    tal = TALInterpreter(program, macros, engine, StringIO(), wrap=0,
                         tal=1, strictinsert=0)
    for i in range(4):
        tal()
    r = [None] * count
    for i in r:
        profiler.runcall(tal)

tal_fn = 'benchmark/tal%.2d.html'
dtml_fn = 'benchmark/dtml%.2d.html'

def compare(n, count, profiler=None):
    t1 = int(time_zpt(tal_fn % n, count) * 1000 + 0.5)
    t2 = int(time_tal(tal_fn % n, count) * 1000 + 0.5)
    t3 = int(time_dtml(dtml_fn % n, count) * 1000 + 0.5)
    print '%.2d: %10s %10s %10s' % (n, t1, t2, t3)
    if profiler:
        profile_tal(tal_fn % n, count, profiler)

def main(count, profiler=None):
    n = 1
    print '##: %10s %10s %10s' % ('ZPT', 'TAL', 'DTML')
    while os.path.isfile(tal_fn % n) and os.path.isfile(dtml_fn % n):
        compare(n, count, profiler)
        n = n + 1

data = {'x':'X', 'r2': range(2), 'r8': range(8), 'r64': range(64)}
for i in range(10):
    data['x%s' % i] = 'X%s' % i

if __name__ == "__main__":
    filename = "markbench.prof"
    profiler = None
    if len(sys.argv) > 1 and sys.argv[1] == "-p":
        import profile
        profiler = profile.Profile()
        del sys.argv[1]

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            compare(int(arg), 25, profiler)
    else:
        main(25, profiler)

    if profiler is not None:
        profiler.dump_stats(filename)
        import pstats
        p = pstats.Stats(filename)
        p.strip_dirs()
        p.sort_stats('time', 'calls')
        try:
            p.print_stats(20)
        except IOError, e:
            if e.errno != errno.EPIPE:
                raise
