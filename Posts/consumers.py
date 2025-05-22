
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .serializers import PostSerializer
from .models import Post

class PostConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("posts", self.channel_name)
        await self.accept()
        print("✅ WebSocket connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("posts", self.channel_name)
        print("❌ WebSocket disconnected")

    async def receive_json(self, content):
        print("📩 Received from client:", content)

    async def post_update(self, event):
        print("[WS][CONSUMER] post_update event:", event)
        await self.send_json({
            "type": "post_update",   # 👈 aici!
            "data": event["data"]
        })
        
    async def post_create(self, event):
        print("[WS][CONSUMER] post_create event:", event)
        await self.send_json({
            "type": "post_create",   # 👈 aici!
            "data": event["data"]
        })

    async def post_delete(self, event):
        print("[WS][CONSUMER] post_delete event:", event)
        await self.send_json({
            "type": "post_delete",
            "data": event["data"]
        })