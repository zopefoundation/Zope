import rfc822,mailbox,cPickle,string

class Keywords:
    """ stupid class to read a list of rfc822 messages and extract
    all words from the subject header. We use this class for testing
    purposes only
    """

    def __init__(self):
        self.kw = []

    def build(self,mbox,limit):

        mb = mailbox.UnixMailbox(open(mbox))
        msg = mb.next()

        while msg and len(self.kw) < limit:

            sub =  msg.dict.get("subject","").split(' ')
            for f in sub:
                ok = 1
                for c in f:
                    if not c in string.letters: ok=0

                if ok==1 and  not f in self.kw : self.kw.append(f)

            msg = mb.next()

        P = cPickle.Pickler(open('data/keywords','w'))
        P.dump(self.kw)

    def reload(self):
        P = cPickle.Unpickler(open('data/keywords','r'))
        self.kw = P.load()


    def keywords(self):
        return self.kw




if __name__=="__main__":

    k = Keywords()
    k.build("/home/andreas/zope.mbox",1000)
