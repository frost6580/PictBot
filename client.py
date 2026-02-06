from lobby_manager import LobbyManager
from room_manager import RoomManager
import asyncio


class Pictsense:
    def __init__(self):
        self._events = {}
        self.lobby = LobbyManager()
        self.room = RoomManager()

    def event(self, func):
        self._events[func.__name__] = func
        return func

    async def connect(self):
        print("[CLIENT]:Connect")
        await self.lobby.connect()

    async def close(self):
        print("[CLIENT]:Close")
        await self.lobby.disconnect()
        await self.room.disconnect()

    async def dispatch_event(self, name, *args):
        func = self._events.get(name)
        if func:
            await func(*args)

    async def _run(self):
        await self.connect()

        await self.dispatch_event("on_ready")
        
        try:
            await asyncio.gather(
                self.lobby.wait(),
                self.room.wait()
            )
        except (asyncio.CancelledError, KeyboardInterrupt):
            await self.close()

    def run(self):
        asyncio.run(self._run())
