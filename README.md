# Veld.py
veld.chat is an up and coming next-gen totally cool social platform and I decided to make a client so bots can use it!

### How to install
`pip install git+https://github.com/14ROVI/veld.py`

### Example
```py
import veld


veld = veld.VeldChatClient("TOKEN")


@veld.event()
async def on_message(message):
    args = message.content.split()
    if message.content.startswith("?"):
        if args[0] == "?say":
            await message.channel.send(" ".join(args[1:]))
        elif args[0] == "?ping":
            await message.channel.send(f"You want my ping??? Here it is then: `{veld.ping}ms`")
        elif args[0] == "?users":
            users = "`\n`".join([repr(veld.users[u_id]) for u_id in veld.users])
            await message.channel.send(f"`{users}`")

@veld.event()
async def on_user_update(old, new):
    print(f"{repr(old)} -> {repr(new)}")


veld.run()```

