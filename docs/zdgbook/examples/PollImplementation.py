from Poll import Poll


class PollImplementation:
    """
    A multiple choice poll, implements the Poll interface.

    The poll has a question and a sequence of responses. Votes
    are stored in a dictionary which maps response indexes to a
    number of votes.
    """

    __implements__ = Poll

    def __init__(self, question, responses):
        self._question = question
        self._responses = responses
        self._votes = {}
        for i in range(len(responses)):
            self._votes[i] = 0

    def castVote(self, index):
        "Votes for a choice"
        self._votes[index] = self._votes[index] + 1

    def getTotalVotes(self):
        "Returns total number of votes cast"
        total = 0
        for v in self._votes.values():
            total = total + v
        return total

    def getVotesFor(self, index):
        "Returns number of votes cast for a given response"
        return self._votes[index]

    def getResponses(self):
        "Returns the sequence of responses"
        return tuple(self._responses)

    def getQuestion(self):
        "Returns the question"
        return self._question
