import random
from democontent import DemoContent


class Overview:

    """View for overview.
    """

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


class NewExample:

    """View for new example.
    """

    def helpsWithOne(self):
        return random.randrange(10)

    def two(self):
        return "Two got called"


class DemoContentAddView:

    """Add view for demo content.
    """

    def __call__(self, add_input_name='', title='', submit_add=''):
        if submit_add:
            obj = DemoContent(add_input_name, title)
            self.context.add(obj)
            self.request.response.redirect(self.context.nextURL())
            return ''
        return self.index()
