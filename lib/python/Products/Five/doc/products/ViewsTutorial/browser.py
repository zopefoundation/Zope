from Products.Five import BrowserView
import random

class Overview(BrowserView):
    def reversedIds(self):
        result = []
        for id in self.context.objectIds():
            l = list(id)
            l.reverse()
            reversed_id = ''.join(l)
            result.append(reversed_id)
        return result

    def directlyPublished(self):
        return "This is directly published"

class NewExample(BrowserView):
    def helpsWithOne(self):
        return random.randrange(10)
    
    def two(self):
        return "Two got called"
