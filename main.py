from client import Pictsense

client = Pictsense()


@client.event
async def on_ready():
    print("Bot起動成功")
    room = await client.lobby.create_room()
    await client.room.connect(room)

if __name__ == "__main__":
    client.run()
