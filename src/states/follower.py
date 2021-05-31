import random

from .voter import Voter
from .base import BaseState
from ..messages.base import BaseMessage
from ..messages.append_entries import AppendEntriesMessage


class Follower(Voter):

    def __init__(self):
        Voter.__init__(self)
        self._next_timeout(self.on_leader_timeout, BaseState.ELECTION_TIMEOUT)

    def set_server(self, server):
        self._server = server
        if self._server._position is None:
            self._position_node()

    def on_receive_message(self, message):
        """This method is called when a message is received,
        and calls one of the other corresponding methods that
        this state reacts to.
        """
        _type = message.type
        response = None
        if _type == BaseMessage.AppendEntries:
            response = self.handle_append_entries(message)
        elif _type == BaseMessage.RequestVote:
            response = self.handle_vote_request(message)
        self._next_timeout(self.on_leader_timeout, BaseState.ELECTION_TIMEOUT * 2)
        return response

    def handle_append_entries(self, message: AppendEntriesMessage):
        """This is called when there is a request to
        append an entry to the log.
        """
        # cancel time (in other to exclude node processing time)
        self._timer.cancel()
        self._server._currentTerm = message.term

        if message.data != {}:
            log = self._server._log
            data = message.data

            # Check if the leader is too far ahead in the log.
            if data["leaderCommit"] != self._server._commitIndex:
                # If the leader is too far ahead then we
                #   use the length of the log - 1
                self._server._commitIndex = min(data["leaderCommit"], len(log) - 1)

            # Can't possibly be up-to-date with the log
            # If the log is smaller than the preLogIndex
            if len(log) < data["prevLogIndex"]:
                return self._response_message(message, success=False)

            # We need to hold the induction proof of the algorithm here.
            #   So, we make sure that the prevLogIndex term is always
            #   equal to the server.
            if len(log) > 0 and log[data["prevLogIndex"]]["term"] != data["prevLogTerm"]:

                # There is a conflict we need to resync so delete everything
                #   from this prevLogIndex and forward and send a failure
                #   to the Leader.
                log = log[:data["prevLogIndex"]]
                response = self._response_message(message, success=False)
                self._server._log = log
                self._server._lastLogIndex = data["prevLogIndex"]
                self._server._lastLogTerm = data["prevLogTerm"]
                return response
            # The induction proof held so lets check if the commitIndex
            #   value is the same as the one on the leader
            else:
                # Make sure that leaderCommit is > 0 and that the
                #   data is different here
                if (len(log) > 0 and
                        data["leaderCommit"] > 0 and
                        log[data["leaderCommit"]]["term"] != message.term):
                    # Data was found to be different so we fix that
                    #   by taking the current log and slicing it to the
                    #   leaderCommit + 1 range then setting the last
                    #   value to the commitValue
                    log = log[:self._server._commitIndex]
                    for e in data["entries"]:
                        log.append(e)
                        self._server._commitIndex += 1

                    response = self._response_message(message)
                    self._server._lastLogIndex = len(log) - 1
                    self._server._lastLogTerm = log[-1]["term"]
                    self._commitIndex = len(log) - 1
                    self._server._log = log
                    return response
                else:
                    # The commit index is not out of the range of the log
                    #   so we can just append it to the log now.
                    #   commitIndex = len(log)
                    #   Is this a heartbeat?
                    if len(data["entries"]) > 0:
                        log.append(data)  # append data to log

                        for entry in data["entries"]:
                            # move follower according to leader
                            move = entry.get('move', [0, 0])
                            self._server.update_position(move)
                            self._server._commitIndex += 1

                        self._server._lastLogIndex = len(log) - 1
                        self._server._lastLogTerm = log[-1]["term"]
                        self._commitIndex = len(log) - 1
                        self._server._log = log

                        return self._response_message(message)
            return self._response_message(message)

    def on_leader_timeout(self):
        """This is called when the leader timeout is reached.
        Follower becomes candidate and calls for an election
        """
        print(f'Leader timed out! \nInitial time {self._currentTime}\nTimeout time {self._timeoutTime}')
        self._server.change_state(BaseState.Candidate)

    def _position_node(self):
        polarity = self._server._polarity
        y = random.randint(-50, 50)
        move = [random.randint(0, 50), y] if polarity == 1 else [random.randint(-50, 0), y]
        self._server.update_position(move)
