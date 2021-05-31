import asyncio
from collections import defaultdict

from .base import BaseState
from ..api.helper import serialize
from ..cache.cache import get_neighbors
from ..messages.base import BaseMessage
from ..messages.append_entries import AppendEntriesMessage
from ..messages.response import ResponseMessage


class Leader(BaseState):

    def __init__(self):
        BaseState.__init__(self)
        self._nextIndexes = defaultdict(int)
        self._matchIndex = defaultdict(int)

    def set_server(self, server):
        self._server = server
        if self._server._currentTerm == 1 and len(self._server._log) == 0:
            self._server._position = [0, 0]

        # continue from where last leader stopped.
        if len(self._server._log) > 0:
            last_log = self._server._log[-1]
            self._server._position = last_log.currentLeaderPosition
        else:
            self._server._position = [0, 0]

        self._send_heartbeat()

        # send message at every heartbeat
        self._next_timeout(self._send_heartbeat, BaseState.HEARTBEAT_TIMEOUT, max_timeout=False)

        self._server._neighbors = get_neighbors(name=self._server._name)

        for n in self._server._neighbors:
            self._nextIndexes[n['_name']] = self._server._lastLogIndex + 1
            self._matchIndex[n['_name']] = 0

    def on_receive_message(self, message):
        # Was the last AppendEntries good?
        _type = message.type

        if _type == BaseMessage.RequestVote:
            # when a new node joins, the new node may want to request an election. If a leader exists, send a heartbeat
            # to the node
            message = ResponseMessage(
                self._server._name,
                message.sender,
                self._server._currentTerm,
                {
                    "response": False,
                    "leaderAlive": self._server._name
                }
            )
            return serialize(message)

        elif _type == BaseMessage.ClientMessage:
            # only when there's a client request to log
            move = message.data.get('move', [0, 0])
            new_position = [coord + move[idx] for idx, coord in enumerate(self._server._position)]
            log = {
                "leaderId": self._server._name,
                "prevLogIndex": self._server._lastLogIndex,
                "prevLogTerm": self._server._lastLogTerm,
                "entries": [{
                    'term': self._server._currentTerm,
                    'previousLeaderPosition': self._server._position,
                    'currentLeaderPosition': new_position,
                    'move': message.data['move']  # direction to move in
                }],
                "leaderCommit": self._server._commitIndex,
            }
            data = self._send_heartbeat(log)

            self._server._log.append(log)
            self._server._position = new_position

            self._handle_node_response(data)

            message = ResponseMessage(
                self._server._name,
                None,
                self._server._currentTerm,
                {
                    'node': self._server._name,
                    'is_leader': True,
                    'log': self._server._log
                }
            )
            return serialize(message)

    def _handle_node_response(self, responses):
        """This is called when the Leader node receives a response from a Follower"""
        for idx, data in enumerate(responses):
            if data:
                if not data['data']['response']:
                    # No, so lets back up the log for this node
                    self._nextIndexes[data['sender']] -= 1

                    # Get the next log entry to send to the client.
                    previousIndex = max(0, self._nextIndexes[data['sender']] - 1)
                    previous = self._server._log[previousIndex]
                    current = self._server._log[self._nextIndexes[data['sender']]]

                    # Send the new log to the client and wait for it to respond.
                    message = AppendEntriesMessage(
                        self._server._name,
                        data['sender'],
                        self._server._currentTerm,
                        {
                            "leaderId": self._server._name,
                            "prevLogIndex": previousIndex,
                            "prevLogTerm": previous["term"],
                            "entries": [current],
                            "leaderCommit": self._server._commitIndex,
                        })
                    data = self._server.send_message(message, neighbors=[{'_name': data['sender']}])
                    responses[idx] = data[0]
                    print(data)
                    # self._handle_node_response(data)  # could cause leader to be unavailable
                else:
                    # The last append was good so increase their index.
                    self._nextIndexes[data['sender']] += 1

                    # Are they caught up?
                    if self._nextIndexes[data['sender']] > self._server._lastLogIndex:
                        self._nextIndexes[data['sender']] = self._server._lastLogIndex
        return responses

    def _send_heartbeat(self, log=None):
        self._server._commitIndex = self._server._commitIndex + 1

        message = AppendEntriesMessage(
            self._server._name,
            None,
            self._server._currentTerm,
            log if log else {}
        )

        data = self._server.send_message(message)
        return data
