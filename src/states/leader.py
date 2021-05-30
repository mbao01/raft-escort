import asyncio
from collections import defaultdict
from .base import BaseState
from ..messages.base import BaseMessage
from ..messages.response import ResponseMessage
from ..messages.append_entries import AppendEntriesMessage


class Leader(BaseState):

    def __init__(self):
        self._nextIndexes = defaultdict(int)
        self._matchIndex = defaultdict(int)

    def set_sever(self, server):
        self._sever = server
        self.__send_heartbeat()

        # send message at every heartbeat
        self._next_timeout(self.__send_heartbeat, BaseState.HEARTBEAT_TIMEOUT)

        for n in self._server._neighbors:
            self._nextIndexes[n._name] = self._server._lastLogIndex + 1
            self._matchIndex[n._name] = 0

    def on_receive_message(self, message):
        # Was the last AppendEntries good?
        _type = message.type

        if _type == BaseMessage.RequestVote:
            # when a new node joins, the new node may want to request an election. If a leader exists, send a heartbeat
            # to the node
            message = AppendEntriesMessage(
                self._server._name,
                message.sender,
                self._server._currentTerm,
                {
                    "leaderId": self._server._name,
                    "prevLogIndex": self._server._lastLogIndex,
                    "prevLogTerm": self._server._lastLogTerm,
                    "entries": [],
                    "leaderCommit": self._server._commitIndex,
                })

            data = asyncio.run(self._server.send_message(message, neighbors=[{'_name': message.sender}]))
            print('Ping from candidate', data)

    def _handle_node_response(self, messages):
        """This is called when the Leader node receives a response from a Follower"""
        print('hmmmm: ', messages)
        for message in messages:
            if message:
                if not message['data']['response']:
                    # No, so lets back up the log for this node
                    self._nextIndexes[message['sender']] -= 1

                    # Get the next log entry to send to the client.
                    previousIndex = max(0, self._nextIndexes[message['sender']] - 1)
                    previous = self._server._log[previousIndex]
                    current = self._server._log[self._nextIndexes[message['sender']]]

                    # Send the new log to the client and wait for it to respond.
                    appendEntry = AppendEntriesMessage(
                        self._server._name,
                        message['sender'],
                        self._server._currentTerm,
                        {
                            "leaderId": self._server._name,
                            "prevLogIndex": previousIndex,
                            "prevLogTerm": previous["term"],
                            "entries": [current],
                            "leaderCommit": self._server._commitIndex,
                        })

                    # self._server(appendEntry)
                else:
                    # The last append was good so increase their index.
                    self._nextIndexes[message['sender']] += 1

                    # Are they caught up?
                    if(self._nextIndexes[message['sender']] > self._server._lastLogIndex):
                        self._nextIndexes[message['sender']] = self._server._lastLogIndex

        return self, None

    def __send_heartbeat(self):
        self._leader_position = [self._leader_position[0] + 1, 0]
        self._server._commitIndex = self._server._commitIndex + 1
        message = AppendEntriesMessage(
            self._server._name,
            None,
            self._server._currentTerm,
            {
                "leaderId": self._server._name,
                "prevLogIndex": self._server._lastLogIndex,
                "prevLogTerm": self._server._lastLogTerm,
                "entries": [{
                    'leader_position': self._leader_position
                }],
                "leaderCommit": self._server._commitIndex,
            })

        data = asyncio.run(self._server.send_message(message))
        self._handle_node_response(data)
