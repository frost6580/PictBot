from client import Pictsense
import asyncio

client = Pictsense()


@client.event
async def on_ready():
    print("Bot起動成功")
    # await client.dos_attack()
    is_create = True
    if is_create:
        await client.create_room()
    else:
        await client.join_room()


@client.event
async def on_join_request(message):
    # print("参加リクエスト:", message)
    name = message[3].get("args", [])[0]
    print(f"参加リクエスト: {name}さん")
    await client.auto_reply_join_request(message)


@client.event
async def on_join(message):
    # print("参加:", message)
    args = message[3].get("args", [])[0]
    uid = args["uid"]
    name = args["userName"]
    point = args["point"]
    color = args["userColor"]
    print(f"参加: {name}さん")
    await client.send_chat(f"{name}さん、来てくれてありがとう！😊")


@client.event
async def on_userleave(message):
    uid = message[3].get("args", [])[0]
    print(f"退室: {uid}さん")


@client.event
async def on_gamestart(message):
    # print("ゲーム開始:", message)
    args = message[3].get("args", [])
    uid_list = args[0]
    users = []
    for uid in uid_list:
        user = await client.get_user_by_uid(uid)
        if user:
            users.append(user)
    user_list = [u["userName"] for u in users if u]
    print(f"ゲーム開始 参加ユーザー: {', '.join(user_list)}")


@client.event
async def on_subject(message):
    # print("お題:", message)
    args = message[3].get("args", [])
    context = args[0]
    print(f"お題: {context}")
    await client.send_pass()


@client.event
async def on_sysmessage(message):
    # print("システムメッセージ:", message)
    args = message[3].get("args", [])
    context = args[0]
    print(f"システムメッセージ: {context}")


@client.event
async def on_clear(message):
    # print("クリア:", message)
    args = message[3].get("args", [])
    user = await client.get_user_by_uid(args[0])
    name = user["userName"]
    print(f"クリア: {name}さん")


@client.event
async def on_stroke(message):
    # print("描画:", message)
    args = message[3].get("args", [])
    uid = args[0]
    size = args[1]
    color = args[2]
    opacity = args[3]
    path = args[4]
    user = await client.get_user_by_uid(uid)
    name = user["userName"]
    hooked_path = [[x + 50, y] for x, y in path]
    print(f"描画: {name}さん")
    await client.send_stroke(size, color, opacity, hooked_path)


@client.event
async def on_error(error):
    print("エラー発生:", error)


@client.event
async def on_question(message):
    # print("問題:", message)
    await client.solve_question_bruteforce(message)


@client.event
async def on_hint(message):
    # print("ヒント:", message)
    pass


@client.event
async def on_chat(message):
    # print("チャット:", message)

    args = message[3].get("args", [])
    user = await client.get_user_by_uid(args[0])
    name = user["userName"]
    context = args[1]

    print(f"チャット: {name}さん {context}")

    await client.on_command(message, "/help", command_help)
    await client.on_command(message, "/chat", command_chat)
    await client.on_command(message, "/game", command_game)
    await client.on_command(message, "/draw", command_draw)


async def command_draw(*args):
    if len(args) < 4:
        await client.send_chat("使い方: /draw <text> <x> <y> <size>")
        return

    text = args[0]

    try:
        x = float(args[1])
        y = float(args[2])
        size = float(args[3])
    except (ValueError, TypeError):
        await client.send_chat("x, y, size は数字で指定してください。")
        return

    asyncio.create_task(client.draw_text(text, x, y, size))


async def command_help(*args):
    help_text = "/help | /chat | /game | /draw"
    await client.send_chat(help_text)


async def command_chat(*args):
    if not args or not args[0]:
        await client.send_chat("使い方: /chat <text>")
        return
    await client.send_chat(args[0])


async def command_game(*args):
    await client.send_game()


if __name__ == "__main__":
    client.run()
