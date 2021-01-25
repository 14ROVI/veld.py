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
    if message.content.startswith("?"):
        args = message.content.split()
        
        if args[0] == "?say":
            await message.channel.send(
                embed = Embed(
                        title = f"{message.author} told me to say:",
                        description = " ".join(args[1:]),
                        footer = "I am not liable for what they said!"
                    )
            )
            
        elif args[0] == "?ping":
            await message.channel.send(f"You want my ping??? Here it is then: `{client.ping}ms`")
            
        elif args[0] == "?users":
            users = "`\n`".join([repr(u) for u in client.users])
            await message.channel.send(f"`{users}`")
           
           
@client.event()
async def on_user_update(old, new):
    print(f"{repr(old)} -> {repr(new)}")


client.run()```

