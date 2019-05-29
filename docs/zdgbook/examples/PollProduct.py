from AccessControl import ClassSecurityInfo
from AccessControl.Role import RoleManager
from Acquisition import Implicit
from Globals import InitializeClass
from Globals import Persistent
from OFS.SimpleItem import Item
from Poll import Poll


class PollProduct(Implicit, Persistent, RoleManager, Item):
    """
    Poll product class, implements Poll interface.

    The poll has a question and a sequence of responses. Votes
    are stored in a dictionary which maps response indexes to a
    number of votes.
    """

    __implements__ = Poll

    meta_type = 'Poll'

    security = ClassSecurityInfo()

    def __init__(self, id, question, responses):
        self.id = id
        self._question = question
        self._responses = responses
        self._votes = {}
        for i in range(len(responses)):
            self._votes[i] = 0

    @security.protected('Use Poll')
    def castVote(self, index):
        "Votes for a choice"
        self._votes[index] = self._votes[index] + 1
        self._votes = self._votes

    @security.protected('View Poll Results')
    def getTotalVotes(self):
        "Returns total number of votes cast"
        total = 0
        for v in self._votes.values():
            total = total + v
        return total

    @security.protected('View Poll Results')
    def getVotesFor(self, index):
        "Returns number of votes cast for a given response"
        return self._votes[index]

    @security.public
    def getResponses(self):
        "Returns the sequence of responses"
        return tuple(self._responses)

    @security.public
    def getQuestion(self):
        "Returns the question"
        return self._question


InitializeClass(PollProduct)
