from Products.ZCTextIndex.ISplitter import ISplitter

import re

class HTMLSplitter:

    __implements__ = ISplitter

    def process(self, text):
        return re.sub('<[^>]*>', ' ', text).split()

class HTMLWordSplitter:

    __implements__ = ISplitter

    def process(self, text):
        splat = []
        for t in text:
            splat += self.split(t)
        return splat    

    def split(self, text):    
        text = text.lower()
        remove = ["<[^>]*>",
                  "&[A-Za-z]+;",
                  "\W+"]
        for pat in remove:
            text = re.sub(pat, " ", text)
        rx = re.compile("[A-Za-z]")
        return [word for word in text.split()
                if len(word) > 1 and rx.search(word)]

if __name__ == "__main__":
    import sys
    splitter = HTMLWordSplitter()
    for path in sys.argv[1:]:
        f = open(path, "rb")
        buf = f.read()
        f.close()
        print path
        print splitter.process([buf])
