# Veld.py
veld.chat is an up and coming next-gen totally cool social platform and I decided to make a client so bots can use it!

### How to install
`pip install git+https://github.com/14ROVI/veld.py`

### Example
```py
import veld


client = veld.VeldChatClient("TOKEN")


@client.event()
async def on_message(message):
    args = message.content.split()
    if message.content.startswith("?"):
        if args[0] == "?say":
            await message.channel.send(" ".join(args[1:]))
        elif args[0] == "?ping":
            await message.channel.send(f"You want my ping??? Here it is then: `{client.ping}ms`")
        elif args[0] == "?users":
            users = "`\n`".join([repr(client.users[u_id]) for u_id in client.users])
            await message.channel.send(f"`{users}`")

@client.event()
async def on_user_update(old, new):
    print(f"{repr(old)} -> {repr(new)}")


client.run()```

