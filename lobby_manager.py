import aiohttp
import asyncio
import json


class LobbyManager:

    def __init__(self):
        self._host = "https://lobby.pictsense.com/socket.io/1/"
        self._wss = "wss://lobby.pictsense.com/socket.io/1/websocket/"

        self._session = None
        self._session_id = None
        self._ws = None

        self._ready_event = asyncio.Event()
        self._create_event = asyncio.Event()

        self.roomList = {}
        self.visitorCount = 0
        self.createRoom = {}

    async def _start(self):
        self._session = aiohttp.ClientSession(
            headers={
                "Origin": "https://pictsense.com",
                "User-Agent": "Mozilla/5.0",
            }
        )

    async def close(self):
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()

    async def connect(self):
        await self._start()
        if not await self._do_handshake():
            print("[lobby] ハンドシェイクに失敗しました")
            return
        if not await self._ws_connect():
            print("[lobby] WebSocket接続に失敗しました")
            return

    async def _do_handshake(self):
        try:
            async with self._session.get(self._host) as response:
                if response.status == 200:
                    text = await response.text()
                    self._session_id = text.split(":")[0]
                    print("[lobby] ハンドシェイク成功")
                    return True
                else:
                    print(f"[lobby] ハンドシェイク失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"[lobby] ハンドシェイク失敗: {e}")
            return False

    async def _ws_connect(self):
        if self._session_id is None:
            print("[lobby] セッションIDがありません")
            return False

        try:
            self._ws = await self._session.ws_connect(self._wss + self._session_id)
            print("[lobby] WebSocket接続成功")

        except aiohttp.ClientConnectorError as e:
            print(f"[lobby] WebSocket接続失敗: {e}")
            return False
        except asyncio.TimeoutError:
            print("[lobby] 接続タイムアウト")
            return False
        except Exception as e:
            print(f"[lobby] WebSocket接続例外: {e}")
            return False
        else:
            asyncio.create_task(self._ws_on_message())
            try:
                await self._ready_event.wait()
            except Exception as e:
                print(f"[lobby] 初期化待機中に例外: {e}")
                return False

            print("[lobby] 初期化完了")
            return True

    async def _ws_on_message(self):
        async for message in self._ws:
            match message.type:
                case aiohttp.WSMsgType.TEXT:
                    await self._handle_socketio_packet(message.data)
                case aiohttp.WSMsgType.ERROR:
                    print("[lobby] WebSocket エラー:", self._ws.exception())
                    break
                case _:
                    print("[lobby] WebSocket メッセージ:", message.type)

    async def _ws_send(self, data):
        if not self._ws or self._ws.closed:
            print("[lobby] WebSocket 未接続または切断済み")
            return
        try:
            await self._ws.send_str(data)
        except Exception as e:
            print("[lobby] WebSocket 送信失敗:", e)

    async def _handle_socketio_packet(self, message):
        parse = await self._parse_socketio(message)
        if not parse:
            return

        io_type, io_ack, io_endpoint, io_data = parse

        match io_type:
            case "1":
                return
            case "2":
                # print("[lobby] ハートビート:")
                await self._ws_send(self._build_socketio(["2", "", "", None]))
                return
            case "5":
                name = io_data.get("name")
                args = io_data.get("args")
                match name:
                    case "error push":
                        # print("[lobby] エラー:", args[0])
                        await self._handle_error(args[0])
                    case "init push":
                        await self._update_visitorCount(args[0])
                        await self._update_roomList(args[1])
                        self._ready_event.set()
                    case "visitorCount push":
                        await self._update_visitorCount(args[0])
                    case "createRoom push":
                        await self._add_roomList(args[0])
                    case "deleteRoom push":
                        await self._remove_roomList(args[0])
                    case "changeRoom push":
                        await self._change_roomList()
                return
            case "6":
                self.createRoom = io_data[0]
                self._create_event.set()
                return
            case _:
                print(f"[lobby] 未処理メッセージ {message}")

    async def _parse_socketio(self, raw):
        if not raw:
            return None
        parts = (raw.split(":", 3) + ["", "", "", ""])[:4]
        if not parts[0].isdigit():
            return None
        if parts[0] == "6":
            parts[1] = parts[3][:2]
            parts[3] = parts[3][2:]
        data = None
        if parts[3]:
            try:
                data = json.loads(parts[3])
            except json.JSONDecodeError:
                data = parts[3]
        return [parts[0], parts[1], parts[2], data]

    def _build_socketio(self, message):
        if not message or len(message) != 4:
            return None
        _type, _id, endpoint, data = message
        if data is None:
            return f"{_type}:{_id}:{endpoint}"
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False)
        else:
            data = str(data)
        return f"{_type}:{_id}:{endpoint}:{data}"

    async def _update_visitorCount(self, count):
        self.visitorCount = count

    async def get_visitorCount(self):
        return self.visitorCount

    async def _update_roomList(self, room):
        self.roomList = room

    async def _add_roomList(self, room):
        self.roomList.append(room)

    async def _remove_roomList(self, room_id):
        self.roomList = [room for room in self.roomList if room.get("id") != room_id]

    async def _change_roomList(self):
        pass

    async def get_room_by_id(self, room_id):
        for room in self.roomList:
            if room.get("id") == room_id:
                return room
        print("[lobby]　ルームが見つかりませんでした")
        return None

    async def get_room_by_name(self, room_name):
        for room in self.roomList:
            if room.get("name") == room_name:
                return room
        print("[lobby]　ルームが見つかりませんでした")
        return None

    async def get_room_by_owner(self, owner_name):
        for room in self.roomList:
            if room.get("ownerName") == owner_name:
                return room
        print("[lobby]　ルームが見つかりませんでした")
        return None

    async def get_room_by_index(self, index):
        try:
            return self.roomList[index]
        except IndexError:
            return None

    async def create_room(
        self,
        name="雑談",
        ownerName="Bot",
        limitRound="5",
        limitTime="120",
        interval="10",
        penalty="0",
        charButtonEnabled="1",
        imageSearchButtonEnabled="0",
        hintLevel="0",
        maxPlayer="20",
        secretKey="",
        dicList=None,
    ):
        if dicList is None:
            dicList = ["1"]

        self._create_event.clear()

        params = {
            "name": "createRoom send",
            "args": [
                {
                    "name": name,
                    "ownerName": ownerName,
                    "limitRound": limitRound,
                    "limitTime": limitTime,
                    "interval": interval,
                    "penalty": penalty,
                    "charButtonEnabled": charButtonEnabled,
                    "imageSearchButtonEnabled": imageSearchButtonEnabled,
                    "hintLevel": hintLevel,
                    "maxPlayer": maxPlayer,
                    "secretKey": secretKey,
                    "dicList": dicList,
                }
            ],
        }

        await self._ws_send(self._build_socketio(["5", "1+", "", params]))
        await self._create_event.wait()

        if not self.createRoom:
            return None

        print(
            "[lobby] 部屋を作成しました",
            f"https://pictsense.com/#!/{self.createRoom.get('id')}",
        )

        return self.createRoom
