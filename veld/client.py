from dateutil import parser
import asyncio
import aiohttp
import time



class User:
    def __init__(self, id, name, avatar_url, bot, badges):
        self.id = id
        self.name = name
        self.avatar_url = avatar_url
        self.bot = bot
        self.badges = badges

    @classmethod
    def from_json(cls, data):
        return User(
            int(data["id"]),
            data["name"],
            data["avatarUrl"],
            data["isBot"],
            data["badges"]
        )
    
    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<User id = {self.id}, name = "{self.name}">'



class Channel:
    def __init__(self, client, id, name, type, members, messages):
        self.client = client
        self.id = id
        self.name = name
        self.type = type
        self.members = members
        self.messages = messages

    @classmethod
    def from_json(cls, client, data):
        return Channel(
            client,
            int(data["id"]),
            data["name"],
            data["type"],
            data["members"],
            data["messages"]
        )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Channel id = {self.id}, name = "{self.name}">'

    async def send(self, content):
        await self.client.session.post(
            f"https://api.veld.chat/channels/{self.id}/messages",
            json = {"content": content},
            headers = {"authorization": f"Bearer {self.client.token}"}
        )



class Message:
    def __init__(self, id, content, embed, created_at, channel, author):
        self.id = id
        self.content = content
        self.embed = embed
        self.created_at = created_at
        self.channel = channel
        self.author = author

    @classmethod
    def from_json(cls, client, data):
        author = client.users.get(int(data["author"]["id"]))
        channel = client.channels.get(int(data["channelId"]))
        return Message(
            int(data["id"]),
            data["content"],
            data["embed"],
            parser.parse(data["timestamp"]),
            channel,
            author
        )

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return f'<Message id = {self.id}, author = "{self.author.name}", channel = "{self.channel.name}">'



class VeldChatClient:
    def __init__(self, token: str):
        self.token = token
        self.session = None
        self.ping = None
        self.user = None
        self.channels = {}
        self.users = {}
        self.events = {}


    def run(self):
        asyncio.run(self.ws_events())
    

    async def heartbeat(self):
        while 1:
            await asyncio.sleep(15)
            self.ping = time.time()
            await self.ws.ping()


    async def ws_events(self):
        self.session = aiohttp.ClientSession()
        async with self.session.ws_connect("wss://api.veld.chat", autoping=False) as ws:
            self.ws = ws
            self.ping = time.time()
            await ws.send_json({
                "t": 0,
                "d": {
                    "token": self.token,
                    "bot": True
                }
            })

            asyncio.create_task(self.heartbeat())

            msg = await ws.receive()
            self.ping = int((time.time() - self.ping)*1000)
            data = msg.json()
            self.user = User.from_json(data["d"]["user"])
            self.channels = {int(c["id"]): Channel.from_json(self, c) for c in data["d"]["channels"]}
            self.users = {int(u["id"]): User.from_json(u) for u in data["d"]["users"]}
            self.users[self.user.id] = self.user

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.PONG:
                    self.ping = int((time.time() - self.ping)*1000)
                    continue

                elif msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    if data["t"] == 12:
                        await self.on_raw_user_update(data["d"]["user"])
                    elif data["t"] == 2:
                        await self.on_raw_message(data["d"])
                    elif data["t"] == 8:
                        await self.on_raw_user_update(data["d"])
                    else:
                        print(data)
                    

    def event(self):
        def registerhandler(handler):
            self.events[handler.__name__] = handler
            return handler
        return registerhandler


    async def on_raw_user_update(self, data):
        old_user = self.users.get(int(data["id"]))
        new_user = User.from_json(data)
        self.users[new_user.id] = new_user

        if "on_user_update" in self.events:
            await self.events["on_user_update"](old_user, new_user)


    async def on_raw_message(self, data):
        message = Message.from_json(self, data)
        if "on_message" in self.events:
            await self.events["on_message"](message)