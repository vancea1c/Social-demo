from channels.generic.websocket import AsyncJsonWebsocketConsumer

class PostConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            # no ticket? no entry.
            return await self.close()

        await self.accept()
        # everyone joins the “posts_broadcast” party…
        await self.channel_layer.group_add("posts_broadcast", self.channel_name)
        # …and their own personal “posts_user_<id>” room
        await self.channel_layer.group_add(f"posts_user_{user.id}", self.channel_name)
        print(f"✅ WS connected for {user.username}")

    async def disconnect(self, close_code):
        user = self.scope["user"]
        await self.channel_layer.group_discard("posts_broadcast", self.channel_name)
        await self.channel_layer.group_discard(f"posts_user_{user.id}", self.channel_name)
        print(f"❌ WS disconnected for {user.username}")

    # (optional) handle messages *from* the client
    async def receive_json(self, content):
        print("📩 Received from client:", content)

    # When Python calls group_send(type="post_update"), we forward it down the socket:
    async def post_update(self, event):
        print("[WS][CONSUMER] post_update event:", event)
        await self.send_json(event)
        
    async def post_user_update(self, event):
        print("[WS][CONSUMER] post_user_update event:", event)
        await self.send_json(event)

    async def post_create(self, event):
        print("[WS][CONSUMER] post_create event:", event)
        await self.send_json(event)

    async def post_delete(self, event):
        print("[WS][CONSUMER] post_delete event:", event)
        await self.send_json(event)
