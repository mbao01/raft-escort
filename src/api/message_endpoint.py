from .base import BaseAPI


class MessageEndpoint(BaseAPI):

    endpoint = BaseAPI.Message

    def __init__(self, message, receiver):
        BaseAPI.__init__(self, message, receiver)
