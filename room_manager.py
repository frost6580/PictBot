from urllib.parse import urlparse
import aiohttp
import asyncio
import json
from bs4 import BeautifulSoup
import time


class RoomManager:

    def __init__(self):
        self._host = None
        self._session = None
        self._session_id = None
        self._ws = None
        self._ready_event = asyncio.Event()
        self.roomInfo = {}
        self.room = {}
        self.answerList = []
        self.visitorCount = 0

        self._stroke_queue = asyncio.Queue()
        self._stroke_task = None
        self._last_stroke_time = 0.0
        self._stroke_pause_until = 0.0

    def _get_domain_from_room(self, room):
        url = room.get("url", None)
        if not url:
            return None
        hostname = urlparse(url).hostname
        if not hostname:
            return None
        return hostname

    async def _start(self, room):
        await self.close()
        self._host = self._get_domain_from_room(room)
        self.roomInfo = room
        self._session = aiohttp.ClientSession(
            headers={
                "Origin": "https://pictsense.com",
                "User-Agent": "Mozilla/5.0",
            }
        )

    async def close(self):
        self._ready_event.clear()
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        self.roomInfo = {}
        self.room = {}
        self.answerList = []
        self.visitorCount = 0

    async def connect(self, room):
        if not room:
            print("[room] ルームの情報が存在しません")
            return
        await self._start(room)
        if not await self._do_handshake(room):
            print("[room] ハンドシェイクに失敗しました")
            return
        if not await self._ws_connect():
            print("[room] WebSocket接続に失敗しました")
            return

    async def _do_handshake(self, room):
        url = f"https://{self._host}/socket.io/1/"
        params = {"rid": room.get("id")}
        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    text = await response.text()
                    self._session_id = text.split(":")[0]
                    print("[room] ハンドシェイク成功")
                    return True
                else:
                    print(f"[room] ハンドシェイク失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"[room] ハンドシェイク失敗: {e}")
            return False

    async def _ws_connect(self):
        if self._session_id is None:
            print("[room] セッションIDがありません")
            return False
        try:
            self._ws = await self._session.ws_connect(
                f"wss://{self._host}/socket.io/1/websocket/{self._session_id}"
            )
            print("[room] WebSocket接続成功")
        except aiohttp.ClientConnectorError as e:
            print(f"[room] WebSocket接続失敗: {e}")
            return False
        except asyncio.TimeoutError:
            print("[room] 接続タイムアウト")
            return False
        except Exception as e:
            print(f"[room] WebSocket接続例外: {e}")
            return False
        else:
            asyncio.create_task(self._ws_on_message())
            self._stroke_task = asyncio.create_task(self._stroke_worker())
            try:
                await self._ready_event.wait()
            except Exception as e:
                print(f"[room] 初期化待機中に例外: {e}")
                return False
            print("[room] 初期化完了")
            return True

    async def _ws_on_message(self):
        async for message in self._ws:
            match message.type:
                case aiohttp.WSMsgType.TEXT:
                    await self._handle_socketio_packet(message.data)
                case aiohttp.WSMsgType.ERROR:
                    print("[room] WebSocket エラー:", self._ws.exception())
                    break
                case _:
                    print("[room] WebSocket メッセージ:", message.type)

    async def _ws_send(self, data):
        if not self._ws or self._ws.closed:
            print("[room] WebSocket 未接続または切断済み")
            return
        try:
            await self._ws.send_str(data)
        except Exception as e:
            print("[room] WebSocket 送信失敗:", e)

    async def _handle_socketio_packet(self, message):
        parse = await self._parse_socketio(message)
        if not parse:
            return
        io_type, io_ack, io_endpoint, io_data = parse
        match io_type:
            case "1":
                return
            case "2":
                # print("[room] ハートビート:")
                await self._ws_send(self._build_socketio(["2", "", "", None]))
                return
            case "5":
                name = io_data.get("name")
                args = io_data.get("args")
                match name:
                    case "error push":
                        if "短時間に連続した" in args[0]:
                            self._stroke_pause_until = time.monotonic() + 1.0
                        else:
                            await self._handle_error(args[0])
                    case "visitorCount push":
                        await self._update_visitorCount(args[0])
                    case "initRoom push":
                        self.room = args[0]
                        self._ready_event.set()
                    case "initCreate push":
                        pass
                    case "entryRoomRequest push":
                        await self._handle_join_request(parse)
                    case "newUser push":
                        await self._add_userList(args[0])
                        await self._handle_join(parse)
                    case "userLeave push":
                        await self._remove_userList(args[0])
                        await self._handle_userleave(parse)
                    case "clear push":
                        await self._handle_clear(parse)
                    case "gameStart push":
                        await self._handle_gamestart(parse)
                    case "subject push":
                        await self._handle_subject(parse)
                    case "sysMessage push":
                        await self._handle_sysmessage(parse)
                    case "question push":
                        await self._handle_question(parse)
                    case "hint push":
                        await self._handle_hint(parse)
                    case "chat push":
                        await self._handle_chat(parse)
                    case "stroke push":
                        await self._handle_stroke(parse)
            case "6":
                print("[room] 6", parse)
            case _:
                print(f"[room] 未処理メッセージ {message}")

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

    async def _get_user_by_uid(self, uid):
        for user in self.room.get("userList", []):
            if user.get("uid") == uid:
                return user
        return None

    async def _get_user_by_name(self, name):
        for user in self.room.get("userList", []):
            if user.get("userName") == name:
                return user
        return None

    async def _update_visitorCount(self, count):
        self.visitorCount = count

    async def _add_userList(self, user):
        self.room.setdefault("userList", []).append(user)

    async def _remove_userList(self, uid):
        self.room["userList"] = [
            u for u in self.room.get("userList", []) if u.get("uid") != uid
        ]

    async def _get_room_dicList(self):
        return self.roomInfo.get("dicList", [])

    async def _fetch_answer_list(self):
        if self.answerList:
            return self.answerList
        dicList = await self._get_room_dicList()
        async with aiohttp.ClientSession() as session:
            for dic in dicList:
                url = f"https://pictsense.com/dic/n{dic[0]}"
                try:
                    async with session.get(url, timeout=10) as resp:
                        resp.raise_for_status()
                        html = await resp.text()
                except Exception as e:
                    print(f"Error fetching {url}: {e}")
                    continue
                soup = BeautifulSoup(html, "html.parser")
                ul = soup.select_one("ul#words")
                if not ul:
                    continue
                for li in ul.select("li"):
                    self.answerList.append(li.get_text(strip=True))
        return self.answerList

    async def _stroke_worker(self):
        while True:
            size, color, opacity, path = await self._stroke_queue.get()

            now = time.monotonic()
            if now < self._stroke_pause_until:
                await asyncio.sleep(self._stroke_pause_until - now)

            now = time.monotonic()
            wait = self._last_stroke_time + 0.2 - now
            if wait > 0:
                await asyncio.sleep(wait)

            params = {
                "name": "stroke send",
                "args": [size, color, opacity, path],
            }
            await self._ws_send(self._build_socketio(["5", "", "", params]))

            self._last_stroke_time = time.monotonic()
            self._stroke_queue.task_done()

    async def join_room(self, name):
        params = {"name": "entryRoomRequest send", "args": [name]}
        await self._ws_send(self._build_socketio(["5", "1+", "", params]))

    async def send_chat(self, text):
        params = {"name": "chat send", "args": [text, 0]}
        await self._ws_send(self._build_socketio(["5", "", "", params]))

    async def send_stroke(self, size=1.0, color=0, opacity=1.0, path=None):
        await self._stroke_queue.put((size, color, opacity, path))

    async def send_clear(self):
        params = {"name": "clear send"}
        await self._ws_send(self._build_socketio(["5", "", "", params]))

    async def send_game(self):
        params = {"name": "gameStart send"}
        await self._ws_send(self._build_socketio(["5", "", "", params]))

    async def send_pass(self):
        params = {"name": "pass send"}
        await self._ws_send(self._build_socketio(["5", "", "", params]))

    async def send_kick(self, uid):
        params = {"name": "kick send", "args": uid}
        await self._ws_send(self._build_socketio(["5", "", "", params]))

    async def send_undo(self):
        params = {"name": "undo send"}
        await self._ws_send(self._build_socketio(["5", "", "", params]))

    async def send_image_search(self):
        params = {"name": "imageSearch send"}
        await self._ws_send(self._build_socketio(["5", "", "", params]))
