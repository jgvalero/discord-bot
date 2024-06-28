class Voting:
    def __init__(self, requiredVotes=0):
        self.requiredVotes = requiredVotes
        self.currentVotes = 0
        self.voters = []

    def addVote(self, user):
        if user not in self.voters:
            self.currentVotes += 1
            self.voters.append(user)
            return True
        return False

    def isDone(self):
        return self.currentVotes >= self.requiredVotes

    def reset(self):
        self.currentVotes = 0
