import time

from .voter import Voter
from .base import BaseState
from ..messages.base import BaseMessage
from ..messages.vote import RequestVoteMessage
from src.cache.cache import save_leader, save_election


class Candidate(Voter):

    def __init__(self):
        Voter.__init__(self)

    def set_server(self, server):
        self._server = server
        self._start_election()

    def on_receive_message(self, message):
        """This method is called when a message is received,
        and calls one of the other corresponding methods
        that this state reacts to.
        """
        _type = message.type

        if message.term > self._server._currentTerm:
            self._server._currentTerm = message.term
        # Is the messages.term < ours? If so we need to tell
        #   them this so they don't get left behind.
        elif message.term < self._server._currentTerm:
            return self._response_message(message, success=False)

        if _type == BaseMessage.AppendEntries:
            self._server._currentTerm -= 1
            self._server.change_state(BaseState.Follower)
            self._server._state.on_receive_message(message)  # forward message as follower

    def _reset_election_timeout(self):
        # candidate wins election if election timeout completely or there's a majority vote
        def callback():
            print(f'Election timeout reset for {self._server._name}')

        self._next_timeout(callback, BaseState.ELECTION_TIMEOUT)

    def _declare_election_winner(self):
        # turn back to follower
        # self._server.change_state(BaseState.Follower)
        pass

        # candidate wins election if election timeout completely or there's a majority vote
        # leader = {
        #     'term': self._server._currentTerm,
        #     '_name': self._server._name,
        #     'timestamp': time.time(),
        #     'no_of_votes': 1,
        #     'voted_for_me': [],
        #     'no_of_voters': 1,
        #     'no_of_opposing_votes': 0,
        #     'no_of_expected_voters': 1,
        #     'leader_by_timeout': True
        # }

        # status = save_leader(leader)
        # if status:
        #     self._server.change_state(BaseState.Leader)
        # else:
        #     self._server.change_state(BaseState.Follower)

        # save_election([], self._server._name, self._server._currentTerm)

    def _start_election(self):
        self._server._currentTerm += 1  # increment term
        self._last_vote = self._server._name

        election = RequestVoteMessage(
            self._server._name,
            None,
            self._server._currentTerm,
            {
                "lastLogIndex": self._server._lastLogIndex,
                "lastLogTerm": self._server._lastLogTerm,
            })

        data = self._server.send_message(election, callback=self._reset_election_timeout)
        self._collate_election_result(data)

    def _collate_election_result(self, ballots):

        if ballots and len(ballots) > 0:
            leader = list(filter(lambda ballot:
                                 ballot and hasattr(ballot, '__getitem__') and ballot['data'].get('leaderAlive', None),
                                 ballots))

            if len(leader) == 0:
                no_of_expected_voters = len(ballots)
                actual_voters = list(filter(lambda ballot: ballot and hasattr(ballot, '__getitem__') and
                                                           self._server._currentTerm == ballot['term'], ballots))
                no_of_voters = len(actual_voters)
                voted_for_me = [voter['sender'] for voter in actual_voters if voter['data']['response']]
                no_of_votes = len(voted_for_me)
                no_of_opposing_votes = no_of_voters - no_of_votes

                if no_of_votes * 2 > no_of_voters:  # leader by majority voting -> tied vote not handled
                    leader = {
                        'term': self._server._currentTerm,
                        '_name': self._server._name,
                        'timestamp': time.time(),
                        'no_of_votes': no_of_votes + 1,
                        'voted_for_me': voted_for_me,
                        'no_of_voters': no_of_voters + 1,
                        'no_of_opposing_votes': no_of_opposing_votes,
                        'no_of_expected_voters': no_of_expected_voters + 1,
                        'leader_by_timeout': False
                    }
                    save_leader(leader)
                    self._server.change_state(BaseState.Leader)

                save_election(ballots, self._server._name, self._server._currentTerm)
            elif self._server._currentTerm >= 2:
                # skip the first and second round of elections because everyone is free to be a candidate
                self._server._currentTerm -= 1
                self._reset_election_timeout()
