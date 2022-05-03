from Interface import Base


class Poll(Base):
    "A multiple choice poll"

    def castVote(self, index):
        "Votes for a choice"

    def getTotalVotes(self):
        "Returns total number of votes cast"

    def getVotesFor(self, index):
        "Returns number of votes cast for a given response"

    def getResponses(self):
        "Returns the sequence of responses"

    def getQuestion(self):
        "Returns the question"
