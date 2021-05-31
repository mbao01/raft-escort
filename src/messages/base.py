import time


class BaseMessage(object):
    AppendEntries = 0
    RequestVote = 1
    CastVote = 2
    Response = 3
    ClientMessage = 4

    def __init__(self, sender, receiver, term, data, type):
        self.timestamp = int(time.time())

        self.sender = sender
        self.receiver = receiver
        self.data = data
        self.term = term
        self.type = type
