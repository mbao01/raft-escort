from abc import ABC

from .base import BaseState
from ..messages.vote import RequestVoteMessage, CastVoteMessage


class Voter(BaseState, ABC):
    _ELECTION_TIMEOUT = 300

    def __init__(self):
        BaseState.__init__(self)
        self._last_vote = None

    def handle_vote_request(self, message: RequestVoteMessage):
        """This is called when there is a vote request."""
        if(self._last_vote is None and
           message.data["lastLogIndex"] >= self._server._lastLogIndex):
            self._last_vote = message.sender
            return self._cast_vote_message(message, vote_for=True)
        else:
            return self._cast_vote_message(message, vote_for=False)

    def _cast_vote_message(self, message: RequestVoteMessage, vote_for: bool) -> CastVoteMessage:
        vote_response = CastVoteMessage(
            self._server._name,
            message.sender,
            message.term,
            {"response": vote_for})

        return vote_response
