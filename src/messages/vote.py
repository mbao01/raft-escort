from .base import BaseMessage


class RequestVoteMessage(BaseMessage):

    def __init__(self, sender, receiver, term, data):
        BaseMessage.__init__(self, sender, receiver, term, data, BaseMessage.RequestVote)


class CastVoteMessage(BaseMessage):

    def __init__(self, sender, receiver, term, data):
        BaseMessage.__init__(self, sender, receiver, term, data, BaseMessage.CastVote)
