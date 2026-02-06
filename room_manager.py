import socketio
import asyncio
from urllib.parse import urlencode


class RoomManager:

    def __init__(self):

        self.io = socketio.AsyncClient()

        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Origin": "https://pictsense.com",
            "Referer": "https://pictsense.com/",
        }

        self.room = None

        self.init_event = asyncio.Event()

        @self.io.event
        async def connect():
            print("[ROOM]:接続成功")

        @self.io.event
        async def disconnect():
            print("[ROOM]:切断されました")
            self.disconnect()

        @self.io.on("initRoom push")
        async def initRoom_push(data):
            print("[ROOM]:initRoom push", data)
            self.init_event.set()

        @self.io.on("error push")
        async def error_push(error):
            print("[ROOM]:error push", error)

        @self.io.on("entryRoomRequest push")
        async def entryRoomRequest_push(name):
            print("[ROOM]:entryRoomRequest_push", name)
            return True, False

        @self.io.on("*")
        async def catch_all(event, *args):
            print("[ROOM]:[wild_push]", event, args)

    async def connect(self, room):
        if not room:
            print("[ROOM]: 部屋情報が空です")
            return
        if self.io.connected:
            await self.disconnect()
        else:
            self.init_event.clear()
            try:
                url = room.get("url").rstrip("/")
                params = {"rid": room.get("id"), "ownerKey": room.get("ownerKey")}
                await self.io.connect(f"{url}?{urlencode(params)}", headers=self.header)
                await self.init_event.wait()
                print("[ROOM]:リンク", f"https://pictsense.com/#!/{room.get('id')}")
                self.room = room
            except Exception as e:
                print("[ROOM]:接続エラー:", e)

    async def disconnect(self):
        if self.io.connected:
            await self.io.disconnect()
        if self.room:
            self.room = None

    async def wait(self):
        await self.io.wait()

    async def send_stroke(self, size=1.0, color=0, opacity=1.0, path=None):
        if path is None:
            path = [[0, 0], [320, 320]]
        await self.io.emit("stroke send", (size, color, opacity, path))
