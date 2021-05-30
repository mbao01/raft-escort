import asyncio
import time

from .base import BaseState
from .voter import Voter
from ..messages.base import BaseMessage
from ..messages.vote import RequestVoteMessage
from src.cache.cache import save_leader, save_election


class Candidate(Voter):

    def set_server(self, server):
        self._server = server
        self._votes = {}
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
            self._server.change_state(BaseState.Follower)
            self._server.state.on_receive_message(message)

    def _reset_election_timeout(self):
        # candidate wins election if election timeout completely or there's a majority vote
        def callback():
            print(f'Election timeout reset for {self._server._name}')
        self._next_timeout(callback, BaseState.ELECTION_TIMEOUT)

    def _declare_election_winner(self):
        # turn back to follower
        self._server.change_state(BaseState.Follower)

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

        data = asyncio.run(self._server.send_message(election, callback=self._reset_election_timeout))
        self._collate_election_result(data)

    def _collate_election_result(self, ballots):
        # [{'data': {'response': False}, 'receiver': '172.18.0.4:8080', 'sender': '172.18.0.6:8080', 'term': 9,
        #   'timestamp': 1622317405, 'type': 2}]
        if ballots and len(ballots) > 0:
            no_of_expected_voters = len(ballots)
            actual_voters = list(filter(lambda ballot: ballot and self._server._currentTerm == ballot['term'], ballots))
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
                status = save_leader(leader)
                if status:
                    self._server.change_state(BaseState.Leader)
                    print('Leader found!!!', self._server._name)
                else:
                    self._server.change_state(BaseState.Follower)
            else:
                self._server.change_state(BaseState.Follower)
            save_election(ballots, self._server._name, self._server._currentTerm)
        else:
            self._server.change_state(BaseState.Follower)
