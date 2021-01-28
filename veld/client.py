from dateutil import parser
import asyncio
import aiohttp
import time



class Embed:
    def __init__(self, title:str=None, description:str=None, footer:str=None, color:int=None, colour:int=None, image_url:str=None, thumbnail_url:str=None):
        self.title = title
        self.description = description
        self.footer = footer
        self.colour = self.color = color or colour
        self.image_url = image_url
        self.thumbnail_url = thumbnail_url
        self.author = {
            "icon_url": None,
            "name": None,
        }

    @classmethod
    def from_json(cls, data: dict):
        return Embed(
            title = data.get("title"),
            description = data.get("description"),
            footer = data.get("footer"),
            color = data.get("color"),
            image_url = data.get("imageUrl"),
            thumbnail_url = data.get("thumbnailUrl")
        )

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return f'<Embed title="{self.title}" description="{self.description}">'

    def set_author(self, name, icon_url):
        self.author["name"] = name
        self.author["icon_url"] = icon_url
        return self

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "footer": self.footer,
            "color": self.color or self.colour,
            "imageUrl": self.image_url,
            "thumbnailUrl": self.thumbnail_url,
            "author" : self.author
        }



class User:
    def __init__(self, id, name, avatar_url, bot, badges, online=None, status=None):
        self.id = id
        self.name = name
        if avatar_url:
            self.avatar_url = f"https://cdn.miki.bot/chat/avatars/{avatar_url}.png"
        else:
            self.avatar_url = f"https://cdn.miki.bot/chat/avatars/{self.id%5}.png"
        self.bot = bot
        self.badges = badges
        self.online = online # true, false, none for unknown
        self.status = status

    @classmethod
    def from_json(cls, data):
        return User(
            int(data["id"]),
            data["name"],
            data["avatarUrl"],
            (data["badges"] & 1<<2) == 1<<2,
            data["badges"]
        )
    
    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<User id={self.id} name="{self.name}" online={self.online}>'

    def __eq__(self, other) -> bool:
        if isinstance(other, User):
            if self.id == other.id:
                return True
        return False



class Message:
    def __init__(self, id, content, embed, created_at, channel, author):
        self.id = id
        self.content = content or ""
        self.embed = embed
        self.created_at = created_at
        self.channel = channel
        self.author = author

    @classmethod
    def from_json(cls, client, data):
        author = client.get_user(int(data["author"]["id"]))
        channel = client.get_channel(int(data["channelId"]))
        embed = Embed.from_json(data["embed"]) if data["embed"] else None
        return Message(
            int(data["id"]),
            data["content"],
            embed,
            parser.parse(data["timestamp"]),
            channel,
            author
        )

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return f'<Message id={self.id} author={repr(self.author)} channel={repr(self.channel)}>'



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
        return f'<Channel id={self.id} name="{self.name}">'

    async def send(self, content: str = None, embed: Embed = None) -> Message:
        embed = None if embed is None else embed.to_dict()
        
        async with self.client.session.post(
            f"https://api.veld.chat/channels/{self.id}/messages",
            json = {"content": content, "embed": embed},
            headers = {"authorization": f"Bearer {self.client.token}"}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
            else:
                raise Exception("Unable to post message")
        
        return Message.from_json(self.client, data)



class VeldChatClient:
    def __init__(self, token: str, max_messages: int = 500):
        self.token = token
        self.session = None
        self.ping = None
        self.user = None
        self._channels = {}
        self._users = {}
        self.events = {}
        self.cached_messages = []
        self.max_messages = max(max_messages, 0)


    def run(self):
        self.start_time = time.time()
        asyncio.run(self.ws_events())
    

    async def heartbeat(self):
        while 1:
            await asyncio.sleep(15)
            self._ping_counter = time.time()
            await self.ws.ping()


    async def ws_events(self):
        self.session = aiohttp.ClientSession()
        async with self.session.ws_connect("wss://api.veld.chat", autoping=False) as ws:
            self.ws = ws
            self._ping_counter = time.time()
            await ws.send_json({
                "t": 0,
                "d": {
                    "token": self.token
                }
            })

            asyncio.create_task(self.heartbeat())

            msg = await ws.receive()
            self.ping = int((time.time() - self._ping_counter)*1000)
            data = msg.json()
            self.user = User.from_json(data["d"]["user"])
            self.user.online = True
            self._channels = {int(c["id"]): Channel.from_json(self, c) for c in data["d"]["channels"]}
            self._users = {int(u["id"]): User.from_json(u) for u in data["d"]["users"]}
            self._users[self.user.id] = self.user
            for u in self.users:
                u.online = True

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.PONG:
                    self.ping = int((time.time() - self._ping_counter)*1000)
                    continue

                elif msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    if data["t"] == 12:
                        await self.on_raw_user_update(data["d"]["user"], data["d"]["statusText"], data["d"]["statusType"])
                    elif data["t"] == 2:
                        await self.on_raw_message(data["d"])
                    elif data["t"] == 8:
                        await self.on_raw_user_update(data["d"])
                    else:
                        print(f'NEW T: {data["t"]}')
                    

    def event(self):
        def registerhandler(handler):
            self.events[handler.__name__] = handler
            return handler
        return registerhandler


    async def on_raw_user_update(self, data, status_text=None, status_type=None):
        if data is None:
            return
        old_user = self._users.get(int(data["id"]))
        new_user = User.from_json(data)

        if status_type is not None:
            new_user.online = not bool(status_type)
        elif old_user is not None:
            new_user.online = old_user.online

        if status_text is not None:
            new_user.status = status_text
        elif old_user is not None:
            new_user.status = old_user.status

        self._users[new_user.id] = new_user

        if "on_user_update" in self.events:
            await self.events["on_user_update"](old_user, new_user)


    async def on_raw_message(self, data):
        message = Message.from_json(self, data)
        self.cached_messages.append(message)
        if len(self.cached_messages) > self.max_messages:
            del self.cached_messages[0]
        if "on_message" in self.events:
            await self.events["on_message"](message)


    @property
    def users(self) -> list:
        return self._users.values()

    
    def get_user(self, user_id: int):
        return self._users.get(user_id)


    @property
    def channels(self) -> list:
        return self._channels.values()

    
    def get_channel(self, channel_id: int):
        return self._channels.get(channel_id)


    @property
    def up_time(self) -> int:
        return int(time.time()-self.start_time)






