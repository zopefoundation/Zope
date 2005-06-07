"""Test script for exercising various catalog features under load

Usage:
    cd lib/python
    python Products/ZCatalog/regressiontests/loadmail.py command args

where each command has its own command-line arguments that it expects.

Note that all of the commands operate on the Zope database,
typically var/Data.fs.

Note that this script uses the proc file system to get memory size.

Many of the commands output performance statisics on lines that look like::

      11.3585170507 0.06 2217781L 7212

where the numbers are:

        - clock time in seconds

        - cpu time used by the main thread, in seconds,

        - Database size growth over the test

        - Memory growth during the test (if the proc file system is available).

Commands:

    base mbox [max]

      Build a base database by:

        - Deleting ../../var/Data.fs

        - Starting Zope

        - Adding a top-level folder names 'mail'

        - Reading up to max messages from the Unix mailbox file, mbox
          and adding them as documents to the mail folder.


    index [threshold]

       Index all of the DTML documents in the database, committing
       sub-transactions after each threshold objects.  threshold defaults to
       1000.

       If the threshold is less than the number of messages, then the
       size of the temporary sub-transaction commit file is output.

    inc mbox start end [threads [wait]]

       Incrementally index messages start to end in unix mailbox mbox.

       If the threads argument is supplied, then it specifies the
       number of threads to use. For example, with:

           python Products/ZCatalog/tests/loadmail.py inc mbox 0 200 2

       One thread indexes messages 0 to 99 and another thread indexes messages
       100 to 199.

       If wait is specified, then after each document is indexed, the
       thread sleeps a random number of seconds between 0 and 2*wait.
       The default wait is 0.25 seconds.

       For each thread, a line that looks like::

           3.41 (0, 1)

      is output, containing:

          - The cpu time

          - The number of ZODB transaction conflicts detected when reading

          - The number of ZODB transaction conflicts detected when committing

    edit edits deletes inserts threads wait

       Incrementally edit edits messages from mail. For each message,
       do a random number of word deletes between 0 and deletes * 2
       and do a random number of inserts between 0 and inserts * 2.

       For each thread, a line that looks like::

           3.41 (0, 1)

       as described above.

    catdel

       Delete the entire catalog in one transaction.  This is a fun one for
       storages that do reference counting garbage collection.

    pdebug command args

       Run one of the other commands in the Python debugger.

sample suite of tests::

    cd lib/python
    python Products/ZCatalog/regressiontests/loadmail.py base ~/zope.mbox 1000
    python Products/ZCatalog/regressiontests/loadmail.py index 100
    python Products/ZCatalog/regressiontests/loadmail.py \
                                                  inc ~/python-dev.mbox 0 10 2
    python Products/ZCatalog/regressiontests/loadmail.py edit 10 10 10 2
    python Products/ZCatalog/regressiontests/loadmail.py catdel

"""


import getopt
import mailbox, time, sys, os, string
sys.path.insert(0, '.')

import random

from string import strip, find, split, lower, atoi
from urllib import quote

import transaction

VERBOSE = 0

def do(db, f, args, returnf=None):
    """Do something and measure it's impact"""
    t = c = size = mem = r = None
    try:
        size=db.getSize()
        mem=VmSize()
        t=time.time()
        c=time.clock()
        r=apply(f, args)
        t=time.time() - t
        c=time.clock() - c
        size=db.getSize()-size
        mem=VmSize()-mem
    finally:
        if returnf is not None:
            returnf(t, c, size, mem, r)
        else:
            return t, c, size, mem, r

def loadmessage(dest, message, i, body=None, headers=None):
    if body is None: body=message.fp.read()
    if headers is None: headers=message.headers
    dest.manage_addDTMLDocument(str(i), file=body)
    doc=dest[str(i)]
    for h in headers:
        h=strip(h)
        l=find(h,':')
        if l <= 0: continue
        name=lower(h[:l])
        if name=='subject': name='title'
        v=strip(h[l+1:])
        type='string'
        if 0 and name=='date': type='date'
        elif 0:
            try: atoi(v)
            except: pass
            else: type=int

        if name=='title':
            doc.manage_changeProperties(title=h)
        else:
            try: doc.manage_addProperty(name, v, type)
            except: pass

def loadmail(dest, name, mbox, max=-1):

    try:
        import Products.BTreeFolder.BTreeFolder
    except:
        dest.manage_addFolder(name)
    else:
        Products.BTreeFolder.BTreeFolder.manage_addBTreeFolder(dest, name)

    dest=getattr(dest, name)
    f=open(mbox)
    mb=mailbox.UnixMailbox(f)
    i=0
    message=mb.next()
    while message:
        if max >= 0 and i > max:
            break
        if i%100 == 0 and VERBOSE:
            fmt = "\t%s\t%s\t\r"
            if os.environ.get('TERM') in ('dumb', 'emacs'):
                fmt = "\t%s\t%s\t\n"
            sys.stdout.write(fmt % (i, f.tell()))
            sys.stdout.flush()
        if i and (i%5000 == 0):
            transaction.commit()
            dest._p_jar._cache.minimize()

        loadmessage(dest, message, i)
        i=i+1
        message=mb.next()

    dest.number_of_messages=i
    print
    transaction.commit()

def loadinc(name, mb, f, max=99999999, wait=1):
    from ZODB.POSException import ConflictError
    from time import sleep
    from random import uniform
    import Zope2, sys
    rconflicts=wconflicts=0

    i=0
    message=mb.next()
    body=message.fp.read()
    headers=list(message.headers)
    while i < max:
        # sys.stderr.write("%s " % i)
        # sys.stdout.flush()
        if wait: sleep(uniform(0,wait))
        jar=Zope2.DB.open()
        app=jar.root()['Application']
        mdest=getattr(app, name)
        if i%100 == 0 and VERBOSE:
            fmt = "\t%s\t%s\t\r"
            if os.environ.get('TERM') in ('dumb', 'emacs'):
                fmt = "\t%s\t%s\t\n"
            sys.stdout.write(fmt % (i, f.tell()))
            sys.stdout.flush()

        did=str(i)
        try:
            loadmessage(mdest, message, did, body, headers)
            doc=mdest[did]
            app.cat.catalog_object(doc)
        except ConflictError, v:
            # print v.args
            rconflicts=rconflicts+1
            transaction.abort()
        else:
            try:
                transaction.commit()
                i=i+1
                message=mb.next()
                body=message.fp.read()
                headers=list(message.headers)
            except ConflictError:
                wconflicts=wconflicts+1
                transaction.abort()

        doc=app=mdest=0
        jar.close()


    if VERBOSE:
        sys.stdout.write("\t%s\t%s\t\n" % (i, f.tell()))
    sys.stdout.flush()
    return rconflicts, wconflicts

def base():
    try: os.unlink('../../var/Data.fs')
    except: pass
    import Zope2
    app=Zope2.app()
    if len(sys.argv) > 3:
        max = atoi(sys.argv[3])
    else:
        max = -1
    print do(Zope2.DB, loadmail, (app, 'mail', sys.argv[2], max))
    Zope2.DB.close()

class RE:
    def redirect(*args, **kw): pass

def indexf(app):
    r=RE()
    r.PARENTS=[0, app.mail]
    app.cat.manage_catalogFoundItems(r,r,'','',['DTML Document'])
    transaction.commit()

def index():
    os.environ['STUPID_LOG_FILE']=''
    os.environ['STUPID_LOG_SEVERITY']='-111'
    import Zope2, Products.ZCatalog.ZCatalog
    import AccessControl.SecurityManagement, AccessControl.SpecialUsers
    app=Zope2.app()
    Products.ZCatalog.ZCatalog.manage_addZCatalog(app, 'cat', '')
    try:
        app.cat.threshold = atoi(sys.argv[2])
    except IndexError:
        app.cat.threashold = 1000

    from Products.ZCTextIndex.ZCTextIndex \
         import PLexicon
    from Products.ZCTextIndex.Lexicon \
         import Splitter, CaseNormalizer

    app.cat._setObject('lex',
                       PLexicon('lex', '', Splitter(), CaseNormalizer())
                       )

    class extra:
        doc_attr = 'PrincipiaSearchSource'
        lexicon_id = 'lex'
        index_type = 'Okapi BM25 Rank'

    app.cat.addIndex('PrincipiaSearchSource', 'ZCTextIndex', extra)

    transaction.commit()
    system = AccessControl.SpecialUsers.system
    AccessControl.SecurityManagement.newSecurityManager(None, system)
    r=RE()
    r.PARENTS=[app.cat, app]
    print do(Zope2.DB, indexf, (app,))
    #hist(sys.argv[2])
    Zope2.DB.close()

def initmaili(n):
    import Zope2
    app=Zope2.app()
    try:
        import Products.BTreeFolder.BTreeFolder
    except:
        app.manage_addFolder(n)
    else:
        Products.BTreeFolder.BTreeFolder.manage_addBTreeFolder(app, n)

    transaction.commit()
    app._p_jar.close()

def hist(n):
    import Zope2
    app=Zope2.app()
    import cPickle
    pickler=cPickle.Pickler(open("h%s.hist" % n, 'w'))
    h=app.cat._catalog.indexes['PrincipiaSearchSource'].histogram()
    pickler.dump(list(h.items()))
    #h=app.cat._catalog.uids.keys()
    #pickler.dump(list(h))

def inc():
    import Zope2, thread
    min, max = atoi(sys.argv[3]), atoi(sys.argv[4])
    count = max-min
    try: threads=atoi(sys.argv[5])
    except:
        threads=1
        wait=0
    else:
        try: wait=atof(sys.argv[6])
        except: wait=0.25
        wait = wait * 2

    count = count / threads
    max = min + count

    omin=min

    db=Zope2.DB

    size=db.getSize()
    mem=VmSize()
    t=time.time()
    c=time.clock()

    mbox=sys.argv[2]
    argss=[]
    for i in range(threads):
        amin=min+i*count
        dest='maili%s' % amin
        initmaili(dest)
        f = open(mbox)
        mb=mailbox.UnixMailbox(f)
        j=0
        while j < amin:
            mb.next()
            j=j+1
        lock=thread.allocate_lock()
        lock.acquire()
        def returnf(t, c, size, mem, r, lock=lock):
            print c, r
            lock.release()
        argss.append((lock, (dest, mb, f, count, wait), returnf))

    for lock, args, returnf in argss:
        thread.start_new_thread(do, (Zope2.DB, loadinc, args, returnf))

    for lock, args, returnf in argss:
        lock.acquire()

    t=time.time() - t
    c=time.clock() - c
    size=db.getSize()-size
    mem=VmSize()-mem

    print t, c, size, mem

    #hist("%s-%s-%s" % (omin, count, threads))

    Zope2.DB.close()

def catdel():
    import Zope2
    app = Zope2.app()
    db = Zope2.DB
    t = time.time()
    c = time.clock()
    size = db.getSize()
    mem = VmSize()

    del app.cat
    transaction.commit()
    
    t = time.time() - t
    c = time.clock() - c
    size = db.getSize() - size
    mem = VmSize() - mem
    print t, c, size, mem


words=['banishment', 'indirectly', 'imprecise', 'peeks',
'opportunely', 'bribe', 'sufficiently', 'Occidentalized', 'elapsing',
'fermenting', 'listen', 'orphanage', 'younger', 'draperies', 'Ida',
'cuttlefish', 'mastermind', 'Michaels', 'populations', 'lent',
'cater', 'attentional', 'hastiness', 'dragnet', 'mangling',
'scabbards', 'princely', 'star', 'repeat', 'deviation', 'agers',
'fix', 'digital', 'ambitious', 'transit', 'jeeps', 'lighted',
'Prussianizations', 'Kickapoo', 'virtual', 'Andrew', 'generally',
'boatsman', 'amounts', 'promulgation', 'Malay', 'savaging',
'courtesan', 'nursed', 'hungered', 'shiningly', 'ship', 'presides',
'Parke', 'moderns', 'Jonas', 'unenlightening', 'dearth', 'deer',
'domesticates', 'recognize', 'gong', 'penetrating', 'dependents',
'unusually', 'complications', 'Dennis', 'imbalances', 'nightgown',
'attached', 'testaments', 'congresswoman', 'circuits', 'bumpers',
'braver', 'Boreas', 'hauled', 'Howe', 'seethed', 'cult', 'numismatic',
'vitality', 'differences', 'collapsed', 'Sandburg', 'inches', 'head',
'rhythmic', 'opponent', 'blanketer', 'attorneys', 'hen', 'spies',
'indispensably', 'clinical', 'redirection', 'submit', 'catalysts',
'councilwoman', 'kills', 'topologies', 'noxious', 'exactions',
'dashers', 'balanced', 'slider', 'cancerous', 'bathtubs', 'legged',
'respectably', 'crochets', 'absenteeism', 'arcsine', 'facility',
'cleaners', 'bobwhite', 'Hawkins', 'stockade', 'provisional',
'tenants', 'forearms', 'Knowlton', 'commit', 'scornful',
'pediatrician', 'greets', 'clenches', 'trowels', 'accepts',
'Carboloy', 'Glenn', 'Leigh', 'enroll', 'Madison', 'Macon', 'oiling',
'entertainingly', 'super', 'propositional', 'pliers', 'beneficiary',
'hospitable', 'emigration', 'sift', 'sensor', 'reserved',
'colonization', 'shrilled', 'momentously', 'stevedore', 'Shanghaiing',
'schoolmasters', 'shaken', 'biology', 'inclination', 'immoderate',
'stem', 'allegory', 'economical', 'daytime', 'Newell', 'Moscow',
'archeology', 'ported', 'scandals', 'Blackfoot', 'leery', 'kilobit',
'empire', 'obliviousness', 'productions', 'sacrificed', 'ideals',
'enrolling', 'certainties', 'Capsicum', 'Brookdale', 'Markism',
'unkind', 'dyers', 'legislates', 'grotesquely', 'megawords',
'arbitrary', 'laughing', 'wildcats', 'thrower', 'sex', 'devils',
'Wehr', 'ablates', 'consume', 'gossips', 'doorways', 'Shari',
'advanced', 'enumerable', 'existentially', 'stunt', 'auctioneers',
'scheduler', 'blanching', 'petulance', 'perceptibly', 'vapors',
'progressed', 'rains', 'intercom', 'emergency', 'increased',
'fluctuating', 'Krishna', 'silken', 'reformed', 'transformation',
'easter', 'fares', 'comprehensible', 'trespasses', 'hallmark',
'tormenter', 'breastworks', 'brassiere', 'bladders', 'civet', 'death',
'transformer', 'tolerably', 'bugle', 'clergy', 'mantels', 'satin',
'Boswellizes', 'Bloomington', 'notifier', 'Filippo', 'circling',
'unassigned', 'dumbness', 'sentries', 'representativeness', 'souped',
'Klux', 'Kingstown', 'gerund', 'Russell', 'splices', 'bellow',
'bandies', 'beefers', 'cameramen', 'appalled', 'Ionian', 'butterball',
'Portland', 'pleaded', 'admiringly', 'pricks', 'hearty', 'corer',
'deliverable', 'accountably', 'mentors', 'accorded',
'acknowledgement', 'Lawrenceville', 'morphology', 'eucalyptus',
'Rena', 'enchanting', 'tighter', 'scholars', 'graduations', 'edges',
'Latinization', 'proficiency', 'monolithic', 'parenthesizing', 'defy',
'shames', 'enjoyment', 'Purdue', 'disagrees', 'barefoot', 'maims',
'flabbergast', 'dishonorable', 'interpolation', 'fanatics', 'dickens',
'abysses', 'adverse', 'components', 'bowl', 'belong', 'Pipestone',
'trainees', 'paw', 'pigtail', 'feed', 'whore', 'conditioner',
'Volstead', 'voices', 'strain', 'inhabits', 'Edwin', 'discourses',
'deigns', 'cruiser', 'biconvex', 'biking', 'depreciation', 'Harrison',
'Persian', 'stunning', 'agar', 'rope', 'wagoner', 'elections',
'reticulately', 'Cruz', 'pulpits', 'wilt', 'peels', 'plants',
'administerings', 'deepen', 'rubs', 'hence', 'dissension', 'implored',
'bereavement', 'abyss', 'Pennsylvania', 'benevolent', 'corresponding',
'Poseidon', 'inactive', 'butchers', 'Mach', 'woke', 'loading',
'utilizing', 'Hoosier', 'undo', 'Semitization', 'trigger', 'Mouthe',
'mark', 'disgracefully', 'copier', 'futility', 'gondola', 'algebraic',
'lecturers', 'sponged', 'instigators', 'looted', 'ether', 'trust',
'feeblest', 'sequencer', 'disjointness', 'congresses', 'Vicksburg',
'incompatibilities', 'commend', 'Luxembourg', 'reticulation',
'instructively', 'reconstructs', 'bricks', 'attache', 'Englishman',
'provocation', 'roughen', 'cynic', 'plugged', 'scrawls', 'antipode',
'injected', 'Daedalus', 'Burnsides', 'asker', 'confronter',
'merriment', 'disdain', 'thicket', 'stinker', 'great', 'tiers',
'oust', 'antipodes', 'Macintosh', 'tented', 'packages',
'Mediterraneanize', 'hurts', 'orthodontist', 'seeder', 'readying',
'babying', 'Florida', 'Sri', 'buckets', 'complementary',
'cartographer', 'chateaus', 'shaves', 'thinkable', 'Tehran',
'Gordian', 'Angles', 'arguable', 'bureau', 'smallest', 'fans',
'navigated', 'dipole', 'bootleg', 'distinctive', 'minimization',
'absorbed', 'surmised', 'Malawi', 'absorbent', 'close', 'conciseness',
'hopefully', 'declares', 'descent', 'trick', 'portend', 'unable',
'mildly', 'Morse', 'reference', 'scours', 'Caribbean', 'battlers',
'astringency', 'likelier', 'Byronizes', 'econometric', 'grad',
'steak', 'Austrian', 'ban', 'voting', 'Darlington', 'bison', 'Cetus',
'proclaim', 'Gilbertson', 'evictions', 'submittal', 'bearings',
'Gothicizer', 'settings', 'McMahon', 'densities', 'determinants',
'period', 'DeKastere', 'swindle', 'promptness', 'enablers', 'wordy',
'during', 'tables', 'responder', 'baffle', 'phosgene', 'muttering',
'limiters', 'custodian', 'prevented', 'Stouffer', 'waltz', 'Videotex',
'brainstorms', 'alcoholism', 'jab', 'shouldering', 'screening',
'explicitly', 'earner', 'commandment', 'French', 'scrutinizing',
'Gemma', 'capacitive', 'sheriff', 'herbivore', 'Betsey', 'Formosa',
'scorcher', 'font', 'damming', 'soldiers', 'flack', 'Marks',
'unlinking', 'serenely', 'rotating', 'converge', 'celebrities',
'unassailable', 'bawling', 'wording', 'silencing', 'scotch',
'coincided', 'masochists', 'graphs', 'pernicious', 'disease',
'depreciates', 'later', 'torus', 'interject', 'mutated', 'causer',
'messy', 'Bechtel', 'redundantly', 'profoundest', 'autopsy',
'philosophic', 'iterate', 'Poisson', 'horridly', 'silversmith',
'millennium', 'plunder', 'salmon', 'missioner', 'advances', 'provers',
'earthliness', 'manor', 'resurrectors', 'Dahl', 'canto', 'gangrene',
'gabler', 'ashore', 'frictionless', 'expansionism', 'emphasis',
'preservations', 'Duane', 'descend', 'isolated', 'firmware',
'dynamites', 'scrawled', 'cavemen', 'ponder', 'prosperity', 'squaw',
'vulnerable', 'opthalmic', 'Simms', 'unite', 'totallers', 'Waring',
'enforced', 'bridge', 'collecting', 'sublime', 'Moore', 'gobble',
'criticizes', 'daydreams', 'sedate', 'apples', 'Concordia',
'subsequence', 'distill', 'Allan', 'seizure', 'Isadore', 'Lancashire',
'spacings', 'corresponded', 'hobble', 'Boonton', 'genuineness',
'artifact', 'gratuities', 'interviewee', 'Vladimir', 'mailable',
'Bini', 'Kowalewski', 'interprets', 'bereave', 'evacuated', 'friend',
'tourists', 'crunched', 'soothsayer', 'fleetly', 'Romanizations',
'Medicaid', 'persevering', 'flimsy', 'doomsday', 'trillion',
'carcasses', 'guess', 'seersucker', 'ripping', 'affliction',
'wildest', 'spokes', 'sheaths', 'procreate', 'rusticates', 'Schapiro',
'thereafter', 'mistakenly', 'shelf', 'ruination', 'bushel',
'assuredly', 'corrupting', 'federation', 'portmanteau', 'wading',
'incendiary', 'thing', 'wanderers', 'messages', 'Paso', 'reexamined',
'freeings', 'denture', 'potting', 'disturber', 'laborer', 'comrade',
'intercommunicating', 'Pelham', 'reproach', 'Fenton', 'Alva', 'oasis',
'attending', 'cockpit', 'scout', 'Jude', 'gagging', 'jailed',
'crustaceans', 'dirt', 'exquisitely', 'Internet', 'blocker', 'smock',
'Troutman', 'neighboring', 'surprise', 'midscale', 'impart',
'badgering', 'fountain', 'Essen', 'societies', 'redresses',
'afterwards', 'puckering', 'silks', 'Blakey', 'sequel', 'greet',
'basements', 'Aubrey', 'helmsman', 'album', 'wheelers', 'easternmost',
'flock', 'ambassadors', 'astatine', 'supplant', 'gird', 'clockwork',
'foxes', 'rerouting', 'divisional', 'bends', 'spacer',
'physiologically', 'exquisite', 'concerts', 'unbridled', 'crossing',
'rock', 'leatherneck', 'Fortescue', 'reloading', 'Laramie', 'Tim',
'forlorn', 'revert', 'scarcer', 'spigot', 'equality', 'paranormal',
'aggrieves', 'pegs', 'committeewomen', 'documented', 'interrupt',
'emerald', 'Battelle', 'reconverted', 'anticipated', 'prejudices',
'drowsiness', 'trivialities', 'food', 'blackberries', 'Cyclades',
'tourist', 'branching', 'nugget', 'Asilomar', 'repairmen', 'Cowan',
'receptacles', 'nobler', 'Nebraskan', 'territorial', 'chickadee',
'bedbug', 'darted', 'vigilance', 'Octavia', 'summands', 'policemen',
'twirls', 'style', 'outlawing', 'specifiable', 'pang', 'Orpheus',
'epigram', 'Babel', 'butyrate', 'wishing', 'fiendish', 'accentuate',
'much', 'pulsed', 'adorned', 'arbiters', 'counted', 'Afrikaner',
'parameterizes', 'agenda', 'Americanism', 'referenda', 'derived',
'liquidity', 'trembling', 'lordly', 'Agway', 'Dillon', 'propellers',
'statement', 'stickiest', 'thankfully', 'autograph', 'parallel',
'impulse', 'Hamey', 'stylistic', 'disproved', 'inquirer', 'hoisting',
'residues', 'variant', 'colonials', 'dequeued', 'especial', 'Samoa',
'Polaris', 'dismisses', 'surpasses', 'prognosis', 'urinates',
'leaguers', 'ostriches', 'calculative', 'digested', 'divided',
'reconfigurer', 'Lakewood', 'illegalities', 'redundancy',
'approachability', 'masterly', 'cookery', 'crystallized', 'Dunham',
'exclaims', 'mainline', 'Australianizes', 'nationhood', 'pusher',
'ushers', 'paranoia', 'workstations', 'radiance', 'impedes',
'Minotaur', 'cataloging', 'bites', 'fashioning', 'Alsop', 'servants',
'Onondaga', 'paragraph', 'leadings', 'clients', 'Latrobe',
'Cornwallis', 'excitingly', 'calorimetric', 'savior', 'tandem',
'antibiotics', 'excuse', 'brushy', 'selfish', 'naive', 'becomes',
'towers', 'popularizes', 'engender', 'introducing', 'possession',
'slaughtered', 'marginally', 'Packards', 'parabola', 'utopia',
'automata', 'deterrent', 'chocolates', 'objectives', 'clannish',
'aspirin', 'ferociousness', 'primarily', 'armpit', 'handfuls',
'dangle', 'Manila', 'enlivened', 'decrease', 'phylum', 'hardy',
'objectively', 'baskets', 'chaired', 'Sepoy', 'deputy', 'blizzard',
'shootings', 'breathtaking', 'sticking', 'initials', 'epitomized',
'Forrest', 'cellular', 'amatory', 'radioed', 'horrified', 'Neva',
'simultaneous', 'delimiter', 'expulsion', 'Himmler', 'contradiction',
'Remus', 'Franklinizations', 'luggage', 'moisture', 'Jews',
'comptroller', 'brevity', 'contradictions', 'Ohio', 'active',
'babysit', 'China', 'youngest', 'superstition', 'clawing', 'raccoons',
'chose', 'shoreline', 'helmets', 'Jeffersonian', 'papered',
'kindergarten', 'reply', 'succinct', 'split', 'wriggle', 'suitcases',
'nonce', 'grinders', 'anthem', 'showcase', 'maimed', 'blue', 'obeys',
'unreported', 'perusing', 'recalculate', 'rancher', 'demonic',
'Lilliputianize', 'approximation', 'repents', 'yellowness',
'irritates', 'Ferber', 'flashlights', 'booty', 'Neanderthal',
'someday', 'foregoes', 'lingering', 'cloudiness', 'guy', 'consumer',
'Berkowitz', 'relics', 'interpolating', 'reappearing', 'advisements',
'Nolan', 'turrets', 'skeletal', 'skills', 'mammas', 'Winsett',
'wheelings', 'stiffen', 'monkeys', 'plainness', 'braziers', 'Leary',
'advisee', 'jack', 'verb', 'reinterpret', 'geometrical', 'trolleys',
'arboreal', 'overpowered', 'Cuzco', 'poetical', 'admirations',
'Hobbes', 'phonemes', 'Newsweek', 'agitator', 'finally', 'prophets',
'environment', 'easterners', 'precomputed', 'faults', 'rankly',
'swallowing', 'crawl', 'trolley', 'spreading', 'resourceful', 'go',
'demandingly', 'broader', 'spiders', 'Marsha', 'debris', 'operates',
'Dundee', 'alleles', 'crunchier', 'quizzical', 'hanging', 'Fisk']

from ZODB.utils import u64

def incedit(edits, wait, ndel=20, nins=20):
    import Zope2, random, string, time
    from ZODB.POSException import ConflictError

    rconflicts=wconflicts=0
    did=str(edits.pop())
    while edits:
        if wait: time.sleep(random.uniform(0,wait))
        jar=Zope2.DB.open()
        app=jar.root()['Application']
        doc=getattr(app.mail, did)

        text=string.split(doc.raw)

        n=random.randint(0,ndel*2)
        for j in range(n):
            if len(text) < 2: break
            j=random.randint(0,len(text)-1)
            #del text[j]

        n=random.randint(0,nins*2)
        for j in range(n):
            word=random.choice(words)
            text.append(word)

        doc.raw=string.join(text)

        try: app.cat.catalog_object(doc)
        except ConflictError, v:
            #print v.args
            rconflicts=rconflicts+1
            transaction.abort()
        else:
            try:
                transaction.commit()
                did=str(edits.pop())
            except ConflictError:
                wconflicts=wconflicts+1
                transaction.abort()

        doc=app=0
        jar.close()

    return rconflicts, wconflicts

def edit():
    import Zope2, thread
    nedit, ndel, nins = atoi(sys.argv[2]), atoi(sys.argv[3]), atoi(sys.argv[4])
    try: threads=atoi(sys.argv[5])
    except:
        threads=1
        wait=0
    else:
        try: wait=atof(sys.argv[6])
        except: wait=0.25
        wait = wait * 2

    if threads==1: start_new_thread=apply
    else: start_new_thread=thread.start_new_thread

    db=Zope2.DB
    app=Zope2.app()
    number_of_messages=app.mail.number_of_messages
    app._p_jar.close()

    size=db.getSize()
    mem=VmSize()
    t=time.time()
    c=time.clock()

    alledits={}
    argss=[]
    for i in range(threads):
        lock=thread.allocate_lock()
        if threads > 1:
            lock.acquire()
            def returnf(t, c, size, mem, r, lock=lock):
                print c, r
                lock.release()
        else:
            def returnf(t, c, size, mem, r, lock=lock):
                print c, r
        edits=[0]
        while len(edits) <= nedit:
            edit=random.randint(0, number_of_messages)
            if not alledits.has_key(edit):
                alledits[edit]=1
                edits.append(edit)
        #print edits
        argss.append((lock, (edits, wait, ndel, nins), returnf))

    for lock, args, returnf in argss:
        start_new_thread(do, (Zope2.DB, incedit, args, returnf))

    for lock, args, returnf in argss:
        lock.acquire()

    t=time.time() - t
    c=time.clock() - c
    size=db.getSize()-size
    mem=VmSize()-mem

    print t, c, size, mem

    #hist("e%s" % (threads))

    Zope2.DB.close()

def VmSize():
    try: f=open('/proc/%s/status' % os.getpid())
    except: return 0
    else:
        l=filter(lambda l: l[:7]=='VmSize:', f.readlines())
        if l:
            l=string.split(string.strip(l[0][7:]))[0]
            return string.atoi(l)
    return 0

def pdebug():
    import pdb
    del sys.argv[1]
    pdb.run('globals()[sys.argv[1]]()')

def usage(code, msg=''):
    print >> sys.stderr, __doc__
    if msg:
        print >> sys.stderr, msg
    sys.exit(code)

if __name__=='__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hv', ['help', 'verbose'])
    except getopt.error, msg:
        usage(1, msg)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-v', '--verbose'):
            VERBOSE = 1

    try:
        f=globals()[sys.argv[1]]
    except:
        print __doc__
        sys.exit(1)
    else:
        f()
