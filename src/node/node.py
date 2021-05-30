import time
import aiohttp
import asyncio

from src.cache.cache import get_neighbors
from src.states.base import BaseState
from src.states.leader import Leader
from src.states.follower import Follower
from src.states.candidate import Candidate
from src.api.message_endpoint import MessageEndpoint


class Node(object):

    def __init__(self, name: str, log: list = None):
        self._neighbors: list[Node] = get_neighbors(name=name)
        self._name = name
        self._creationTime = int(time.time())
        self._log = log if log else []
        self._total_nodes = 0

        self._commitIndex = 0
        self._currentTerm = 0

        self._lastApplied = 0

        self._lastLogIndex = 0
        self._lastLogTerm = None
        self._state = None
        self.change_state(BaseState.Follower)  # any node entering the raft enters as a Follower

        print(f'::: New node instantiated ::: Node name: {self._name}')

    def __str__(self):
        return f'Node:: {self._name}'

    async def send_message(self, message, neighbors=None, callback=None, **kwargs):
        neighbors = neighbors if neighbors else get_neighbors(name=self._name)
        async with aiohttp.ClientSession() as session:
            data = await asyncio.gather(
                *[self._post_message(session, message, receiver=node['_name'], callback=callback, **kwargs)
                  for node in neighbors], return_exceptions=True)
            return data

    def reply_message_sender(self, message):
        n = [n for n in self._neighbors if n._name == message.receiver]
        if len(n) > 0:
            self.send_message(message, neighbors=n)

    @staticmethod
    async def _post_message(session, message, receiver=None, callback=None, **kwargs):
        async with MessageEndpoint(message, receiver).post(session, **kwargs) as resp:
            try:
                data = await resp.json()
            except:
                data = None

            if callback:
                callback()  # reset election timeout
            return data

    def on_message(self, message):
        state, response = self._state.on_message(message)
        self._state = state

    def change_state(self, new_state=BaseState.Follower):
        if self._state and hasattr(self._state, '_timer'):
            self._state._timer.cancel()

        if new_state == BaseState.Leader:
            state = Leader()
        elif new_state == BaseState.Follower:
            state = Follower()
        elif new_state == BaseState.Candidate:
            state = Candidate()

        self._state = state
        state.set_server(self)
