import socketio
import asyncio


class LobbyManager:
    def __init__(self):
        self.io = socketio.AsyncClient()
        self.host = "https://wl.pictsense.com"
        self.header = {
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://pictsense.com",
            "Referer": "https://pictsense.com/",
        }

        self.init_event = asyncio.Event()

        self.visitorCount = 0
        self.roomList = []

        @self.io.event
        async def connect():
            print("[LOBBY]:接続成功")

        @self.io.event
        async def disconnect():
            print("[LOBBY]:切断されました")

        @self.io.on("init push")
        async def init_push(count, rooms, time):
            self.visitorCount = count
            self.roomList = rooms
            print("[LOBBY]:init push")
            self.init_event.set()

        @self.io.on("error push")
        async def error_push(error):
            print("[LOBBY]:error push", error)

        @self.io.on("visitorCount push")
        async def visitorCount(count):
            self.visitorCount = count
            print("[LOBBY]:visitorCount push", count)

        @self.io.on("createRoom push")
        async def createRoom(room):
            self.roomList.append(room)
            print("[LOBBY]:createRoom push", room)

        @self.io.on("deleteRoom push")
        async def deleteRoom(id):
            self.roomList = [r for r in self.roomList if r.get("id") != id]
            print("[LOBBY]:deleteRoom push", id)

    async def connect(self):
        if not self.io.connected:
            try:
                await self.io.connect(self.host, headers=self.header)
                await self.init_event.wait()
            except Exception as e:
                print("[LOBBY]:接続エラー:", e)

    async def disconnect(self):
        if self.io.connected:
            await self.io.disconnect()

    async def wait(self):
        await self.io.wait()

    async def get_room_by_id(self, room_id):
        return next((r for r in self.roomList if r.get("id") == room_id), None)

    async def get_room_by_name(self, room_name):
        return next((r for r in self.roomList if r.get("name") == room_name), None)

    async def create_room(self, name="room", owner_name="guest"):
        if not self.io.connected:
            return

        data = {
            "name": name,
            "ownerName": owner_name,
            "limitRound": "5",
            "limitTime": "120",
            "interval": "10",
            "penalty": "0",
            "charButtonEnabled": "1",
            "imageSearchButtonEnabled": "0",
            "hintLevel": "3",
            "maxPlayer": "20",
            "secretKey": "",
            "dicList": ["1"],
        }

        future = asyncio.get_event_loop().create_future()

        async def on_response(room):
            future.set_result(room)

        await self.io.emit("createRoom send", data, callback=on_response)

        return await future
