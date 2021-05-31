from .base import BaseMessage


class ClientMessage(BaseMessage):

    def __init__(self, sender, receiver, term, data):
        BaseMessage.__init__(self, sender, receiver, term, data, BaseMessage.ClientMessage)
