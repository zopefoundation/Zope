from Poll import Poll
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Acquisition import Implicit
from Globals import Persistent
from AccessControl.Role import RoleManager
from OFS.SimpleItem import Item

class PollProduct(Implicit, Persistent, RoleManager, Item):
    """
    Poll product class, implements Poll interface.

    The poll has a question and a sequence of responses. Votes
    are stored in a dictionary which maps response indexes to a
    number of votes.
    """

    __implements__=Poll

    meta_type='Poll'

    security=ClassSecurityInfo()

    def __init__(self, id, question, responses):
        self.id=id
        self._question = question
        self._responses = responses
        self._votes = {}
        for i in range(len(responses)):
            self._votes[i] = 0

    security.declareProtected('Use Poll', 'castVote')
    def castVote(self, index):
        "Votes for a choice"
        self._votes[index] = self._votes[index] + 1
        self._votes = self._votes

    security.declareProtected('View Poll Results', 'getTotalVotes') 
    def getTotalVotes(self):
        "Returns total number of votes cast"
        total = 0
        for v in self._votes.values():
            total = total + v
        return total

    security.declareProtected('View Poll Results', 'getVotesFor') 
    def getVotesFor(self, index):
        "Returns number of votes cast for a given response"
        return self._votes[index]

    security.declarePublic('getResponses') 
    def getResponses(self):
        "Returns the sequence of responses"
        return tuple(self._responses)

    security.declarePublic('getQuestion') 
    def getQuestion(self):
        "Returns the question"
        return self._question


InitializeClass(PollProduct)
