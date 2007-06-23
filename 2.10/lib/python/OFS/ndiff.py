#! /usr/bin/env python

# Module ndiff version 1.4.0
# Released to the public domain 27-Mar-1999,
# by Tim Peters (tim_one@email.msn.com).

# Provided as-is; use at your own risk; no warranty; no promises; enjoy!

"""ndiff [-q] file1 file2
    or
ndiff (-r1 | -r2) < ndiff_output > file1_or_file2

Print a human-friendly file difference report to stdout.  Both inter-
and intra-line differences are noted.  In the second form, recreate file1
(-r1) or file2 (-r2) on stdout, from an ndiff report on stdin.

In the first form, if -q ("quiet") is not specified, the first two lines
of output are

-: file1
+: file2

Each remaining line begins with a two-letter code:

    "- "    line unique to file1
    "+ "    line unique to file2
    "  "    line common to both files
    "? "    line not present in either input file

Lines beginning with "? " attempt to guide the eye to intraline
differences, and were not present in either input file.  These lines can
be confusing if the source files contain tab characters.

The first file can be recovered by retaining only lines that begin with
"  " or "- ", and deleting those 2-character prefixes; use ndiff with -r1.

The second file can be recovered similarly, but by retaining only "  "
and "+ " lines; use ndiff with -r2; or, on Unix, the second file can be
recovered by piping the output through

    sed -n '/^[+ ] /s/^..//p'

See module comments for details and programmatic interface.
"""

__version__ = 1, 4, 0

# SequenceMatcher tries to compute a "human-friendly diff" between
# two sequences (chiefly picturing a file as a sequence of lines,
# and a line as a sequence of characters, here).  Unlike e.g. UNIX(tm)
# diff, the fundamental notion is the longest *contiguous* & junk-free
# matching subsequence.  That's what catches peoples' eyes.  The
# Windows(tm) windiff has another interesting notion, pairing up elements
# that appear uniquely in each sequence.  That, and the method here,
# appear to yield more intuitive difference reports than does diff.  This
# method appears to be the least vulnerable to synching up on blocks
# of "junk lines", though (like blank lines in ordinary text files,
# or maybe "<P>" lines in HTML files).  That may be because this is
# the only method of the 3 that has a *concept* of "junk" <wink>.
#
# Note that ndiff makes no claim to produce a *minimal* diff.  To the
# contrary, minimal diffs are often counter-intuitive, because they
# synch up anywhere possible, sometimes accidental matches 100 pages
# apart.  Restricting synch points to contiguous matches preserves some
# notion of locality, at the occasional cost of producing a longer diff.
#
# With respect to junk, an earlier version of ndiff simply refused to
# *start* a match with a junk element.  The result was cases like this:
#     before: private Thread currentThread;
#     after:  private volatile Thread currentThread;
# If you consider whitespace to be junk, the longest contiguous match
# not starting with junk is "e Thread currentThread".  So ndiff reported
# that "e volatil" was inserted between the 't' and the 'e' in "private".
# While an accurate view, to people that's absurd.  The current version
# looks for matching blocks that are entirely junk-free, then extends the
# longest one of those as far as possible but only with matching junk.
# So now "currentThread" is matched, then extended to suck up the
# preceding blank; then "private" is matched, and extended to suck up the
# following blank; then "Thread" is matched; and finally ndiff reports
# that "volatile " was inserted before "Thread".  The only quibble
# remaining is that perhaps it was really the case that " volatile"
# was inserted after "private".  I can live with that <wink>.
#
# NOTE on junk:  the module-level names
#    IS_LINE_JUNK
#    IS_CHARACTER_JUNK
# can be set to any functions you like.  The first one should accept
# a single string argument, and return true iff the string is junk.
# The default is whether the regexp r"\s*#?\s*$" matches (i.e., a
# line without visible characters, except for at most one splat).
# The second should accept a string of length 1 etc.  The default is
# whether the character is a blank or tab (note: bad idea to include
# newline in this!).
#
# After setting those, you can call fcompare(f1name, f2name) with the
# names of the files you want to compare.  The difference report
# is sent to stdout.  Or you can call main(args), passing what would
# have been in sys.argv[1:] had the cmd-line form been used.

TRACE = 0

# define what "junk" means
import re

def IS_LINE_JUNK(line, pat=re.compile(r"\s*#?\s*$").match):
    return pat(line) is not None

def IS_CHARACTER_JUNK(ch, ws=" \t"):
    return ch in ws

del re

class SequenceMatcher:
    def __init__(self, isjunk=None, a='', b=''):
        # Members:
        # a
        #      first sequence
        # b
        #      second sequence; differences are computed as "what do
        #      we need to do to 'a' to change it into 'b'?"
        # b2j
        #      for x in b, b2j[x] is a list of the indices (into b)
        #      at which x appears; junk elements do not appear
        # b2jhas
        #      b2j.has_key
        # fullbcount
        #      for x in b, fullbcount[x] == the number of times x
        #      appears in b; only materialized if really needed (used
        #      only for computing quick_ratio())
        # matching_blocks
        #      a list of (i, j, k) triples, where a[i:i+k] == b[j:j+k];
        #      ascending & non-overlapping in i and in j; terminated by
        #      a dummy (len(a), len(b), 0) sentinel
        # opcodes
        #      a list of (tag, i1, i2, j1, j2) tuples, where tag is
        #      one of
        #          'replace'   a[i1:i2] should be replaced by b[j1:j2]
        #          'delete'    a[i1:i2] should be deleted
        #          'insert'    b[j1:j2] should be inserted
        #          'equal'     a[i1:i2] == b[j1:j2]
        # isjunk
        #      a user-supplied function taking a sequence element and
        #      returning true iff the element is "junk" -- this has
        #      subtle but helpful effects on the algorithm, which I'll
        #      get around to writing up someday <0.9 wink>.
        #      DON'T USE!  Only __chain_b uses this.  Use isbjunk.
        # isbjunk
        #      for x in b, isbjunk(x) == isjunk(x) but much faster;
        #      it's really the has_key method of a hidden dict.
        #      DOES NOT WORK for x in a!

        self.isjunk = isjunk
        self.a = self.b = None
        self.set_seqs(a, b)

    def set_seqs(self, a, b):
        self.set_seq1(a)
        self.set_seq2(b)

    def set_seq1(self, a):
        if a is self.a:
            return
        self.a = a
        self.matching_blocks = self.opcodes = None

    def set_seq2(self, b):
        if b is self.b:
            return
        self.b = b
        self.matching_blocks = self.opcodes = None
        self.fullbcount = None
        self.__chain_b()

    # For each element x in b, set b2j[x] to a list of the indices in
    # b where x appears; the indices are in increasing order; note that
    # the number of times x appears in b is len(b2j[x]) ...
    # when self.isjunk is defined, junk elements don't show up in this
    # map at all, which stops the central find_longest_match method
    # from starting any matching block at a junk element ...
    # also creates the fast isbjunk function ...
    # note that this is only called when b changes; so for cross-product
    # kinds of matches, it's best to call set_seq2 once, then set_seq1
    # repeatedly

    def __chain_b(self):
        # Because isjunk is a user-defined (not C) function, and we test
        # for junk a LOT, it's important to minimize the number of calls.
        # Before the tricks described here, __chain_b was by far the most
        # time-consuming routine in the whole module!  If anyone sees
        # Jim Roskind, thank him again for profile.py -- I never would
        # have guessed that.
        # The first trick is to build b2j ignoring the possibility
        # of junk.  I.e., we don't call isjunk at all yet.  Throwing
        # out the junk later is much cheaper than building b2j "right"
        # from the start.
        b = self.b
        self.b2j = b2j = {}
        self.b2jhas = b2jhas = b2j.has_key
        for i in xrange(len(b)):
            elt = b[i]
            if b2jhas(elt):
                b2j[elt].append(i)
            else:
                b2j[elt] = [i]

        # Now b2j.keys() contains elements uniquely, and especially when
        # the sequence is a string, that's usually a good deal smaller
        # than len(string).  The difference is the number of isjunk calls
        # saved.
        isjunk, junkdict = self.isjunk, {}
        if isjunk:
            for elt in b2j.keys():
                if isjunk(elt):
                    junkdict[elt] = 1   # value irrelevant; it's a set
                    del b2j[elt]

        # Now for x in b, isjunk(x) == junkdict.has_key(x), but the
        # latter is much faster.  Note too that while there may be a
        # lot of junk in the sequence, the number of *unique* junk
        # elements is probably small.  So the memory burden of keeping
        # this dict alive is likely trivial compared to the size of b2j.
        self.isbjunk = junkdict.has_key

    def find_longest_match(self, alo, ahi, blo, bhi):
        """Find longest matching block in a[alo:ahi] and b[blo:bhi].

        If isjunk is not defined:

        Return (i,j,k) such that a[i:i+k] is equal to b[j:j+k], where
            alo <= i <= i+k <= ahi
            blo <= j <= j+k <= bhi
        and for all (i',j',k') meeting those conditions,
            k >= k'
            i <= i'
            and if i == i', j <= j'
        In other words, of all maximal matching blocks, return one
        that starts earliest in a, and of all those maximal matching
        blocks that start earliest in a, return the one that starts
        earliest in b.

        If isjunk is defined, first the longest matching block is
        determined as above, but with the additional restriction that
        no junk element appears in the block.  Then that block is
        extended as far as possible by matching (only) junk elements on
        both sides.  So the resulting block never matches on junk except
        as identical junk happens to be adjacent to an "interesting"
        match.

        If no blocks match, return (alo, blo, 0).
        """

        # CAUTION:  stripping common prefix or suffix would be incorrect.
        # E.g.,
        #    ab
        #    acab
        # Longest matching block is "ab", but if common prefix is
        # stripped, it's "a" (tied with "b").  UNIX(tm) diff does so
        # strip, so ends up claiming that ab is changed to acab by
        # inserting "ca" in the middle.  That's minimal but unintuitive:
        # "it's obvious" that someone inserted "ac" at the front.
        # Windiff ends up at the same place as diff, but by pairing up
        # the unique 'b's and then matching the first two 'a's.

        a, b, b2j, isbjunk = self.a, self.b, self.b2j, self.isbjunk
        besti, bestj, bestsize = alo, blo, 0
        # find longest junk-free match
        # during an iteration of the loop, j2len[j] = length of longest
        # junk-free match ending with a[i-1] and b[j]
        j2len = {}
        nothing = []
        for i in xrange(alo, ahi):
            # look at all instances of a[i] in b; note that because
            # b2j has no junk keys, the loop is skipped if a[i] is junk
            j2lenget = j2len.get
            newj2len = {}
            for j in b2j.get(a[i], nothing):
                # a[i] matches b[j]
                if j < blo:
                    continue
                if j >= bhi:
                    break
                k = newj2len[j] = j2lenget(j-1, 0) + 1
                if k > bestsize:
                    besti, bestj, bestsize = i-k+1, j-k+1, k
            j2len = newj2len

        # Now that we have a wholly interesting match (albeit possibly
        # empty!), we may as well suck up the matching junk on each
        # side of it too.  Can't think of a good reason not to, and it
        # saves post-processing the (possibly considerable) expense of
        # figuring out what to do with it.  In the case of an empty
        # interesting match, this is clearly the right thing to do,
        # because no other kind of match is possible in the regions.
        while besti > alo and bestj > blo and \
              isbjunk(b[bestj-1]) and \
              a[besti-1] == b[bestj-1]:
            besti, bestj, bestsize = besti-1, bestj-1, bestsize+1
        while besti+bestsize < ahi and bestj+bestsize < bhi and \
              isbjunk(b[bestj+bestsize]) and \
              a[besti+bestsize] == b[bestj+bestsize]:
            bestsize = bestsize + 1

        if TRACE:
            print "get_matching_blocks", alo, ahi, blo, bhi
            print "    returns", besti, bestj, bestsize
        return besti, bestj, bestsize

    def get_matching_blocks(self):
        if self.matching_blocks is not None:
            return self.matching_blocks
        self.matching_blocks = []
        la, lb = len(self.a), len(self.b)
        self.__helper(0, la, 0, lb, self.matching_blocks)
        self.matching_blocks.append( (la, lb, 0) )
        if TRACE:
            print '*** matching blocks', self.matching_blocks
        return self.matching_blocks

    # builds list of matching blocks covering a[alo:ahi] and
    # b[blo:bhi], appending them in increasing order to answer

    def __helper(self, alo, ahi, blo, bhi, answer):
        i, j, k = x = self.find_longest_match(alo, ahi, blo, bhi)
        # a[alo:i] vs b[blo:j] unknown
        # a[i:i+k] same as b[j:j+k]
        # a[i+k:ahi] vs b[j+k:bhi] unknown
        if k:
            if alo < i and blo < j:
                self.__helper(alo, i, blo, j, answer)
            answer.append(x)
            if i+k < ahi and j+k < bhi:
                self.__helper(i+k, ahi, j+k, bhi, answer)

    def ratio(self):
        """Return a measure of the sequences' similarity (float in [0,1]).

        Where T is the total number of elements in both sequences, and
        M is the number of matches, this is 2*M / T.
        Note that this is 1 if the sequences are identical, and 0 if
        they have nothing in common.
        """

        matches = reduce(lambda sum, triple: sum + triple[-1],
                         self.get_matching_blocks(), 0)
        return 2.0 * matches / (len(self.a) + len(self.b))

    def quick_ratio(self):
        """Return an upper bound on ratio() relatively quickly."""
        # viewing a and b as multisets, set matches to the cardinality
        # of their intersection; this counts the number of matches
        # without regard to order, so is clearly an upper bound
        if self.fullbcount is None:
            self.fullbcount = fullbcount = {}
            for elt in self.b:
                fullbcount[elt] = fullbcount.get(elt, 0) + 1
        fullbcount = self.fullbcount
        # avail[x] is the number of times x appears in 'b' less the
        # number of times we've seen it in 'a' so far ... kinda
        avail = {}
        availhas, matches = avail.has_key, 0
        for elt in self.a:
            if availhas(elt):
                numb = avail[elt]
            else:
                numb = fullbcount.get(elt, 0)
            avail[elt] = numb - 1
            if numb > 0:
                matches = matches + 1
        return 2.0 * matches / (len(self.a) + len(self.b))

    def real_quick_ratio(self):
        """Return an upper bound on ratio() very quickly"""
        la, lb = len(self.a), len(self.b)
        # can't have more matches than the number of elements in the
        # shorter sequence
        return 2.0 * min(la, lb) / (la + lb)

    def get_opcodes(self):
        if self.opcodes is not None:
            return self.opcodes
        i = j = 0
        self.opcodes = answer = []
        for ai, bj, size in self.get_matching_blocks():
            # invariant:  we've pumped out correct diffs to change
            # a[:i] into b[:j], and the next matching block is
            # a[ai:ai+size] == b[bj:bj+size].  So we need to pump
            # out a diff to change a[i:ai] into b[j:bj], pump out
            # the matching block, and move (i,j) beyond the match
            tag = ''
            if i < ai and j < bj:
                tag = 'replace'
            elif i < ai:
                tag = 'delete'
            elif j < bj:
                tag = 'insert'
            if tag:
                answer.append( (tag, i, ai, j, bj) )
            i, j = ai+size, bj+size
            # the list of matching blocks is terminated by a
            # sentinel with size 0
            if size:
                answer.append( ('equal', ai, i, bj, j) )
        return answer

# meant for dumping lines
def dump(tag, x, lo, hi):
    for i in xrange(lo, hi):
        print tag, x[i],

# figure out which mark to stick under characters in lines that
# have changed (blank = same, - = deleted, + = inserted, ^ = replaced)
_combine = { '  ': ' ',
             '. ': '-',
             ' .': '+',
             '..': '^' }

def plain_replace(a, alo, ahi, b, blo, bhi):
    assert alo < ahi and blo < bhi
    # dump the shorter block first -- reduces the burden on short-term
    # memory if the blocks are of very different sizes
    if bhi - blo < ahi - alo:
        dump('+', b, blo, bhi)
        dump('-', a, alo, ahi)
    else:
        dump('-', a, alo, ahi)
        dump('+', b, blo, bhi)

# When replacing one block of lines with another, this guy searches
# the blocks for *similar* lines; the best-matching pair (if any) is
# used as a synch point, and intraline difference marking is done on
# the similar pair.  Lots of work, but often worth it.

def fancy_replace(a, alo, ahi, b, blo, bhi):
    if TRACE:
        print '*** fancy_replace', alo, ahi, blo, bhi
        dump('>', a, alo, ahi)
        dump('<', b, blo, bhi)

    # don't synch up unless the lines have a similarity score of at
    # least cutoff; best_ratio tracks the best score seen so far
    best_ratio, cutoff = 0.74, 0.75
    cruncher = SequenceMatcher(IS_CHARACTER_JUNK)
    eqi, eqj = None, None   # 1st indices of equal lines (if any)

    # search for the pair that matches best without being identical
    # (identical lines must be junk lines, & we don't want to synch up
    # on junk -- unless we have to)
    for j in xrange(blo, bhi):
        bj = b[j]
        cruncher.set_seq2(bj)
        for i in xrange(alo, ahi):
            ai = a[i]
            if ai == bj:
                if eqi is None:
                    eqi, eqj = i, j
                continue
            cruncher.set_seq1(ai)
            # computing similarity is expensive, so use the quick
            # upper bounds first -- have seen this speed up messy
            # compares by a factor of 3.
            # note that ratio() is only expensive to compute the first
            # time it's called on a sequence pair; the expensive part
            # of the computation is cached by cruncher
            if cruncher.real_quick_ratio() > best_ratio and \
                  cruncher.quick_ratio() > best_ratio and \
                  cruncher.ratio() > best_ratio:
                best_ratio, best_i, best_j = cruncher.ratio(), i, j
    if best_ratio < cutoff:
        # no non-identical "pretty close" pair
        if eqi is None:
            # no identical pair either -- treat it as a straight replace
            plain_replace(a, alo, ahi, b, blo, bhi)
            return
        # no close pair, but an identical pair -- synch up on that
        best_i, best_j, best_ratio = eqi, eqj, 1.0
    else:
        # there's a close pair, so forget the identical pair (if any)
        eqi = None

    # a[best_i] very similar to b[best_j]; eqi is None iff they're not
    # identical
    if TRACE:
        print '*** best_ratio', best_ratio, best_i, best_j
        dump('>', a, best_i, best_i+1)
        dump('<', b, best_j, best_j+1)

    # pump out diffs from before the synch point
    fancy_helper(a, alo, best_i, b, blo, best_j)

    # do intraline marking on the synch pair
    aelt, belt = a[best_i], b[best_j]
    if eqi is None:
        # pump out a '-', '+', '?' triple for the synched lines;
        atags = btags = ""
        cruncher.set_seqs(aelt, belt)
        for tag, ai1, ai2, bj1, bj2 in cruncher.get_opcodes():
            la, lb = ai2 - ai1, bj2 - bj1
            if tag == 'replace':
                atags = atags + '.' * la
                btags = btags + '.' * lb
            elif tag == 'delete':
                atags = atags + '.' * la
            elif tag == 'insert':
                btags = btags + '.' * lb
            elif tag == 'equal':
                atags = atags + ' ' * la
                btags = btags + ' ' * lb
            else:
                raise ValueError, 'unknown tag ' + `tag`
        la, lb = len(atags), len(btags)
        if la < lb:
            atags = atags + ' ' * (lb - la)
        elif lb < la:
            btags = btags + ' ' * (la - lb)
        combined = map(lambda x,y: _combine[x+y], atags, btags)
        print '-', aelt, '+', belt, '?', \
              ''.join(combined).rstrip()
    else:
        # the synch pair is identical
        print ' ', aelt,

    # pump out diffs from after the synch point
    fancy_helper(a, best_i+1, ahi, b, best_j+1, bhi)

def fancy_helper(a, alo, ahi, b, blo, bhi):
    if alo < ahi:
        if blo < bhi:
            fancy_replace(a, alo, ahi, b, blo, bhi)
        else:
            dump('-', a, alo, ahi)
    elif blo < bhi:
        dump('+', b, blo, bhi)

def fail(msg):
    import sys
    out = sys.stderr.write
    out(msg + "\n\n")
    out(__doc__)
    return 0

# open a file & return the file object; gripe and return 0 if it
# couldn't be opened
def fopen(fname):
    try:
        return open(fname, 'r')
    except IOError, detail:
        return fail("couldn't open " + fname + ": " + str(detail))

# open two files & spray the diff to stdout; return false iff a problem
def fcompare(f1name, f2name):
    f1 = fopen(f1name)
    f2 = fopen(f2name)
    if not f1 or not f2:
        return 0

    a = f1.readlines(); f1.close()
    b = f2.readlines(); f2.close()

    cruncher = SequenceMatcher(IS_LINE_JUNK, a, b)
    for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
        if tag == 'replace':
            fancy_replace(a, alo, ahi, b, blo, bhi)
        elif tag == 'delete':
            dump('-', a, alo, ahi)
        elif tag == 'insert':
            dump('+', b, blo, bhi)
        elif tag == 'equal':
            dump(' ', a, alo, ahi)
        else:
            raise ValueError, 'unknown tag ' + `tag`

    return 1

# crack args (sys.argv[1:] is normal) & compare;
# return false iff a problem

def main(args):
    import getopt
    try:
        opts, args = getopt.getopt(args, "qr:")
    except getopt.error, detail:
        return fail(str(detail))
    noisy = 1
    qseen = rseen = 0
    for opt, val in opts:
        if opt == "-q":
            qseen = 1
            noisy = 0
        elif opt == "-r":
            rseen = 1
            whichfile = val
    if qseen and rseen:
        return fail("can't specify both -q and -r")
    if rseen:
        if args:
            return fail("no args allowed with -r option")
        if whichfile in "12":
            restore(whichfile)
            return 1
        return fail("-r value must be 1 or 2")
    if len(args) != 2:
        return fail("need 2 filename args")
    f1name, f2name = args
    if noisy:
        print '-:', f1name
        print '+:', f2name
    return fcompare(f1name, f2name)

def restore(which):
    import sys
    tag = {"1": "- ", "2": "+ "}[which]
    prefixes = ("  ", tag)
    for line in sys.stdin.readlines():
        if line[:2] in prefixes:
            print line[2:],

if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    if "-profile" in args:
        import profile, pstats
        args.remove("-profile")
        statf = "ndiff.pro"
        profile.run("main(args)", statf)
        stats = pstats.Stats(statf)
        stats.strip_dirs().sort_stats('time').print_stats()
    else:
        main(args)
