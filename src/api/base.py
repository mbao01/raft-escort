import time

from src.api.helper import serialize


class BaseAPI(object):
    Message = '/message'

    def __init__(self, message, receiver=None):
        self.timestamp = int(time.time())

        self.url = f'http://{receiver if receiver else message.receiver}{self.endpoint}'
        self.body = message

    def post(self, session, **kwargs):
        data = serialize(self.body)
        return session.post(self.url, json=data, timeout=15, **kwargs)
