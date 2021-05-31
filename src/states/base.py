import time
import random
from threading import Timer
from decouple import config

from abc import abstractmethod, ABC
from ..messages.response import ResponseMessage


class BaseState(ABC):
    Leader = 'leader'
    Follower = 'follower'
    Candidate = 'candidate'
    ELECTION_TIMEOUT = int(config('ELECTION_TIMEOUT'))
    HEARTBEAT_TIMEOUT = int(config('HEARTBEAT_TIMEOUT'))

    def __init__(self):
        self._currentTime = None
        self._timeoutTime = None
        self._timer = None

    @abstractmethod
    def set_server(self, server):
        """Provision the server having this state
        """

    def _next_timeout(self, callback, timeout, max_timeout=True):
        if self._timer:
            self._timer.cancel()
        self._currentTime = time.time()
        self._timeoutTime = self._currentTime + random.randrange(timeout, 2 * timeout if max_timeout else timeout + 1)
        timer = Timer(self._timeoutTime - self._currentTime, callback)
        timer.start()
        self._timer = timer

    @abstractmethod
    def on_receive_message(self, message):
        """This method is called when a message is received,
        and calls one of the other corresponding methods
        that the specific state reacts to.
        """

    def _response_message(self, msg, success=True):
        response = ResponseMessage(self._server._name, msg.sender, msg.term, {
            "response": success,
            "currentTerm": self._server._currentTerm,
        })
        return response
